"""
API开发示例

展示如何使用FastAPI开发标准的RESTful API接口
包括参数校验、响应处理、权限控制等
"""

from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query

from backend.api_core.deps import get_current_user, require_permissions
from backend.api_core.exceptions import BusinessError
from backend.api_core.response import response
from backend.controllers.user_controller import user_controller
from backend.schemas.user import UserCreate, UserResponse, UserUpdate

# ==================== 基础API示例 ====================

# 创建路由器
user_router = APIRouter(prefix="/users", tags=["用户管理"])


@user_router.post("/", response_model=dict, summary="创建用户")
async def create_user(user_data: UserCreate):
    """
    创建新用户

    - **username**: 用户名，3-50字符，只能包含字母、数字和下划线
    - **email**: 有效的邮箱地址
    - **password**: 密码，至少6字符
    - **full_name**: 用户全名（可选）

    Returns:
        创建的用户信息

    Raises:
        400: 参数验证失败
        409: 用户名或邮箱已存在
    """
    return await user_controller.create_user(user_data)


@user_router.get("/{user_id}", response_model=dict, summary="获取用户详情")
async def get_user(user_id: int = Path(..., gt=0, description="用户ID")):
    """
    获取指定用户的详细信息

    Args:
        user_id: 用户ID，必须大于0

    Returns:
        用户详细信息

    Raises:
        404: 用户不存在
    """
    return await user_controller.get_user_by_id(user_id)


@user_router.get("/", response_model=dict, summary="获取用户列表")
async def get_users(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    search: Optional[str] = Query(None, min_length=2, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
):
    """
    获取用户列表（支持分页和搜索）

    - **page**: 页码，从1开始
    - **page_size**: 每页数量，最大100
    - **search**: 搜索关键词，支持用户名和全名搜索
    - **is_active**: 过滤激活状态

    Returns:
        分页的用户列表
    """
    if search:
        return await user_controller.search_users(search, page, page_size, is_active)
    else:
        return await user_controller.get_users_paginated(page, page_size, is_active)


@user_router.put("/{user_id}", response_model=dict, summary="更新用户")
async def update_user(
    user_id: int = Path(..., gt=0, description="用户ID"),
    user_data: UserUpdate = Body(..., description="用户更新数据"),
):
    """
    更新用户信息

    Args:
        user_id: 用户ID
        user_data: 用户更新数据

    Returns:
        更新后的用户信息

    Raises:
        404: 用户不存在
        409: 邮箱已被使用
    """
    return await user_controller.update_user(user_id, user_data)


@user_router.delete("/{user_id}", summary="删除用户")
async def delete_user(user_id: int = Path(..., gt=0, description="用户ID")):
    """
    删除指定用户

    Args:
        user_id: 用户ID

    Returns:
        删除成功消息

    Raises:
        404: 用户不存在
    """
    return await user_controller.delete_user(user_id)


# ==================== 权限控制API示例 ====================


@user_router.get("/admin/all", summary="获取所有用户（管理员）")
async def get_all_users_admin(
    current_user=Depends(get_current_user),
    _: None = Depends(require_permissions(["user:read_all"])),
):
    """
    获取所有用户（需要管理员权限）

    需要权限: user:read_all
    """
    return await user_controller.get_all_users()


@user_router.post("/{user_id}/activate", summary="激活用户")
async def activate_user(
    user_id: int = Path(..., gt=0),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permissions(["user:manage"])),
):
    """
    激活指定用户

    需要权限: user:manage
    """
    return await user_controller.activate_user(user_id)


@user_router.post("/{user_id}/deactivate", summary="停用用户")
async def deactivate_user(
    user_id: int = Path(..., gt=0),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permissions(["user:manage"])),
):
    """
    停用指定用户

    需要权限: user:manage
    """
    return await user_controller.deactivate_user(user_id)


# ==================== 批量操作API示例 ====================

from backend.schemas.batch import BatchOperation, BatchUserCreate


@user_router.post("/batch", summary="批量创建用户")
async def batch_create_users(
    batch_data: BatchUserCreate,
    current_user=Depends(get_current_user),
    _: None = Depends(require_permissions(["user:create_batch"])),
):
    """
    批量创建用户

    需要权限: user:create_batch
    """
    return await user_controller.batch_create_users(batch_data.users)


@user_router.patch("/batch/status", summary="批量更新用户状态")
async def batch_update_user_status(
    operation: BatchOperation,
    current_user=Depends(get_current_user),
    _: None = Depends(require_permissions(["user:manage_batch"])),
):
    """
    批量更新用户状态

    需要权限: user:manage_batch
    """
    return await user_controller.batch_update_status(
        operation.user_ids, operation.is_active
    )


# ==================== 文件上传API示例 ====================

from fastapi import File, UploadFile

from backend.controllers.upload_controller import upload_controller

upload_router = APIRouter(prefix="/upload", tags=["文件上传"])


@upload_router.post("/avatar", summary="上传头像")
async def upload_avatar(
    file: UploadFile = File(..., description="头像文件"),
    current_user=Depends(get_current_user),
):
    """
    上传用户头像

    支持的文件格式: jpg, jpeg, png, gif
    文件大小限制: 5MB
    """
    # 验证文件类型
    allowed_types = {"image/jpeg", "image/png", "image/gif"}
    if file.content_type not in allowed_types:
        raise BusinessError("不支持的文件类型", code=400)

    # 验证文件大小
    max_size = 5 * 1024 * 1024  # 5MB
    if file.size > max_size:
        raise BusinessError("文件大小超过限制", code=400)

    return await upload_controller.upload_avatar(file, current_user.id)


@upload_router.post("/documents", summary="上传文档")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Query(..., description="文档分类"),
    current_user=Depends(get_current_user),
):
    """
    上传文档文件

    支持的文件格式: pdf, doc, docx, txt
    文件大小限制: 10MB
    """
    return await upload_controller.upload_document(file, category, current_user.id)


# ==================== 搜索API示例 ====================

from backend.schemas.search import SearchRequest, SearchResponse

search_router = APIRouter(prefix="/search", tags=["搜索"])


@search_router.post("/users", response_model=SearchResponse, summary="搜索用户")
async def search_users(
    search_request: SearchRequest, current_user=Depends(get_current_user)
):
    """
    搜索用户

    支持多字段搜索和高级过滤
    """
    return await user_controller.advanced_search(search_request)


@search_router.get("/suggestions", summary="搜索建议")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    type: str = Query("user", description="搜索类型"),
    limit: int = Query(10, ge=1, le=20, description="建议数量"),
):
    """
    获取搜索建议

    根据输入的关键词返回搜索建议
    """
    return await user_controller.get_search_suggestions(q, type, limit)


# ==================== 统计API示例 ====================

stats_router = APIRouter(prefix="/stats", tags=["统计"])


@stats_router.get("/users", summary="用户统计")
async def get_user_stats(
    current_user=Depends(get_current_user),
    _: None = Depends(require_permissions(["stats:read"])),
):
    """
    获取用户统计信息

    需要权限: stats:read
    """
    return await user_controller.get_user_statistics()


@stats_router.get("/users/daily", summary="用户日统计")
async def get_daily_user_stats(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permissions(["stats:read"])),
):
    """
    获取用户日统计数据

    Args:
        days: 统计天数，最大365天

    需要权限: stats:read
    """
    return await user_controller.get_daily_user_stats(days)


# ==================== 导出API示例 ====================

import csv
import io

from fastapi.responses import StreamingResponse

export_router = APIRouter(prefix="/export", tags=["数据导出"])


@export_router.get("/users/csv", summary="导出用户CSV")
async def export_users_csv(
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permissions(["user:export"])),
):
    """
    导出用户数据为CSV格式

    需要权限: user:export
    """
    # 获取用户数据
    users = await user_controller.get_users_for_export(is_active)

    # 创建CSV内容
    output = io.StringIO()
    writer = csv.writer(output)

    # 写入表头
    writer.writerow(["ID", "用户名", "邮箱", "全名", "是否激活", "创建时间"])

    # 写入数据
    for user in users:
        writer.writerow(
            [
                user.id,
                user.username,
                user.email,
                user.full_name or "",
                "是" if user.is_active else "否",
                user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )

    # 创建响应
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"},
    )


# ==================== 异步任务API示例 ====================

from backend.api_core.tasks import create_background_task

task_router = APIRouter(prefix="/tasks", tags=["异步任务"])


@task_router.post("/users/bulk-import", summary="批量导入用户")
async def bulk_import_users(
    file: UploadFile = File(..., description="用户数据文件"),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permissions(["user:import"])),
):
    """
    批量导入用户（异步任务）

    支持CSV和Excel格式
    需要权限: user:import
    """
    # 创建后台任务
    task_id = await create_background_task(
        "bulk_import_users",
        file_content=await file.read(),
        filename=file.filename,
        user_id=current_user.id,
    )

    return response.success(
        data={"task_id": task_id}, msg="导入任务已创建，请稍后查看结果"
    )


@task_router.get("/status/{task_id}", summary="查询任务状态")
async def get_task_status(
    task_id: str = Path(..., description="任务ID"),
    current_user=Depends(get_current_user),
):
    """
    查询异步任务状态
    """
    return await user_controller.get_task_status(task_id, current_user.id)


# ==================== 版本控制API示例 ====================

# v1版本API
v1_router = APIRouter(prefix="/v1/users", tags=["用户管理 v1"])


@v1_router.get("/{user_id}")
async def get_user_v1(user_id: int):
    """v1版本 - 获取用户信息（简化版）"""
    user = await user_controller.get_user_by_id(user_id)
    # 返回简化的用户信息
    return {
        "id": user["data"]["id"],
        "username": user["data"]["username"],
        "email": user["data"]["email"],
    }


# v2版本API
v2_router = APIRouter(prefix="/v2/users", tags=["用户管理 v2"])


@v2_router.get("/{user_id}")
async def get_user_v2(user_id: int):
    """v2版本 - 获取用户信息（完整版）"""
    return await user_controller.get_user_by_id(user_id)


# ==================== 错误处理示例 ====================


@user_router.get("/test/error", summary="错误处理测试")
async def test_error_handling():
    """测试各种错误处理情况"""

    # 业务异常
    raise BusinessError("这是一个业务异常示例", code=400)

    # HTTP异常
    # raise HTTPException(status_code=404, detail="资源不存在")

    # 系统异常
    # raise Exception("这是一个系统异常")


# ==================== 主路由器 ====================


def create_api_router():
    """创建主API路由器"""
    main_router = APIRouter()

    # 注册子路由
    main_router.include_router(user_router)
    main_router.include_router(upload_router)
    main_router.include_router(search_router)
    main_router.include_router(stats_router)
    main_router.include_router(export_router)
    main_router.include_router(task_router)

    # 版本控制路由
    main_router.include_router(v1_router)
    main_router.include_router(v2_router)

    return main_router


# 使用示例
api_router = create_api_router()
