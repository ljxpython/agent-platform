import hashlib
from datetime import datetime, timedelta
from typing import Optional, Union

from jose import JWTError, jwt
from loguru import logger

from backend.conf.config import settings

# JWT配置
SECRET_KEY = settings.get("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return get_password_hash(plain_password) == hashed_password


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """验证令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def decode_access_token(token: str) -> Optional[dict]:
    """解码访问令牌"""
    try:
        logger.debug(f"[JWT] 开始解码令牌: {token[:20]}...")
        logger.debug(f"[JWT] 使用密钥: {SECRET_KEY[:10]}...")
        logger.debug(f"[JWT] 使用算法: {ALGORITHM}")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"[JWT] 解码成功，载荷: {payload}")

        # 获取用户信息，兼容不同的字段格式
        sub = payload.get("sub")  # 字符串格式的用户ID
        user_id = payload.get("user_id")  # 整数格式的用户ID
        username: str = payload.get("username")

        # 转换sub为整数
        if sub is not None:
            try:
                user_id = int(sub)
            except (ValueError, TypeError):
                logger.warning(f"[JWT] 无法转换sub为整数: {sub}")
                user_id = None

        logger.debug(
            f"[JWT] 提取的用户信息: sub={sub}, user_id={user_id}, username={username}"
        )

        if user_id is None or username is None:
            logger.warning(
                f"[JWT] 载荷中缺少必要字段: user_id={user_id}, username={username}"
            )
            return None

        return {"user_id": user_id, "username": username, "sub": user_id}
    except JWTError as e:
        logger.error(f"[JWT] 解码失败: {type(e).__name__}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"[JWT] 解码异常: {type(e).__name__}: {str(e)}")
        return None
