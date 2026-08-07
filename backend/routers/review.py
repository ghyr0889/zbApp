import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import ReviewDecision, TaskAssignCreate

router = APIRouter(prefix="/api/v1/review", tags=["Owner Review"])


def ensure_project_owner(db: Session, reviewer_id: str, work_log: models.WorkLog):
    reviewer = db.query(models.User).filter(models.User.id == str(reviewer_id)).first()
    if not reviewer or str(reviewer.role).upper() not in ["OWNER", "LEADER"]:
        raise HTTPException(status_code=403, detail="只有项目负责人可以审核工作包申请")

    work_package = work_log.work_package
    project = work_package.project if work_package else None
    if not project or project.owner_id != str(reviewer_id):
        raise HTTPException(status_code=403, detail="只能审核自己负责项目下的工作包申请")


@router.get("/reviews/pending")
def get_pending_reviews(user_id: str = Query(...), db: Session = Depends(get_db)):
    reviewer = db.query(models.User).filter(models.User.id == str(user_id)).first()
    if not reviewer or str(reviewer.role).upper() not in ["OWNER", "LEADER"]:
        return {"code": 200, "data": []}

    pending_logs = db.query(models.WorkLog).join(
        models.WorkPackage,
        models.WorkLog.work_package_id == models.WorkPackage.id
    ).join(
        models.Project,
        models.WorkPackage.project_id == models.Project.id
    ).filter(
        models.WorkLog.status == "PENDING",
        models.Project.owner_id == str(user_id)
    ).order_by(models.WorkLog.created_at.desc()).all()

    data = []
    for log in pending_logs:
        work_package = log.work_package
        project = work_package.project if work_package else None
        category = work_package.category if work_package else None
        data.append({
            "id": log.id,
            "work_package_id": log.work_package_id,
            "applicant_name": log.user.username if log.user else log.user_id,
            "user_id": log.user_id,
            "project_id": project.id if project else None,
            "project_name": project.name if project else "-",
            "project_owner_id": project.owner_id if project else "-",
            "category_name": category.name if category else "-",
            "work_package_name": work_package.name if work_package else "-",
            "deadline": work_package.deadline if work_package else "-",
            "node_requirement": work_package.deadline if work_package else "-",
            "base_score": log.base_score,
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "-",
            "status": log.status
        })

    return {"code": 200, "data": data}


@router.post("/{log_id}")
def review_log(log_id: str, decision: ReviewDecision, db: Session = Depends(get_db)):
    work_log = db.query(models.WorkLog).filter(models.WorkLog.id == str(log_id)).first()
    if not work_log:
        raise HTTPException(status_code=404, detail="工作日志记录不存在")
    if work_log.status != "PENDING":
        raise HTTPException(status_code=400, detail="该申请已处理，不能重复审核")

    ensure_project_owner(db, decision.reviewer_id, work_log)

    work_log.reviewer_id = str(decision.reviewer_id)
    work_log.review_comment = decision.remark or ("审核通过" if decision.approved else "")
    if decision.approved:
        package = work_log.work_package
        base_score = package.score if package else work_log.base_score
        work_log.base_score = base_score * decision.weight
        work_log.status = "APPROVED"
    else:
        work_log.status = "REJECTED"
        work_log.base_score = 0.0

    db.commit()
    return {
        "code": 200,
        "message": "审核通过" if decision.approved else "已驳回该申请",
        "data": {
            "log_id": work_log.id,
            "status": work_log.status,
            "score_earned": work_log.base_score
        }
    }


@router.get("/projects/my/{user_id}")
def get_projects_for_current_user(user_id: str, db: Session = Depends(get_db)):
    my_projects = db.query(models.Project).filter(models.Project.owner_id == str(user_id)).all()
    data = []

    for project in my_projects:
        work_packages = db.query(models.WorkPackage).filter(
            models.WorkPackage.project_id == project.id
        ).all()

        package_data = []
        for package in work_packages:
            assignment = db.query(models.TaskAssignment).filter(
                models.TaskAssignment.work_package_id == package.id
            ).first()
            assignee_id = assignment.assignee_id if assignment else None
            assignee_name = None
            if assignee_id:
                assignee_user = db.query(models.User).filter(models.User.id == assignee_id).first()
                assignee_name = assignee_user.username if assignee_user else assignee_id

            package_data.append({
                "id": package.id,
                "project_id": package.project_id,
                "name": package.name,
                "score": package.score,
                "deadline": package.deadline,
                "category_name": package.category_name,
                "current_assignee_id": assignee_id,
                "current_assignee_name": assignee_name
            })

        data.append({
            "project_id": project.id,
            "project_name": project.name,
            "work_packages": package_data
        })

    return {"code": 200, "data": data}


@router.post("/projects/assign")
def assign_work_package(req: TaskAssignCreate, db: Session = Depends(get_db)):
    pkg = db.query(models.WorkPackage).filter(models.WorkPackage.id == req.work_package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="工作包不存在")

    project = pkg.project
    if not project or project.owner_id != str(req.assigner_id):
        raise HTTPException(status_code=403, detail="只能指派自己负责项目下的工作包")

    assignee = db.query(models.User).filter(models.User.id == req.assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="指定员工不存在")

    assignments = db.query(models.TaskAssignment).filter(
        models.TaskAssignment.work_package_id == req.work_package_id
    ).all()

    try:
        if assignments:
            primary_assignment = assignments[0]
            primary_assignment.assignee_id = req.assignee_id
            primary_assignment.assigner_id = req.assigner_id
            primary_assignment.status = "IN_PROGRESS"

            for duplicate_assignment in assignments[1:]:
                db.delete(duplicate_assignment)
        else:
            db.add(models.TaskAssignment(
                id=str(uuid.uuid4())[:8],
                assigner_id=req.assigner_id,
                assignee_id=req.assignee_id,
                work_package_id=req.work_package_id,
                status="IN_PROGRESS"
            ))

        db.commit()
        return {"code": 200, "message": "工作包指派成功"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"指派保存失败: {str(e)}")
