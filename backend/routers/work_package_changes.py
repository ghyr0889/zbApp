"""工作包变更查询和领导审核接口。"""
from typing import Literal
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
from services import work_package_change_service as service

router = APIRouter(prefix='/api/v1/work-package-changes', tags=['工作包变更审批'])


class ReviewBody(BaseModel):
    decision: Literal['APPROVE', 'REJECT']
    comment: str = Field(default='', max_length=2000)

# 查询工作包变更申请列表
@router.get('')
def list_changes(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return service.list_requests(db, user)

# 领导通过或驳回指定申请
@router.post('/{request_id}/review')
def review_change(request_id: int, body: ReviewBody,
                  db: Session = Depends(get_db), user=Depends(get_current_user)):
    return service.review(db, user, request_id, body.decision, body.comment)