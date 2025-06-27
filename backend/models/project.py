"""
项目管理模型
"""

from tortoise import fields

from .base import BaseModel, TimestampMixin


class Project(BaseModel, TimestampMixin):
    """项目模型"""

    name = fields.CharField(max_length=100, unique=True, description="项目名称")
    display_name = fields.CharField(max_length=200, description="显示名称")
    description = fields.TextField(null=True, description="项目描述")

    # 项目配置
    is_default = fields.BooleanField(default=False, description="是否为默认项目")
    is_active = fields.BooleanField(default=True, description="是否激活")

    # 项目详细信息（可选字段）
    department = fields.CharField(max_length=200, null=True, description="所属部门")
    manager = fields.CharField(max_length=100, null=True, description="项目经理")
    members = fields.JSONField(default=list, description="项目成员列表")
    tags = fields.JSONField(default=list, description="项目标签")
    start_date = fields.DateField(null=True, description="项目开始日期")
    end_date = fields.DateField(null=True, description="项目结束日期")
    priority = fields.CharField(
        max_length=20,
        default="medium",
        description="项目优先级: low, medium, high, urgent",
    )
    status = fields.CharField(
        max_length=20,
        default="planning",
        description="项目状态: planning, active, paused, completed, cancelled",
    )
    budget = fields.DecimalField(
        max_digits=15, decimal_places=2, null=True, description="项目预算"
    )
    contact_email = fields.CharField(max_length=255, null=True, description="联系邮箱")
    contact_phone = fields.CharField(max_length=50, null=True, description="联系电话")
    repository_url = fields.CharField(
        max_length=500, null=True, description="代码仓库地址"
    )
    documentation_url = fields.CharField(
        max_length=500, null=True, description="文档地址"
    )

    # 项目设置
    settings = fields.JSONField(default=dict, description="项目设置")

    # 创建者
    created_by = fields.ForeignKeyField(
        "models.User", related_name="created_projects", null=True, description="创建者"
    )

    class Meta:
        table = "projects"
        table_description = "项目表"

    def __str__(self):
        return f"Project({self.name})"

    async def get_stats(self):
        """获取项目统计信息"""
        from backend.models.rag import RAGCollection
        from backend.models.testcase import TestCase

        # 统计RAG知识库数量
        rag_count = await RAGCollection.filter(project=self).count()

        # 统计测试用例数量
        testcase_count = await TestCase.filter(project=self).count()

        return {
            "rag_collections": rag_count,
            "test_cases": testcase_count,
        }
