# xiangmu/backend/routers/work_logs.py
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import MonthScoreIn
from utils import work_package_summary, deadline_str, parse_deadline, calc_progress
from routers.score_board import compute_calc_score, compute_deducted, monthly_quality_score

router = APIRouter(prefix="/api/v1/work-logs", tags=["Work Logs"])




# ---------------------------------------------------------------- 我的工作包（员工用于申请拆分）
@router.get("/my-assigned-work-packages/{user_id}")
def get_my_assigned_work_packages(user_id: str, db: Session = Depends(get_db)):
    """返回当前用户负责的工作包（用于申请拆分工作包等场景）。"""
    packages = db.query(models.WorkPackage).filter(
        models.WorkPackage.owner_id == user_id
    ).all()
    data = []
    for pkg in packages:
        project = pkg.project
        proj_owner = project.owner if project else None
        data.append({
            "work_package_id": pkg.id,
            "project_id": pkg.project_id,
            "project_name": project.name if project else "-",
            "category_name": pkg.category_name or "-",
            "project_owner": proj_owner.username
        })
    return {"code": 200, "data": data}


# ---------------------------------------------------------------- 公开工作包（项目总览）
def _public_package_view(pkg, db):
    project = pkg.project
    # 项目负责人（供前端“项目行”展示）
    proj_owner = project.owner if project else None
    # 工作包负责人（供前端“工作包行”展示）
    pkg_owner = pkg.owner
    pkg_owner_id = pkg.owner_id or ""
    pkg_owner_name = pkg_owner.username if pkg_owner else ""

    return {
        "id": pkg.id,
        "project_id": pkg.project_id,
        "project_code": project.code,
        "project_name": project.name if project else "-",
        "project_category": project.category if project else "",  # 项目类别
        "category_name": pkg.category_name or "-",
        "next_step_work": pkg.next_step_work or "",  # 下阶段工作
        "objective": pkg.objective or "",  # 目标
        "project_owner_id": project.owner_id if project else "",
        "project_owner_name": proj_owner.username if proj_owner else "",
        "package_owner_id": pkg_owner_id,
        "package_owner_name": pkg_owner_name,
        "level": project.level if project else "",
    }


@router.get("/public-work-packages")
def get_public_work_packages(db: Session = Depends(get_db)):
    packages = db.query(models.WorkPackage).all()

    # 累计各工作项所有月份分值（进度 = 累计完成量 / 工作项分值，封顶 100%）
    sum_by_item = {}
    for r in db.query(models.WorkItemMonthlyScore).all():
        sum_by_item[r.work_item_id] = sum_by_item.get(r.work_item_id, 0.0) + (r.score or 0.0)

    # 项目聚合：完成量 / 满分
    project_done = {}
    for pkg in packages:
        done = sum(sum_by_item.get(it.id, 0.0) for it in (pkg.work_items or []))
        full = sum(it.score or 0.0 for it in (pkg.work_items or []))
        d, f = project_done.get(pkg.project_id, (0.0, 0.0))
        project_done[pkg.project_id] = (d + done, f + full)

    data = []
    for pkg in packages:
        view = _public_package_view(pkg, db)
        done = sum(sum_by_item.get(it.id, 0.0) for it in (pkg.work_items or []))
        full = sum(it.score or 0.0 for it in (pkg.work_items or []))
        view["package_progress"] = calc_progress(done, full)
        pd, pf = project_done.get(pkg.project_id, (0.0, 0.0))
        view["project_progress"] = calc_progress(pd, pf)
        data.append(view)

    # 补充没有任何工作包的项目（占位记录），保证新建项目在总览中也能显示
    project_ids_with_pkgs = {p["project_id"] for p in data}
    for project in db.query(models.Project).all():
        if project.id in project_ids_with_pkgs:
            continue
        owner = project.owner
        data.append({
            "id": "",
            "project_id": project.id,
            "project_code": project.code,
            "project_name": project.name,
            "project_category": project.category or "",
            "category_name": "-",
            "next_step_work": "",
            "objective": "",
            "project_owner_id": project.owner_id or "",
            "project_owner_name": owner.username if owner else "",
            "package_owner_id": "",
            "package_owner_name": "",
            "package_progress": 0,
            "project_progress": 0,
            "score": 0,
            "deadline": "-",
            "pkg_completed": False,
            "project_completed": False,
            "level": project.level or "",
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
        "completed_at": deadline_str(item.completed_at),
        "complete_status": item.complete_status or "",
        "work_package_id": item.work_package_id,
    }



@router.get("/work-packages/{work_package_id}/work-items")
def get_work_items(work_package_id: str, db: Session = Depends(get_db)):
    """查询某个工作包下的全部工作项（含工作包信息与当月分值，供工作项页面使用）。"""
    pkg = db.query(models.WorkPackage).filter(
        models.WorkPackage.id == work_package_id
    ).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="工作包不存在")

    items = db.query(models.WorkItem).filter(
        models.WorkItem.work_package_id == work_package_id
    ).order_by(models.WorkItem.id).all()
    project = pkg.project
    owner_job_grade = pkg.owner.job_grade if pkg.owner else ""

    # 当月分值：从月度分值表取当月记录（覆盖单列冗余值）
    cur_month = datetime.now().strftime("%Y-%m")
    item_ids = [it.id for it in items]
    month_scores = {}
    calc_scores = {}
    if item_ids:
        rows = db.query(models.WorkItemMonthlyScore).filter(
            models.WorkItemMonthlyScore.work_item_id.in_(item_ids),
            models.WorkItemMonthlyScore.month == cur_month
        ).all()
        month_scores = {r.work_item_id: r.score for r in rows}
        calc_scores = {r.work_item_id: r.calculate_score for r in rows}

    # 累计各工作项所有月份分值（进度 = 累计完成量 / 工作项分值，封顶 100%）
    acc_sum = {}
    if item_ids:
        for r in db.query(models.WorkItemMonthlyScore).filter(
            models.WorkItemMonthlyScore.work_item_id.in_(item_ids)
        ).all():
            acc_sum[r.work_item_id] = acc_sum.get(r.work_item_id, 0.0) + (r.score or 0.0)

    # 工作包级扣分汇总：超期完成的工作项每个扣 1 分
    deducted = sum(compute_deducted(it) for it in items)

    return {
        "code": 200,
        "data": {
            "work_package": {
                "id": pkg.id,
                "project_id": pkg.project_id,
                "project_code":project.code if project else "-",
                "project_name": project.name if project else "-",
                "category_name": pkg.category_name or "-",
                "next_step_work": pkg.next_step_work or "",
                "objective": pkg.objective or "",
                "owner_id": pkg.owner_id or "",
                "owner_name": pkg.owner.username if pkg.owner else "",
                "deducted_score": deducted,
            },
            "work_items": [
                {
                    **_work_item_view(it),
                    "month_score": month_scores.get(it.id, 0.0),
                    "quality_score": monthly_quality_score(db, it.id, cur_month),
                    "calc_score": calc_scores.get(it.id) if calc_scores.get(it.id) is not None else compute_calc_score(month_scores.get(it.id, 0.0), it, db, owner_job_grade, monthly_quality_score(db, it.id, cur_month)),
                    "progress": calc_progress(acc_sum.get(it.id, 0.0), it.score or 0.0),
                    "deducted_score": compute_deducted(it),
                    "month": cur_month,
                }
                for it in items
            ],
        }
    }


@router.delete("/work-items/{work_item_id}")
def delete_work_item(work_item_id: int, db: Session = Depends(get_db)):
    """删除工作项。"""
    item = db.query(models.WorkItem).filter(models.WorkItem.id == work_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="工作项不存在")
    if item.complete_status:
        raise HTTPException(status_code=400, detail="工作项已完成，不能删除")

    db.delete(item)
    db.commit()
    return {"code": 200, "message": "工作项删除成功"}

