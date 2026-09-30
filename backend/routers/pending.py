# xiangmu/backend/routers/pending.py
"""待办数量汇总：一次请求驱动左侧菜单红点与三个页签的角标。

口径与各页面列表保持一致（前端「红点」= 页内能看到的待处理条数）：
- review    审批查阅 → 拆分申请：按角色取 PENDING / SUBMITTED / REJECTED
- complete  完成申请 → 工作项完成审核：与 complete_review 列表同样的可见范围
- transfers 工作包转办 → 待我接收的转办：to_user_id + PENDING

只做 count() 聚合查询，不把行拉回 Python：该接口会被前端轮询（约 45s 一次）。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

import models
from database import get_db
from utils import pending_status_for

router = APIRouter(prefix="/api/v1/pending", tags=["Pending"])


def _review_pending(db: Session, viewer, role: str) -> int:
    """审批查阅：我该处理的拆分申请数量。"""
    status = pending_status_for(role)
    if not status:
        return 0  # 未知角色视为没有待办，不因为脏数据让整个红点接口报错
    q = db.query(models.WorkPackageSplitRequest).filter(
        models.WorkPackageSplitRequest.status == status
    )
    if role == "EMPLOYEE":
        # 员工只认自己名下被驳回的申请，别把全公司的驳回都算给他
        q = q.filter(models.WorkPackageSplitRequest.applicant_id == viewer.id)
    return q.count()


def _complete_pending(db: Session, role: str, user_id: str) -> int:
    """完成申请：待审核的工作项完成申请数量（可见范围同 complete_review 列表）。"""
    q = db.query(models.WorkItemCompletionReview).filter(
        models.WorkItemCompletionReview.status == "PENDING"
    )
    if role not in ("LEADER", "ADMIN", "DEPARTMENT"):
        # 普通员工：我提交的 + 待我（技术负责人）审核的
        to_review = models.WorkItemCompletionReview.work_item.has(
            models.WorkItem.tech_owner_id == user_id
        )
        q = q.filter(or_(
            models.WorkItemCompletionReview.applicant_id == user_id,
            to_review,
        ))
    return q.count()


def _transfer_pending(db: Session, user_id: str) -> int:
    """工作包转办：待我接收的转办数量（同 /transfers/my-incoming）。"""
    return db.query(models.TaskTransfer).filter(
        models.TaskTransfer.to_user_id == user_id,
        models.TaskTransfer.status == "PENDING",
    ).count()


@router.get("/summary")
def get_pending_summary(user_id: str = Query(...), db: Session = Depends(get_db)):
    """返回当前用户的待办汇总：{review, complete, transfers, total}。"""
    viewer = db.query(models.User).filter(models.User.id == user_id).first()
    if not viewer:
        raise HTTPException(status_code=404, detail="用户不存在")

    role = str(viewer.role or "").upper()
    review = _review_pending(db, viewer, role)
    complete = _complete_pending(db, role, user_id)
    transfers = _transfer_pending(db, user_id)

    return {
        "code": 200,
        "data": {
            "review": review,
            "complete": complete,
            "transfers": transfers,
            "total": review + complete + transfers,
        },
    }
