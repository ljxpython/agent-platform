"""
Midscene 数据库模型
用于存储 Midscene 智能体系统的相关数据
"""

from datetime import datetime
from typing import Optional

from tortoise import fields
from tortoise.models import Model


class MidsceneSession(Model):
    """Midscene 会话模型"""

    id = fields.IntField(pk=True)
    session_id = fields.CharField(max_length=100, unique=True, description="会话ID")
    user_id = fields.IntField(null=True, description="用户ID")
    user_requirement = fields.TextField(description="用户需求描述")
    status = fields.CharField(
        max_length=20,
        default="pending",
        description="会话状态: pending, processing, completed, failed",
    )

    # 项目关联
    project = fields.ForeignKeyField(
        "models.Project",
        related_name="midscene_sessions",
        null=True,
        description="所属项目",
    )

    # 文件信息
    uploaded_files = fields.JSONField(default=list, description="上传的文件列表")
    file_count = fields.IntField(default=0, description="文件数量")

    # 生成结果
    ui_analysis_result = fields.TextField(null=True, description="UI分析结果")
    interaction_analysis_result = fields.TextField(
        null=True, description="交互分析结果"
    )
    midscene_generation_result = fields.TextField(
        null=True, description="Midscene生成结果"
    )
    script_generation_result = fields.TextField(null=True, description="脚本生成结果")

    # 最终输出
    yaml_script = fields.TextField(null=True, description="YAML脚本")
    playwright_script = fields.TextField(null=True, description="Playwright脚本")
    script_info = fields.JSONField(null=True, description="脚本信息")

    # 统计信息
    processing_time = fields.FloatField(null=True, description="处理时间(秒)")
    agent_count = fields.IntField(default=4, description="参与的智能体数量")
    total_tokens = fields.IntField(null=True, description="总token消耗")

    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    completed_at = fields.DatetimeField(null=True, description="完成时间")

    class Meta:
        table = "midscene_sessions"
        table_description = "Midscene会话记录表"


class MidsceneAgentLog(Model):
    """Midscene 智能体日志模型"""

    id = fields.IntField(pk=True)
    session_id = fields.CharField(max_length=100, description="会话ID")
    agent_name = fields.CharField(max_length=50, description="智能体名称")
    agent_type = fields.CharField(max_length=30, description="智能体类型")

    # 执行信息
    step = fields.CharField(max_length=100, description="执行步骤")
    status = fields.CharField(
        max_length=20, description="状态: start, processing, complete, error"
    )

    # 内容
    input_content = fields.TextField(null=True, description="输入内容")
    output_content = fields.TextField(null=True, description="输出内容")
    error_message = fields.TextField(null=True, description="错误信息")

    # 统计
    processing_time = fields.FloatField(null=True, description="处理时间(秒)")
    token_count = fields.IntField(null=True, description="token消耗")
    chunk_count = fields.IntField(default=0, description="流式输出块数")

    # 时间戳
    started_at = fields.DatetimeField(description="开始时间")
    completed_at = fields.DatetimeField(null=True, description="完成时间")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "midscene_agent_logs"
        table_description = "Midscene智能体执行日志表"


class MidsceneUploadedFile(Model):
    """Midscene 上传文件模型"""

    id = fields.IntField(pk=True)
    session_id = fields.CharField(max_length=100, description="会话ID")

    # 文件信息
    original_filename = fields.CharField(max_length=255, description="原始文件名")
    stored_filename = fields.CharField(max_length=255, description="存储文件名")
    file_path = fields.CharField(max_length=500, description="文件路径")
    file_size = fields.IntField(description="文件大小(字节)")
    file_type = fields.CharField(max_length=50, description="文件类型")
    mime_type = fields.CharField(max_length=100, description="MIME类型")

    # 图片信息
    image_width = fields.IntField(null=True, description="图片宽度")
    image_height = fields.IntField(null=True, description="图片高度")
    image_format = fields.CharField(max_length=20, null=True, description="图片格式")

    # 处理状态
    status = fields.CharField(
        max_length=20,
        default="uploaded",
        description="状态: uploaded, processing, processed, error",
    )
    processed_at = fields.DatetimeField(null=True, description="处理时间")

    # 时间戳
    uploaded_at = fields.DatetimeField(auto_now_add=True, description="上传时间")

    class Meta:
        table = "midscene_uploaded_files"
        table_description = "Midscene上传文件记录表"


class MidsceneTemplate(Model):
    """Midscene 模板模型"""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, description="模板名称")
    description = fields.TextField(description="模板描述")
    category = fields.CharField(max_length=50, description="模板分类")

    # 模板内容
    requirement_template = fields.TextField(description="需求模板")
    yaml_template = fields.TextField(null=True, description="YAML模板")
    playwright_template = fields.TextField(null=True, description="Playwright模板")

    # 配置
    agent_config = fields.JSONField(default=dict, description="智能体配置")
    parameters = fields.JSONField(default=dict, description="模板参数")

    # 统计
    usage_count = fields.IntField(default=0, description="使用次数")
    success_rate = fields.FloatField(default=0.0, description="成功率")

    # 状态
    is_active = fields.BooleanField(default=True, description="是否启用")
    is_public = fields.BooleanField(default=False, description="是否公开")

    # 创建者
    created_by = fields.IntField(null=True, description="创建者ID")

    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "midscene_templates"
        table_description = "Midscene模板表"


class MidsceneStatistics(Model):
    """Midscene 统计模型"""

    id = fields.IntField(pk=True)
    date = fields.DateField(description="统计日期")

    # 会话统计
    total_sessions = fields.IntField(default=0, description="总会话数")
    completed_sessions = fields.IntField(default=0, description="完成会话数")
    failed_sessions = fields.IntField(default=0, description="失败会话数")

    # 文件统计
    total_files = fields.IntField(default=0, description="总文件数")
    total_file_size = fields.BigIntField(default=0, description="总文件大小")

    # 性能统计
    avg_processing_time = fields.FloatField(default=0.0, description="平均处理时间")
    total_tokens = fields.IntField(default=0, description="总token消耗")

    # 智能体统计
    ui_analysis_count = fields.IntField(default=0, description="UI分析次数")
    interaction_analysis_count = fields.IntField(default=0, description="交互分析次数")
    midscene_generation_count = fields.IntField(
        default=0, description="Midscene生成次数"
    )
    script_generation_count = fields.IntField(default=0, description="脚本生成次数")

    # 成功率
    success_rate = fields.FloatField(default=0.0, description="成功率")

    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "midscene_statistics"
        table_description = "Midscene统计表"
        unique_together = ("date",)


# 导出所有模型
__all__ = [
    "MidsceneSession",
    "MidsceneAgentLog",
    "MidsceneUploadedFile",
    "MidsceneTemplate",
    "MidsceneStatistics",
]
