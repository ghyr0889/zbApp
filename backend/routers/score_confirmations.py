from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
from services import score_confirmation_service as service

router = APIRouter(prefix="/api/v1/score-confirmations", tags=["月度积分确认"])

class ConfirmationBody(BaseModel):
    fingerprint: str = Field(min_length=64, max_length=64)

@router.get("/mine")
def mine(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return service.mine(db, user)

@router.post("/{request_id}/confirm")
def confirm(request_id: int, body: ConfirmationBody, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return service.confirm(db, user, request_id, body.fingerprint)


class SelfEvaluationBody(BaseModel):
    content: str = Field(min_length=1, max_length=500)


@router.put("/{request_id}/self-evaluation")
def self_evaluation(request_id: int, body: SelfEvaluationBody, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return service.save_evaluation(db, user, request_id, body.content)


from typing import Literal
from services import historical_score_service as history

class HistoricalScoreBody(BaseModel):
    user_id: str
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    month_score: float = Field(ge=0, allow_inf_nan=False)
    calculate_score: float = Field(allow_inf_nan=False)
    deducted_score: float = Field(ge=0, allow_inf_nan=False)
    tech_improve: float = Field(allow_inf_nan=False)
    daily_manage: float = Field(allow_inf_nan=False)
    tech_growth_score: float = Field(allow_inf_nan=False)
    total_calculated: float = Field(allow_inf_nan=False)
    converted_score: float = Field(allow_inf_nan=False)
    grade: Literal["S", "A", "B", "C", "D"]
    reason: str = Field(min_length=1, max_length=2000)

@router.get("/history/drafts")
def historical_drafts(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return history.listing(db, user)

@router.put("/history/drafts")
def save_historical_draft(body: HistoricalScoreBody, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return history.save(db, user, body)

@router.post("/history/drafts/{draft_id}/publish")
def publish_historical_draft(draft_id: int, body: ConfirmationBody, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return history.publish(db, user, draft_id, body.fingerprint)
