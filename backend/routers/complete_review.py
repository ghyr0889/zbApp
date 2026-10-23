from decimal import Decimal, ROUND_HALF_UP
import math
import json
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, selectinload

import models
from database import get_db
from dependencies import get_current_user
from schemas import CompleteRequestReview, CompleteRequestCreate
from services.score_board_service import apply_completion_quality
from utils import ensure_open, effective_complete, item_progress

router = APIRouter(prefix="/api/v1/complete_review", tags=["Complete Review"])

def _complete_request_view(req):
    """把完成申请展开为前端需要的结构。"""
    item = req.work_item
    work_package = item.work_package if item else None
    project = work_package.project if work_package else None
    return {
        "id": req.id,
        "work_item_id": req.work_item_id,
        "work_package_id": work_package.id if work_package else None,
        "work_package_code": work_package.code if work_package else "-",
        "work_package_name": work_package.name if work_package else "-",
        "work_package_objective": work_package.objective if work_package else "-",
        "pkg_closed": bool(work_package.isclosed) if work_package else False,
        "project_id": work_package.project_id if work_package else None,
        "project_name": project.name if project else "-",
        "project_owner_id": project.owner_id if project else "",
        "project_owner_name": project.owner.username if (project and project.owner) else "",
        "project_closed": bool(project.isclosed) if project else False,
        "category_name": work_package.category_name if work_package else "-",
        "applicant_id": req.applicant_id,
        "applicant_name": req.applicant.username if req.applicant else req.applicant_id,
        "status": req.status,
        "reason": req.reason or "",
        "reviewer_id": req.reviewer_id or "",
        "review_comment": req.review_comment or "",
        "created_at": req.created_at.strftime("%Y-%m-%d %H:%M") if req.created_at else "-",
        "reviewed_at": req.reviewed_at.strftime("%Y-%m-%d %H:%M") if req.reviewed_at else "-",
        # 工作项摘要（不要直接把 ORM 对象交给前端）
        "complete_item": {
            "id": item.id,
            "name": item.name,
            "standard": item.standard,
            "difficulty": item.difficulty,
            "importance": item.importance,
            "innovation": item.innovation,
            "notes": item.notes,
            "score": item.score or 0.0,
            "deadline": item.deadline.strftime("%Y-%m-%d") if item.deadline else "",
            "owner_id": item.owner_id or "",
            "owner_name": item.owner.username if item.owner else "",
            "tech_owner_id": item.tech_owner_id or "",
            "tech_owner_name": item.tech_owner.username if item.tech_owner else "",
            "progress": item_progress(item),
            "complete_status": bool(item.complete_status),
        } if item else None,
    }

@router.get("/complete-requests")
def get_complete_requests(user_id: str = Query(...), db: Session = Depends(get_db)):
    """查询完成申请。普通员工：只看自己的申请。
    科室主任 / 领导 / 管理员：查看全部申请（各自审核对应状态的申请）"""
    viewer = db.query(models.User).filter(models.User.id == user_id).first()
    if not viewer:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 预加载关联对象，避免逐行懒加载（N+1）
    opts = (
        selectinload(models.WorkItemCompletionReview.applicant),
        selectinload(models.WorkItemCompletionReview.work_item).selectinload(models.WorkItem.owner),
        selectinload(models.WorkItemCompletionReview.work_item).selectinload(models.WorkItem.tech_owner),
        selectinload(models.WorkItemCompletionReview.work_item).selectinload(models.WorkItem.monthly_scores),
        selectinload(models.WorkItemCompletionReview.work_item)
            .selectinload(models.WorkItem.work_package)
            .selectinload(models.WorkPackage.project)
            .selectinload(models.Project.owner),
    )
    role = str(viewer.role).upper()
    if role in ["LEADER", "ADMIN", "DEPARTMENT"]:
        requests = db.query(models.WorkItemCompletionReview).options(*opts).order_by(
            models.WorkItemCompletionReview.created_at.desc()
        ).all()
    else:
        # 普通员工：我提交的申请 + 待我（作为技术负责人）审核的申请
        to_review = models.WorkItemCompletionReview.work_item.has( models.WorkItem.tech_owner_id == user_id)
        requests = db.query(models.WorkItemCompletionReview).options(*opts).filter(
            or_(models.WorkItemCompletionReview.applicant_id == user_id,
                and_(models.WorkItemCompletionReview.status == "PENDING", to_review),)).order_by(
                    models.WorkItemCompletionReview.created_at.desc()).all()

    return {"code": 200, "data": [_complete_request_view(r) for r in requests]}

@router.post("/complete-requests/{request_id}/review")
def review_complete_request(request_id: int, body: CompleteRequestReview, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """工作项技术负责人审核完成申请：APPROVE → 写完成状态与完成时间 / REJECT → 驳回。"""
    req = db.query(models.WorkItemCompletionReview).options(
        selectinload(models.WorkItemCompletionReview.work_item),
    ).filter(models.WorkItemCompletionReview.id == request_id).with_for_update().first()
    if not req:
        raise HTTPException(status_code=404, detail="申请不存在")

    # 以申请单关联的工作项为准（不信任前端传入的 item_id，避免审错对象）
    item = db.query(models.WorkItem).filter(models.WorkItem.id == req.work_item_id).with_for_update().populate_existing().first()
    if not item:
        raise HTTPException(status_code=400, detail="工作项不存在，无法处理")

    reviewer = db.query(models.User).filter(models.User.id == user.id).first()
    if not reviewer:
        raise HTTPException(status_code=404, detail="审核人不存在")

    action = (body.action or "APPROVE").upper()
    if action not in ["APPROVE", "REJECT"]:
        raise HTTPException(status_code=400, detail="无效的审核动作，只能是 APPROVE / REJECT")

    # 只有该工作项的技术负责人可以审核；
    is_tech_owner = bool(item.tech_owner_id) and str(reviewer.id) == str(item.tech_owner_id)
    if not is_tech_owner:
        raise HTTPException(status_code=403, detail="只有该工作项的技术负责人可以审核")

    # 只有待审核状态可以处理，避免重复审核
    if req.status != "PENDING":
        raise HTTPException(status_code=400, detail="该申请已处理，不能重复审核")

    try:
        req.reviewer_id = reviewer.id
        req.reviewed_at = datetime.now(timezone(timedelta(hours=8))).replace(tzinfo=None)

        if action == "REJECT":
            comment = (body.comment or "").strip()
            if not comment:
                raise HTTPException(status_code=400, detail="驳回时必须填写驳回原因")
            req.status = "REJECTED"
            req.review_comment = comment
            # 驳回：不产生完成时间，也就不参与扣分
            item.complete_status = False
            item.completed_at = None
        else:  # APPROVE
            work_package = item.work_package
            project = work_package.project if work_package else None
            ensure_open(item, work_package, project)  # 已关闭不能审批生效
            if body.quality_percent is None:
                raise HTTPException(400, "通过完成审批时必须填写质量系数（百分比）")
            if item.complete_status:
                raise HTTPException(409, "该工作项已完成，不能重复审批打分")
            base_score = Decimal(str(item.score or 0))
            percent = Decimal(str(body.quality_percent))
            calculated = base_score * (percent / Decimal("100") - 1)
            if not calculated.is_finite() or not math.isfinite(float(calculated)):
                raise HTTPException(422, "质量系数过大，无法计算")
            quality_score = float(calculated.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            month = apply_completion_quality(db, item, quality_score, req.reviewed_at)
            req.status = "APPROVED"
            req.review_comment = ((body.comment or "").strip() or "审核通过") + f"；基础总分：{base_score}；质量系数：{body.quality_percent}%；{month}质量分：{quality_score}"
            # 完成时间 = 审核通过时间；扣分以其是否超出 deadline+7 天 判定
            item.complete_status = True
            item.completed_at = req.reviewed_at

        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"处理完成申请失败: {str(e)}")

    message = "申请已通过，该工作项已完成" if action == "APPROVE" else "申请已驳回"
    return {"code": 200, "message": message, "data": {"id": req.id, "status": req.status}}

@router.post("/complete-requests")
def create_complete_request(body: CompleteRequestCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """提交工作项完成申请：进度已满或负责人手动确认后可提交，等待技术负责人审核。"""
    item = db.query(models.WorkItem).options(
        selectinload(models.WorkItem.monthly_scores),
    ).filter(models.WorkItem.id == body.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="工作项不存在")

    work_package = item.work_package
    ensure_open(item, work_package, work_package.project)

    applicant = db.query(models.User).filter(models.User.id == user.id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="申请人不存在")

    # 完成说明必须由责任人本人提交，不能通过请求体指定其他申请人。
    if str(applicant.id) != str(item.owner_id or ""):
        raise HTTPException(status_code=403, detail="请由工作项责任人填写说明并提交完成审核")
    reason = body.reason.strip()
    if not reason:
        raise HTTPException(status_code=400, detail="请对照工作项目标填写完成说明")

    # 已审核通过的不需要再提交
    if bool(item.complete_status):
        raise HTTPException(status_code=400, detail="该工作项已完成，无需重复提交")

    existing = db.query(models.WorkItemCompletionReview).filter(
            models.WorkItemCompletionReview.work_item_id == item.id,
            models.WorkItemCompletionReview.status == "PENDING").first()
    if existing:
        return {"code": 200, "message": "该工作项已有待审核的完成申请",
                "data": {"id": existing.id, "work_item_id": existing.work_item_id,
                         "status": existing.status}}

    # 条件校验：进度已满 或 手动确认
    if not effective_complete(item):
        raise HTTPException(
            status_code=400,
            detail="进度未满且未手动确认，暂不能提交完工申请",
        )

    # 创建审核单
    review = models.WorkItemCompletionReview(
        work_item_id=item.id,
        applicant_id=applicant.id,
        reason=reason,
        status="PENDING",
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return {"code": 200, "message": "已提交，等待技术负责人审核",
            "data": {"id": review.id, "work_item_id": review.work_item_id,
                     "status": review.status}}
