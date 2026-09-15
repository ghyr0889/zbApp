# xiangmu/backend/routers/work_logs.py
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, or_, exists

import models
import json
from database import get_db
from schemas import ConfirmCompletionIn, MonthScoreIn, ConfirmClosed
from utils import project_effective_complete, package_effective_complete, deadline_str, effective_complete, calc_progress, ensure_open
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
            "work_package_name": pkg.name,
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
    pkg_tech_owner = pkg.tech_owner
    pkg_tech_owner_id = pkg.tech_owner_id or ""
    pkg_tech_owner_name = pkg_tech_owner.username if pkg_tech_owner else ""

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
        "package_tech_owner_id": pkg_tech_owner_id,
        "package_tech_owner_name": pkg_tech_owner_name,
        "level": project.level if project else "",
        "name": pkg.name or "-",
        # 生效完成状态（由调用方追加）：手动确认 或 其下全部工作项已完成
        "manual_complete_status": bool(pkg.complete_status),
        "closed_status": bool(pkg.isclosed),
        "project_closed": bool(project.isclosed if project else False)
    }


# ---------------------------------------------------------------- 项目分页/筛选（大数据量项目总览）
@router.get("/projects")
def get_paged_projects(page: int = 1,
                       page_size: int = 20,
                       keyword: str = None,
                       owner_id: str = None,
                       level: str = None,
                       complete_status: str = None,
                       db: Session = Depends(get_db)):
    """项目分页 + 筛选 + 聚合统计：keyword(编号/名称)、owner_id、level、complete_status。"""
    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 20), 1), 100)

    q = db.query(models.Project)
    if keyword and str(keyword).strip():
        kw = f"%{str(keyword).strip()}%"
        q = q.filter(or_(models.Project.code.like(kw), 
                         models.Project.name.like(kw),
                         models.Project.tech_owner.has(models.User.username.like(kw)),
                        )
                    )
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
            "complete_status": project_effective_complete(p),
            "manual_complete_status": bool(p.complete_status),
            "closed_status": bool(p.isclosed),
            "work_package_count": len(wps),
            "done_count": sum(1 for w in wps if package_effective_complete(w)),
            "work_item_count": sum(len(list(w.work_items or [])) for w in wps),
            "project_progress": calc_progress(done, full),
        })
    return {"code": 200, "data": {"total": total, "page": page, "page_size": page_size, "items": items}}


@router.get("/projects/{project_id}")
def get_project_detail(project_id: int, db: Session = Depends(get_db)):
    """项目详情（含聚合统计），供项目详情页标题/信息卡使用。"""
    project = db.query(models.Project).options(
        selectinload(models.Project.owner),
        selectinload(models.Project.tech_owner),
        selectinload(models.Project.work_packages).selectinload(
            models.WorkPackage.work_items
        ).selectinload(models.WorkItem.monthly_scores),
    ).filter(models.Project.id == project_id).first()
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
        "complete_status": project_effective_complete(project),
        "manual_complete_status": bool(project.complete_status),
        "closed_status": bool(project.isclosed),
        "work_package_count": len(wps),
        "done_count": sum(1 for w in wps if package_effective_complete(w)),
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
        view["done_count"] = sum(1 for it in (pkg.work_items or []) if effective_complete(it))
        view["complete_status"] = package_effective_complete(pkg)
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

    # 我负责的工作包 + 我负责的工作项所属的工作包（转办接收后能看到自己的工作项）
    q = db.query(models.WorkPackage).filter(or_(
        models.WorkPackage.owner_id == user_id,
        exists().where(
            models.WorkItem.work_package_id == models.WorkPackage.id,
            models.WorkItem.owner_id == user_id,
        )
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
        view["complete_status"] = package_effective_complete(pkg)
        items.append(view)
    return {"code": 200, "data": {
        "user_id": user_id,
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }}


# ---------------------------------------------------------------- 工作项管理
def _work_item_view(item, pending_review_id=None):
    """把 WorkItem 展开为前端需要的结构。

    - complete_status：是否已完成（以技术负责人审核通过为准）
    - pending_complete_review：是否有待审核的完成申请
    - can_submit_complete：是否满足提交完成申请的条件（进度满 或 已手动确认）
    """
    return {
        "id": item.id,
        "name": item.name,
        "standard": item.standard or "",
        "difficulty": item.difficulty or "",
        "importance": item.importance or "",
        "innovation": item.innovation or "",
        "deadline": deadline_str(item.deadline) if item.deadline else "",
        "score": item.score or 0.0,
        "completed_at": deadline_str(item.completed_at),
        # 已完成：只有审核通过（complete_status 置位）才算
        "complete_status": bool(item.complete_status),
        # 是否有待审核的完成申请
        "pending_complete_review": bool(pending_review_id),
        "pending_review_id": pending_review_id,
        # 是否满足“提交完成申请”的条件
        "can_submit_complete": effective_complete(item),
        # 兼容旧字段：含义与 complete_status 一致
        "manual_complete_status": bool(item.complete_status),
        "owner_id": item.owner_id or "",
        "owner_name": item.owner.username if item.owner else "",
        "tech_owner_id": item.tech_owner_id or "",
        "tech_owner_name": item.tech_owner.username if item.tech_owner else "",
        "notes": item.notes or "-",
        "work_package_id": item.work_package_id,
        "work_package_code": item.work_package.code,
        "closed_status": bool(item.isclosed)
    }



@router.get("/work-packages/{work_package_id}/work-items")
def get_work_items(work_package_id: str, month: str = None, db: Session = Depends(get_db)):
    """查询某个工作包下的全部工作项（含指定月份的分值，默认当月，供工作项页面使用）。"""
    pkg = db.query(models.WorkPackage).filter(
        models.WorkPackage.id == work_package_id
    ).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="工作包不存在")

    # 预加载月度分值与负责人：_work_item_view 的进度/提交条件需要
    items = db.query(models.WorkItem).options(
        selectinload(models.WorkItem.owner),
        selectinload(models.WorkItem.tech_owner),
        selectinload(models.WorkItem.monthly_scores),
    ).filter(
        models.WorkItem.work_package_id == work_package_id
    ).order_by(models.WorkItem.id).all()
    project = pkg.project
    owner_job_grade = pkg.owner.job_grade if pkg.owner else ""

    # 指定月份分值：默认当月；前端在每月前2天可切换查看/补填上月
    cur_month = month or datetime.now().strftime("%Y-%m")
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

    # 待技术负责人审核的完成申请：work_item_id -> 申请 id
    pending_reviews = {}
    if item_ids:
        for r in db.query(models.WorkItemCompletionReview).filter(
            models.WorkItemCompletionReview.work_item_id.in_(item_ids),
            models.WorkItemCompletionReview.status == "PENDING"
        ).all():
            pending_reviews[r.work_item_id] = r.id

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
                "name": pkg.name or "-",
                "closed_status": bool(pkg.isclosed),
                "project_closed": bool(project.isclosed if project else False)
            },
            "work_items": [
                {
                    **_work_item_view(it, pending_reviews.get(it.id)),
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
    item = db.query(models.WorkItem).options(
        selectinload(models.WorkItem.monthly_scores),
    ).filter(models.WorkItem.id == work_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="工作项不存在")
    
    pending_requests = db.query(models.WorkPackageSplitRequest).filter(
        models.WorkPackageSplitRequest.work_package_id == item.work_package_id,
        models.WorkPackageSplitRequest.status.in_(["PENDING", "SUBMITTED"])
    ).all()

    for req in pending_requests:
        try:
            split_items = json.loads(req.split_items or "[]")
        except (TypeError, ValueError):
            split_items = []                      # 兼容脏数据 / 空值
        if not isinstance(split_items, list):
            continue
        for split_item in split_items:
            if not isinstance(split_item, dict):
                continue
            if str(split_item.get("work_item_id")) == str(work_item_id):
                raise HTTPException(status_code=400, detail="该工作项正在审核申请中，不能删除")
            
    # 已完成（审核通过）或存在待审核完成申请时，不能删除
    if bool(item.complete_status):
        raise HTTPException(status_code=400, detail="工作项已完成，不能删除")
    if db.query(models.WorkItemCompletionReview).filter(
        models.WorkItemCompletionReview.work_item_id == work_item_id,
        models.WorkItemCompletionReview.status == "PENDING"
    ).first():
        raise HTTPException(status_code=400, detail="该工作项有待审核的完成申请，不能删除")

    ensure_open(item, item.work_package,
                item.work_package.project if item.work_package else None)

    # 一并清理该工作项的完成申请记录（表未设级联删除）
    db.query(models.WorkItemCompletionReview).filter(
        models.WorkItemCompletionReview.work_item_id == work_item_id
    ).delete(synchronize_session=False)

    db.delete(item)
    db.commit()
    return {"code": 200, "message": "工作项删除成功"}


# ---------------------------------------------------------------- 确认完成（负责人手动标记，完成时间随确认记录）
@router.put("/confirm-completion")
def confirm_completion(data: ConfirmCompletionIn, db: Session = Depends(get_db)):
    """确认/取消完成。

    - 工作项：改为“提交完成申请 / 撤回申请”，由技术负责人在 complete_review 里审核，
      审核通过后才置 complete_status 并写 completed_at。
    - 工作包 / 项目：仍是负责人（或领导/管理员）直接手动确认。
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
                # 工作项负责人优先，其次工作包负责人
                owner_id = target.owner_id
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
            raise HTTPException(status_code=400, detail="目标类型必须是 work_item / work_package / project")
    except ValueError:
        raise HTTPException(status_code=400, detail="目标 id 格式错误")

    if not target:
        raise HTTPException(status_code=404, detail="目标不存在")

    # 权限：负责人本人 / 领导 / 管理员
    if role not in ("LEADER", "ADMIN") and str(owner_id or "") != str(operator.id):
        raise HTTPException(status_code=403, detail="只有负责人、领导和管理员可以确认完成")

    # 关闭后不能再确认/取消完成（自身或其父级任一关闭都锁定）
    chain = [target]
    if data.target_type == "work_item" and target.work_package:
        chain += [target.work_package, target.work_package.project]
    elif data.target_type == "work_package" and target.project:
        chain += [target.project]
    ensure_open(*chain)

    confirmed = bool(data.confirmed)

    # ---------- 工作项：走“提交完成申请 → 技术负责人审核”流程 ----------
    if data.target_type == "work_item":
        if confirmed:
            # 幂等：已有待审核申请则复用，不重复建单
            existing = db.query(models.WorkItemCompletionReview).filter(
                models.WorkItemCompletionReview.work_item_id == target.id,
                models.WorkItemCompletionReview.status == "PENDING",
            ).first()
            if not existing:
                db.add(models.WorkItemCompletionReview(
                    work_item_id=target.id,
                    applicant_id=operator.id,
                    reason="负责人手动确认完成",
                    status="PENDING",
                ))
            db.commit()
            return {
                "code": 200,
                "message": "已提交，等待技术负责人审核",
                "data": {
                    "target_type": "work_item",
                    "target_id": target.id,
                    "complete_status": bool(target.complete_status),
                    "pending_complete_review": True,
                    "manual_complete_status": True,
                },
            }

        # 取消 = 撤回待审核的完成申请（保留记录，标记为已驳回）
        pending = db.query(models.WorkItemCompletionReview).filter(
            models.WorkItemCompletionReview.work_item_id == target.id,
            models.WorkItemCompletionReview.status == "PENDING",
        ).first()
        if pending:
            pending.status = "REJECTED"
            pending.review_comment = "申请人撤回"
            pending.reviewed_at = datetime.now()
        db.commit()
        return {
            "code": 200,
            "message": "已撤回完成申请",
            "data": {
                "target_type": "work_item",
                "target_id": target.id,
                "complete_status": bool(target.complete_status),
                "pending_complete_review": False,
                "manual_complete_status": False,
            },
        }

    # ---------- 工作包 / 项目：保持手动确认 ----------
    target.complete_status = confirmed
    db.commit()
    return {
        "code": 200,
        "message": "已确认完成" if confirmed else "已取消完成",
        "data": {
            "target_type": data.target_type,
            "target_id": data.target_id,
            "complete_status": confirmed,
            "manual_complete_status": confirmed,
        },
    }

# ---------------------------------------------------------------- 确认关闭（只有领导和管理员有权限）
@router.put("/confirm-closed")
def confirm_closed(data: ConfirmClosed, db: Session = Depends(get_db)):
    """确认关闭：或领导/管理员可操作。"""
    operator = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="操作人不存在")
    role = str(operator.role).upper()

    # 定位目标对象与负责人
    target = None
    try:
        if data.target_type == "work_item":
            target = db.query(models.WorkItem).filter(models.WorkItem.id == int(data.target_id)).first()
        elif data.target_type == "work_package":
            target = db.query(models.WorkPackage).filter(models.WorkPackage.id == data.target_id).first()
        elif data.target_type == "project":
            target = db.query(models.Project).filter(models.Project.id == int(data.target_id) ).first()
        else:
            raise HTTPException(status_code=400, detail="目标类型 必须是 work_item / work_package / project")
    except ValueError:
        raise HTTPException(status_code=400, detail="目标id 格式错误")

    if not target:
        raise HTTPException(status_code=404, detail="目标不存在")

    # 权限：只有领导和管理员可以确认关闭
    if role not in ("LEADER", "ADMIN"):
        raise HTTPException(status_code=403, detail="只有领导或管理员可以确认关闭")

    confirmed = bool(data.confirmed)

    if not confirmed and role != "ADMIN":
        raise HTTPException(status_code=403, detail="只有管理员可以取消关闭")
    
    target.isclosed = confirmed

    db.commit()
    return {
        "code": 200,
        "message": "已确认关闭" if confirmed else "已取消关闭",
        "data": {
            "target_type": data.target_type,
            "target_id": data.target_id,
            "closed_status": confirmed,
        },
    }