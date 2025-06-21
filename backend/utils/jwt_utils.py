"""
JWT工具函数
"""

from datetime import datetime, timedelta
from typing import Optional

import jwt

from backend.conf.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.get("SECRET_KEY", "your-secret-key"), algorithm="HS256"
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """验证令牌"""
    try:
        payload = jwt.decode(
            token, settings.get("SECRET_KEY", "your-secret-key"), algorithms=["HS256"]
        )
        return payload
    except jwt.PyJWTError:
        return None


def decode_token(token: str) -> Optional[dict]:
    """解码令牌（不验证过期时间）"""
    try:
        payload = jwt.decode(
            token,
            settings.get("SECRET_KEY", "your-secret-key"),
            algorithms=["HS256"],
            options={"verify_exp": False},
        )
        return payload
    except jwt.PyJWTError:
        return None
