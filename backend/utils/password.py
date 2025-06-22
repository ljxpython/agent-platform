"""
密码工具函数
"""

from passlib import pwd
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


def generate_password() -> str:
    """生成随机密码"""
    return pwd.genword()


# 为了向后兼容，保留旧的函数名
def hash_password(password: str) -> str:
    """哈希密码（向后兼容）"""
    return get_password_hash(password)
