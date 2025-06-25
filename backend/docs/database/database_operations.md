# 数据库操作指南

## 🗄️ 数据库架构

### ORM框架
系统使用 **Tortoise ORM** 作为数据库操作框架，提供异步数据库操作能力。

### 数据库支持
- **PostgreSQL** (推荐生产环境)
- **MySQL** (支持)
- **SQLite** (开发环境)

## 🏗️ 模型定义

### 1. 基础模型继承

```python
# models/base.py
from tortoise.models import Model
from tortoise import fields
from datetime import datetime

class BaseModel(Model):
    """所有模型的基类"""

    id = fields.IntField(pk=True, description="主键ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        abstract = True
        ordering = ["-created_at"]

class SoftDeleteModel(BaseModel):
    """支持软删除的模型基类"""

    is_deleted = fields.BooleanField(default=False, description="是否删除")
    deleted_at = fields.DatetimeField(null=True, description="删除时间")

    class Meta:
        abstract = True

    async def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        await self.save()
```

### 2. 具体模型示例

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

    # 状态字段
    is_active = fields.BooleanField(default=True, description="是否激活")
    is_superuser = fields.BooleanField(default=False, description="是否超级用户")

    # 时间字段
    last_login = fields.DatetimeField(null=True, description="最后登录时间")

    class Meta:
        table = "users"
        table_description = "用户表"
        # 复合索引
        indexes = [
            ["username", "email"],
            ["is_active", "is_deleted"],
        ]

    def __str__(self):
        return f"User(username={self.username})"
```

## 🔧 CRUD基类使用

### 1. CRUDBase类

```python
# api_core/crud.py
from typing import TypeVar, Generic, Type, List, Optional, Dict, Any
from tortoise.models import Model
from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, id: Any) -> Optional[ModelType]:
        """根据ID获取单个对象"""
        return await self.model.get_or_none(id=id)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """获取多个对象"""
        return await self.model.all().offset(skip).limit(limit)

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """创建对象"""
        obj_data = obj_in.dict()
        return await self.model.create(**obj_data)

    async def update(
        self,
        db_obj: ModelType,
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """更新对象"""
        obj_data = obj_in.dict(exclude_unset=True)
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        await db_obj.save()
        return db_obj

    async def delete(self, id: Any) -> None:
        """删除对象"""
        obj = await self.get(id)
        if obj:
            await obj.delete()
```

### 2. 控制器中使用CRUD

```python
# controllers/user_controller.py
from backend.api_core.crud import CRUDBase
from backend.models.user import User
from backend.schemas.user import UserCreate, UserUpdate


class UserController(CRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(User)

    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return await self.model.get_or_none(username=username)

    async def get_active_users(self) -> List[User]:
        """获取活跃用户"""
        return await self.model.filter(is_active=True, is_deleted=False).all()
```

## 📊 查询操作

### 1. 基础查询

```python
# 获取所有用户
users = await User.all()

# 根据条件过滤
active_users = await User.filter(is_active=True).all()

# 获取单个对象
user = await User.get(id=1)
user = await User.get_or_none(username="john")

# 检查是否存在
exists = await User.exists(email="john@example.com")

# 计数
count = await User.all().count()
active_count = await User.filter(is_active=True).count()
```

### 2. 复杂查询

```python
from tortoise.expressions import Q

# OR查询
users = await User.filter(
    Q(username__icontains="john") | Q(email__icontains="john")
).all()

# AND查询
users = await User.filter(
    Q(is_active=True) & Q(is_deleted=False)
).all()

# NOT查询
users = await User.filter(~Q(is_superuser=True)).all()

# 范围查询
from datetime import datetime, timedelta
recent_users = await User.filter(
    created_at__gte=datetime.now() - timedelta(days=7)
).all()

# 排序
users = await User.all().order_by("-created_at", "username")

# 分页
users = await User.all().offset(20).limit(10)
```

### 3. 关联查询

```python
# 一对多关系 - 预加载
articles = await Article.all().select_related("author").all()

# 多对多关系 - 预加载
articles = await Article.all().prefetch_related("tags").all()

# 反向关联
user = await User.get(id=1).prefetch_related("articles")
user_articles = user.articles

# 关联过滤
articles = await Article.filter(author__username="john").all()
users = await User.filter(articles__title__icontains="python").all()
```

### 4. 聚合查询

```python
from tortoise.functions import Count, Sum, Avg, Max, Min

# 计数
user_stats = await User.annotate(
    article_count=Count("articles")
).values("id", "username", "article_count")

# 求和
article_stats = await Article.annotate(
    total_views=Sum("view_count")
).values("author_id", "total_views")

# 平均值
avg_views = await Article.all().annotate(
    avg_views=Avg("view_count")
).values("avg_views")

# 分组统计
daily_stats = await User.annotate(
    count=Count("id")
).group_by("created_at__date").values("created_at__date", "count")
```

## ✏️ 数据操作

### 1. 创建操作

```python
# 单个创建
user = await User.create(
    username="john",
    email="john@example.com",
    hashed_password="hashed_password"
)

# 批量创建
users_data = [
    {"username": "user1", "email": "user1@example.com"},
    {"username": "user2", "email": "user2@example.com"},
]
users = await User.bulk_create([User(**data) for data in users_data])

# 获取或创建
user, created = await User.get_or_create(
    username="john",
    defaults={"email": "john@example.com"}
)
```

### 2. 更新操作

```python
# 单个更新
user = await User.get(id=1)
user.email = "new_email@example.com"
await user.save()

# 部分字段更新
await user.save(update_fields=["email", "updated_at"])

# 批量更新
await User.filter(is_active=False).update(is_deleted=True)

# 条件更新
await User.filter(
    last_login__lt=datetime.now() - timedelta(days=30)
).update(is_active=False)
```

### 3. 删除操作

```python
# 单个删除
user = await User.get(id=1)
await user.delete()

# 批量删除
await User.filter(is_deleted=True).delete()

# 软删除
user = await User.get(id=1)
await user.soft_delete()

# 批量软删除
await User.filter(is_active=False).update(
    is_deleted=True,
    deleted_at=datetime.utcnow()
)
```

## 🔄 事务处理

### 1. 基础事务

```python
from tortoise.transactions import in_transaction

async def transfer_operation():
    async with in_transaction() as connection:
        # 在事务中执行多个操作
        user1 = await User.get(id=1).using_db(connection)
        user2 = await User.get(id=2).using_db(connection)

        # 更新操作
        user1.balance -= 100
        user2.balance += 100

        await user1.save(using_db=connection)
        await user2.save(using_db=connection)
```

### 2. 装饰器事务

```python
from tortoise.transactions import atomic

@atomic()
async def create_user_with_profile(user_data, profile_data):
    # 创建用户
    user = await User.create(**user_data)

    # 创建用户资料
    profile_data["user_id"] = user.id
    profile = await UserProfile.create(**profile_data)

    return user, profile
```

### 3. 手动事务控制

```python
from tortoise.transactions import get_connection

async def complex_operation():
    connection = get_connection("default")

    try:
        await connection.execute_query("BEGIN")

        # 执行多个操作
        user = await User.create(username="test")
        await Article.create(title="Test", author=user)

        await connection.execute_query("COMMIT")
    except Exception:
        await connection.execute_query("ROLLBACK")
        raise
```

## 🚀 性能优化

### 1. 查询优化

```python
# 使用select_related减少查询次数
articles = await Article.all().select_related("author", "category")

# 使用prefetch_related处理多对多关系
articles = await Article.all().prefetch_related("tags")

# 只查询需要的字段
users = await User.all().values("id", "username", "email")

# 使用values_list获取元组
usernames = await User.all().values_list("username", flat=True)
```

### 2. 索引优化

```python
class User(BaseModel):
    username = fields.CharField(max_length=50, index=True)
    email = fields.CharField(max_length=255, index=True)

    class Meta:
        table = "users"
        indexes = [
            # 单字段索引
            ["created_at"],
            ["is_active"],

            # 复合索引
            ["username", "email"],
            ["is_active", "is_deleted"],

            # 部分索引（PostgreSQL）
            # Index(fields=["email"], condition=Q(is_active=True))
        ]
```

### 3. 批量操作

```python
# 批量创建
users = [User(username=f"user{i}") for i in range(1000)]
await User.bulk_create(users, batch_size=100)

# 批量更新
await User.bulk_update(
    users,
    fields=["email", "updated_at"],
    batch_size=100
)

# 使用原生SQL进行大批量操作
from tortoise import connections

async def bulk_update_sql():
    connection = connections.get("default")
    await connection.execute_query(
        "UPDATE users SET is_active = false WHERE last_login < %s",
        [datetime.now() - timedelta(days=90)]
    )
```

## 🔍 原生SQL

### 1. 执行原生查询

```python
from tortoise import connections

async def execute_raw_sql():
    connection = connections.get("default")

    # 查询
    results = await connection.execute_query(
        "SELECT * FROM users WHERE created_at > %s",
        [datetime.now() - timedelta(days=7)]
    )

    # 更新
    await connection.execute_query(
        "UPDATE users SET last_login = %s WHERE id = %s",
        [datetime.now(), user_id]
    )
```

### 2. 使用raw方法

```python
# 原生查询返回模型实例
users = await User.raw(
    "SELECT * FROM users WHERE username LIKE %s",
    ["john%"]
)

# 原生查询返回字典
results = await User.raw(
    "SELECT username, COUNT(*) as article_count "
    "FROM users u JOIN articles a ON u.id = a.author_id "
    "GROUP BY u.username"
).values()
```

## 📝 最佳实践

### 1. 模型设计

```python
# 合理的字段约束
class User(BaseModel):
    username = fields.CharField(
        max_length=50,
        unique=True,
        index=True,
        description="用户名"
    )

    # 使用枚举
    status = fields.CharEnumField(
        enum_type=UserStatus,
        default=UserStatus.ACTIVE
    )

    # JSON字段存储灵活数据
    preferences = fields.JSONField(default=dict)
```

### 2. 查询优化

```python
# 避免N+1查询
# 错误方式
articles = await Article.all()
for article in articles:
    author = await article.author  # N+1查询

# 正确方式
articles = await Article.all().select_related("author")
for article in articles:
    author = article.author  # 已预加载
```

### 3. 错误处理

```python
from tortoise.exceptions import DoesNotExist, IntegrityError

async def get_user_safe(user_id: int):
    try:
        return await User.get(id=user_id)
    except DoesNotExist:
        raise BusinessError("用户不存在", 404)
    except IntegrityError as e:
        raise BusinessError(f"数据完整性错误: {e}", 400)
```

### 4. 连接管理

```python
# 数据库配置
TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": "localhost",
                "port": "5432",
                "user": "username",
                "password": "password",
                "database": "database_name",
                "minsize": 1,
                "maxsize": 10,
            }
        }
    },
    "apps": {
        "models": {
            "models": ["backend.models"],
            "default_connection": "default",
        }
    }
}
```
