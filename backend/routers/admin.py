# xiangmu/backend/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import traceback

import models
from database import get_db
from schemas import UserCreate, ProjectCreate, WorkPackageCreate, ScoreRuleUpdate, LevelDefsUpdate, UserUpdate
from utils import work_package_summary, ensure_default_work_item

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Management"])
# 兼容前端历史路径：deleteUserApi 实际请求 DELETE /api/v1/users/{id}
legacy_router = APIRouter(prefix="/api/v1", tags=["Legacy Compat"])


# ---------------------------------------------------------------- 用户
@router.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return {"code": 200, "data": [
        {"id": u.id, "username": u.username, "role": u.role, "job_grade": u.job_grade} for u in users
    ]}


@router.post("/users")
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    user_id = (user_in.id or "").strip()
    if not user_id or not (user_in.username or "").strip():
        raise HTTPException(status_code=400, detail="工号和姓名不能为空")

    if db.query(models.User).filter(models.User.id == user_id).first():
        raise HTTPException(status_code=400, detail="工号已存在！")

    try:
        new_user = models.User(
            id=user_id,
            username=user_in.username.strip(),
            password=user_in.password or "123456",
            role=(user_in.role or "EMPLOYEE").upper(),
            job_grade=user_in.job_grade
        )
        db.add(new_user)
        db.commit()
        return {"code": 200, "message": "添加用户成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"数据库写入异常: {str(e)}")

@router.put("/users/{userId}")
def update_user(userId: str, data: UserUpdate, db:Session = Depends(get_db)):
    updater = db.query(models.User).filter(models.User.id == data.updated_by_id).first()
    role = (updater.role).upper()
    if role != "ADMIN":
        raise HTTPException(status_code=404, detail="只有管理员可以修改人员信息")
    
    user = db.query(models.User).filter(models.User.id == userId).first()
    if not user:
        raise HTTPException(status_code=400, detail="数据库中没有这个人")

    user.username = data.username or user.username
    user.role = data.role or user.role
    user.job_grade = data.job_grade or user.job_grade
    db.commit()
    return{"code":200,
           "message":"人员信息已更新"
           }

@router.delete("/users/{userId}")
def delete_user(userId: str, db:Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == userId).first()
    if not user:
        raise HTTPException(status_code=400, detail="数据库中没有这个人")

    project = db.query(models.Project).filter(models.Project.owner_id == userId).all()
    wp = db.query(models.WorkPackage).filter(models.WorkPackage.owner_id == userId).all()

    if (project and project.complete_status) or (wp and wp.complete_status):
        raise HTTPException(status_code=402, detail="该员工有未完成的工作")
        
    db.delete(user)
    db.commit()
    return {"code": 200, "message": "删除用户成功"}


# ---------------------------------------------------------------- 项目
@router.get("/projects")
def get_all_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    res = []
    for project in projects:
        res.append({
            "id": project.id,
            "name": project.name,
            "code": project.code,
            "owner_id": project.owner_id or "-",
            "owner_name": project.owner.username if project.owner else "未指定负责人",
            "level": project.level or "",
        })
    return {"code": 200, "data": res}


@router.post("/projects")
def create_or_update_project(project_in: ProjectCreate, db: Session = Depends(get_db)):
    project_name = (project_in.name or "").strip()
    if not project_name:
        raise HTTPException(status_code=400, detail="项目名称不能为空！")

    try:
        if project_in.id:
            project = db.query(models.Project).filter(
                models.Project.id == project_in.id
            ).first()
            if not project:
                raise HTTPException(status_code=404, detail="项目不存在")
            if project.complete_status:
                raise HTTPException(status_code=400, detail="项目已完成，不能修改")
            project.name = project_name
            project.code = project_in.code
            project.owner_id = project_in.owner_id or None
            project.category = project_in.category or "-"
            project.level = project_in.level or "-"
        else:
            project = models.Project(
                name=project_name,
                code=project_in.code,
                owner_id=project_in.owner_id or None,
                category=project_in.category or "-",
                level=project_in.level or "-"
            )
            db.add(project)

        db.commit()
        db.refresh(project)
        return {"code": 200, 
                "message": "项目配置成功", 
                "data": {"id": project.id, 
                         "name": project.name}}
    except Exception as e:
        db.rollback()
        print("❌ 保存项目报错详情:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"保存项目失败: {str(e)}")


# ---------------------------------------------------------------- 工作包
def _work_package_view(pkg):
    """构造工作包视图：聚合分值/节点，附带负责人与指派信息。"""
    score, deadline = work_package_summary(pkg)
    project = pkg.project
    owner = pkg.owner
    owner_id = pkg.owner_id or ""
    owner_name = owner.username if owner else ""
    return {
        "id": pkg.id,
        "name": pkg.name,
        "project_id": pkg.project_id,
        "project_name": project.name if project else "-",
        "category_name": pkg.category_name or "-",
        "score": score,
        "deadline": deadline or "-",
        "owner_id": owner_id,
        "owner_name": owner_name,
    }


@router.post("/work-packages")
def create_or_update_work_package(pkg_in: WorkPackageCreate, db: Session = Depends(get_db)):
    if pkg_in.category_name not in models.FIXED_WORK_CATEGORIES:
        raise HTTPException(status_code=400, detail="工作类型只能选择：类型1、类型2、类型3、类型4")

    # 确定所属项目：优先用 project_id，其次按 project_name 反查
    project = None
    if pkg_in.project_id:
        project = db.query(models.Project).filter(
            models.Project.id == pkg_in.project_id
        ).first()
    if not project and pkg_in.project_name:
        project = db.query(models.Project).filter(
            models.Project.name == pkg_in.project_name.strip()
        ).first()
    if not project:
        raise HTTPException(status_code=400, detail="所属项目不存在，请先选择正确的项目")

    try:
        if pkg_in.work_package_id:
            pkg = db.query(models.WorkPackage).filter(
                models.WorkPackage.id == pkg_in.work_package_id
            ).first()
            if not pkg:
                raise HTTPException(status_code=404, detail="未找到要修改的工作包")
            if pkg.complete_status:
                raise HTTPException(status_code=400, detail="工作包已完成，不能修改")

            pkg.project_id = project.id
            pkg.category_name = pkg_in.category_name
            new_owner = pkg_in.owner_id
            pkg.owner_id = new_owner or None
            pkg.next_step_work = (pkg_in.next_step_work or "").strip()
            pkg.objective = (pkg_in.objective or "").strip()
            message = "工作包更新成功"
        else:
            # 自动生成工作包 ID（项目下递增序号）
            existing_count = db.query(models.WorkPackage).filter(
                models.WorkPackage.project_id == project.id
            ).count()
            pkg = models.WorkPackage(
                id=f"P{project.id}-WP{existing_count + 1:02d}",
                project_id=project.id,
                category_name=pkg_in.category_name,
                owner_id=pkg_in.owner_id or None,
                next_step_work=pkg_in.next_step_work or "",
                objective=pkg_in.objective or ""
            )
            db.add(pkg)
            message = "工作包创建成功"

        db.flush()  # 先落库拿到 pkg.id，供关系使用
        # 把前端传的 分值/节点 保存到默认工作项
        ensure_default_work_item(db, pkg)
        db.commit()
        db.refresh(pkg)
        return {"code": 200, "message": message, "data": {"id": pkg.id}}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print("❌ 保存工作包报错详情:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"保存工作包失败: {str(e)}")


@router.get("/work-packages-overview")
def get_work_packages_overview(db: Session = Depends(get_db)):
    try:
        packages = db.query(models.WorkPackage).all()
        res = [_work_package_view(pkg) for pkg in packages]
        return {"code": 200, "data": res}
    except Exception as e:
        print("❌ work-packages-overview 接口报错详情:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"查询工作包概览失败: {str(e)}")


# ---------------------------------------------------------------- 计算得分：评分维度与档位
@router.get("/computed-score-dimensions")
def get_computed_score_dimensions(db: Session = Depends(get_db)):
    """返回计算得分所需的评分维度及各档位系数（变量固定为工作项的难度/创新度/重要度）。"""
    variable = {
        "difficulty": "难度",
        "innovation": "创新度",
        "importance": "重要度",
    }
    levels = db.query(models.ScoreDimensionLevel).order_by(models.ScoreDimensionLevel.id).all()

    levels_by_dim = {}
    for lv in levels:
        levels_by_dim.setdefault(lv.variable, []).append({
            "job_grade": lv.job_grade or "",
            "level": lv.level,
            "factor": round(lv.factor or 0.0, 3)
        })

    data = [{
        "variable": key,
        "name": variable.get(key, key),
        "levels": levels_by_dim.get(key, []),
    } for key in ["difficulty", "innovation", "importance"]]

    return {"code": 200, "data": data}


@router.put("/computed-score-dimensions")
def put_computed_score_dimensions(body: ScoreRuleUpdate, db: Session = Depends(get_db)):
    """管理员保存各维度档位系数（仅 ADMIN 可操作，不再有权重）。"""
    user = db.query(models.User).filter(models.User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if str(user.role).upper() != "ADMIN":
        raise HTTPException(status_code=403, detail="仅管理员可以配置评分规则")

    for item in body.items:
        for lv in item.levels:
            rec = db.query(models.ScoreDimensionLevel).filter(
                models.ScoreDimensionLevel.variable == item.variable,
                models.ScoreDimensionLevel.job_grade == (lv.job_grade or ""),
                models.ScoreDimensionLevel.level == lv.level
            ).first()
            if rec:
                rec.factor = round(float(lv.factor or 0.0), 3)
    db.commit()
    return {"code": 200, "message": "评分规则已保存"}


# ---------------------------------------------------------------- 档位字典表（职级/难度/重要度/创新度 档位定义）
def rebuild_score_matrix(db, job_grades, difficulty_levels, importance_levels, innovation_levels):
    """按档位定义重建系数矩阵，保留已有系数（新增档位默认 0）。"""
    old = {}
    for row in db.query(models.ScoreDimensionLevel).all():
        old[(row.variable, row.job_grade or "", row.level)] = row.factor or 0
    db.query(models.ScoreDimensionLevel).delete()
    for g in job_grades:
        for lv in difficulty_levels:
            db.add(models.ScoreDimensionLevel(variable="difficulty", job_grade=g, level=lv,
                                              factor=old.get(("difficulty", g, lv), 0)))
        for lv in importance_levels:
            db.add(models.ScoreDimensionLevel(variable="importance", job_grade=g, level=lv,
                                              factor=old.get(("importance", g, lv), 0)))
    for lv in innovation_levels:
        db.add(models.ScoreDimensionLevel(variable="innovation", job_grade="", level=lv,
                                          factor=old.get(("innovation", "", lv), 0)))


@router.get("/level-defs")
def get_level_defs(db: Session = Depends(get_db)):
    """返回职级、难度、重要度、创新度的档位定义。"""
    rows = db.query(models.ScoreLevelDef).order_by(models.ScoreLevelDef.category, models.ScoreLevelDef.sort_order).all()
    result = {"job_grade": [], "difficulty": [], "importance": [], "innovation": []}
    for r in rows:
        if r.category in result:
            result[r.category].append(r.name)
    return {"code": 200, "data": result}


@router.put("/level-defs")
def put_level_defs(body: LevelDefsUpdate, db: Session = Depends(get_db)):
    """管理员维护档位定义并重建系数矩阵（仅 ADMIN）。"""
    user = db.query(models.User).filter(models.User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if str(user.role).upper() != "ADMIN":
        raise HTTPException(status_code=403, detail="仅管理员可以维护档位定义")

    def clean(items):
        seen = []
        for x in items or []:
            x = (x or "").strip()
            if x and x not in seen:
                seen.append(x)
        return seen

    job_grades = clean(body.job_grade)
    difficulty_levels = clean(body.difficulty)
    importance_levels = clean(body.importance)
    innovation_levels = clean(body.innovation)
    if not job_grades or not difficulty_levels or not importance_levels or not innovation_levels:
        raise HTTPException(status_code=400, detail="职级、难度、重要度、创新度档位都不能为空")

    # 1) 重写档位字典表
    db.query(models.ScoreLevelDef).delete()
    for cat, names in [("job_grade", job_grades), ("difficulty", difficulty_levels),
                       ("importance", importance_levels), ("innovation", innovation_levels)]:
        for i, name in enumerate(names):
            db.add(models.ScoreLevelDef(category=cat, name=name, sort_order=i, is_active=1))

    # 2) 重建系数矩阵（保留已有 factor）
    rebuild_score_matrix(db, job_grades, difficulty_levels, importance_levels, innovation_levels)
    db.commit()
    return {"code": 200, "message": "档位定义已保存并重建系数矩阵", "data": {
        "job_grade": job_grades, "difficulty": difficulty_levels,
        "importance": importance_levels, "innovation": innovation_levels}}