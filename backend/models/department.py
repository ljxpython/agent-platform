"""
部门模型
"""

from tortoise import fields

from .base import BaseModel, TimestampMixin


class Department(BaseModel, TimestampMixin):
    """部门模型"""

    name = fields.CharField(max_length=100, unique=True, description="部门名称")
    description = fields.TextField(null=True, description="部门描述")
    parent = fields.ForeignKeyField(
        "models.Department", related_name="children", null=True, description="上级部门"
    )
    sort_order = fields.IntField(default=0, description="排序")
    is_active = fields.BooleanField(default=True, description="是否激活")

    class Meta:
        table = "departments"
        table_description = "部门表"

    def __str__(self):
        return self.name

    async def get_full_path(self):
        """获取部门完整路径"""
        path = [self.name]
        parent = await self.parent
        while parent:
            path.insert(0, parent.name)
            parent = await parent.parent
        return " / ".join(path)
