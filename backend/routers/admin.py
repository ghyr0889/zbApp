# xiangmu/backend/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import traceback

import models
from database import get_db
from schemas import UserCreate, ProjectCreate, WorkPackageCreate
from utils import work_package_summary, ensure_default_work_item

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Management"])
# 兼容前端历史路径：deleteUserApi 实际请求 DELETE /api/v1/users/{id}
legacy_router = APIRouter(prefix="/api/v1", tags=["Legacy Compat"])


# ---------------------------------------------------------------- 用户
@router.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return {"code": 200, "data": [
        {"id": u.id, "username": u.username, "role": u.role} for u in users
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
            role=(user_in.role or "EMPLOYEE").upper()
        )
        db.add(new_user)
        db.commit()
        return {"code": 200, "message": "添加用户成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"数据库写入异常: {str(e)}")


def _delete_user(user_id: str, db: Session):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="数据库中没有这个人")

    # 解除该用户作为“项目负责人 / 工作包负责人”的绑定，避免外键冲突
    db.query(models.Project).filter(models.Project.owner_id == user_id).update(
        {models.Project.owner_id: None}, synchronize_session=False
    )
    db.query(models.WorkPackage).filter(models.WorkPackage.owner_id == user_id).update(
        {models.WorkPackage.owner_id: None}, synchronize_session=False
    )

    db.delete(user)
    db.commit()
    return {"code": 200, "message": "删除用户成功"}


@router.delete("/users/{userId}")
def delete_user(userId: str, db: Session = Depends(get_db)):
    return _delete_user(userId, db)


@legacy_router.delete("/users/{userId}")
def legacy_delete_user(userId: str, db: Session = Depends(get_db)):
    """兼容前端 deleteUserApi 请求的 /api/v1/users/{id}。"""
    return _delete_user(userId, db)


# ---------------------------------------------------------------- 项目
@router.get("/projects")
def get_all_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    res = []
    for project in projects:
        res.append({
            "id": project.id,
            "name": project.name,
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
            project.name = project_name
            project.owner_id = project_in.owner_id or None
        else:
            project = models.Project(
                name=project_name,
                owner_id=project_in.owner_id or None
            )
            db.add(project)

        db.commit()
        db.refresh(project)
        return {"code": 200, "message": "项目配置成功", "data": {"id": project.id, "name": project.name}}
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
        "assignee_id": owner_id,
        "assignee_name": owner_name,
        "assigned_employees": [{"id": owner_id, "name": owner_name}] if owner_id else [],
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

            conflict = db.query(models.WorkPackage).filter(
                models.WorkPackage.id != pkg.id,
                models.WorkPackage.project_id == project.id,
                models.WorkPackage.name == pkg_in.name
            ).first()
            if conflict:
                raise HTTPException(status_code=400, detail="同一项目下工作包名称已存在，请换一个名称！")

            pkg.name = pkg_in.name
            pkg.project_id = project.id
            pkg.category_name = pkg_in.category_name
            new_owner = pkg_in.owner_id or pkg_in.assignee_id
            if new_owner:
                pkg.owner_id = new_owner
            message = "工作包更新成功"
        else:
            conflict = db.query(models.WorkPackage).filter(
                models.WorkPackage.project_id == project.id,
                models.WorkPackage.name == pkg_in.name
            ).first()
            if conflict:
                raise HTTPException(status_code=400, detail="同一项目下工作包名称已存在！")

            # 自动生成工作包 ID（项目下递增序号）
            existing_count = db.query(models.WorkPackage).filter(
                models.WorkPackage.project_id == project.id
            ).count()
            pkg = models.WorkPackage(
                id=f"P{project.id}-WP{existing_count + 1:02d}",
                name=pkg_in.name,
                project_id=project.id,
                category_name=pkg_in.category_name,
                owner_id=pkg_in.owner_id or pkg_in.assignee_id or None,
            )
            db.add(pkg)
            message = "工作包创建成功"

        db.flush()  # 先落库拿到 pkg.id，供关系使用
        # 把前端传的 分值/节点 保存到默认工作项
        ensure_default_work_item(db, pkg, score=pkg_in.score, deadline_str_val=pkg_in.deadline or "")
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
