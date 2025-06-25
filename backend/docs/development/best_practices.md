# 后端开发最佳实践

## 🎯 总体原则

### 1. 代码质量
- **可读性优先** - 代码应该易于理解和维护
- **一致性** - 遵循统一的编码规范和架构模式
- **简洁性** - 避免过度设计，保持代码简洁
- **可测试性** - 编写易于测试的代码

### 2. 架构设计
- **分层架构** - 明确的API、控制器、服务、模型分层
- **单一职责** - 每个模块只负责一个功能
- **依赖注入** - 使用依赖注入提高代码的可测试性
- **接口隔离** - 定义清晰的接口边界

## 🏗️ 架构最佳实践

### 1. 目录结构规范

```
backend/
├── api/                    # API路由层
│   └── v1/                # 版本控制
├── controllers/           # 控制器层
├── services/             # 服务层
├── models/               # 数据模型层
├── schemas/              # 数据验证层
├── core/                 # 核心工具
│   ├── crud.py          # CRUD基类
│   ├── response.py      # 响应处理
│   ├── exceptions.py    # 异常定义
│   └── deps.py          # 依赖注入
├── utils/               # 工具函数
└── tests/               # 测试代码
```

### 2. 分层职责

```python
# API层 - 只处理HTTP请求响应
@router.post("/users")
async def create_user(user_data: UserCreate):
    return await user_controller.create_user(user_data)

# 控制器层 - 业务逻辑控制
class UserController:
    async def create_user(self, user_data: UserCreate):
        # 业务验证
        # 调用服务层
        # 返回响应

# 服务层 - 具体业务实现
class UserService:
    async def create_user(self, user_data: UserCreate):
        # 具体业务逻辑
        # 数据库操作
        # 外部服务调用

# 模型层 - 数据定义
class User(BaseModel):
    username = fields.CharField(max_length=50)
    # 其他字段定义
```

## 📝 编码规范

### 1. 命名规范

```python
# 类名 - PascalCase
class UserController:
    pass

# 函数名 - snake_case
async def create_user():
    pass

# 变量名 - snake_case
user_data = UserCreate()

# 常量 - UPPER_SNAKE_CASE
MAX_PAGE_SIZE = 100

# 私有方法 - 下划线开头
def _validate_user_data(self):
    pass
```

### 2. 类型注解

```python
# 完整的类型注解
async def create_user(
    user_data: UserCreate,
    current_user: Optional[User] = None
) -> UserResponse:
    pass

# 复杂类型注解
from typing import List, Dict, Optional, Union

async def batch_process(
    items: List[Dict[str, Any]],
    options: Optional[Dict[str, Union[str, int]]] = None
) -> List[ProcessResult]:
    pass
```

### 3. 文档字符串

```python
async def create_user(user_data: UserCreate) -> UserResponse:
    """
    创建新用户

    Args:
        user_data: 用户创建数据

    Returns:
        UserResponse: 创建的用户信息

    Raises:
        BusinessError: 当用户名或邮箱已存在时
        ValidationError: 当数据验证失败时

    Example:
        >>> user_data = UserCreate(username="john", email="john@example.com")
        >>> result = await create_user(user_data)
        >>> print(result.username)
        john
    """
    pass
```

## 🔧 开发模式

### 1. CRUD操作模式

```python
# 使用基类简化CRUD操作
class UserController(CRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(User)

    # 继承基础CRUD方法
    # 添加业务特定方法
    async def get_active_users(self):
        return await self.model.filter(is_active=True).all()
```

### 2. 响应处理模式

```python
# 统一响应格式
from backend.api_core.response import response

# 成功响应
return response.success(data=user, msg="用户创建成功")

# 分页响应
return response.success_with_pagination(
    data=users, total=100, page=1, page_size=20
)

# 错误通过异常处理
raise BusinessError("用户不存在", code=404)
```

### 3. 依赖注入模式

```python
# 权限检查
@router.post("/admin/users")
async def create_admin_user(
    user_data: UserCreate,
    current_user = Depends(get_current_user),
    _: None = Depends(require_permissions(["user:create"]))
):
    pass

# 数据库会话
@router.get("/users")
async def get_users(db: Session = Depends(get_db)):
    pass
```

## 🚨 错误处理

### 1. 异常层次设计

```python
# 基础异常
class BusinessError(Exception):
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code
        super().__init__(message)

# 具体异常
class UserNotFoundError(BusinessError):
    def __init__(self, user_id: int):
        super().__init__(f"用户不存在: {user_id}", 404)

class DuplicateUserError(BusinessError):
    def __init__(self, field: str, value: str):
        super().__init__(f"{field}已存在: {value}", 409)
```

### 2. 全局异常处理

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(BusinessError)
async def business_error_handler(request: Request, exc: BusinessError):
    return JSONResponse(
        status_code=exc.code,
        content={
            "code": exc.code,
            "msg": exc.message,
            "data": None
        }
    )
```

### 3. 错误日志记录

```python
from loguru import logger

async def create_user(user_data: UserCreate):
    try:
        # 业务逻辑
        user = await User.create(**user_data.dict())
        logger.info(f"用户创建成功: {user.username}")
        return user
    except Exception as e:
        logger.error(f"用户创建失败: {e}")
        raise BusinessError("用户创建失败")
```

## 📊 性能优化

### 1. 数据库查询优化

```python
# 使用select_related减少查询次数
users = await User.all().select_related("profile", "roles")

# 使用prefetch_related处理多对多关系
articles = await Article.all().prefetch_related("tags", "comments")

# 只查询需要的字段
users = await User.all().values("id", "username", "email")

# 使用索引优化查询
class User(BaseModel):
    username = fields.CharField(max_length=50, index=True)
    email = fields.CharField(max_length=255, index=True)

    class Meta:
        indexes = [
            ["username", "email"],  # 复合索引
            ["is_active", "created_at"],
        ]
```

### 2. 缓存策略

```python
from backend.api_core.cache import cache


async def get_user_cached(user_id: int):
    # 尝试从缓存获取
    cache_key = f"user:{user_id}"
    user = await cache.get(cache_key)

    if user is None:
        # 从数据库获取
        user = await User.get(id=user_id)
        # 缓存结果
        await cache.set(cache_key, user, expire=300)

    return user
```

### 3. 分页优化

```python
async def get_users_paginated(page: int, page_size: int):
    # 限制页面大小
    page_size = min(page_size, 100)

    # 计算偏移量
    offset = (page - 1) * page_size

    # 并行查询数据和总数
    users_task = User.all().offset(offset).limit(page_size)
    count_task = User.all().count()

    users, total = await asyncio.gather(users_task, count_task)

    return users, total
```

## 🔒 安全最佳实践

### 1. 输入验证

```python
from pydantic import validator

class UserCreate(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50)

    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v
```

### 2. 权限控制

```python
# 基于角色的权限控制
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user = Depends(get_current_user),
    _: None = Depends(require_roles(["admin"]))
):
    pass

# 基于资源的权限控制
@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user = Depends(get_current_user)
):
    # 只能修改自己的信息或管理员可以修改任何人
    if user_id != current_user.id and not current_user.is_admin:
        raise BusinessError("无权限修改其他用户信息", 403)
```

### 3. 敏感数据处理

```python
class UserResponse(BaseSchema):
    id: int
    username: str
    email: str

    class Config:
        # 排除敏感字段
        fields = {
            'password': {'write_only': True},
            'hashed_password': {'write_only': True}
        }

# 日志中避免记录敏感信息
logger.info(f"用户登录: {user.username}")  # ✅
logger.info(f"用户登录: {user.password}")  # ❌
```

## 🧪 测试最佳实践

### 1. 单元测试

```python
import pytest
from backend.controllers.user_controller import UserController

class TestUserController:
    @pytest.mark.asyncio
    async def test_create_user_success(self):
        controller = UserController()
        user_data = UserCreate(
            username="test_user",
            email="test@example.com"
        )

        result = await controller.create_user(user_data)

        assert result["code"] == 201
        assert result["data"]["username"] == "test_user"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self):
        controller = UserController()
        # 先创建一个用户
        # 然后测试重复用户名的情况
        with pytest.raises(BusinessError) as exc_info:
            await controller.create_user(duplicate_user_data)

        assert exc_info.value.code == 409
```

### 2. 集成测试

```python
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_create_user_api():
    response = client.post("/api/v1/users", json={
        "username": "test_user",
        "email": "test@example.com",
        "password": "password123"
    })

    assert response.status_code == 201
    assert response.json()["data"]["username"] == "test_user"
```

### 3. 测试数据管理

```python
@pytest.fixture
async def test_user():
    """创建测试用户"""
    user = await User.create(
        username="test_user",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    yield user
    # 清理
    await user.delete()

@pytest.fixture
async def authenticated_client(test_user):
    """认证的测试客户端"""
    token = create_access_token({"sub": test_user.username})
    client.headers.update({"Authorization": f"Bearer {token}"})
    yield client
    # 清理
    client.headers.pop("Authorization", None)
```

## 📝 文档规范

### 1. API文档

```python
@router.post(
    "/users",
    response_model=UserResponse,
    summary="创建用户",
    description="创建新的用户账户",
    responses={
        201: {"description": "用户创建成功"},
        400: {"description": "请求参数错误"},
        409: {"description": "用户名或邮箱已存在"}
    }
)
async def create_user(user_data: UserCreate):
    pass
```

### 2. 代码注释

```python
class UserController:
    def __init__(self):
        # 初始化CRUD基类
        super().__init__(User)
        # 设置缓存过期时间
        self.cache_expire = 300

    async def create_user(self, user_data: UserCreate):
        # 1. 验证用户名唯一性
        if await self._check_username_exists(user_data.username):
            raise DuplicateUserError("username", user_data.username)

        # 2. 创建用户
        user = await self.create(user_data)

        # 3. 清除相关缓存
        await self._clear_user_cache()

        return user
```

## 🔄 部署和运维

### 1. 环境配置

```python
# 使用环境变量管理配置
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    secret_key: str
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

### 2. 健康检查

```python
@router.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 检查数据库连接
        await User.all().limit(1)

        # 检查Redis连接
        await cache.ping()

        return {"status": "healthy", "timestamp": datetime.utcnow()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### 3. 监控和日志

```python
from loguru import logger
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # 记录请求
    logger.info(f"请求开始: {request.method} {request.url}")

    response = await call_next(request)

    # 记录响应
    process_time = time.time() - start_time
    logger.info(
        f"请求完成: {request.method} {request.url} "
        f"状态码: {response.status_code} 耗时: {process_time:.3f}s"
    )

    return response
```
