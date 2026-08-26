# xiangmu/backend/routers/work_logs.py
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, or_

import models
from database import get_db
from schemas import ConfirmCompletionIn, MonthScoreIn
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
            "work_package_code": pkg.code,
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
        "code": pkg.code,
        "project_id": pkg.project_id,
        "project_code": project.code,
        "project_name": project.name if project else "-",
        "project_category": project.category if project else "",  # 项目类别
        "category_name": pkg.category_name or "-",
        "objective": pkg.objective or "",  # 目标
        "project_owner_id": project.owner_id if project else "",
        "project_owner_name": proj_owner.username if proj_owner else "",
        "package_owner_id": pkg_owner_id,
        "package_owner_name": pkg_owner_name,
        "level": project.level if project else "",
        "package_tech_owner":pkg.tech_owner
    }


# ---------------------------------------------------------------- 项目分页/筛选（大数据量项目总览）
@router.get("/projects")
def get_paged_projects(page: int = 1,
                       page_size: int = 20,
                       keyword: str = None,
                       owner_id: str = None,
                       tech_owner_id: str = None,
                       level: str = None,
                       complete_status: str = None,
                       db: Session = Depends(get_db)):
    """项目分页 + 筛选 + 聚合统计：keyword(编号/名称)、owner_id、level、complete_status。"""
    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 20), 1), 100)

    q = db.query(models.Project)
    if keyword and str(keyword).strip():
        kw = f"%{str(keyword).strip()}%"
        q = q.filter(or_(models.Project.code.like(kw), models.Project.name.like(kw)))
    if owner_id:
        q = q.filter(models.Project.owner_id == owner_id)
    if level:
        q = q.filter(models.Project.level == level)
    if complete_status is not None and str(complete_status) != "":
        flag = str(complete_status).lower() in ("1", "true", "yes")
        q = q.filter(models.Project.complete_status == flag)

    total = q.count()
    projects = q.options(
        selectinload(models.Project.owner),
        selectinload(models.Project.work_packages).selectinload(
            models.WorkPackage.work_items
        ).selectinload(models.WorkItem.monthly_scores),
    ).order_by(models.Project.id).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for p in projects:
        wps = list(p.work_packages or [])
        done, full = 0.0, 0.0
        for wp in wps:
            for it in (wp.work_items or []):
                full += it.score or 0.0
                done += sum((ms.score or 0.0) for ms in (it.monthly_scores or []))
        items.append({
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "owner_id": p.owner_id or "-",
            "owner_name": p.owner.username if p.owner else "未指定负责人",
            "tech_owner_id": p.tech_owner_id or "-",
            "tech_owner_name": p.tech_owner.username if p.tech_owner else "未指定机型主管",
            "level": p.level or "",
            "category": p.category or "",
            "complete_status": bool(p.complete_status),
            "work_package_count": len(wps),
            "done_count": sum(1 for w in wps if w.complete_status),
            "work_item_count": sum(len(list(w.work_items or [])) for w in wps),
            "project_progress": calc_progress(done, full),
        })
    return {"code": 200, "data": {"total": total, "page": page, "page_size": page_size, "items": items}}


@router.get("/projects/{project_id}")
def get_project_detail(project_id: int, db: Session = Depends(get_db)):
    """项目详情（含聚合统计），供项目详情页标题/信息卡使用。"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    wps = list(project.work_packages or [])
    done, full = 0.0, 0.0
    for wp in wps:
        for it in (wp.work_items or []):
            full += it.score or 0.0
            done += sum((ms.score or 0.0) for ms in (it.monthly_scores or []))
    return {"code": 200, "data": {
        "id": project.id,
        "name": project.name,
        "code": project.code,
        "owner_id": project.owner_id or "-",
        "owner_name": project.owner.username if project.owner else "未指定负责人",
        "tech_owner_id": project.tech_owner_id or "-",
        "tech_owner_name": project.tech_owner.username if project.tech_owner else "未指定机型主管",
        "level": project.level or "",
        "category": project.category or "",
        "complete_status": bool(project.complete_status),
        "work_package_count": len(wps),
        "done_count": sum(1 for w in wps if w.complete_status),
        "work_item_count": sum(len(list(w.work_items or [])) for w in wps),
        "project_progress": calc_progress(done, full),
    }}


@router.get("/projects/{project_id}/work-packages")
def get_paged_project_work_packages(project_id: int,
                                    page: int = 1,
                                    page_size: int = 20,
                                    keyword: str = None,
                                    db: Session = Depends(get_db)):
    """某项目下的工作包分页 + 筛选：keyword(工作包编号/类别/下阶段工作)。"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 20), 1), 100)

    q = db.query(models.WorkPackage).filter(models.WorkPackage.project_id == project_id)
    if keyword and str(keyword).strip():
        kw = f"%{str(keyword).strip()}%"
        q = q.filter(or_(
            models.WorkPackage.id.like(kw),
            models.WorkPackage.category_name.like(kw),
        ))

    total = q.count()
    pkgs = q.options(
        selectinload(models.WorkPackage.owner),
        selectinload(models.WorkPackage.project).selectinload(models.Project.owner),
        selectinload(models.WorkPackage.work_items).selectinload(models.WorkItem.monthly_scores),
    ).order_by(models.WorkPackage.id).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for pkg in pkgs:
        view = _public_package_view(pkg, db)
        done = sum(
            sum((ms.score or 0.0) for ms in (it.monthly_scores or []))
            for it in (pkg.work_items or [])
        )
        full = sum(it.score or 0.0 for it in (pkg.work_items or []))
        view["package_progress"] = calc_progress(done, full)
        view["work_item_count"] = len(list(pkg.work_items or []))
        view["done_count"] = sum(1 for it in (pkg.work_items or []) if it.complete_status)
        view["complete_status"] = bool(pkg.complete_status)
        items.append(view)
    return {"code": 200, "data": {
        "project_id": project_id,
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }}


@router.get("/my-work-packages/{user_id}")
def get_my_work_packages_paged(user_id: str,
                              page: int = 1,
                              page_size: int = 20,
                              db: Session = Depends(get_db)):
    """我的工作：当前用户负责的工作包（分页 + 进度统计）。"""
    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 20), 1), 100)

    q = db.query(models.WorkPackage).filter(models.WorkPackage.owner_id == user_id)
    total = q.count()
    pkgs = q.options(
        selectinload(models.WorkPackage.owner),
        selectinload(models.WorkPackage.project).selectinload(models.Project.owner),
        selectinload(models.WorkPackage.work_items).selectinload(models.WorkItem.monthly_scores),
    ).order_by(models.WorkPackage.id).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for pkg in pkgs:
        view = _public_package_view(pkg, db)
        done = sum(
            sum((ms.score or 0.0) for ms in (it.monthly_scores or []))
            for it in (pkg.work_items or [])
        )
        full = sum(it.score or 0.0 for it in (pkg.work_items or []))
        view["package_progress"] = calc_progress(done, full)
        view["work_item_count"] = len(list(pkg.work_items or []))
        view["complete_status"] = bool(pkg.complete_status)
        items.append(view)
    return {"code": 200, "data": {
        "user_id": user_id,
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }}


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
        "work_package_code": item.work_package.code
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

    remaining_scores = {}
    if item_ids:
        work_items = db.query(models.WorkItem).filter(models.WorkItem.id.in_(item_ids)).all()
        for item in work_items:
            total_score = item.score or 0.0
            completed_score = acc_sum.get(item.id, 0.0)
            remaining_scores[item.id] = total_score - completed_score

    # 工作包级扣分汇总：超期完成的工作项每个扣 1 分
    deducted = sum(compute_deducted(it) for it in items)

    return {
        "code": 200,
        "data": {
            "work_package": {
                "id": pkg.id,
                "code": pkg.code,
                "project_id": pkg.project_id,
                "project_code":project.code if project else "-",
                "project_name": project.name if project else "-",
                "category_name": pkg.category_name or "-",
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
                    "remaining_score": remaining_scores.get(it.id, 0.0),
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


# ---------------------------------------------------------------- 确认完成（负责人手动标记，完成时间随确认记录）
@router.put("/confirm-completion")
def confirm_completion(data: ConfirmCompletionIn, db: Session = Depends(get_db)):
    """确认/取消完成：只有负责人（或领导/管理员）可操作。
    确认时记录完成时间（仅工作项有 completed_at）；取消时清空。
    """
    operator = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="操作人不存在")
    role = str(operator.role).upper()

    # 定位目标对象与负责人
    target = None
    owner_id = None
    try:
        if data.target_type == "work_item":
            target = db.query(models.WorkItem).filter(
                models.WorkItem.id == int(data.target_id)
            ).first()
            if target:
                owner_id = target.work_package.owner_id if target.work_package else None
        elif data.target_type == "work_package":
            target = db.query(models.WorkPackage).filter(
                models.WorkPackage.id == data.target_id
            ).first()
            if target:
                owner_id = target.owner_id
        elif data.target_type == "project":
            target = db.query(models.Project).filter(
                models.Project.id == int(data.target_id)
            ).first()
            if target:
                owner_id = target.owner_id
        else:
            raise HTTPException(status_code=400, detail="target_type 必须是 work_item / work_package / project")
    except ValueError:
        raise HTTPException(status_code=400, detail="target_id 格式错误")

    if not target:
        raise HTTPException(status_code=404, detail="目标不存在")

    # 权限：负责人本人 / 领导 / 管理员
    if role not in ("LEADER", "ADMIN") and str(owner_id or "") != str(operator.id):
        raise HTTPException(status_code=403, detail="只有负责人或领导可以确认完成")

    confirmed = bool(data.confirmed)
    target.complete_status = confirmed

    # 完成时间：仅工作项有 completed_at 列，且只在确认完成时记录 / 取消时清空
    if data.target_type == "work_item":
        if confirmed:
            if not target.completed_at:
                target.completed_at = datetime.now()
        else:
            target.completed_at = None

    db.commit()
    return {
        "code": 200,
        "message": "已确认完成" if confirmed else "已取消完成",
        "data": {
            "target_type": data.target_type,
            "target_id": data.target_id,
            "complete_status": confirmed,
        },
    }

