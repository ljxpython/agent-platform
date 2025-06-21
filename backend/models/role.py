"""
角色模型
"""

from tortoise import fields

from .base import BaseModel, TimestampMixin


class Role(BaseModel, TimestampMixin):
    """角色模型"""

    name = fields.CharField(max_length=50, unique=True, description="角色名称")
    description = fields.TextField(null=True, description="角色描述")
    is_active = fields.BooleanField(default=True, description="是否激活")

    # 关联字段
    apis = fields.ManyToManyField(
        "models.Api", related_name="roles", description="角色API权限"
    )

    class Meta:
        table = "roles"
        table_description = "角色表"

    def __str__(self):
        return self.name


class RoleApi(BaseModel):
    """角色API关联表"""

    role = fields.ForeignKeyField(
        "models.Role", related_name="role_apis", description="角色"
    )
    api = fields.ForeignKeyField(
        "models.Api", related_name="role_apis", description="API"
    )

    class Meta:
        table = "role_apis"
        table_description = "角色API关联表"
        unique_together = (("role", "api"),)
