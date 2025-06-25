"""
统一异常处理系统
"""

from fastapi.exceptions import (
    HTTPException,
    RequestValidationError,
    ResponseValidationError,
)
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from loguru import logger
from tortoise.exceptions import DoesNotExist, IntegrityError

# ==================== 自定义异常类 ====================


class SettingNotFound(Exception):
    """Raised when settings cannot be imported or found"""

    pass


class ConfigurationError(Exception):
    """Raised when there's a configuration error"""

    pass


class ServiceError(Exception):
    """Raised when there's a service-related error"""

    pass


class RAGError(Exception):
    """RAG相关异常"""

    pass


class CollectionNotFoundError(RAGError):
    """Collection不存在异常"""

    pass


class DocumentNotFoundError(RAGError):
    """文档不存在异常"""

    pass


class ValidationError(Exception):
    """数据验证异常"""

    pass


class BusinessError(Exception):
    """业务逻辑异常"""

    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code
        super().__init__(message)


# ==================== 异常处理器 ====================


async def does_not_exist_handler(req: Request, exc: DoesNotExist) -> JSONResponse:
    """处理数据库对象不存在异常"""
    logger.error(f"DoesNotExist异常: {exc}, 查询参数: {req.query_params}")
    content = {"code": 404, "msg": f"请求的资源不存在", "data": None}
    return JSONResponse(content=content, status_code=404)


async def integrity_error_handler(_: Request, exc: IntegrityError) -> JSONResponse:
    """处理数据库完整性约束异常"""
    logger.error(f"IntegrityError异常: {exc}")
    content = {
        "code": 500,
        "msg": "数据完整性错误，可能存在重复数据或约束冲突",
        "data": None,
    }
    return JSONResponse(content=content, status_code=500)


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    """处理HTTP异常"""
    logger.error(f"HTTP异常: {exc.status_code} - {exc.detail}")
    content = {"code": exc.status_code, "msg": exc.detail, "data": None}
    return JSONResponse(content=content, status_code=exc.status_code)


async def request_validation_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """处理请求参数验证异常"""
    logger.error(f"请求参数验证异常: {exc}")
    content = {"code": 422, "msg": "请求参数验证失败", "data": {"errors": exc.errors()}}
    return JSONResponse(content=content, status_code=422)


async def response_validation_handler(
    _: Request, exc: ResponseValidationError
) -> JSONResponse:
    """处理响应验证异常"""
    logger.error(f"响应验证异常: {exc}")
    content = {"code": 500, "msg": "服务器响应格式错误", "data": None}
    return JSONResponse(content=content, status_code=500)


async def business_error_handler(_: Request, exc: BusinessError) -> JSONResponse:
    """处理业务逻辑异常"""
    logger.warning(f"业务异常: {exc.message}")
    content = {"code": exc.code, "msg": exc.message, "data": None}
    return JSONResponse(content=content, status_code=exc.code)


async def rag_error_handler(_: Request, exc: RAGError) -> JSONResponse:
    """处理RAG相关异常"""
    logger.error(f"RAG异常: {exc}")
    content = {"code": 400, "msg": str(exc), "data": None}
    return JSONResponse(content=content, status_code=400)


async def validation_error_handler(_: Request, exc: ValidationError) -> JSONResponse:
    """处理数据验证异常"""
    logger.warning(f"数据验证异常: {exc}")
    content = {"code": 400, "msg": str(exc), "data": None}
    return JSONResponse(content=content, status_code=400)


async def general_exception_handler(req: Request, exc: Exception) -> JSONResponse:
    """处理通用异常"""
    logger.error(f"未处理的异常: {exc} | 请求: {req.url}")
    content = {"code": 500, "msg": "服务器内部错误", "data": None}
    return JSONResponse(content=content, status_code=500)
