# xiangmu/backend/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
import traceback

import models
from database import get_db
from schemas import UserCreate, ProjectCreate, WorkPackageCreate, ScoreRuleUpdate, LevelDefsUpdate, UserUpdate
from datetime import datetime
from utils import (ensure_open, effective_complete,
                   package_effective_complete, project_effective_complete)
from services.score_board_service import compute_calc_score, monthly_quality_score

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Management"])


# ---------------------------------------------------------------- 用户
@router.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).filter(models.User.is_deleted == False).all()
    return {"code": 200, "data": [
        {"id": u.id, "username": u.username, "role": u.role, "job_grade": u.job_grade, "password": u.password, "department": u.department} 
        for u in users]}


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
            job_grade=user_in.job_grade,
            department=user_in.department.strip() or None
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

    old_grade = user.job_grade
    user.username = data.username or user.username
    user.role = data.role or user.role
    user.job_grade = data.job_grade or old_grade
    user.department = data.department.strip() or None
    grade_changed = (user.job_grade or "") != (old_grade or "")

    # 职级变化 → 重算该人员作为“工作项负责人”的【当月】已填月度分值计算得分
    # （难度/重要度系数按工作项负责人职级查；历史月份保持原快照不动）
    if grade_changed:
        this_month = datetime.now().strftime("%Y-%m")
        rows = (db.query(models.WorkItemMonthlyScore)
                .join(models.WorkItem, models.WorkItem.id == models.WorkItemMonthlyScore.work_item_id)
                .filter(models.WorkItem.owner_id == user.id,
                        models.WorkItemMonthlyScore.month == this_month)
                .all())
        for rec in rows:
            item = rec.work_item
            if not item:
                continue
            q = monthly_quality_score(db, rec.work_item_id, rec.month)
            rec.calculate_score = compute_calc_score(rec.score or 0.0, item, db,
                                                     user.job_grade or "", q)

    db.commit()
    return{"code":200,
           "message":"人员信息已更新" + ("，当月计算得分已按新职级重算" if grade_changed else "")
           }

@router.delete("/users/{userId}")
def delete_user(userId: str, currentUserId: str, db:Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == userId, models.User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=400, detail="数据库中没有这个人")

    project = db.query(models.Project).options(
        selectinload(models.Project.work_packages).selectinload(
            models.WorkPackage.work_items
        ).selectinload(models.WorkItem.monthly_scores),
    ).filter(models.Project.owner_id == userId).all()
    wp = db.query(models.WorkPackage).options(
        selectinload(models.WorkPackage.work_items).selectinload(models.WorkItem.monthly_scores),
    ).filter(models.WorkPackage.owner_id == userId).all()
    item = db.query(models.WorkItem).options(
        selectinload(models.WorkItem.monthly_scores),
    ).filter(models.WorkItem.owner_id == userId).all()

    # 完成判定采用合成口径：手动确认完成，或进度已满（含满分 0）
    has_uncompleted_project = any(not project_effective_complete(p) for p in project)
    has_uncompleted_wp = any(not package_effective_complete(w) for w in wp)
    has_uncompleted_item = any(not effective_complete(i) for i in item)

    if has_uncompleted_project or has_uncompleted_wp or has_uncompleted_item:
        raise HTTPException(status_code=402, detail="该员工有未完成的工作")

    user.is_deleted = True
    user.deleted_at = datetime.now()
    user.deleted_by = currentUserId  # 记录谁删除的
    # db.delete(user)
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
            "tech_owner_id": project.tech_owner_id or "-",
            "tech_owner_name": project.tech_owner.username if project.tech_owner else "未指定机型主管",
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
            ensure_open(project)  # 已关闭的项目不能再编辑
            project.name = project_in.name
            project.code = project_in.code
            project.owner_id = project_in.owner_id or None
            project.tech_owner_id = project_in.tech_owner_id or None
            project.category = project_in.category or "-"
            project.level = project_in.level or "-"
        else:
            project = models.Project(
                name=project_name,
                code=project_in.code,
                owner_id=project_in.owner_id or None,
                tech_owner_id=project_in.tech_owner_id or None,
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


@router.delete("/projects/{project_id}")
def delete_project(project_id: int, user_id: str, db: Session = Depends(get_db)):
    """删除项目"""
    project = db.query(models.Project).options(
        selectinload(models.Project.work_packages).selectinload(
            models.WorkPackage.work_items
        ).selectinload(models.WorkItem.monthly_scores),
    ).filter(models.Project.id == project_id).first()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    if not user:
        raise HTTPException(status_code=404, detail=f"查不到对应的用户 (接收到的 user_id: {user_id})")
    if user.role not in ["LEADER", "DEPARTMENT", "ADMIN"] and (not project or project.owner_id != user.id):
        raise HTTPException(status_code=405, detail="只有项目负责人和部门领导、科室主任、管理员可以删除项目")
    if project_effective_complete(project):
        raise HTTPException(status_code=400, detail="项目已完成，不能删除")
    if project.isclosed:
        raise HTTPException(status_code=403, detail="项目已关闭，不能删除")

    db.delete(project)  
    db.commit()
    return {"code": 200, "message": "项目删除成功"}


# ---------------------------------------------------------------- 工作包

@router.get("/work-categories")
def get_work_categories(db: Session = Depends(get_db)):
    """返回工作包类别（来自 work_project_categories 表，随数据库变化）。"""
    cats = db.query(models.WorkPackageCategory.name).order_by(models.WorkPackageCategory.name).all()
    return {"code": 200, "data": [c[0] for c in cats]}


@router.post("/work-packages")
def create_or_update_work_package(pkg_in: WorkPackageCreate, db: Session = Depends(get_db)):
    valid_cats = {c[0] for c in db.query(models.WorkPackageCategory.name).all()}
    if not valid_cats or pkg_in.category_name not in valid_cats:
        raise HTTPException(status_code=400, detail="工作类型只能从已有类别中选择")

    work_package_code = (pkg_in.work_package_code or "").strip()
    if not work_package_code:
        raise HTTPException(status_code=400, detail="工作包编号不能为空")

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
    ensure_open(project)  # 已关闭的项目不能再新增/修改工作包

    try:
        if pkg_in.id:
            pkg = db.query(models.WorkPackage).filter(
                models.WorkPackage.id == pkg_in.id
            ).first()
            if not pkg:
                raise HTTPException(status_code=404, detail="未找到要修改的工作包")
            ensure_open(pkg)  # 已关闭的工作包不能再编辑

            pkg.project_id = project.id
            pkg.code = pkg_in.work_package_code
            pkg.category_name = pkg_in.category_name
            new_owner = pkg_in.owner_id
            pkg.owner_id = new_owner or None
            new_tech_owner = pkg_in.tech_owner_id
            pkg.tech_owner_id = new_tech_owner or None
            pkg.objective = (pkg_in.objective or "").strip()
            pkg.name = (pkg_in.name or "-").strip()
            message = "工作包更新成功"
        else:
            pkg = models.WorkPackage(
                code=work_package_code,
                project_id=project.id,
                category_name=pkg_in.category_name,
                owner_id=pkg_in.owner_id or None,
                tech_owner_id=pkg_in.tech_owner_id or None,
                objective=pkg_in.objective or "",
                name=pkg_in.name or "-"
            )
            db.add(pkg)
            message = "工作包创建成功"

        db.flush()  # 先落库拿到 pkg.id，供关系使用
        # 把前端传的 分值/节点 保存到默认工作项
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


@router.delete("/work-packages/{work_package_id}")
def delete_work_package(work_package_id: int, user_id: str, db: Session = Depends(get_db)):
    """删除工作包"""
    work_package = db.query(models.WorkPackage).options(
        selectinload(models.WorkPackage.work_items).selectinload(models.WorkItem.monthly_scores),
    ).filter(models.WorkPackage.id == work_package_id).first()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not work_package:
        raise HTTPException(status_code=404, detail="工作包不存在")
    if not user:
        raise HTTPException(status_code=404, detail=f"查不到对应的用户 (接收到的 user_id: {user_id})")
    if user.role not in ["LEADER", "DEPARTMENT", "ADMIN"] and (not work_package or work_package.owner_id != user.id):
        raise HTTPException(status_code=405, detail="只有改工作包负责人和部门领导、科室主任、管理员可以删除项目")
    if package_effective_complete(work_package):
        raise HTTPException(status_code=400, detail="工作包已完成，不能删除")
    if work_package.isclosed or (work_package.project and work_package.project.isclosed):
        raise HTTPException(status_code=403, detail="工作包或所属项目已关闭，不能删除")

    db.delete(work_package)
    db.commit()
    return {"code": 200, "message": "工作包删除成功"}

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

    # 系数更新后，只重算【当月】已填月度分值的计算得分（历史月份保持原快照不动）
    this_month = datetime.now().strftime("%Y-%m")
    for rec in db.query(models.WorkItemMonthlyScore).filter(
            models.WorkItemMonthlyScore.month == this_month).all():
        item = rec.work_item
        if not item:
            continue
        owner_job_grade = item.owner.job_grade if (item and item.owner) else ""
        q = monthly_quality_score(db, rec.work_item_id, rec.month)
        rec.calculate_score = compute_calc_score(rec.score, item, db, owner_job_grade, q)

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
