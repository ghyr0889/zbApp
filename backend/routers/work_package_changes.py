"""工作包变更查询和部门审核接口。"""
from typing import Literal
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
import models
from services.approval_termination_service import terminate_request
from services import work_package_change_service as service

router = APIRouter(prefix='/api/v1/work-package-changes', tags=['工作包变更审批'])


@router.post('/{request_id}/terminate')
def terminate_change(request_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """发起人可终止尚未由部门处理的工作包变更申请。"""
    return terminate_request(db, models.WorkPackageChangeRequest, request_id, user.id,
                             models.WorkPackageChangeRequest.applicant_id, ("PENDING", "REJECTED"))


class ReviewBody(BaseModel):
    decision: Literal['APPROVE', 'REJECT']
    comment: str = Field(default='', max_length=2000)

# 查询工作包变更申请列表
@router.get('')
def list_changes(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return service.list_requests(db, user)

# 部门通过或驳回指定申请
@router.post('/{request_id}/review')
def review_change(request_id: int, body: ReviewBody,
                  db: Session = Depends(get_db), user=Depends(get_current_user)):
    return service.review(db, user, request_id, body.decision, body.comment)
