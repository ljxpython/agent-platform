# API开发规范

## 🎯 API设计原则

### RESTful设计
遵循RESTful API设计原则，使用标准HTTP方法：

- `GET` - 获取资源
- `POST` - 创建资源
- `PUT` - 更新资源（完整更新）
- `PATCH` - 更新资源（部分更新）
- `DELETE` - 删除资源

### URL设计规范
```
# 资源集合
GET    /api/v1/users          # 获取用户列表
POST   /api/v1/users          # 创建用户

# 单个资源
GET    /api/v1/users/{id}     # 获取指定用户
PUT    /api/v1/users/{id}     # 更新指定用户
DELETE /api/v1/users/{id}     # 删除指定用户

# 嵌套资源
GET    /api/v1/users/{id}/posts    # 获取用户的文章
POST   /api/v1/users/{id}/posts    # 为用户创建文章
```

## 📡 API接口开发流程

### 1. 定义Schema模型

```python
# schemas/user.py
from typing import Optional
from pydantic import Field, EmailStr
from backend.schemas.base import BaseSchema

class UserCreate(BaseSchema):
    """用户创建Schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")

class UserUpdate(BaseSchema):
    """用户更新Schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class UserResponse(BaseSchema):
    """用户响应Schema"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
```

### 2. 实现控制器

```python
# controllers/user_controller.py
from typing import List, Optional
from backend.api_core.crud import CRUDBase
from backend.api_core.response import response
from backend.models.user import User
from backend.schemas.user import UserCreate, UserUpdate


class UserController(CRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(User)

    async def get_users_with_pagination(
            self,
            page: int = 1,
            page_size: int = 20,
            search: Optional[str] = None
    ):
        """获取用户列表（分页）"""
        query = self.model.all()

        # 搜索过滤
        if search:
            query = query.filter(
                Q(username__icontains=search) |
                Q(full_name__icontains=search)
            )

        # 分页
        total = await query.count()
        users = await query.offset((page - 1) * page_size).limit(page_size)

        return response.success_with_pagination(
            data=[UserResponse.from_orm(user) for user in users],
            total=total,
            page=page,
            page_size=page_size
        )


# 创建控制器实例
user_controller = UserController()
```

### 3. 定义API路由

```python
# api/v1/users.py
from fastapi import APIRouter, Query, Path, Depends
from typing import Optional
from backend.controllers.user_controller import user_controller
from backend.schemas.user import UserCreate, UserUpdate, UserResponse
from backend.api_core.deps import get_current_active_user

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("/", summary="获取用户列表")
async def get_users(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        search: Optional[str] = Query(None, description="搜索关键词")
):
    """
    获取用户列表

    - **page**: 页码，从1开始
    - **page_size**: 每页数量，最大100
    - **search**: 搜索关键词，支持用户名和全名搜索
    """
    return await user_controller.get_users_with_pagination(page, page_size, search)


@router.post("/", response_model=UserResponse, summary="创建用户")
async def create_user(user_data: UserCreate):
    """
    创建新用户

    - **username**: 用户名，3-50字符
    - **email**: 邮箱地址
    - **password**: 密码，至少6字符
    - **full_name**: 全名（可选）
    """
    return await user_controller.create(user_data)


@router.get("/{user_id}", response_model=UserResponse, summary="获取用户详情")
async def get_user(
        user_id: int = Path(..., description="用户ID")
):
    """获取指定用户的详细信息"""
    return await user_controller.get(user_id)


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户")
async def update_user(
        user_id: int = Path(..., description="用户ID"),
        user_data: UserUpdate
):
    """
    更新用户信息

    - **email**: 邮箱地址
    - **full_name**: 全名
    - **is_active**: 是否激活
    """
    return await user_controller.update(user_id, user_data)


@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
        user_id: int = Path(..., description="用户ID"),
        current_user=Depends(get_current_active_user)
):
    """删除指定用户"""
    return await user_controller.delete(user_id)
```

## ✅ 参数校验规范

### 1. 路径参数校验
```python
from fastapi import Path

@router.get("/users/{user_id}")
async def get_user(
    user_id: int = Path(..., gt=0, description="用户ID")
):
    pass
```

### 2. 查询参数校验
```python
from fastapi import Query

@router.get("/users")
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, regex="^(active|inactive)$", description="状态")
):
    pass
```

### 3. 请求体校验
```python
from pydantic import Field, validator

class UserCreate(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=6)

    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v
```

## 📤 统一响应格式

### 1. 使用响应工具类

```python
from backend.api_core.response import response


# 成功响应
@router.get("/users")
async def get_users():
    users = await User.all()
    return response.success(
        data=users,
        msg="获取用户列表成功"
    )


# 分页响应
@router.get("/users/paginated")
async def get_users_paginated():
    return response.success_with_pagination(
        data=users,
        total=100,
        page=1,
        page_size=20,
        msg="获取用户列表成功"
    )


# 错误响应（通过异常处理）
from backend.api_core.exceptions import BusinessError


@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise BusinessError("用户不存在", code=404)
    return response.success(data=user)
```

### 2. 响应格式标准

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    // 具体数据
  }
}

// 分页响应
{
  "code": 200,
  "msg": "操作成功",
  "data": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}

// 错误响应
{
  "code": 400,
  "msg": "错误信息",
  "data": null
}
```

## 🗄️ 数据库交互

### 1. 使用CRUD基类

```python
from backend.api_core.crud import CRUDBase


class UserController(CRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(User)

    # 继承的方法：
    # - create(obj_in) -> 创建
    # - get(id) -> 获取单个
    # - get_multi(skip, limit) -> 获取多个
    # - update(db_obj, obj_in) -> 更新
    # - delete(id) -> 删除
```

### 2. 自定义查询方法

```python
class UserController(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_username(self, username: str):
        """根据用户名获取用户"""
        user = await self.model.get_or_none(username=username)
        if not user:
            raise BusinessError("用户不存在", code=404)
        return response.success(data=UserResponse.from_orm(user))

    async def get_active_users(self):
        """获取活跃用户"""
        users = await self.model.filter(is_active=True).all()
        return response.success(
            data=[UserResponse.from_orm(user) for user in users]
        )
```

## 🔒 权限控制

### 1. 依赖注入权限检查

```python
from backend.api_core.deps import get_current_active_user, require_permissions


@router.get("/admin/users")
async def get_all_users(
        current_user=Depends(get_current_active_user),
        _: None = Depends(require_permissions(["user:read"]))
):
    """需要用户读取权限"""
    pass


@router.delete("/users/{user_id}")
async def delete_user(
        user_id: int,
        current_user=Depends(get_current_active_user),
        _: None = Depends(require_permissions(["user:delete"]))
):
    """需要用户删除权限"""
    pass
```

### 2. 角色权限控制

```python
from backend.api_core.deps import require_roles


@router.post("/admin/users")
async def create_admin_user(
        user_data: UserCreate,
        _: None = Depends(require_roles(["admin", "super_admin"]))
):
    """只有管理员可以创建用户"""
    pass
```

## 📝 API文档规范

### 1. 接口描述

```python
@router.post("/users", summary="创建用户", description="创建新的用户账户")
async def create_user(user_data: UserCreate):
    """
    创建新用户

    创建一个新的用户账户，需要提供用户名、邮箱和密码。

    - **username**: 用户名，3-50字符，只能包含字母和数字
    - **email**: 有效的邮箱地址
    - **password**: 密码，至少6字符
    - **full_name**: 用户全名（可选）

    Returns:
        UserResponse: 创建的用户信息

    Raises:
        400: 参数验证失败
        409: 用户名或邮箱已存在
    """
    pass
```

### 2. 响应模型定义

```python
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """指定响应模型，自动生成文档"""
    pass
```

## 🚨 错误处理

### 1. 统一异常处理

```python
from backend.api_core.exceptions import BusinessError, ValidationError


@router.post("/users")
async def create_user(user_data: UserCreate):
    # 业务逻辑异常
    if await User.exists(username=user_data.username):
        raise BusinessError("用户名已存在", code=409)

    # 数据验证异常
    if not user_data.email.endswith("@company.com"):
        raise ValidationError("只允许公司邮箱注册")

    # 其他异常会被全局异常处理器捕获
    user = await user_controller.create(user_data)
    return user
```

### 2. HTTP状态码规范

- `200` - 成功
- `201` - 创建成功
- `400` - 请求参数错误
- `401` - 未认证
- `403` - 无权限
- `404` - 资源不存在
- `409` - 资源冲突
- `422` - 参数验证失败
- `500` - 服务器错误

## 🔄 版本控制

### 1. API版本管理

```python
# api/v1/users.py
router = APIRouter(prefix="/v1/users")

# api/v2/users.py
router = APIRouter(prefix="/v2/users")
```

### 2. 向后兼容

```python
# 保持旧版本接口可用
@router.get("/v1/users/{user_id}")
async def get_user_v1(user_id: int):
    """v1版本接口，保持兼容"""
    pass

@router.get("/v2/users/{user_id}")
async def get_user_v2(user_id: int):
    """v2版本接口，新功能"""
    pass
```
