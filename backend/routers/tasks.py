#任务转办
from datetime import datetime
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

#发起转办申请
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

    assignment = db.query(models.TaskAssignment).filter(
        models.TaskAssignment.id == payload.task_id,
        models.TaskAssignment.assignee_id == payload.from_user_id,
        models.TaskAssignment.work_package_name == payload.task_name
    ).first()
    if not assignment:
        raise HTTPException(status_code=403, detail="只能转办当前由自己负责的工作包")

    duplicate = db.query(models.TaskTransfer).filter(
        models.TaskTransfer.task_name == payload.task_name,
        models.TaskTransfer.from_user_id == payload.from_user_id,
        models.TaskTransfer.status == "PENDING"
    ).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="该工作包已有待处理的转办申请")

    transfer = models.TaskTransfer(
        task_name=payload.task_name,
        from_user_id=payload.from_user_id,
        to_user_id=payload.to_user_id,
        status="PENDING"
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    return {"code": 200, "message": "转办申请已发送", "data": {"id": transfer.id}}

#给我的转办申请
@router.get("/my-incoming")
def get_incoming_transfers(user_id: str = Query(...), db: Session = Depends(get_db)):
    transfers = db.query(models.TaskTransfer).filter(
        models.TaskTransfer.to_user_id == user_id,
        models.TaskTransfer.status == "PENDING"
    ).order_by(models.TaskTransfer.created_at.desc()).all()

    from_user_ids = {item.from_user_id for item in transfers}
    users = []
    if from_user_ids:
        users = db.query(models.User).filter(models.User.id.in_(from_user_ids)).all()
    users_by_id = {item.id: item for item in users}

    data = []
    for item in transfers:
        from_user = users_by_id.get(item.from_user_id)
        data.append({
            "id": item.id,
            "task_name": item.task_name,
            "from_user_id": item.from_user_id,
            "from_username": user_label(from_user),
            "to_user_id": item.to_user_id,
            "status": item.status,
            "created_at": item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else "-"
        })

    return {"code": 200, "data": data}

#处理转办申请
@router.post("/process")
def process_transfer(
    transfer_id: int = Query(...),
    action: str = Query(...),
    db: Session = Depends(get_db)
):
    action = action.upper()
    if action not in ["ACCEPT", "REJECT"]:
        raise HTTPException(status_code=400, detail="操作只能是 ACCEPT 或 REJECT")

    transfer = db.query(models.TaskTransfer).filter(models.TaskTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="未找到该转办申请")
    if transfer.status != "PENDING":
        raise HTTPException(status_code=400, detail="该转办申请已处理")

    if action == "REJECT":
        transfer.status = "REJECTED"
        db.commit()
        return {"code": 200, "message": "已拒绝该转办申请"}

    assignment = db.query(models.TaskAssignment).filter(
        models.TaskAssignment.work_package_name == transfer.task_name,
        models.TaskAssignment.assignee_id == transfer.from_user_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=400, detail="原负责人当前已不负责该工作包，无法接受")

    target_assignment = db.query(models.TaskAssignment).filter(
        models.TaskAssignment.work_package_name == transfer.task_name,
        models.TaskAssignment.assignee_id == transfer.to_user_id
    ).first()
    if target_assignment:
        raise HTTPException(status_code=400, detail="接收人已负责该工作包，无需重复转办")

    assignment.assignee_id = transfer.to_user_id
    assignment.assigner_id = transfer.from_user_id
    assignment.assigned_at = datetime.now()
    transfer.status = "ACCEPTED"

    db.query(models.TaskTransfer).filter(
        models.TaskTransfer.id != transfer.id,
        models.TaskTransfer.task_name == transfer.task_name,
        models.TaskTransfer.from_user_id == transfer.from_user_id,
        models.TaskTransfer.status == "PENDING"
    ).update({models.TaskTransfer.status: "REJECTED"}, synchronize_session=False)

    db.commit()
    return {"code": 200, "message": "已接受转办申请，工作包负责人已变更"}
