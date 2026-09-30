"""登录身份依赖：从请求令牌查找会话，再取得数据库中的当前用户。"""
import hashlib
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

import models
from database import get_db

# 不让 HTTPBearer 自行返回错误，统一使用 401 表示需要重新登录。
bearer = HTTPBearer(auto_error=False)


def get_current_session(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
):
    """验证令牌及八小时有效期；数据库只保存令牌哈希，不保存原始令牌。"""
    error = HTTPException(
        status_code=401,
        detail="未登录或登录已过期，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise error
    token_hash = hashlib.sha256(credentials.credentials.encode("utf-8")).hexdigest()
    session = db.query(models.LoginSession).filter(
        models.LoginSession.token_hash == token_hash,
        # 与登录签发保持一致，数据库中的会话时间使用 UTC。
        models.LoginSession.expires_at > datetime.utcnow(),
    ).first()
    if session is None:
        raise error
    return session


def get_current_user(
    session=Depends(get_current_session),
    db: Session = Depends(get_db),
):
    """仅负责确认用户身份；公告等接口原有的业务权限仍由各自服务层判断。"""
    user = db.query(models.User).filter(
        models.User.id == session.user_id,
        models.User.is_deleted == False,
    ).first()
    if user is None:
        raise HTTPException(status_code=401, detail="登录用户已失效，请重新登录",
                            headers={"WWW-Authenticate": "Bearer"})
    return user
