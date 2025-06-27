"""
项目管理控制器
"""

from typing import List, Optional, Tuple

from loguru import logger
from tortoise.expressions import Q
from tortoise.queryset import QuerySet

from backend.controllers.base import BaseController
from backend.models.project import Project
from backend.schemas.project import ProjectCreate, ProjectUpdate


class ProjectController(BaseController[Project, ProjectCreate, ProjectUpdate]):
    """项目管理控制器"""

    def __init__(self):
        super().__init__(Project)

    async def get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
        created_by_id: Optional[int] = None,
    ) -> Tuple[List[Project], int]:
        """获取项目列表"""

        # 构建查询条件
        query = self.model.all()

        if name:
            query = query.filter(
                Q(name__icontains=name) | Q(display_name__icontains=name)
            )

        if is_active is not None:
            query = query.filter(is_active=is_active)

        if created_by_id is not None:
            query = query.filter(created_by_id=created_by_id)

        # 获取总数
        total = await query.count()

        # 分页查询
        offset = (page - 1) * page_size
        projects = (
            await query.offset(offset).limit(page_size).prefetch_related("created_by")
        )

        return projects, total

    async def get_by_name(self, name: str) -> Optional[Project]:
        """根据名称获取项目"""
        return await self.model.get_or_none(name=name)

    async def get_default_project(self) -> Optional[Project]:
        """获取默认项目"""
        return await self.model.get_or_none(is_default=True)

    async def create_project(
        self, project_in: ProjectCreate, created_by_id: Optional[int] = None
    ) -> Project:
        """创建项目"""

        # 检查名称是否已存在
        existing = await self.get_by_name(project_in.name)
        if existing:
            raise ValueError(f"项目名称 '{project_in.name}' 已存在")

        # 创建项目
        project_data = project_in.model_dump()
        if created_by_id:
            project_data["created_by_id"] = created_by_id

        project = await self.model.create(**project_data)
        logger.info(f"创建项目成功: {project.name}")

        return project

    async def set_default_project(self, project_id: int) -> Project:
        """设置默认项目"""

        # 取消所有项目的默认状态
        await self.model.all().update(is_default=False)

        # 设置指定项目为默认
        project = await self.get(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        project.is_default = True
        await project.save()

        logger.info(f"设置默认项目: {project.name}")
        return project

    async def get_project_stats(self, project_id: int) -> dict:
        """获取项目统计信息"""
        project = await self.get(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        return await project.get_stats()

    async def activate_project(self, project_id: int) -> Project:
        """激活项目"""
        project = await self.get(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        project.is_active = True
        await project.save()

        logger.info(f"激活项目: {project.name}")
        return project

    async def deactivate_project(self, project_id: int) -> Project:
        """停用项目"""
        project = await self.get(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        # 不能停用默认项目
        if project.is_default:
            raise ValueError("不能停用默认项目")

        project.is_active = False
        await project.save()

        logger.info(f"停用项目: {project.name}")
        return project

    async def delete_project(self, project_id: int) -> bool:
        """删除项目"""
        project = await self.get(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        # 不能删除默认项目
        if project.is_default:
            raise ValueError("不能删除默认项目")

        # 检查是否有关联数据
        stats = await project.get_stats()
        if any(stats.values()):
            raise ValueError("项目下还有数据，不能删除")

        await project.delete()
        logger.info(f"删除项目: {project.name}")

        return True


# 创建全局实例
project_controller = ProjectController()
