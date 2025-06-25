from typing import Any, Dict, Generic, List, NewType, Tuple, Type, TypeVar, Union

from pydantic import BaseModel
from tortoise.expressions import Q
from tortoise.models import Model

Total = NewType("Total", int)
ModelType = TypeVar("ModelType", bound=Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """CRUD基础类，提供通用的增删改查操作"""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, id: int) -> ModelType:
        """根据ID获取单个对象"""
        return await self.model.get(id=id)

    async def list(
        self, page: int, page_size: int, search: Q = Q(), order: list = []
    ) -> Tuple[Total, List[ModelType]]:
        """分页查询列表"""
        query = self.model.filter(search)
        return await query.count(), await query.offset((page - 1) * page_size).limit(
            page_size
        ).order_by(*order)

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """创建新对象"""
        if isinstance(obj_in, Dict):
            obj_dict = obj_in
        else:
            obj_dict = obj_in.model_dump()
        obj = self.model(**obj_dict)
        await obj.save()
        return obj

    async def update(
        self, id: int, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """更新对象"""
        if isinstance(obj_in, Dict):
            obj_dict = obj_in
        else:
            obj_dict = obj_in.model_dump(exclude_unset=True, exclude={"id"})
        obj = await self.get(id=id)
        obj = obj.update_from_dict(obj_dict)
        await obj.save()
        return obj

    async def remove(self, id: int) -> None:
        """删除对象"""
        obj = await self.get(id=id)
        await obj.delete()

    async def exists(self, **kwargs) -> bool:
        """检查对象是否存在"""
        return await self.model.exists(**kwargs)

    async def get_by_field(self, field: str, value: Any) -> ModelType:
        """根据字段值获取对象"""
        return await self.model.get(**{field: value})

    async def filter(self, **kwargs) -> List[ModelType]:
        """根据条件过滤对象"""
        return await self.model.filter(**kwargs)

    async def count(self, search: Q = Q()) -> int:
        """统计数量"""
        return await self.model.filter(search).count()
