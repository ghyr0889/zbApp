"""新版数据看板接口：身份来自登录凭证，参数在接口层校验。"""
from typing import Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
from services import dashboard_service as service

router = APIRouter(prefix="/api/v1/dashboard", tags=["数据看板"])


@router.get("/overview")
def overview(period: Literal["month", "quarter", "year"],
             year: int = Query(..., ge=2000, le=2100),
             month: int = Query(1, ge=1, le=12),
             quarter: int = Query(1, ge=1, le=4),
             dimension: Literal["department", "person", "project", "time"] = "department",
             year_granularity: Literal["month", "quarter"] = "month",
             db: Session = Depends(get_db), user=Depends(get_current_user)):
    return {"code": 200, "data": service.overview(db, user, period, year, month, quarter, dimension, year_granularity)}
