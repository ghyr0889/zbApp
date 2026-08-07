from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
import models
import traceback
import uuid
from schemas import UserCreate, ProjectCreate, WorkPackageCreate

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Management"])

CATEGORY_MIGRATION_MAP = {
    "算法研发": "类型1",
    "硬件集成": "类型2",
    "软件开发": "类型3",
    "测试验证": "类型4",
}

@router.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return {"code": 200, "data": [{"id": u.id, "username": u.username, "role": u.role} for u in users]}


@router.post("/users")
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    user_id = user_in.id.strip()
    if not user_id or not user_in.username.strip():
        raise HTTPException(status_code=400, detail="工号和姓名不能为空")

    exist_user = db.query(models.User).filter(models.User.id == user_in.id).first()
    if exist_user:
        raise HTTPException(status_code=400, detail="工号已存在！")

    try:
        new_user = models.User(
            id=user_in.id,
            username=user_in.username,
            password=user_in.password,
            role=user_in.role
        )
        db.add(new_user)
        db.commit()
        return {"code": 200, "message": "添加用户成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"数据库写入异常:{str(e)}")

@router.delete("/users/{user_id}")
def delete_user(user_id:str, db:Session = Depends(get_db)):
    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=400,detail="数据库中没有这个人")

    db.delete(user_to_delete)
    db.commit(user_to_delete)

    return {
        "code": 200, "message": "删除用户成功"
    }

@router.post("/projects")
def create_or_update_project(project_in: ProjectCreate, db: Session = Depends(get_db)):
    project_name = project_in.name.strip()
    if not project_name:
        raise HTTPException(status_code=400, detail="项目名称不能为空！")

    if project_in.id:
        project = db.query(models.Project).filter(models.Project.id == project_in.id).first()
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

    try:
        db.commit()
        db.refresh(project)
        return {"code": 200, "message": "项目配置成功", "data": {"name": project.name}}
    except Exception as e:
        db.rollback()
        print("❌ 保存项目报错详情（请看下方终端提示）:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"保存项目失败: {str(e)}")


@router.get("/projects")
def get_all_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    res = []
    for project in projects:
        owner_name = project.owner.username if project.owner else "未指定负责人"
        res.append({
            "id": project.id,
            "name": project.name,
            "owner_id": project.owner_id or "-",
            "owner_name": owner_name
        })
    return {"code": 200, "data": res}


@router.post("/work-packages")
def create_or_update_work_package(pkg_in: WorkPackageCreate, db: Session = Depends(get_db)):
    if pkg_in.category_name not in models.FIXED_WORK_CATEGORIES:
        raise HTTPException(status_code=400, detail="工作类型只能选择：类型1、类型2、类型3、类型4")

    deadline = pkg_in.deadline or ""

    if pkg_in.work_package_id:
        pkg = db.query(models.WorkPackage).filter(models.WorkPackage.id == pkg_in.work_package_id).first()
        if not pkg:
            raise HTTPException(status_code=404, detail="未找到要修改的工作包")

        conflict = db.query(models.WorkPackage).filter(
            models.WorkPackage.id != pkg.id,
            models.WorkPackage.project_id == pkg_in.project_id,
            models.WorkPackage.name == pkg_in.name
        ).first()
        if conflict:
            raise HTTPException(status_code=400, detail="同一项目下工作包名称已存在，请换一个名称！")

        pkg.name = pkg_in.name
        pkg.score = pkg_in.score
        pkg.deadline = deadline
        pkg.project_name = pkg_in.project_name
        pkg.category_name = pkg_in.category_name
        message = "工作包更新成功"

    else:
        conflict = db.query(models.WorkPackage).filter(
            models.WorkPackage.project_id == pkg_in.project_id,
            models.WorkPackage.name == pkg_in.name
        ).first()
        if conflict:
            raise HTTPException(status_code=400, detail="同一项目下工作包名称已存在！")

        pkg = models.WorkPackage(
            name=pkg_in.name,
            score=pkg_in.score,
            deadline=deadline,
            project_name=pkg_in.project_name,
            category_name=pkg_in.category_name
        )
        db.add(pkg)
        message = "工作包创建成功"

    db.commit()
    db.refresh(pkg)
    return {"code": 200, "message": message, "data": {"id": pkg.id}}


@router.get("/work-packages-overview")
def get_work_packages_overview(db: Session = Depends(get_db)):
    try:
        packages = db.query(models.WorkPackage).all()
        res = []

        for pkg in packages:
            assignment = db.query(models.TaskAssignment).filter(
                models.TaskAssignment.work_package_id == pkg.id
            ).first()

            primary_assignee_id = assignment.assignee_id if assignment else ""
            primary_assignee = None
            if primary_assignee_id:
                primary_assignee = db.query(models.User).filter(models.User.id == primary_assignee_id).first()

            res.append({
                "id": pkg.id,
                "name": pkg.name,
                "project_id": pkg.project_id,
                "project_name": pkg.project.name or "-",
                "category_name": pkg.category_name or "-",
                "score": pkg.score,
                "deadline": pkg.deadline or "-",
                "assignee_id": primary_assignee_id,
                "assignee_name": primary_assignee.username if primary_assignee else "",
                "assigned_employee_ids": [primary_assignee_id] if primary_assignee_id else [],
                "assigned_employees": [primary_assignee.username if primary_assignee else primary_assignee_id] if primary_assignee_id else []
            })

        return {"code": 200, "data": res}
    except Exception as e:
        print("❌ work-packages-overview 接口报错详情:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"查询工作包概览失败: {str(e)}")
