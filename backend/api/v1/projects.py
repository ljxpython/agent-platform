"""
项目管理API路由
"""

from typing import List

from fastapi import APIRouter, HTTPException, Query, Request
from loguru import logger

from backend.controllers.project_controller import project_controller
from backend.schemas.base import Success, SuccessExtra
from backend.schemas.project import (
    ProjectCreate,
    ProjectListParams,
    ProjectResponse,
    ProjectStats,
    ProjectSwitchRequest,
    ProjectSwitchResponse,
    ProjectUpdate,
)

# 创建路由
project_router = APIRouter()


@project_router.get("/projects", summary="获取项目列表")
async def get_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: str = Query(None, description="项目名称搜索"),
    is_active: bool = Query(None, description="是否激活"),
    created_by_id: int = Query(None, description="创建者ID"),
):
    """获取项目列表"""
    try:
        projects, total = await project_controller.get_list(
            page=page,
            page_size=page_size,
            name=name,
            is_active=is_active,
            created_by_id=created_by_id,
        )

        # 转换为响应格式
        project_list = []
        for project in projects:
            project_dict = {
                "id": project.id,
                "name": project.name,
                "display_name": project.display_name,
                "description": project.description,
                "is_default": project.is_default,
                "is_active": project.is_active,
                "settings": project.settings,
                "created_by_id": project.created_by_id,
                "created_at": (
                    project.created_at.isoformat() if project.created_at else None
                ),
                "updated_at": (
                    project.updated_at.isoformat() if project.updated_at else None
                ),
            }

            # 获取统计信息
            try:
                stats = await project.get_stats()
                project_dict["stats"] = stats
            except Exception as e:
                logger.warning(f"获取项目统计信息失败: {e}")
                project_dict["stats"] = {
                    "rag_collections": 0,
                    "test_cases": 0,
                    "midscene_sessions": 0,
                }

            project_list.append(project_dict)

        return SuccessExtra(
            data=project_list,
            total=total,
            page=page,
            page_size=page_size,
            msg="获取项目列表成功",
        )

    except Exception as e:
        logger.error(f"获取项目列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@project_router.get("/projects/{project_id}", summary="获取项目详情")
async def get_project(project_id: int):
    """获取项目详情"""
    try:
        project = await project_controller.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 获取统计信息
        stats = await project.get_stats()

        project_data = {
            "id": project.id,
            "name": project.name,
            "display_name": project.display_name,
            "description": project.description,
            "is_default": project.is_default,
            "is_active": project.is_active,
            "settings": project.settings,
            "created_by_id": project.created_by_id,
            "created_at": (
                project.created_at.isoformat() if project.created_at else None
            ),
            "updated_at": (
                project.updated_at.isoformat() if project.updated_at else None
            ),
            "stats": stats,
        }

        return Success(data=project_data, msg="获取项目详情成功")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@project_router.post("/projects", summary="创建项目")
async def create_project(project_in: ProjectCreate, request: Request):
    """创建项目"""
    try:
        # TODO: 从请求中获取当前用户ID
        created_by_id = None  # 暂时设为None，后续集成认证系统时修改

        project = await project_controller.create_project(project_in, created_by_id)

        return Success(data={"id": project.id}, msg="项目创建成功")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建项目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@project_router.put("/projects/{project_id}", summary="更新项目")
async def update_project(project_id: int, project_in: ProjectUpdate):
    """更新项目"""
    try:
        # 检查项目是否存在
        existing_project = await project_controller.get(project_id)
        if not existing_project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 如果更新名称，检查是否重复
        if project_in.name and project_in.name != existing_project.name:
            existing_name = await project_controller.get_by_name(project_in.name)
            if existing_name:
                raise HTTPException(
                    status_code=400, detail=f"项目名称 '{project_in.name}' 已存在"
                )

        # 更新项目
        project = await project_controller.update(id=project_id, obj_in=project_in)

        return Success(msg="项目更新成功")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新项目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@project_router.delete("/projects/{project_id}", summary="删除项目")
async def delete_project(project_id: int):
    """删除项目"""
    try:
        await project_controller.delete_project(project_id)
        return Success(msg="项目删除成功")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@project_router.post("/projects/{project_id}/set-default", summary="设置默认项目")
async def set_default_project(project_id: int):
    """设置默认项目"""
    try:
        project = await project_controller.set_default_project(project_id)
        return Success(msg=f"已设置 '{project.display_name}' 为默认项目")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"设置默认项目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@project_router.post("/projects/{project_id}/activate", summary="激活项目")
async def activate_project(project_id: int):
    """激活项目"""
    try:
        project = await project_controller.activate_project(project_id)
        return Success(msg=f"项目 '{project.display_name}' 已激活")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"激活项目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@project_router.post("/projects/{project_id}/deactivate", summary="停用项目")
async def deactivate_project(project_id: int):
    """停用项目"""
    try:
        project = await project_controller.deactivate_project(project_id)
        return Success(msg=f"项目 '{project.display_name}' 已停用")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"停用项目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@project_router.get("/projects/{project_id}/stats", summary="获取项目统计")
async def get_project_stats(project_id: int):
    """获取项目统计信息"""
    try:
        stats = await project_controller.get_project_stats(project_id)
        return Success(data=stats, msg="获取项目统计成功")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取项目统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@project_router.get("/projects/default", summary="获取默认项目")
async def get_default_project():
    """获取默认项目"""
    try:
        project = await project_controller.get_default_project()
        if not project:
            raise HTTPException(status_code=404, detail="未设置默认项目")

        project_data = {
            "id": project.id,
            "name": project.name,
            "display_name": project.display_name,
            "description": project.description,
            "is_default": project.is_default,
            "is_active": project.is_active,
            "settings": project.settings,
            "created_at": (
                project.created_at.isoformat() if project.created_at else None
            ),
            "updated_at": (
                project.updated_at.isoformat() if project.updated_at else None
            ),
        }

        return Success(data=project_data, msg="获取默认项目成功")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取默认项目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
