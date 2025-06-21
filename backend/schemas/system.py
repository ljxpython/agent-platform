"""
系统管理相关的Schema
"""

from typing import List, Optional

from pydantic import BaseModel, Field

# ==================== 用户管理 ====================


class UserBase(BaseModel):
    """用户基础Schema"""

    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, description="全名")
    is_active: bool = Field(True, description="是否激活")
    dept_id: Optional[int] = Field(None, description="部门ID")


class UserCreate(UserBase):
    """创建用户Schema"""

    password: str = Field(..., description="密码")
    role_ids: List[int] = Field(default=[], description="角色ID列表")


class UserUpdate(UserBase):
    """更新用户Schema"""

    id: int = Field(..., description="用户ID")
    role_ids: List[int] = Field(default=[], description="角色ID列表")


class UserResponse(UserBase):
    """用户响应Schema"""

    id: int
    is_superuser: bool
    last_login: Optional[str] = None
    created_at: str
    updated_at: str
    dept: Optional[dict] = None
    roles: List[dict] = []

    class Config:
        from_attributes = True


# ==================== 角色管理 ====================


class RoleBase(BaseModel):
    """角色基础Schema"""

    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    is_active: bool = Field(True, description="是否激活")


class RoleCreate(RoleBase):
    """创建角色Schema"""

    pass


class RoleUpdate(RoleBase):
    """更新角色Schema"""

    id: int = Field(..., description="角色ID")


class RoleResponse(RoleBase):
    """角色响应Schema"""

    id: int
    created_at: str
    updated_at: str
    apis: List[dict] = []

    class Config:
        from_attributes = True


class RoleUpdateApis(BaseModel):
    """更新角色API权限Schema"""

    id: int = Field(..., description="角色ID")
    api_ids: List[int] = Field(default=[], description="API ID列表")


# ==================== 部门管理 ====================


class DepartmentBase(BaseModel):
    """部门基础Schema"""

    name: str = Field(..., description="部门名称")
    description: Optional[str] = Field(None, description="部门描述")
    parent_id: Optional[int] = Field(None, description="上级部门ID")
    sort_order: int = Field(0, description="排序")
    is_active: bool = Field(True, description="是否激活")


class DepartmentCreate(DepartmentBase):
    """创建部门Schema"""

    pass


class DepartmentUpdate(DepartmentBase):
    """更新部门Schema"""

    id: int = Field(..., description="部门ID")


class DepartmentResponse(DepartmentBase):
    """部门响应Schema"""

    id: int
    created_at: str
    updated_at: str
    children: List["DepartmentResponse"] = []
    users_count: int = 0

    class Config:
        from_attributes = True


# ==================== API管理 ====================


class ApiBase(BaseModel):
    """API基础Schema"""

    path: str = Field(..., description="API路径")
    method: str = Field(..., description="请求方法")
    summary: Optional[str] = Field(None, description="API简介")
    description: Optional[str] = Field(None, description="API描述")
    tags: Optional[str] = Field(None, description="API标签")
    is_active: bool = Field(True, description="是否激活")


class ApiCreate(ApiBase):
    """创建API Schema"""

    pass


class ApiUpdate(ApiBase):
    """更新API Schema"""

    id: int = Field(..., description="API ID")


class ApiResponse(ApiBase):
    """API响应Schema"""

    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# 解决循环引用
DepartmentResponse.model_rebuild()
