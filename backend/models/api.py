"""
API管理模型
"""

from tortoise import fields

from .base import BaseModel, TimestampMixin


class Api(BaseModel, TimestampMixin):
    """API模型"""

    path = fields.CharField(max_length=255, description="API路径")
    method = fields.CharField(max_length=10, description="请求方法")
    summary = fields.CharField(max_length=255, null=True, description="API简介")
    description = fields.TextField(null=True, description="API描述")
    tags = fields.CharField(max_length=100, null=True, description="API标签")
    is_active = fields.BooleanField(default=True, description="是否激活")

    class Meta:
        table = "apis"
        table_description = "API表"
        unique_together = (("path", "method"),)

    def __str__(self):
        return f"{self.method} {self.path}"

    @property
    def full_path(self):
        """完整路径"""
        return f"{self.method} {self.path}"
