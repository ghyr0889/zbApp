# xiangmu/backend/routers/work_logs.py
import re
import traceback
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import WorkItemCreate
from utils import work_package_summary, deadline_str, parse_deadline

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


def work_item_detail(log):
    """把一条 WorkLog 展开为前端需要的明细结构（用于排行榜 / 我的日志）。"""
    item = log.work_item
    wp = item.work_package if item else None
    project = wp.project if wp else None
    category = wp.category if wp else None
    return {
        "log_id": log.id,
        "work_item_id": item.id if item else None,
        "work_item_name": item.name if item else "-",
        "work_package_id": wp.id if wp else None,
        "work_package_name": wp.name if wp else "-",
        "project_id": project.id if project else None,
        "project_name": project.name if project else "-",
        "category_name": category.name if category else "-",
        "base_score": log.base_score,
        "approved_at": log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "-",
    }


# ---------------------------------------------------------------- 公开工作包（项目总览）
def _public_package_view(pkg, db):
    project = pkg.project
    # 项目负责人（供前端“项目行”展示）
    proj_owner = project.owner if project else None
    # 工作包负责人（供前端“工作包行”展示）
    pkg_owner = pkg.owner
    pkg_owner_id = pkg.owner_id or ""
    pkg_owner_name = pkg_owner.username if pkg_owner else ""
    score, deadline = work_package_summary(pkg)
    items = list(pkg.work_items or [])
    # 工作包完成：其下所有工作项都有 APPROVED 日志
    approved_item_ids = {
        row[0] for row in db.query(models.WorkLog.work_item_id).filter(
            models.WorkLog.status == "APPROVED",
            models.WorkLog.work_item_id.in_([it.id for it in items])
        ).all()
    } if items else set()
    pkg_completed = bool(items) and all(it.id in approved_item_ids for it in items)

    return {
        "id": pkg.id,
        "score": score,
        "deadline": deadline or "-",
        "project_id": pkg.project_id,
        "project_name": project.name if project else "-",
        "project_category": project.category if project else "",  # 项目类别
        "category_name": pkg.category_name or "-",
        "next_step_work": pkg.next_step_work or "",  # 下阶段工作
        "objective": pkg.objective or "",  # 目标
        "owner_id": project.owner_id if project else "",
        "owner_name": proj_owner.username if proj_owner else "",
        "assignee_id": pkg_owner_id,
        "assignee_name": pkg_owner_name,
        "assigned_employees": [{"id": pkg_owner_id, "name": pkg_owner_name}] if pkg_owner_id else [],
        "pkg_completed": pkg_completed,
        "project_completed": False,  # 占位，下方按项目统一计算
        "level": project.level if project else "",
    }


@router.get("/public-work-packages")
def get_public_work_packages(db: Session = Depends(get_db)):
    packages = db.query(models.WorkPackage).all()
    data = []
    # 先算好每个工作包的完成状态
    for pkg in packages:
        data.append(_public_package_view(pkg, db))

    # 项目整体完成：该项目下所有工作包都完成（且至少有一个工作包）
    project_ids = {pkg.project_id for pkg in packages}
    project_pkg_count = {}
    project_done_count = {}
    for pkg in data:
        project_pkg_count[pkg["project_id"]] = project_pkg_count.get(pkg["project_id"], 0) + 1
        if pkg["pkg_completed"]:
            project_done_count[pkg["project_id"]] = project_done_count.get(pkg["project_id"], 0) + 1
    for pkg in data:
        pid = pkg["project_id"]
        pkg["project_completed"] = (
            project_pkg_count.get(pid, 0) > 0
            and project_done_count.get(pid, 0) >= project_pkg_count[pid]
        )

    return {"code": 200, "data": data}


# ---------------------------------------------------------------- 积分
@router.get("/score-board/{user_id}")
def get_score_board(user_id: str, period: str = "all", db: Session = Depends(get_db)):
    query = db.query(models.WorkLog).filter(
        models.WorkLog.user_id == user_id,
        models.WorkLog.status == "APPROVED"
    )
    now = datetime.now()
    filtered_logs = [log for log in query.all() if is_log_in_period(log.created_at, period, now)]
    total_score = sum(item.base_score for item in filtered_logs)
    details = [work_item_detail(item) for item in filtered_logs]
    return {
        "code": 200,
        "data": {"total_score": total_score, "period": period, "details": details}
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
        people.append({
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "total_score": sum(item.base_score for item in user_logs),
            "details": [work_item_detail(item) for item in user_logs],
        })

    people.sort(key=lambda item: item["total_score"], reverse=True)
    return {"code": 200, "data": {"period": period, "people": people}}


# ---------------------------------------------------------------- 级联选项（备用）
@router.get("/cascade-options")
def get_cascade_options(user_id: str, db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    data = []
    for project in projects:
        packages = []
        for wp in project.work_packages:
            packages.append({
                "id": wp.id,
                "name": wp.name,
                "work_items": [
                    {"id": it.id, "name": it.name, "score": it.score}
                    for it in (wp.work_items or [])
                ]
            })
        data.append({
            "project_id": project.id,
            "project_name": project.name,
            "work_packages": packages
        })
    return {"code": 200, "data": data}


# ---------------------------------------------------------------- 工作项管理
def _work_item_view(item):
    """把 WorkItem 展开为前端需要的结构。"""
    return {
        "id": item.id,
        "name": item.name,
        "standard": item.standard or "",
        "difficulty": item.difficulty or "",
        "importance": item.importance or "",
        "innovation": item.innovation or "",
        "deadline": deadline_str(item.deadline) if item.deadline else "",
        "score": item.score or 0.0,
        "category": item.category or "",
        "work_package_id": item.work_package_id,
    }


@router.get("/work-packages/{work_package_id}/work-items")
def get_work_items(work_package_id: str, db: Session = Depends(get_db)):
    """查询某个工作包下的全部工作项（含工作包信息，供工作项页面使用）。"""
    pkg = db.query(models.WorkPackage).filter(
        models.WorkPackage.id == work_package_id
    ).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="工作包不存在")

    items = db.query(models.WorkItem).filter(
        models.WorkItem.work_package_id == work_package_id
    ).order_by(models.WorkItem.id).all()
    project = pkg.project
    return {
        "code": 200,
        "data": {
            "work_package": {
                "id": pkg.id,
                "project_id": pkg.project_id,
                "project_name": project.name if project else "-",
                "category_name": pkg.category_name or "-",
                "next_step_work": pkg.next_step_work or "",
                "objective": pkg.objective or "",
                "owner_id": pkg.owner_id or "",
                "owner_name": pkg.owner.username if pkg.owner else "",
            },
            "work_items": [_work_item_view(it) for it in items],
        }
    }


@router.post("/work-packages/{work_package_id}/work-items")
def create_or_update_work_item(
    work_package_id: str,
    item_in: WorkItemCreate,
    db: Session = Depends(get_db),
):
    """创建/更新工作项（由工作包负责人分配工作项）。"""
    pkg = db.query(models.WorkPackage).filter(
        models.WorkPackage.id == work_package_id
    ).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="工作包不存在")

    name = (item_in.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="工作项名称不能为空")

    # 权限校验（宽松）：工作包负责人 / 项目负责人 / 管理员 可分配工作项
    operator_id = getattr(item_in, "operator_id", None)
    if operator_id:
        operator = db.query(models.User).filter(models.User.id == str(operator_id)).first()
        is_manager = operator and str(operator.role).upper() in ["ADMIN", "OWNER", "LEADER"]
        is_pkg_owner = pkg.owner_id == str(operator_id)
        is_proj_owner = pkg.project and pkg.project.owner_id == str(operator_id)
        if not (is_manager or is_pkg_owner or is_proj_owner):
            raise HTTPException(status_code=403, detail="只有工作包负责人或项目负责人可以分配工作项")

    try:
        if item_in.work_item_id:
            item = db.query(models.WorkItem).filter(
                models.WorkItem.id == item_in.work_item_id
            ).first()
            if not item:
                raise HTTPException(status_code=404, detail="未找到要修改的工作项")
            if str(item.work_package_id) != str(work_package_id):
                raise HTTPException(status_code=400, detail="工作项不属于该工作包")
        else:
            item = models.WorkItem(work_package_id=work_package_id)
            db.add(item)

        item.name = name
        item.standard = item_in.standard
        item.difficulty = item_in.difficulty
        item.importance = item_in.importance
        item.innovation = item_in.innovation
        item.deadline = parse_deadline(item_in.deadline) if item_in.deadline else None
        item.score = item_in.score if item_in.score is not None else 0.0
        item.category = item_in.category
        db.commit()
        db.refresh(item)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"保存工作项失败: {str(e)}")

    return {"code": 200, "message": "工作项保存成功", "data": {"id": item.id}}


@router.delete("/work-items/{work_item_id}")
def delete_work_item(work_item_id: int, db: Session = Depends(get_db)):
    """删除工作项（已有日志引用时禁止删除）。"""
    item = db.query(models.WorkItem).filter(models.WorkItem.id == work_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="工作项不存在")

    has_log = db.query(models.WorkLog).filter(
        models.WorkLog.work_item_id == work_item_id
    ).first()
    if has_log:
        raise HTTPException(status_code=400, detail="该工作项已有日志记录，不能删除")

    db.delete(item)
    db.commit()
    return {"code": 200, "message": "工作项删除成功"}
