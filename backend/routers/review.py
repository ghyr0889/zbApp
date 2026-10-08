# 工作项新建/编辑

"""接口层：只接收参数、注入数据库会话并调用业务层。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas import SplitRequestCreate, SplitRequestReview, SplitRequestEdit, RemoveSplitItem
from services import review_service as service

router = APIRouter(prefix='/api/v1/review', tags=['Owner Review'])


@router.post("/split-requests")
def create_split_request(req: SplitRequestCreate, db: Session = Depends(get_db)):
    """员工提交“拆解工作包为多个工作项”的申请。"""
    return service.create_split_request(req=req, db=db)


@router.get("/split-requests")
def get_split_requests(user_id: str = Query(...), db: Session = Depends(get_db)):
    """查询拆分申请。
    - 普通员工：只看自己的申请
    - 科室主任 / 领导 / 管理员：查看全部申请（各自审核对应状态的申请）
    """
    return service.get_split_requests(user_id=user_id, db=db)


@router.post("/split-requests/{request_id}/review")
def review_split_request(request_id: int, body: SplitRequestReview, db: Session = Depends(get_db)):
    """两级审核：
    - 科室主任 DEPARTMENT 审核 PENDING：同意(APPROVE)→直接生效 / 驳回(REJECT) / 提交(SUBMIT)→转领导
    - 领导 LEADER/ADMIN 审核 SUBMITTED：通过(APPROVE)→生效 / 驳回(REJECT)
    """
    return service.review_split_request(request_id=request_id, body=body, db=db)


@router.put("/split-requests/{request_id}")
def edit_split_request(request_id: int, body: SplitRequestEdit, db:Session = Depends(get_db)):
    return service.edit_split_request(request_id=request_id, body=body, db=db)


@router.post("/split-requests/{request_id}/remove-item")
def remove_item_from_split_request(request_id: int, body: RemoveSplitItem, db: Session = Depends(get_db)):
    """从拆分申请中移除一个工作项（编辑时使用）。"""
    return service.remove_item_from_split_request(request_id=request_id, body=body, db=db)
