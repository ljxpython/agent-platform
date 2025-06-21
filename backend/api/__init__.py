"""
API 路由模块
"""

from fastapi import APIRouter

from .v1 import v1_router

# 创建主API路由
api_router = APIRouter()
api_router.include_router(v1_router, prefix="/v1")

__all__ = ["api_router"]
