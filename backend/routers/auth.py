# xiangmu/backend/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import LoginRequest, ChangePasswordRequest
from dependencies import get_current_user, get_current_session

import hashlib
import secrets
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


def authenticate(data: LoginRequest, db: Session, allowed_roles=None):
    current_user = db.query(models.User).filter(models.User.id == data.user_id).first()

    if not current_user or current_user.is_deleted or current_user.password != data.password:
        raise HTTPException(status_code=400, detail="工号或密码错误！")

    if allowed_roles is not None:
        normalized_role = str(current_user.role).upper()
        allowed_role_set = {role.upper() for role in allowed_roles}
        if normalized_role not in allowed_role_set:
            raise HTTPException(status_code=403, detail="当前账号没有权限登录该入口")

    # 生成无法轻易猜测的随机令牌
    token = secrets.token_urlsafe(32)
    # 数据库只保存令牌哈希
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    session = models.LoginSession(
        user_id=current_user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=8),
    )

    # 签发失败时回滚，不向前端返回无法使用的凭证。
    try:
        db.add(session)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "code": 200,
        "message": "登录成功",
        "access_token": token,
        "token_type": "bearer",
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "job_grade": current_user.job_grade,
            "department": current_user.department
        }
    }


@router.post("/user-login")
def user_login(data: LoginRequest, db: Session = Depends(get_db)):
    return authenticate(data, db, allowed_roles=["EMPLOYEE", "LEADER", "DEPARTMENT"])


@router.post("/admin-login")
def admin_login(data: LoginRequest, db: Session = Depends(get_db)):
    return authenticate(data, db, allowed_roles=["ADMIN"])


@router.put("/password")
def change_password(data: ChangePasswordRequest, db: Session = Depends(get_db)):
    """修改自己的登录密码：校验旧密码后更新，所有角色通用。"""
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.password != data.old_password:
        raise HTTPException(status_code=400, detail="旧密码不正确")
    new_pwd = str(data.new_password or "")
    if len(new_pwd) < 6:
        raise HTTPException(status_code=400, detail="新密码长度不能少于6位")
    if new_pwd == data.old_password:
        raise HTTPException(status_code=400, detail="新密码不能与旧密码相同")
    user.password = new_pwd
    db.commit()
    return {"code": 200, "message": "密码修改成功"}


@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    """通过令牌获取自己的最新信息，前端刷新后用它恢复登录状态。"""
    return {"code": 200, "data": {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "job_grade": current_user.job_grade,
        "department": current_user.department,
    }}


@router.post("/logout")
def logout(session=Depends(get_current_session), db: Session = Depends(get_db)):
    """退出只删除本次登录对应的会话，不影响其他设备的登录。"""
    try:
        db.delete(session)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"code": 200, "message": "已退出登录"}

# 查询个人信息(登录认证时使用)
@router.get("/profile/{user_id}")
def get_profile(user_id: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.is_deleted == False
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "code": 200,
        "data": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "job_grade": user.job_grade,
            "department": user.department
        }
    }
