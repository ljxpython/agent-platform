"""
基础控制器类
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from tortoise.models import Model

ModelType = TypeVar("ModelType", bound=Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseController(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """基础控制器类"""

    def __init__(self, model: Type[ModelType]):
        """
        初始化控制器

        Args:
            model: Tortoise ORM 模型类
        """
        self.model = model

    async def get(self, id: Any) -> Optional[ModelType]:
        """根据ID获取单个对象"""
        return await self.model.get_or_none(id=id)

    async def get_multi(
        self, skip: int = 0, limit: int = 100, **filters
    ) -> List[ModelType]:
        """获取多个对象"""
        query = self.model.filter(**filters) if filters else self.model.all()
        return await query.offset(skip).limit(limit)

    async def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """创建对象"""
        obj_data = (
            obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in.dict()
        )
        return await self.model.create(**obj_data)

    async def update(
        self, *, id: Any, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> Optional[ModelType]:
        """更新对象"""
        obj = await self.get(id)
        if not obj:
            return None

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = (
                obj_in.model_dump(exclude_unset=True)
                if hasattr(obj_in, "model_dump")
                else obj_in.dict(exclude_unset=True)
            )

        # 过滤掉 None 值，避免更新不必要的字段
        filtered_data = {k: v for k, v in update_data.items() if v is not None}

        if filtered_data:
            # 使用 update_fields 参数来指定要更新的字段
            for field, value in filtered_data.items():
                setattr(obj, field, value)

            await obj.save(update_fields=list(filtered_data.keys()))

        return obj

    async def remove(self, *, id: Any) -> bool:
        """删除对象"""
        obj = await self.get(id)
        if obj:
            await obj.delete()
            return True
        return False

    async def count(self, **filters) -> int:
        """统计对象数量"""
        query = self.model.filter(**filters) if filters else self.model.all()
        return await query.count()

    async def exists(self, **filters) -> bool:
        """检查对象是否存在"""
        return await self.model.filter(**filters).exists()
