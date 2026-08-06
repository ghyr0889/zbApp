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


def ensure_fixed_work_categories(db: Session):
    for old_name, new_name in CATEGORY_MIGRATION_MAP.items():
        db.query(models.WorkPackage).filter(
            models.WorkPackage.category_name == old_name
        ).update({models.WorkPackage.category_name: new_name}, synchronize_session=False)

    db.query(models.WorkPackage).filter(
        ~models.WorkPackage.category_name.in_(models.FIXED_WORK_CATEGORIES)
    ).update({models.WorkPackage.category_name: "类型1"}, synchronize_session=False)

    existing = {item.name for item in db.query(models.WorkCategory).all()}
    for category_name in models.FIXED_WORK_CATEGORIES:
        if category_name not in existing:
            db.add(models.WorkCategory(name=category_name))
    if not set(models.FIXED_WORK_CATEGORIES).issuperset(existing):
        db.query(models.WorkCategory).filter(
            ~models.WorkCategory.name.in_(models.FIXED_WORK_CATEGORIES)
        ).delete(synchronize_session=False)
    db.commit()


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

    project = db.query(models.Project).filter(models.Project.name == project_name).first()
    if project:
        project.owner_id = project_in.owner_id or None
    else:
        project = models.Project(name=project_name, owner_id=project_in.owner_id or None)
        db.add(project)

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
            "name": project.name,
            "owner_id": project.owner_id or "-",
            "owner_name": owner_name
        })
    return {"code": 200, "data": res}


def sync_work_package_assignment(db: Session, work_package_name: str, assignee_id: str, assigner_id: Optional[str]):
    assignee = db.query(models.User).filter(models.User.id == assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="指定员工不存在")

    actual_assigner_id = assigner_id or assignee_id
    assigner = db.query(models.User).filter(models.User.id == actual_assigner_id).first()
    if not assigner:
        actual_assigner_id = assignee_id

    assignments = db.query(models.TaskAssignment).filter(
        models.TaskAssignment.work_package_name == work_package_name
    ).all()

    if assignments:
        primary_assignment = assignments[0]
        primary_assignment.assignee_id = assignee_id
        primary_assignment.assigner_id = actual_assigner_id
        primary_assignment.status = "IN_PROGRESS"

        for duplicate_assignment in assignments[1:]:
            db.delete(duplicate_assignment)
    else:
        db.add(models.TaskAssignment(
            id=str(uuid.uuid4())[:8],
            assigner_id=actual_assigner_id,
            assignee_id=assignee_id,
            work_package_name=work_package_name,
            status="IN_PROGRESS"
        ))


@router.post("/work-packages")
def create_or_update_work_package(pkg_in: WorkPackageCreate, db: Session = Depends(get_db)):
    ensure_fixed_work_categories(db)
    if pkg_in.category_name not in models.FIXED_WORK_CATEGORIES:
        raise HTTPException(status_code=400, detail="工作类型只能选择：类型1、类型2、类型3、类型4")
    assignee_id = pkg_in.assignee_id or pkg_in.owner_id
    if not assignee_id:
        raise HTTPException(status_code=400, detail="必须指定工作包负责员工")

    if pkg_in.original_name:
        pkg = db.query(models.WorkPackage).filter(models.WorkPackage.name == pkg_in.original_name).first()
        if not pkg:
            raise HTTPException(status_code=404, detail="未找到要修改的工作包")

    # 如果连名字都改了，要确保新名字没有和别人的冲突
        if pkg_in.name != pkg_in.original_name:
            conflict = db.query(models.WorkPackage).filter(models.WorkPackage.name == pkg_in.name).first()
            if conflict:
                raise HTTPException(status_code=400, detail="修改后的工作包名称已存在，请换一个名称！")
            # 更改主键名称
            pkg.name = pkg_in.name
            db.query(models.TaskAssignment).filter(
                models.TaskAssignment.work_package_name == pkg_in.original_name
            ).update({models.TaskAssignment.work_package_name: pkg_in.name}, synchronize_session=False)
            db.query(models.WorkLog).filter(
                models.WorkLog.work_package_name == pkg_in.original_name
            ).update({models.WorkLog.work_package_name: pkg_in.name}, synchronize_session=False)
            db.query(models.TaskTransfer).filter(
                models.TaskTransfer.task_name == pkg_in.original_name
            ).update({models.TaskTransfer.task_name: pkg_in.name}, synchronize_session=False)
            
        # 更新其他字段
        pkg.score = pkg_in.score
        pkg.deadline = pkg_in.deadline or pkg_in.node_requirement or ""
        pkg.project_name = pkg_in.project_name
        pkg.category_name = pkg_in.category_name
        sync_work_package_assignment(db, pkg_in.name, assignee_id, pkg_in.assigner_id)
            
        message = "工作包更新成功"
        
    else:
        # ============ 不存在 original_name，说明是【新增全新数据】 ============
        conflict = db.query(models.WorkPackage).filter(models.WorkPackage.name == pkg_in.name).first()
        if conflict:
            raise HTTPException(status_code=400, detail="工作包名称已存在！")
            
        pkg = models.WorkPackage(
            name=pkg_in.name,
            score=pkg_in.score,
            deadline=pkg_in.deadline or pkg_in.node_requirement or "",
            project_name=pkg_in.project_name,
            category_name=pkg_in.category_name
        )
        db.add(pkg)
        db.flush()
        sync_work_package_assignment(db, pkg_in.name, assignee_id, pkg_in.assigner_id)
        message = "工作包创建成功"

    db.commit()
    return {"code": 200, "message": message}


@router.get("/work-packages-overview")
def get_work_packages_overview(db: Session = Depends(get_db)):
    try:
        ensure_fixed_work_categories(db)
        packages = db.query(models.WorkPackage).all()
        res = []

        for pkg in packages:
            assignments = db.query(models.TaskAssignment).filter(
                models.TaskAssignment.work_package_name == pkg.name
            ).all()

            assignee_ids = [assign.assignee_id for assign in assignments if assign.assignee_id]
            assigned_employees = []
            assigned_employee_ids = []
            users_by_id = []
            if assignee_ids:
                users = db.query(models.User).filter(models.User.id.in_(assignee_ids)).all()
                users_by_id = {u.id: u for u in users}
                assigned_employee_ids = assignee_ids
                assigned_employees = [u.username for u in users]
            primary_assignee_id = assigned_employee_ids[0] if assigned_employee_ids else ""
            primary_assignee = users_by_id.get(primary_assignee_id) if primary_assignee_id and assignee_ids else None

            res.append({
                "name": pkg.name,
                "project_name": pkg.project_name or "-",
                "category_name": pkg.category_name or "-",
                "score": pkg.score,
                "deadline": pkg.deadline or "-",
                "assignee_id": primary_assignee_id,
                "assignee_name": primary_assignee.username if primary_assignee else "",
                "assigned_employee_ids": assigned_employee_ids,
                "assigned_employees": assigned_employees
            })

        return {"code": 200, "data": res}
    except Exception as e:
        print("❌ work-packages-overview 接口报错详情:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"查询工作包概览失败: {str(e)}")
