"""
Application initialization functions
"""

from typing import List

from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.api import api_router


async def init_data(app=None):
    """Initialize application data"""
    logger.info("开始初始化应用数据...")

    try:
        # 使用database.py中的统一初始化函数
        from backend.api_core.database import init_data as db_init_data

        await db_init_data(app)

        logger.success("🚀 应用数据初始化完成")
    except Exception as e:
        logger.error(f"应用数据初始化失败: {e}")
        raise


def make_middlewares() -> List[Middleware]:
    """Create and configure middlewares"""
    logger.info("配置应用中间件...")

    middlewares = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]

    logger.debug(f"已配置 {len(middlewares)} 个中间件")
    return middlewares


def register_exceptions(app: FastAPI):
    """Register exception handlers"""
    from fastapi import HTTPException, Request
    from fastapi.exceptions import RequestValidationError, ResponseValidationError
    from fastapi.responses import JSONResponse
    from tortoise.exceptions import DoesNotExist, IntegrityError

    from backend.api_core.exceptions import (  # 原有异常; 新增异常; 异常处理器
        BusinessError,
        CollectionNotFoundError,
        ConfigurationError,
        DocumentNotFoundError,
        RAGError,
        ServiceError,
        SettingNotFound,
        ValidationError,
        business_error_handler,
        does_not_exist_handler,
        general_exception_handler,
        http_exception_handler,
        integrity_error_handler,
        rag_error_handler,
        request_validation_handler,
        response_validation_handler,
        validation_error_handler,
    )

    logger.info("注册统一异常处理器...")

    # 注册数据库异常处理器
    app.add_exception_handler(DoesNotExist, does_not_exist_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)

    # 注册FastAPI异常处理器
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_handler)
    app.add_exception_handler(ResponseValidationError, response_validation_handler)

    # 注册业务异常处理器
    app.add_exception_handler(BusinessError, business_error_handler)
    app.add_exception_handler(RAGError, rag_error_handler)
    app.add_exception_handler(CollectionNotFoundError, rag_error_handler)
    app.add_exception_handler(DocumentNotFoundError, rag_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)

    # 注册原有异常处理器（保持兼容性）
    app.add_exception_handler(SettingNotFound, general_exception_handler)
    app.add_exception_handler(ServiceError, general_exception_handler)
    app.add_exception_handler(ConfigurationError, general_exception_handler)

    # 注册通用异常处理器
    app.add_exception_handler(Exception, general_exception_handler)

    logger.success("统一异常处理器注册完成")


def register_routers(app: FastAPI, prefix: str = "/api"):
    """Register application routers"""
    logger.info("注册应用路由...")

    # 注册API路由
    app.include_router(api_router, prefix=prefix)
    logger.debug("API路由注册完成")

    # 注册基础路由
    @app.get("/")
    async def root():
        logger.debug("根路径被访问")
        return {"message": "AI测试实验室 API is running!"}

    @app.get("/health")
    async def health_check():
        logger.debug("健康检查被访问")
        return {"status": "healthy"}

    logger.success(f"✅ 路由注册完成，前缀: {prefix}")
