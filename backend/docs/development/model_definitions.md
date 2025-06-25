# 模型定义规范

## 🗄️ 模型设计原则

### 基础原则

1. **继承基类** - 所有模型都继承自 `BaseModel`
2. **字段约束** - 合理设置字段约束和验证
3. **关系映射** - 正确定义模型间的关系
4. **索引优化** - 为常用查询字段添加索引
5. **软删除** - 重要数据使用软删除机制

## 🏗️ 基础模型结构

### 1. 基础模型类

```python
# models/base.py
from tortoise.models import Model
from tortoise import fields
from datetime import datetime
from typing import Optional

class BaseModel(Model):
    """基础模型类，所有模型都应继承此类"""

    id = fields.IntField(pk=True, description="主键ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.id})"

    @classmethod
    def get_table_name(cls):
        """获取表名"""
        return cls._meta.db_table or cls.__name__.lower()

class SoftDeleteModel(BaseModel):
    """支持软删除的基础模型"""

    is_deleted = fields.BooleanField(default=False, description="是否删除")
    deleted_at = fields.DatetimeField(null=True, description="删除时间")

    class Meta:
        abstract = True

    async def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        await self.save()

    async def restore(self):
        """恢复删除"""
        self.is_deleted = False
        self.deleted_at = None
        await self.save()
```

### 2. 用户模型示例

```python
# models/user.py
from tortoise import fields
from backend.models.base import SoftDeleteModel

class User(SoftDeleteModel):
    """用户模型"""

    # 基础字段
    username = fields.CharField(
        max_length=50,
        unique=True,
        description="用户名",
        index=True
    )
    email = fields.CharField(
        max_length=255,
        unique=True,
        description="邮箱",
        index=True
    )
    hashed_password = fields.CharField(max_length=255, description="密码哈希")

    # 个人信息
    full_name = fields.CharField(max_length=100, null=True, description="全名")
    avatar = fields.CharField(max_length=500, null=True, description="头像URL")
    phone = fields.CharField(max_length=20, null=True, description="手机号")

    # 状态字段
    is_active = fields.BooleanField(default=True, description="是否激活")
    is_superuser = fields.BooleanField(default=False, description="是否超级用户")
    is_staff = fields.BooleanField(default=False, description="是否员工")

    # 时间字段
    last_login = fields.DatetimeField(null=True, description="最后登录时间")
    email_verified_at = fields.DatetimeField(null=True, description="邮箱验证时间")

    # 关系字段
    roles = fields.ManyToManyField(
        "models.Role",
        related_name="users",
        through="user_roles",
        description="用户角色"
    )

    class Meta:
        table = "users"
        table_description = "用户表"
        indexes = [
            ["username", "email"],  # 复合索引
            ["is_active", "is_deleted"],  # 状态索引
        ]

    def __str__(self):
        return f"User(username={self.username})"

    @property
    def is_verified(self) -> bool:
        """是否已验证邮箱"""
        return self.email_verified_at is not None

    async def get_permissions(self):
        """获取用户权限"""
        permissions = set()
        roles = await self.roles.all().prefetch_related("permissions")
        for role in roles:
            role_permissions = await role.permissions.all()
            permissions.update(perm.code for perm in role_permissions)
        return list(permissions)
```

## 🔗 关系映射

### 1. 一对一关系

```python
# models/user_profile.py
from tortoise import fields
from backend.models.base import BaseModel

class UserProfile(BaseModel):
    """用户详细信息"""

    user = fields.OneToOneField(
        "models.User",
        related_name="profile",
        on_delete=fields.CASCADE,
        description="关联用户"
    )

    bio = fields.TextField(null=True, description="个人简介")
    website = fields.CharField(max_length=200, null=True, description="个人网站")
    location = fields.CharField(max_length=100, null=True, description="所在地")
    birth_date = fields.DateField(null=True, description="出生日期")

    # JSON字段存储扩展信息
    extra_data = fields.JSONField(default=dict, description="扩展数据")

    class Meta:
        table = "user_profiles"
        table_description = "用户详细信息表"
```

### 2. 一对多关系

```python
# models/article.py
from tortoise import fields
from backend.models.base import SoftDeleteModel

class Category(BaseModel):
    """文章分类"""

    name = fields.CharField(max_length=100, unique=True, description="分类名称")
    slug = fields.CharField(max_length=100, unique=True, description="URL别名")
    description = fields.TextField(null=True, description="分类描述")
    parent = fields.ForeignKeyField(
        "models.Category",
        related_name="children",
        null=True,
        on_delete=fields.CASCADE,
        description="父分类"
    )

    class Meta:
        table = "categories"
        table_description = "文章分类表"

class Article(SoftDeleteModel):
    """文章模型"""

    title = fields.CharField(max_length=200, description="标题", index=True)
    slug = fields.CharField(max_length=200, unique=True, description="URL别名")
    content = fields.TextField(description="内容")
    summary = fields.CharField(max_length=500, null=True, description="摘要")

    # 状态字段
    status = fields.CharEnumField(
        enum_type=ArticleStatus,
        default=ArticleStatus.DRAFT,
        description="状态"
    )
    is_featured = fields.BooleanField(default=False, description="是否推荐")
    view_count = fields.IntField(default=0, description="浏览次数")

    # 关系字段
    author = fields.ForeignKeyField(
        "models.User",
        related_name="articles",
        on_delete=fields.CASCADE,
        description="作者"
    )
    category = fields.ForeignKeyField(
        "models.Category",
        related_name="articles",
        on_delete=fields.SET_NULL,
        null=True,
        description="分类"
    )

    # 时间字段
    published_at = fields.DatetimeField(null=True, description="发布时间")

    class Meta:
        table = "articles"
        table_description = "文章表"
        indexes = [
            ["status", "is_deleted"],
            ["author_id", "status"],
            ["category_id", "status"],
            ["published_at"],
        ]

    async def publish(self):
        """发布文章"""
        self.status = ArticleStatus.PUBLISHED
        self.published_at = datetime.utcnow()
        await self.save()

    async def increment_view_count(self):
        """增加浏览次数"""
        self.view_count += 1
        await self.save(update_fields=["view_count"])
```

### 3. 多对多关系

```python
# models/tag.py
from tortoise import fields
from backend.models.base import BaseModel

class Tag(BaseModel):
    """标签模型"""

    name = fields.CharField(max_length=50, unique=True, description="标签名称")
    slug = fields.CharField(max_length=50, unique=True, description="URL别名")
    color = fields.CharField(max_length=7, default="#007bff", description="标签颜色")

    # 多对多关系
    articles = fields.ManyToManyField(
        "models.Article",
        related_name="tags",
        through="article_tags",
        description="关联文章"
    )

    class Meta:
        table = "tags"
        table_description = "标签表"

# 中间表模型（可选，用于添加额外字段）
class ArticleTag(BaseModel):
    """文章标签关联表"""

    article = fields.ForeignKeyField("models.Article", on_delete=fields.CASCADE)
    tag = fields.ForeignKeyField("models.Tag", on_delete=fields.CASCADE)

    # 额外字段
    weight = fields.IntField(default=1, description="权重")
    added_by = fields.ForeignKeyField(
        "models.User",
        on_delete=fields.SET_NULL,
        null=True,
        description="添加者"
    )

    class Meta:
        table = "article_tags"
        table_description = "文章标签关联表"
        unique_together = [["article", "tag"]]
```

## 📊 字段类型和约束

### 1. 常用字段类型

```python
from tortoise import fields
from enum import Enum

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class ExampleModel(BaseModel):
    """字段类型示例"""

    # 字符串字段
    name = fields.CharField(max_length=100, description="名称")
    slug = fields.CharField(max_length=100, unique=True, description="别名")
    description = fields.TextField(null=True, description="描述")

    # 数字字段
    price = fields.DecimalField(max_digits=10, decimal_places=2, description="价格")
    quantity = fields.IntField(default=0, description="数量")
    rating = fields.FloatField(null=True, description="评分")

    # 布尔字段
    is_active = fields.BooleanField(default=True, description="是否激活")
    is_featured = fields.BooleanField(default=False, description="是否推荐")

    # 时间字段
    start_date = fields.DateField(description="开始日期")
    end_time = fields.DatetimeField(null=True, description="结束时间")

    # 枚举字段
    status = fields.CharEnumField(
        enum_type=UserStatus,
        default=UserStatus.ACTIVE,
        description="状态"
    )

    # JSON字段
    metadata = fields.JSONField(default=dict, description="元数据")
    settings = fields.JSONField(default=list, description="设置")

    # 二进制字段
    file_data = fields.BinaryField(null=True, description="文件数据")

    class Meta:
        table = "examples"
```

### 2. 字段约束和验证

```python
from tortoise import fields
from tortoise.validators import MinLengthValidator, MaxLengthValidator

class ValidatedModel(BaseModel):
    """带验证的模型"""

    # 长度约束
    username = fields.CharField(
        max_length=50,
        validators=[MinLengthValidator(3), MaxLengthValidator(50)],
        description="用户名"
    )

    # 数值约束
    age = fields.IntField(
        validators=[lambda x: x >= 0 and x <= 150],
        description="年龄"
    )

    # 邮箱验证
    email = fields.CharField(
        max_length=255,
        validators=[EmailValidator()],
        description="邮箱"
    )

    # 自定义验证器
    @classmethod
    def validate_phone(cls, phone: str):
        """手机号验证"""
        import re
        if not re.match(r'^1[3-9]\d{9}$', phone):
            raise ValueError("手机号格式不正确")
        return phone

    phone = fields.CharField(
        max_length=11,
        validators=[validate_phone],
        description="手机号"
    )
```

## 🔍 索引和性能优化

### 1. 索引设置

```python
class OptimizedModel(BaseModel):
    """优化的模型"""

    name = fields.CharField(max_length=100, index=True, description="名称")
    email = fields.CharField(max_length=255, unique=True, description="邮箱")
    status = fields.CharField(max_length=20, description="状态")
    category_id = fields.IntField(description="分类ID")
    created_date = fields.DateField(description="创建日期")

    class Meta:
        table = "optimized_models"
        indexes = [
            # 单字段索引
            ["status"],
            ["created_date"],

            # 复合索引
            ["status", "category_id"],
            ["category_id", "created_date"],

            # 部分索引（PostgreSQL）
            # fields.Index(fields=["email"], condition=Q(is_active=True))
        ]

        # 唯一约束
        unique_together = [
            ["name", "category_id"],
        ]
```

### 2. 查询优化

```python
class ArticleModel(BaseModel):
    """文章模型 - 查询优化示例"""

    @classmethod
    async def get_published_articles(cls, limit: int = 10):
        """获取已发布文章（优化查询）"""
        return await cls.filter(
            status="published",
            is_deleted=False
        ).select_related(
            "author", "category"
        ).prefetch_related(
            "tags"
        ).order_by("-published_at").limit(limit)

    @classmethod
    async def get_articles_by_author(cls, author_id: int):
        """获取作者文章（使用索引）"""
        return await cls.filter(
            author_id=author_id,
            is_deleted=False
        ).order_by("-created_at")

    @classmethod
    async def search_articles(cls, keyword: str):
        """搜索文章（全文搜索）"""
        from tortoise.expressions import Q

        return await cls.filter(
            Q(title__icontains=keyword) | Q(content__icontains=keyword),
            status="published",
            is_deleted=False
        ).select_related("author")
```

## 🛠️ 模型方法和属性

### 1. 实例方法

```python
class UserModel(BaseModel):
    """用户模型 - 方法示例"""

    username = fields.CharField(max_length=50)
    email = fields.CharField(max_length=255)
    hashed_password = fields.CharField(max_length=255)
    is_active = fields.BooleanField(default=True)

    def check_password(self, password: str) -> bool:
        """验证密码"""
        from backend.api_core.security import verify_password
        return verify_password(password, self.hashed_password)

    def set_password(self, password: str):
        """设置密码"""
        from backend.api_core.security import get_password_hash
        self.hashed_password = get_password_hash(password)

    async def activate(self):
        """激活用户"""
        self.is_active = True
        await self.save(update_fields=["is_active"])

    async def deactivate(self):
        """停用用户"""
        self.is_active = False
        await self.save(update_fields=["is_active"])

    @property
    def display_name(self) -> str:
        """显示名称"""
        return self.full_name or self.username
```

### 2. 类方法

```python
class UserModel(BaseModel):
    """用户模型 - 类方法示例"""

    @classmethod
    async def create_user(cls, username: str, email: str, password: str, **kwargs):
        """创建用户"""
        from backend.api_core.security import get_password_hash

        user = await cls.create(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            **kwargs
        )
        return user

    @classmethod
    async def get_by_username(cls, username: str):
        """根据用户名获取用户"""
        return await cls.get_or_none(username=username, is_deleted=False)

    @classmethod
    async def get_active_users(cls):
        """获取活跃用户"""
        return await cls.filter(is_active=True, is_deleted=False).all()

    @classmethod
    async def count_by_status(cls, status: str):
        """按状态统计用户数"""
        return await cls.filter(status=status, is_deleted=False).count()
```

## 📝 模型最佳实践

### 1. 命名规范

- **模型名**: 使用单数形式，PascalCase
- **字段名**: 使用snake_case
- **表名**: 使用复数形式，snake_case
- **关系名**: 使用有意义的名称

### 2. 字段设计

- **必填字段**: 合理设置null=False
- **默认值**: 为字段设置合适的默认值
- **长度限制**: 根据业务需求设置合理的长度
- **索引**: 为常用查询字段添加索引

### 3. 关系设计

- **外键**: 合理设置on_delete行为
- **反向关系**: 使用有意义的related_name
- **多对多**: 考虑是否需要中间表存储额外信息

### 4. 性能考虑

- **查询优化**: 使用select_related和prefetch_related
- **索引策略**: 根据查询模式设计索引
- **分页**: 大数据量查询使用分页
- **缓存**: 对频繁查询的数据使用缓存
