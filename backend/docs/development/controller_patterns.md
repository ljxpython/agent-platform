# 控制器模式与代码复用

## 🎮 控制器设计原则

控制器层负责处理业务逻辑控制，连接API层和服务层，遵循以下原则：

- **单一职责** - 每个控制器只处理一类业务
- **代码复用** - 使用基类和混入模式减少重复代码
- **统一响应** - 使用统一的响应格式
- **异常处理** - 统一的异常处理机制

## 🏗️ CRUD基类使用

### 1. 基础CRUD控制器

```python
# controllers/base_controller.py
from typing import TypeVar, Generic, Type, List, Optional
from backend.api_core.crud import CRUDBase
from backend.api_core.response import response
from backend.api_core.exceptions import BusinessError
from backend.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseController(CRUDBase[ModelType, CreateSchemaType, UpdateSchemaType]):
    """基础控制器，提供标准CRUD操作"""

    def __init__(self, model: Type[ModelType]):
        super().__init__(model)
        self.model = model

    async def create_item(self, obj_in: CreateSchemaType):
        """创建项目"""
        try:
            item = await self.create(obj_in)
            return response.success(
                data=item,
                msg=f"{self.model.__name__}创建成功",
                code=201
            )
        except Exception as e:
            raise BusinessError(f"创建失败: {str(e)}")

    async def get_item(self, item_id: int):
        """获取单个项目"""
        item = await self.get(item_id)
        if not item:
            raise BusinessError(f"{self.model.__name__}不存在", code=404)

        return response.success(
            data=item,
            msg=f"获取{self.model.__name__}成功"
        )

    async def get_items_paginated(
            self,
            page: int = 1,
            page_size: int = 20,
            filters: Optional[dict] = None
    ):
        """获取分页列表"""
        query = self.model.all()

        # 应用过滤条件
        if filters:
            query = self._apply_filters(query, filters)

        total = await query.count()
        items = await query.offset((page - 1) * page_size).limit(page_size)

        return response.success_with_pagination(
            data=items,
            total=total,
            page=page,
            page_size=page_size,
            msg=f"获取{self.model.__name__}列表成功"
        )

    async def update_item(self, item_id: int, obj_in: UpdateSchemaType):
        """更新项目"""
        item = await self.get(item_id)
        if not item:
            raise BusinessError(f"{self.model.__name__}不存在", code=404)

        updated_item = await self.update(item, obj_in)
        return response.success(
            data=updated_item,
            msg=f"{self.model.__name__}更新成功"
        )

    async def delete_item(self, item_id: int):
        """删除项目"""
        item = await self.get(item_id)
        if not item:
            raise BusinessError(f"{self.model.__name__}不存在", code=404)

        await self.delete(item_id)
        return response.success(msg=f"{self.model.__name__}删除成功")

    def _apply_filters(self, query, filters: dict):
        """应用过滤条件 - 子类可重写"""
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.filter(**{field: value})
        return query
```

### 2. 具体控制器实现

```python
# controllers/user_controller.py
from typing import Optional
from tortoise.expressions import Q
from backend.models.user import User
from backend.schemas.user import UserCreate, UserUpdate, UserResponse
from backend.controllers.base_controller import BaseController

class UserController(BaseController[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(User)

    async def get_users_with_search(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ):
        """获取用户列表（支持搜索）"""
        query = self.model.all()

        # 搜索过滤
        if search:
            query = query.filter(
                Q(username__icontains=search) |
                Q(full_name__icontains=search) |
                Q(email__icontains=search)
            )

        # 状态过滤
        if is_active is not None:
            query = query.filter(is_active=is_active)

        total = await query.count()
        users = await query.offset((page - 1) * page_size).limit(page_size)

        return response.success_with_pagination(
            data=[UserResponse.from_orm(user) for user in users],
            total=total,
            page=page,
            page_size=page_size,
            msg="获取用户列表成功"
        )

    async def get_user_by_username(self, username: str):
        """根据用户名获取用户"""
        user = await self.model.get_or_none(username=username)
        if not user:
            raise BusinessError("用户不存在", code=404)

        return response.success(
            data=UserResponse.from_orm(user),
            msg="获取用户信息成功"
        )

    async def activate_user(self, user_id: int):
        """激活用户"""
        user = await self.get(user_id)
        if not user:
            raise BusinessError("用户不存在", code=404)

        user.is_active = True
        await user.save()

        return response.success(
            data=UserResponse.from_orm(user),
            msg="用户激活成功"
        )

    async def deactivate_user(self, user_id: int):
        """停用用户"""
        user = await self.get(user_id)
        if not user:
            raise BusinessError("用户不存在", code=404)

        user.is_active = False
        await user.save()

        return response.success(
            data=UserResponse.from_orm(user),
            msg="用户已停用"
        )

# 创建控制器实例
user_controller = UserController()
```

## 🔄 控制器复用模式

### 1. 混入模式 (Mixin)

```python
# controllers/mixins.py
from typing import Optional
from backend.api_core.response import response


class SearchMixin:
    """搜索功能混入"""

    async def search_items(
            self,
            search_term: str,
            search_fields: list,
            page: int = 1,
            page_size: int = 20
    ):
        """通用搜索方法"""
        from tortoise.expressions import Q

        query = self.model.all()

        # 构建搜索条件
        search_conditions = Q()
        for field in search_fields:
            search_conditions |= Q(**{f"{field}__icontains": search_term})

        query = query.filter(search_conditions)

        total = await query.count()
        items = await query.offset((page - 1) * page_size).limit(page_size)

        return response.success_with_pagination(
            data=items,
            total=total,
            page=page,
            page_size=page_size,
            msg="搜索完成"
        )


class SoftDeleteMixin:
    """软删除功能混入"""

    async def soft_delete_item(self, item_id: int):
        """软删除项目"""
        item = await self.get(item_id)
        if not item:
            raise BusinessError(f"{self.model.__name__}不存在", code=404)

        item.is_deleted = True
        item.deleted_at = datetime.utcnow()
        await item.save()

        return response.success(msg=f"{self.model.__name__}删除成功")

    async def restore_item(self, item_id: int):
        """恢复删除的项目"""
        item = await self.model.get_or_none(id=item_id, is_deleted=True)
        if not item:
            raise BusinessError(f"{self.model.__name__}不存在或未删除", code=404)

        item.is_deleted = False
        item.deleted_at = None
        await item.save()

        return response.success(msg=f"{self.model.__name__}恢复成功")


class StatusMixin:
    """状态管理功能混入"""

    async def change_status(self, item_id: int, status: str):
        """更改项目状态"""
        item = await self.get(item_id)
        if not item:
            raise BusinessError(f"{self.model.__name__}不存在", code=404)

        if not hasattr(item, 'status'):
            raise BusinessError("该模型不支持状态管理")

        item.status = status
        await item.save()

        return response.success(
            data=item,
            msg=f"{self.model.__name__}状态更新成功"
        )
```

### 2. 使用混入的控制器

```python
# controllers/article_controller.py
from backend.models.article import Article
from backend.schemas.article import ArticleCreate, ArticleUpdate
from backend.controllers.base_controller import BaseController
from backend.controllers.mixins import SearchMixin, SoftDeleteMixin, StatusMixin

class ArticleController(
    BaseController[Article, ArticleCreate, ArticleUpdate],
    SearchMixin,
    SoftDeleteMixin,
    StatusMixin
):
    def __init__(self):
        super().__init__(Article)

    async def search_articles(self, search_term: str, page: int = 1, page_size: int = 20):
        """搜索文章"""
        return await self.search_items(
            search_term=search_term,
            search_fields=["title", "content", "summary"],
            page=page,
            page_size=page_size
        )

    async def publish_article(self, article_id: int):
        """发布文章"""
        return await self.change_status(article_id, "published")

    async def draft_article(self, article_id: int):
        """文章转为草稿"""
        return await self.change_status(article_id, "draft")

# 创建控制器实例
article_controller = ArticleController()
```

## 🎯 专用控制器模式

### 1. 认证控制器

```python
# controllers/auth_controller.py
from datetime import datetime, timedelta
from backend.models.user import User
from backend.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from backend.api_core.security import verify_password, create_access_token
from backend.api_core.response import response
from backend.api_core.exceptions import BusinessError


class AuthController:
    """认证控制器"""

    async def register(self, register_data: RegisterRequest):
        """用户注册"""
        # 检查用户名是否存在
        if await User.exists(username=register_data.username):
            raise BusinessError("用户名已存在", code=409)

        # 检查邮箱是否存在
        if await User.exists(email=register_data.email):
            raise BusinessError("邮箱已被注册", code=409)

        # 创建用户
        user = await User.create(
            username=register_data.username,
            email=register_data.email,
            hashed_password=get_password_hash(register_data.password),
            full_name=register_data.full_name
        )

        return response.success(
            data={"user_id": user.id, "username": user.username},
            msg="注册成功",
            code=201
        )

    async def login(self, login_data: LoginRequest):
        """用户登录"""
        # 验证用户
        user = await User.get_or_none(username=login_data.username)
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise BusinessError("用户名或密码错误", code=401)

        if not user.is_active:
            raise BusinessError("账户已被停用", code=403)

        # 生成token
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(hours=24)
        )

        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        await user.save()

        return response.success(
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name
                }
            },
            msg="登录成功"
        )

    async def refresh_token(self, current_user: User):
        """刷新token"""
        access_token = create_access_token(
            data={"sub": current_user.username},
            expires_delta=timedelta(hours=24)
        )

        return response.success(
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 86400
            },
            msg="Token刷新成功"
        )


# 创建控制器实例
auth_controller = AuthController()
```

### 2. 文件上传控制器

```python
# controllers/upload_controller.py
import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from backend.api_core.response import response
from backend.api_core.exceptions import BusinessError
from backend.models.file import FileRecord


class UploadController:
    """文件上传控制器"""

    def __init__(self):
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        self.allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"}
        self.max_file_size = 10 * 1024 * 1024  # 10MB

    async def upload_file(self, file: UploadFile, user_id: int):
        """上传文件"""
        # 验证文件
        self._validate_file(file)

        # 生成文件名
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = self.upload_dir / unique_filename

        # 保存文件
        try:
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
        except Exception as e:
            raise BusinessError(f"文件保存失败: {str(e)}")

        # 记录到数据库
        file_record = await FileRecord.create(
            original_name=file.filename,
            stored_name=unique_filename,
            file_path=str(file_path),
            file_size=len(content),
            content_type=file.content_type,
            uploaded_by_id=user_id
        )

        return response.success(
            data={
                "file_id": file_record.id,
                "filename": file.filename,
                "file_size": len(content),
                "file_url": f"/files/{unique_filename}"
            },
            msg="文件上传成功"
        )

    async def delete_file(self, file_id: int, user_id: int):
        """删除文件"""
        file_record = await FileRecord.get_or_none(id=file_id, uploaded_by_id=user_id)
        if not file_record:
            raise BusinessError("文件不存在或无权限删除", code=404)

        # 删除物理文件
        file_path = Path(file_record.file_path)
        if file_path.exists():
            file_path.unlink()

        # 删除数据库记录
        await file_record.delete()

        return response.success(msg="文件删除成功")

    def _validate_file(self, file: UploadFile):
        """验证文件"""
        if not file.filename:
            raise BusinessError("文件名不能为空", code=400)

        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.allowed_extensions:
            raise BusinessError(f"不支持的文件类型: {file_extension}", code=400)

        if file.size and file.size > self.max_file_size:
            raise BusinessError("文件大小超过限制", code=400)


# 创建控制器实例
upload_controller = UploadController()
```

## 📊 控制器最佳实践

### 1. 错误处理

```python
class BaseController:
    async def safe_execute(self, operation, *args, **kwargs):
        """安全执行操作"""
        try:
            return await operation(*args, **kwargs)
        except BusinessError:
            # 业务异常直接抛出
            raise
        except Exception as e:
            # 其他异常转换为业务异常
            logger.error(f"控制器操作失败: {e}")
            raise BusinessError("操作失败，请稍后重试")
```

### 2. 日志记录

```python
from loguru import logger

class BaseController:
    def __init__(self, model):
        super().__init__(model)
        self.logger = logger.bind(controller=self.__class__.__name__)

    async def create_item(self, obj_in):
        self.logger.info(f"创建{self.model.__name__}: {obj_in}")
        result = await super().create_item(obj_in)
        self.logger.success(f"{self.model.__name__}创建成功")
        return result
```

### 3. 缓存支持

```python
from backend.api_core.cache import cache


class BaseController:
    async def get_item_cached(self, item_id: int):
        """获取项目（带缓存）"""
        cache_key = f"{self.model.__name__}:{item_id}"

        # 尝试从缓存获取
        cached_item = await cache.get(cache_key)
        if cached_item:
            return response.success(data=cached_item)

        # 从数据库获取
        item = await self.get(item_id)
        if not item:
            raise BusinessError(f"{self.model.__name__}不存在", code=404)

        # 缓存结果
        await cache.set(cache_key, item, expire=300)  # 5分钟过期

        return response.success(data=item)
```
