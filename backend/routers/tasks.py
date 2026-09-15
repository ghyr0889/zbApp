# xiangmu/backend/routers/tasks.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
from database import get_db
from schemas import TransferCreate
from utils import ensure_open

router = APIRouter(prefix="/api/v1/transfers", tags=["Task Transfers"])


def user_label(user):
    if not user:
        return "-"
    return user.username or user.id


def item_remaining_score(db, item):
    """工作项剩余分数 = 基础总分值 - 已填月度分值之和。"""
    total = item.score or 0.0
    filled = db.query(func.coalesce(func.sum(models.WorkItemMonthlyScore.score), 0.0)).filter(
        models.WorkItemMonthlyScore.work_item_id == item.id
    ).scalar() or 0.0
    return round(total - filled, 2)


def _transfer_view(item, users_by_id=None):
    """把一条转办记录展开为前端需要的结构（工作包/工作项通用）。"""
    users_by_id = users_by_id or {}
    pkg = item.work_package
    wi = item.work_item
    return {
        "id": item.id,
        "transfer_type": item.transfer_type or "work_item",
        "work_package_id": item.work_package_id,
        "work_package_code": pkg.code if pkg else "-",
        "work_item_id": item.work_item_id,
        "work_item_name": wi.name if wi else "-",
        "transfer_score": item.transfer_score or 0.0,
        "project_id": pkg.project_id if pkg else None,
        "project_name": pkg.project.name if (pkg and pkg.project) else "-",
        "from_user_id": item.from_user_id,
        "from_username": user_label(users_by_id.get(item.from_user_id)),
        "to_user_id": item.to_user_id,
        "to_username": user_label(users_by_id.get(item.to_user_id)),
        "status": item.status,
        "created_at": item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else "-",
    }


# ---------------------------------------------------------------- 发起转办
@router.post("/initiate")
def initiate_transfer(payload: TransferCreate, db: Session = Depends(get_db)):
    if payload.from_user_id == payload.to_user_id:
        raise HTTPException(status_code=400, detail="不能转办给自己")

    from_user = db.query(models.User).filter(models.User.id == payload.from_user_id).first()
    to_user = db.query(models.User).filter(models.User.id == payload.to_user_id).first()
    if not from_user:
        raise HTTPException(status_code=404, detail="发起人不存在")
    if not to_user:
        raise HTTPException(status_code=404, detail="接收人不存在")

    transfer_type = (payload.transfer_type or "work_package").lower()

    if transfer_type == "work_package":
        # ---- 工作包转办：整体转办，负责人直接变更 ----
        pkg = db.query(models.WorkPackage).filter(
            models.WorkPackage.id == payload.work_package_id
        ).first()
        if not pkg:
            raise HTTPException(status_code=404, detail="工作包不存在")
        if from_user.role not in ["LEADER", "DEPARTMENT", "ADMIN"] and  pkg.owner_id != payload.from_user_id:
            raise HTTPException(status_code=403, detail="只有管理员、科室、领导和该工作包负责人可以转包")
        ensure_open(pkg, pkg.project)  # 已关闭的工作包/项目不能再转办

        duplicate = db.query(models.TaskTransfer).filter(
            models.TaskTransfer.work_package_id == payload.work_package_id,
            models.TaskTransfer.from_user_id == payload.from_user_id,
            models.TaskTransfer.status == "PENDING"
        ).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="该工作包已有待处理的转办申请")

        transfer = models.TaskTransfer(
            work_package_id=pkg.id,
            from_user_id=payload.from_user_id,
            to_user_id=payload.to_user_id,
            status="PENDING",
            transfer_type="work_package",
        )

    elif transfer_type == "work_item":
        # ---- 工作项转办：可选择转出分数（不能超过该工作项剩余分数）----
        item = db.query(models.WorkItem).filter(models.WorkItem.id == payload.work_item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="工作项不存在")
        if from_user.role not in ["LEADER", "DEPARTMENT", "ADMIN"] and item.owner_id != payload.from_user_id:
            raise HTTPException(status_code=403, detail="只有管理员、科室、领导和该工作项负责人可以转包")
        ensure_open(item, item.work_package,
                    item.work_package.project if item.work_package else None)  # 已关闭不能再转办

        remaining = item_remaining_score(db, item)
        score = round(float(payload.transfer_score or 0.0), 2)
        if score <= 0:
            raise HTTPException(status_code=400, detail="转出分值必须大于 0")
        if score > remaining:
            raise HTTPException(status_code=400, detail=f"转出分值不能超过剩余分值（剩余 {remaining} 分）")

        # 已有待处理转办占用的分数要扣除
        pending_used = db.query(func.coalesce(func.sum(models.TaskTransfer.transfer_score), 0.0)).filter(
            models.TaskTransfer.work_item_id == item.id,
            models.TaskTransfer.status == "PENDING"
        ).scalar() or 0.0
        available = round(remaining - pending_used, 2)
        if score > available:
            raise HTTPException(status_code=400,
                                detail=f"转出分值不能超过可用分值（剩余 {remaining}，待处理占用 {pending_used}，可用 {available}）")

        transfer = models.TaskTransfer(
            work_package_id=item.work_package_id,
            work_item_id=item.id,
            transfer_score=score,
            from_user_id=payload.from_user_id,
            to_user_id=payload.to_user_id,
            status="PENDING",
            transfer_type="work_item",
        )

    else:
        raise HTTPException(status_code=400, detail="transfer_type 只能是 work_package / work_item")

    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    return {"code": 200, "message": "转办申请已发送", "data": {"id": transfer.id}}


# ---------------------------------------------------------------- 我的收件箱
@router.get("/my-incoming")
def get_incoming_transfers(user_id: str = Query(...), db: Session = Depends(get_db)):
    transfers = (
        db.query(models.TaskTransfer)
        .filter(
            models.TaskTransfer.to_user_id == user_id,
            models.TaskTransfer.status == "PENDING"
        )
        .order_by(models.TaskTransfer.created_at.desc())
        .all()
    )

    user_ids = {t.from_user_id for t in transfers} | {t.to_user_id for t in transfers}
    users_by_id = {}
    if user_ids:
        users_by_id = {u.id: u for u in db.query(models.User).filter(models.User.id.in_(user_ids)).all()}

    return {"code": 200, "data": [_transfer_view(t, users_by_id) for t in transfers]}


# ---------------------------------------------------------------- 我发起的转办
@router.get("/my-outgoing")
def get_outgoing_transfers(user_id: str = Query(...), db: Session = Depends(get_db)):
    transfers = (
        db.query(models.TaskTransfer)
        .filter(models.TaskTransfer.from_user_id == user_id)
        .order_by(models.TaskTransfer.created_at.desc())
        .all()
    )

    user_ids = {t.from_user_id for t in transfers} | {t.to_user_id for t in transfers}
    users_by_id = {}
    if user_ids:
        users_by_id = {u.id: u for u in db.query(models.User).filter(models.User.id.in_(user_ids)).all()}

    return {"code": 200, "data": [_transfer_view(t, users_by_id) for t in transfers]}


# ---------------------------------------------------------------- 处理转办
@router.post("/process")
def process_transfer(
    transfer_id: int = Query(...),
    action: str = Query(...),
    db: Session = Depends(get_db)
):
    action = action.upper()
    if action not in ["ACCEPT", "REJECT"]:
        raise HTTPException(status_code=400, detail="操作只能是 ACCEPT 或 REJECT")

    transfer = db.query(models.TaskTransfer).filter(
        models.TaskTransfer.id == transfer_id
    ).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="未找到该转办申请")
    if transfer.status != "PENDING":
        raise HTTPException(status_code=400, detail="该转办申请已处理")

    if action == "REJECT":
        transfer.status = "REJECTED"
        db.commit()
        return {"code": 200, "message": "已拒绝该转办申请"}

    transfer_type = (transfer.transfer_type or "work_item").lower()

    if transfer_type == "work_item":
        # ---- 工作项转办：接受时拆分 / 全量转出直接变更负责人 ----
        item = db.query(models.WorkItem).filter(
            models.WorkItem.id == transfer.work_item_id
        ).first()
        if not item:
            raise HTTPException(status_code=400, detail="工作项不存在，无法接受")
        ensure_open(item, item.work_package,
                    item.work_package.project if item.work_package else None)  # 已关闭不能再接受转办

        score = round(float(transfer.transfer_score or 0.0), 2)
        remaining = item_remaining_score(db, item)
        # 接受前再次校验剩余分数（期间原负责人可能又填写了分值）
        if score > remaining:
            raise HTTPException(status_code=400, detail=f"该工作项剩余分值不足，无法接受（剩余 {remaining} 分）")

        if score >= (item.score or 0.0):
            # 全量转出：直接变更工作项负责人，不拆分
            item.owner_id = transfer.to_user_id
        else:
            # 部分转出：原工作项减分保留（已填月度分值留在原工作项），新建一个工作项给接收人
            item.score = round((item.score or 0.0) - score, 2)
            db.flush()                        # 先让新的满分落库，SUM 查询才准
            # 新工作项没有任何月度分值（累计 0 < score），必定未完成，completed_at 保持 None
            new_item = models.WorkItem(
                work_package_id=item.work_package_id,
                name=item.name,
                standard=item.standard,
                difficulty=item.difficulty,
                importance=item.importance,
                innovation=item.innovation,
                deadline=item.deadline,
                score=score,
                owner_id=transfer.to_user_id,
                complete_status=False,
            )
            db.add(new_item)

        transfer.status = "ACCEPTED"
        db.commit()
        return {"code": 200, "message": "已接受转办申请，工作项已更新"}

    # ---- 工作包转办：负责人整体变更 ----
    pkg = db.query(models.WorkPackage).filter(
        models.WorkPackage.id == transfer.work_package_id
    ).first()
    if not pkg:
        raise HTTPException(status_code=400, detail="工作包不存在，无法接受")
    ensure_open(pkg, pkg.project)  # 已关闭的工作包/项目不能再接受转办

    pkg.owner_id = transfer.to_user_id
    transfer.status = "ACCEPTED"

    # 该工作包其它待处理转办一并作废
    db.query(models.TaskTransfer).filter(
        models.TaskTransfer.id != transfer.id,
        models.TaskTransfer.work_package_id == transfer.work_package_id,
        models.TaskTransfer.status == "PENDING"
    ).update({models.TaskTransfer.status: "REJECTED"}, synchronize_session=False)

    db.commit()
    return {"code": 200, "message": "已接受转办申请，工作包负责人已变更"}
