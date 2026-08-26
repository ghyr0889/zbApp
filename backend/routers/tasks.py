# xiangmu/backend/routers/tasks.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import TransferCreate

router = APIRouter(prefix="/api/v1/transfers", tags=["Task Transfers"])


def user_label(user):
    if not user:
        return "-"
    return user.username or user.id


# ---------------------------------------------------------------- 发起转办
@router.post("/initiate")
def initiate_transfer(payload: TransferCreate, db: Session = Depends(get_db)):
    if payload.from_user_id == payload.to_user_id:
        raise HTTPException(status_code=400, detail="不能将工作包转办给自己")

    from_user = db.query(models.User).filter(models.User.id == payload.from_user_id).first()
    to_user = db.query(models.User).filter(models.User.id == payload.to_user_id).first()
    if not from_user:
        raise HTTPException(status_code=404, detail="发起人不存在")
    if not to_user:
        raise HTTPException(status_code=404, detail="接收人不存在")

    pkg = db.query(models.WorkPackage).filter(
        models.WorkPackage.id == payload.work_package_id
    ).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="工作包不存在")
    if pkg.owner_id != payload.from_user_id:
        raise HTTPException(status_code=403, detail="只能转办当前由自己负责的工作包")

    duplicate = db.query(models.TaskTransfer).filter(
        models.TaskTransfer.work_package_id == payload.work_package_id,
        models.TaskTransfer.from_user_id == payload.from_user_id,
        models.TaskTransfer.status == "PENDING"
    ).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="该工作包已有待处理的转办申请")

    transfer = models.TaskTransfer(
        task_assignment_id=payload.task_id or pkg.id,
        work_package_id=pkg.id,
        from_user_id=payload.from_user_id,
        to_user_id=payload.to_user_id,
        status="PENDING"
    )
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

    from_user_ids = {item.from_user_id for item in transfers}
    users_by_id = {}
    if from_user_ids:
        users_by_id = {u.id: u for u in db.query(models.User).filter(models.User.id.in_(from_user_ids)).all()}

    data = []
    for item in transfers:
        from_user = users_by_id.get(item.from_user_id)
        pkg = item.work_package
        data.append({
            "id": item.id,
            "task_assignment_id": item.task_assignment_id,
            "work_package_id": item.work_package_id,
            "work_package_code": item_package_code,
            "project_id": pkg.project_id if pkg else None,
            "project_name": pkg.project.name if (pkg and pkg.project) else "-",
            "from_user_id": item.from_user_id,
            "from_username": user_label(from_user),
            "to_user_id": item.to_user_id,
            "status": item.status,
            "created_at": item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else "-",
        })

    return {"code": 200, "data": data}


# ---------------------------------------------------------------- 我发起的转办
@router.get("/my-outgoing")
def get_outgoing_transfers(user_id: str = Query(...), db: Session = Depends(get_db)):
    transfers = (
        db.query(models.TaskTransfer)
        .filter(models.TaskTransfer.from_user_id == user_id)
        .order_by(models.TaskTransfer.created_at.desc())
        .all()
    )

    to_user_ids = {item.to_user_id for item in transfers}
    users_by_id = {}
    if to_user_ids:
        users_by_id = {u.id: u for u in db.query(models.User).filter(models.User.id.in_(to_user_ids)).all()}

    data = []
    for item in transfers:
        to_user = users_by_id.get(item.to_user_id)
        pkg = item.work_package
        data.append({
            "id": item.id,
            "task_assignment_id": item.task_assignment_id,
            "work_package_id": item.work_package_id,
            "work_package_code": item.work_package_code,
            "project_id": pkg.project_id if pkg else None,
            "project_name": pkg.project.name if (pkg and pkg.project) else "-",
            "from_user_id": item.from_user_id,
            "to_user_id": item.to_user_id,
            "to_username": user_label(to_user),
            "status": item.status,
            "created_at": item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else "-",
        })

    return {"code": 200, "data": data}


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

    pkg = db.query(models.WorkPackage).filter(
        models.WorkPackage.id == transfer.work_package_id
    ).first()
    if not pkg:
        raise HTTPException(status_code=400, detail="工作包不存在，无法接受")

    # 变更工作包负责人
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
