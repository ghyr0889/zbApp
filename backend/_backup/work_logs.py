from datetime import datetime
import re
import traceback
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db

router = APIRouter(prefix="/api/v1/work-logs", tags=["Work Logs"])


def parse_node_date(node_str):
    if not node_str:
        return datetime.max
    match = re.search(r"\d{4}-\d{2}-\d{2}", str(node_str))
    if match:
        try:
            return datetime.strptime(match.group(), "%Y-%m-%d")
        except ValueError:
            pass
    return datetime.max


def is_log_in_period(log_date, period, now=None):
    period = str(period or "all").lower()
    now = now or datetime.now()
    log_date = log_date or now

    if period == "day":
        return log_date.date() == now.date()
    if period == "month":
        return log_date.year == now.year and log_date.month == now.month
    if period == "quarter":
        current_quarter = (now.month - 1) // 3 + 1
        log_quarter = (log_date.month - 1) // 3 + 1
        return log_date.year == now.year and log_quarter == current_quarter
    return True


def work_package_detail(log):
    work_package = log.work_package
    return {
        "log_id": log.id,
        "work_package_id": log.work_package_id,
        "work_package_name": work_package.name if work_package else "-",
        "project_name": work_package.project.name if (work_package and work_package.project) else "-",
        "category_name": work_package.category.name if (work_package and work_package.category) else "-",
        "base_score": log.base_score,
        "approved_at": log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "-"
    }


def judge_work_package_status(work_package_id: int, db: Session) -> bool:
    return db.query(models.WorkLog).filter(
        models.WorkLog.work_package_id == work_package_id,
        models.WorkLog.status == "APPROVED"
    ).first() is not None


def judge_project_status(project_id: int, db: Session) -> bool:
    work_packages = db.query(models.WorkPackage).filter(
        models.WorkPackage.project_id == project_id
    ).all()
    if not work_packages:
        return False
    return all(judge_work_package_status(pkg.id, db) for pkg in work_packages)


@router.get("/my-assigned-work-packages/{user_id}")
def get_my_assigned_work_packages(user_id: str, db: Session = Depends(get_db)):
    submitted_packages = db.query(models.WorkLog.work_package_id).filter(
        models.WorkLog.user_id == user_id,
        models.WorkLog.status.in_(["PENDING", "APPROVED"])
    ).all()
    submitted_work_package_ids = {item[0] for item in submitted_packages}

    assignments = db.query(models.TaskAssignment).filter(
        models.TaskAssignment.assignee_id == user_id
    ).all()

    res = []
    for assign in assignments:
        if assign.work_package_id in submitted_work_package_ids:
            continue

        pkg = assign.work_package
        if not pkg:
            continue

        res.append({
            "task_id": assign.id,
            "work_package_id": pkg.id,
            "work_package_name": pkg.name,
            "score": pkg.score,
            "deadline": pkg.deadline,
            "category_name": pkg.category_name,
            "project_id": pkg.project.id if pkg.project else None,
            "project_name": pkg.project.name if pkg.project else "-"
        })

    res.sort(key=lambda item: parse_node_date(item.get("deadline")))
    return {"code": 200, "data": res}


@router.get("/my/{user_id}")
def get_my_logs(user_id: str, db: Session = Depends(get_db)):
    logs = db.query(models.WorkLog).filter(models.WorkLog.user_id == user_id).all()
    res = []
    for log in logs:
        work_package = log.work_package
        res.append({
            "id": log.id,
            "work_package_id": log.work_package_id,
            "project_id": work_package.project.id if (work_package and work_package.project) else None,
            "project_name": work_package.project.name if (work_package and work_package.project) else "-",
            "category_name": work_package.category.name if (work_package and work_package.category) else "-",
            "work_package_name": work_package.name if work_package else "-",
            "deadline": work_package.deadline if work_package else "-",
            "base_score": log.base_score,
            "status": log.status,
            "review_comment": log.review_comment or "-",
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "-"
        })
    return {"code": 200, "data": res}


@router.get("/public-work-packages")
def get_public_work_packages(db: Session = Depends(get_db)):
    packages = db.query(models.WorkPackage).all()
    res = []

    for pkg in packages:
        owner = pkg.project.owner if pkg.project else None
        assignment = db.query(models.TaskAssignment).filter(
            models.TaskAssignment.work_package_id == pkg.id
        ).first()
        primary_assignee_id = assignment.assignee_id if assignment else ""
        primary_assignee = None
        if primary_assignee_id:
            primary_assignee = db.query(models.User).filter(models.User.id == primary_assignee_id).first()

        assigned_employees = []
        if primary_assignee_id:
            assigned_employees.append({
                "id": primary_assignee_id,
                "name": primary_assignee.username if primary_assignee else primary_assignee_id
            })

        res.append({
            "id": pkg.id,
            "name": pkg.name,
            "score": pkg.score,
            "deadline": pkg.deadline,
            "project_id": pkg.project_id,
            "project_name": pkg.project.name,
            "category_name": pkg.category_name,
            "owner_id": owner.id if owner else "-",
            "owner_name": owner.username if owner else "未指定负责人",
            "assignee_id": primary_assignee_id,
            "assignee_name": primary_assignee.username if primary_assignee else "",
            "assigned_employees": assigned_employees,
            "pkg_completed": judge_work_package_status(pkg.id, db),
            "project_completed": judge_project_status(pkg.project_id, db)
        })

    return {"code": 200, "data": res}


@router.get("/score-board/{user_id}")
def get_score_board(user_id: str, period: str = "all", db: Session = Depends(get_db)):
    query = db.query(models.WorkLog).filter(
        models.WorkLog.user_id == user_id,
        models.WorkLog.status == "APPROVED"
    )

    period = str(period or "all").lower()
    now = datetime.now()
    filtered_logs = [log for log in query.all() if is_log_in_period(log.created_at, period, now)]
    total_score = sum(item.base_score for item in filtered_logs)
    details = [work_package_detail(item) for item in filtered_logs]

    return {
        "code": 200,
        "data": {
            "total_score": total_score,
            "period": period,
            "details": details
        }
    }


@router.get("/public-score-board")
def get_public_score_board(period: str = "all", db: Session = Depends(get_db)):
    period = str(period or "all").lower()
    now = datetime.now()

    users = db.query(models.User).all()
    approved_logs = db.query(models.WorkLog).filter(
        models.WorkLog.status == "APPROVED"
    ).all()

    logs_by_user = {}
    for log in approved_logs:
        if is_log_in_period(log.created_at, period, now):
            logs_by_user.setdefault(log.user_id, []).append(log)

    people = []
    for user in users:
        user_logs = logs_by_user.get(user.id, [])
        details = [work_package_detail(item) for item in user_logs]
        total_score = sum(item.base_score for item in user_logs)
        people.append({
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "total_score": total_score,
            "details": details
        })

    people.sort(key=lambda item: item["total_score"], reverse=True)

    return {
        "code": 200,
        "data": {
            "period": period,
            "people": people
        }
    }
