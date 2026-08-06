from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
import models
import traceback
import uuid
import re
from schemas import LogCreate

router = APIRouter(prefix="/api/v1/work-logs", tags=["工作日志与积分"])

def parse_node_date(node_str):
    if not node_str:
        return datetime.max
    match = re.search(r'\d{4}-\d{2}-\d{2}', str(node_str))
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


def work_package_detail(item):
    work_package = item.work_package
    return {
        "log_id": item.id,
        "work_package_name": item.work_package_name,
        "project_name": work_package.project.name if (work_package and work_package.project) else "-",
        "category_name": work_package.category.name if (work_package and work_package.category) else "-",
        "score_earned": item.score_earned,
        "approved_at": item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else "-"
    }

#工作包完成状态判断函数
def Judge_workpackage_Status(work_package_name: str, db: Session) -> bool:
    approved_log = db.query(models.WorkLog).filter(
        models.WorkLog.work_package_name == work_package_name,
        models.WorkLog.status == "APPROVED"
    ).first()

    if approved_log:
        return True
    return False

#项目完成状态判断函数
def Judge_project_Status(project_name: str, db: Session) -> bool:
    work_packages = db.query(models.WorkPackage).filter(
        models.WorkPackage.project_name == project_name
    ).all()
    if not work_packages:
        return False

    for pkg in work_packages:
        is_pkg_completed = Judge_workpackage_Status(pkg.name, db)
        if not is_pkg_completed:
            return False
    return True

#可填报工作包
# @router.get("/cascade-options")
# def get_cascade_options(user_id: str = Query(...), db: Session = Depends(get_db)):
#     try:
#         user = db.query(models.User).filter(models.User.id == str(user_id)).first()

#         assigned_work_package_names = set()
#         if not user or user.role in ["ADMIN", "OWNER", "LEADER"]:
#             all_pkgs = db.query(models.WorkPackage).all()
#             assigned_work_package_names = {p.name for p in all_pkgs}
#         else:
#             assignments = db.query(models.TaskAssignment).filter(
#                 models.TaskAssignment.assignee_id == str(user_id)
#             ).all()
#             assigned_work_package_names = {a.work_package_name for a in assignments if a.work_package_name}

#         submitted_logs = db.query(models.WorkLog).filter(
#             models.WorkLog.user_id == str(user_id)
#         ).all()
#         submitted_names = {log.work_package_name for log in submitted_logs}

#         projects = db.query(models.Project).all()
#         categories = db.query(models.WorkCategory).all()

#         tree = []
#         for project in projects:
#             project_node = {"value": project.name, "label": project.name, "children": []}

#             for cat in categories:
#                 cat_node = {"value": cat.name, "label": cat.name, "children": []}

#                 pkgs = db.query(models.WorkPackage).filter(
#                     models.WorkPackage.project_name == project.name,
#                     models.WorkPackage.category_name == cat.name
#                 ).all()

#                 pkgs_sorted = sorted(pkgs, key=lambda p: parse_node_date(p.deadline))

#                 for pkg in pkgs_sorted:
#                     if pkg.name not in assigned_work_package_names or pkg.name in submitted_names:
#                         continue

#                     req_text = pkg.deadline or "无节点要求"
#                     cat_node["children"].append({
#                         "value": pkg.name,
#                         "label": f"⏰ [{req_text}] {pkg.name} (+{pkg.score}分)",
#                         "score": pkg.score,
#                         "deadline": req_text
#                     })

#                 if cat_node["children"]:
#                     project_node["children"].append(cat_node)

#             if project_node["children"]:
#                 tree.append(project_node)

#         return {"code": 200, "data": tree}

#     except Exception as e:
#         print("❌ cascade-options 排序与解析报错:", e)
#         return {"code": 200, "data": []}

#我的工作包
@router.get("/my-assigned-work-packages/{user_id}")
def get_my_assigned_work_packages(user_id: str, db: Session = Depends(get_db)):
    submitted_packages = db.query(models.WorkLog.work_package_name).filter(
        models.WorkLog.user_id == user_id,
        models.WorkLog.status.in_(["PENDING", "APPROVED"])
    ).all()
    submitted_work_package_names = [item[0] for item in submitted_packages]

    assignments = db.query(models.TaskAssignment).filter(
        models.TaskAssignment.assignee_id == user_id
    ).all()

    res = []
    for assign in assignments:
        if assign.work_package_name in submitted_work_package_names:
            continue

        pkg = db.query(models.WorkPackage).filter(
            models.WorkPackage.name == assign.work_package_name
        ).first()

        if pkg:
            res.append({
                "task_id": assign.id,
                "work_package_name": pkg.name,
                "score": pkg.score,
                "deadline": pkg.deadline,
                "category_name": pkg.category_name,
                "project_name": pkg.project.name if (pkg.category and pkg.project) else "-"
            })

    return {"code": 200, "data": res}

#提交审核
@router.post("")
def create_log(log_in: LogCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == log_in.user_id).first()

    if user and user.role not in ["ADMIN", "OWNER"]:
        is_assigned = db.query(models.TaskAssignment).filter(
            models.TaskAssignment.assignee_id == log_in.user_id,
            models.TaskAssignment.work_package_name == log_in.work_package_name
        ).first()

        if not is_assigned:
            raise HTTPException(
                status_code=403,
                detail=f"权限不足，工作包[{log_in.work_package_name}]未分配给你，无法提交日志"
            )

    pkg = db.query(models.WorkPackage).filter(
        models.WorkPackage.name == log_in.work_package_name
    ).first()

    if not pkg:
        raise HTTPException(status_code=400, detail=f"工作包 [{log_in.work_package_name}] 不存在！")

    earned_score = log_in.score_earned if (log_in.score_earned and log_in.score_earned > 0) else pkg.score

    try:
        new_log = models.WorkLog(
            id=str(uuid.uuid4()),
            user_id=log_in.user_id,
            work_package_name=log_in.work_package_name,
            score_earned=earned_score,
            status="PENDING"
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
    except Exception as e:
        db.rollback()
        print("❌ 提交日志后端报错 500 详细日志:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"数据库异常: {str(e)}")

    return {
        "code": 200,
        "message": "日志提交成功",
        "data": {"id": new_log.id}
    }

#查看自己提交过的日志、审核状态、反馈意见
@router.get("/my/{user_id}")
def get_my_logs(user_id: str, db: Session = Depends(get_db)):
    logs = db.query(models.WorkLog).filter(models.WorkLog.user_id == user_id).all()
    res = []
    for log in logs:
        work_package = log.work_package
        res.append({
            "id": log.id,
            "project_name": work_package.project.name if (work_package and work_package.project) else "-",
            "category_name": work_package.category.name if (work_package and work_package.category) else "-",
            "work_package_name": log.work_package_name,
            "deadline": work_package.deadline if work_package else "-",
            "score_earned": log.score_earned,
            "status": log.status,
            "review_comment": log.review_comment or "-",
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "-"
        })
    return {"code": 200, "data": res}

#公开工作包大厅数据
@router.get("/public-work-packages")
def get_public_work_packages(db: Session = Depends(get_db)):
    packages = db.query(models.WorkPackage).all()
    res = []

    for pkg in packages:
        owner = pkg.project.owner if pkg.project else None
        assignments = db.query(models.TaskAssignment).filter(
            models.TaskAssignment.work_package_name == pkg.name
        ).all()
        assignee_ids = [assign.assignee_id for assign in assignments if assign.assignee_id]
        assignees = []
        if assignee_ids:
            assignees = db.query(models.User).filter(models.User.id.in_(assignee_ids)).all()
        assignees_by_id = {user.id: user for user in assignees}
        primary_assignee_id = assignee_ids[0] if assignee_ids else ""
        primary_assignee = assignees_by_id.get(primary_assignee_id)
        assigned_employees = [
            {
                "id": assignee_id,
                "name": assignees_by_id[assignee_id].username if assignee_id in assignees_by_id else assignee_id
            }
            for assignee_id in assignee_ids
        ]
        pkg_completed = Judge_workpackage_Status(pkg.name, db)
        project_completed = Judge_project_Status(pkg.project_name, db)
        res.append({
            "name": pkg.name,
            "score": pkg.score,
            "deadline": pkg.deadline,
            "project_name": pkg.project_name,
            "category_name": pkg.category_name,
            "owner_id": owner.id if owner else "-",
            "assignee_id": primary_assignee_id,
            "assignee_name": primary_assignee.username if primary_assignee else "",
            "assigned_employees": assigned_employees,
            "owner_name": owner.username if owner else "未指定负责人",
            "pkg_completed": pkg_completed,
            "project_completed": project_completed
        })

    return {"code": 200, "data": res}

#某个人的分值统计
@router.get("/score-board/{user_id}")
def get_score_board(user_id: str, period: str = "all", db: Session = Depends(get_db)):
    query = db.query(models.WorkLog).filter(
        models.WorkLog.user_id == user_id,
        models.WorkLog.status == "APPROVED"
    )

    period = str(period or "all").lower()
    now = datetime.now()
    filtered_logs = [log for log in query.all() if is_log_in_period(log.created_at, period, now)]
    total_score = sum(item.score_earned for item in filtered_logs)
    details = [work_package_detail(item) for item in filtered_logs]

    return {
        "code": 200,
        "data": {
            "total_score": total_score,
            "period": period,
            "details": details
        }
    }

#积分看板
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
        total_score = sum(item.score_earned for item in user_logs)
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
