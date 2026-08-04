from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
import models


router = APIRouter(prefix="/api/v1/review", tags=["Owner Review"])


class ReviewDecision(BaseModel):
    reviewer_id: str
    approved: bool
    remark: Optional[str] = ""


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
        models.WorkLog.work_package_name == models.WorkPackage.name
    ).join(
        models.Project,
        models.WorkPackage.project_name == models.Project.name
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
            "applicant_name": log.user.username if log.user else log.user_id,
            "user_id": log.user_id,
            "project_name": project.name if project else "-",
            "project_owner_id": project.owner_id if project else "-",
            "category_name": category.name if category else "-",
            "work_package_name": log.work_package_name,
            "deadline": work_package.deadline if work_package else "-",
            "node_requirement": work_package.deadline if work_package else "-",
            "content": log.content,
            "score_earned": log.score_earned,
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
        work_log.status = "APPROVED"
    else:
        work_log.status = "REJECTED"
        work_log.score_earned = 0.0

    db.commit()
    return {
        "code": 200,
        "message": "审核通过" if decision.approved else "已驳回该申请",
        "data": {
            "log_id": work_log.id,
            "status": work_log.status,
            "score_earned": work_log.score_earned
        }
    }
