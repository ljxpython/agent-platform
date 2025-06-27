"""
项目管理相关的Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """项目基础Schema"""

    name: str = Field(..., description="项目名称", min_length=1, max_length=100)
    display_name: str = Field(..., description="显示名称", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="项目描述")
    is_active: bool = Field(True, description="是否激活")

    # 项目详细信息（可选字段）
    department: Optional[str] = Field(None, description="所属部门", max_length=200)
    manager: Optional[str] = Field(None, description="项目经理", max_length=100)
    members: List[str] = Field(default_factory=list, description="项目成员列表")
    tags: List[str] = Field(default_factory=list, description="项目标签")
    start_date: Optional[date] = Field(None, description="项目开始日期")
    end_date: Optional[date] = Field(None, description="项目结束日期")
    priority: str = Field(
        "medium", description="项目优先级", pattern="^(low|medium|high|urgent)$"
    )
    status: str = Field(
        "planning",
        description="项目状态",
        pattern="^(planning|active|paused|completed|cancelled)$",
    )
    budget: Optional[Decimal] = Field(None, description="项目预算")
    contact_email: Optional[str] = Field(None, description="联系邮箱", max_length=255)
    contact_phone: Optional[str] = Field(None, description="联系电话", max_length=50)
    repository_url: Optional[str] = Field(
        None, description="代码仓库地址", max_length=500
    )
    documentation_url: Optional[str] = Field(
        None, description="文档地址", max_length=500
    )

    settings: Dict[str, Any] = Field(default_factory=dict, description="项目设置")


class ProjectCreate(ProjectBase):
    """创建项目Schema"""

    pass


class ProjectUpdate(BaseModel):
    """更新项目Schema"""

    name: Optional[str] = Field(
        None, description="项目名称", min_length=1, max_length=100
    )
    display_name: Optional[str] = Field(
        None, description="显示名称", min_length=1, max_length=200
    )
    description: Optional[str] = Field(None, description="项目描述")
    is_active: Optional[bool] = Field(None, description="是否激活")

    # 项目详细信息（可选字段）
    department: Optional[str] = Field(None, description="所属部门", max_length=200)
    manager: Optional[str] = Field(None, description="项目经理", max_length=100)
    members: Optional[List[str]] = Field(None, description="项目成员列表")
    tags: Optional[List[str]] = Field(None, description="项目标签")
    start_date: Optional[date] = Field(None, description="项目开始日期")
    end_date: Optional[date] = Field(None, description="项目结束日期")
    priority: Optional[str] = Field(
        None, description="项目优先级", pattern="^(low|medium|high|urgent)$"
    )
    status: Optional[str] = Field(
        None,
        description="项目状态",
        pattern="^(planning|active|paused|completed|cancelled)$",
    )
    budget: Optional[Decimal] = Field(None, description="项目预算")
    contact_email: Optional[str] = Field(None, description="联系邮箱", max_length=255)
    contact_phone: Optional[str] = Field(None, description="联系电话", max_length=50)
    repository_url: Optional[str] = Field(
        None, description="代码仓库地址", max_length=500
    )
    documentation_url: Optional[str] = Field(
        None, description="文档地址", max_length=500
    )

    settings: Optional[Dict[str, Any]] = Field(None, description="项目设置")


class ProjectResponse(ProjectBase):
    """项目响应Schema"""

    id: int
    is_default: bool
    created_by_id: Optional[int] = None
    created_at: str
    updated_at: str

    # 统计信息
    stats: Optional[Dict[str, int]] = None

    class Config:
        from_attributes = True


class ProjectListParams(BaseModel):
    """项目列表查询参数"""

    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    name: Optional[str] = Field(None, description="项目名称搜索")
    is_active: Optional[bool] = Field(None, description="是否激活")
    created_by_id: Optional[int] = Field(None, description="创建者ID")


class ProjectStats(BaseModel):
    """项目统计信息"""

    rag_collections: int = Field(0, description="RAG知识库数量")
    test_cases: int = Field(0, description="测试用例数量")
    midscene_sessions: int = Field(0, description="Midscene会话数量")


class ProjectSwitchRequest(BaseModel):
    """项目切换请求"""

    project_id: int = Field(..., description="目标项目ID")


class ProjectSwitchResponse(BaseModel):
    """项目切换响应"""

    project_id: int
    project_name: str
    display_name: str
    message: str = "项目切换成功"
