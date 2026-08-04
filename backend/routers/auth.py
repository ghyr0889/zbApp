# xiangmu/backend/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
import models

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])

class LoginRequest(BaseModel):
    user_id: str
    password: str

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    # 1. 明确按用户 ID 查询用户对象
    current_user = db.query(models.User).filter(models.User.id == data.user_id).first()

    # 2. 校验用户是否存在以及密码是否正确
    if not current_user or current_user.password != data.password:
        raise HTTPException(status_code=400, detail="工号或密码错误！")

    # 3. 返回登录成功信息
    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role
        }
    }