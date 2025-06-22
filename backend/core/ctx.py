"""
上下文管理
用于在请求生命周期内传递用户信息等数据
"""

import contextvars

from starlette.background import BackgroundTasks

# 用户ID上下文变量
CTX_USER_ID: contextvars.ContextVar[int] = contextvars.ContextVar("user_id", default=0)

# 后台任务上下文变量
CTX_BG_TASKS: contextvars.ContextVar[BackgroundTasks] = contextvars.ContextVar(
    "bg_task", default=None
)

# 当前用户上下文变量
CTX_CURRENT_USER: contextvars.ContextVar = contextvars.ContextVar(
    "current_user", default=None
)


def get_current_user_id() -> int:
    """获取当前用户ID"""
    return CTX_USER_ID.get()


def set_current_user_id(user_id: int) -> None:
    """设置当前用户ID"""
    CTX_USER_ID.set(user_id)


def get_current_user():
    """获取当前用户"""
    return CTX_CURRENT_USER.get()


def set_current_user(user) -> None:
    """设置当前用户"""
    CTX_CURRENT_USER.set(user)
