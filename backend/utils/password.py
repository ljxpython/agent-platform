"""
密码工具函数
"""

import hashlib
import secrets


def hash_password(password: str) -> str:
    """哈希密码"""
    # 生成盐值
    salt = secrets.token_hex(16)
    # 使用SHA256哈希密码
    hashed = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        salt, stored_hash = hashed_password.split(":")
        # 使用相同的盐值哈希输入密码
        password_hash = hashlib.sha256(
            (plain_password + salt).encode("utf-8")
        ).hexdigest()
        return password_hash == stored_hash
    except ValueError:
        return False


def generate_salt() -> str:
    """生成盐值"""
    return secrets.token_hex(16)


def hash_password_with_salt(password: str, salt: str) -> str:
    """使用指定盐值哈希密码"""
    hashed = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return f"{salt}:{hashed}"
