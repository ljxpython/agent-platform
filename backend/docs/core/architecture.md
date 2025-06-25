# 后端系统架构设计

## 🏗️ 整体架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   React UI      │  │   Admin Panel   │  │   Mobile App │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   FastAPI       │  │   路由管理      │  │   中间件     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Business Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Controllers   │  │   Services      │  │   AI Core    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   PostgreSQL    │  │   Redis Cache   │  │   Milvus     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

- **Web框架**: FastAPI
- **ORM**: Tortoise ORM
- **数据库**: PostgreSQL (主)、Redis (缓存)、Milvus (向量)
- **AI框架**: AutoGen、LlamaIndex
- **任务队列**: Celery + Redis
- **监控**: Prometheus + Grafana
- **日志**: Loguru

## 📁 目录结构

```
backend/
├── api/                    # API路由层
│   ├── __init__.py
│   ├── deps.py            # 依赖注入
│   └── v1/                # API版本控制
│       ├── __init__.py
│       ├── auth.py        # 认证相关
│       ├── users.py       # 用户管理
│       ├── testcase.py    # 测试用例
│       ├── ai_chat.py     # AI对话
│       └── rag.py         # RAG知识库
├── controllers/           # 控制器层
│   ├── __init__.py
│   ├── base_controller.py # 基础控制器
│   ├── auth_controller.py # 认证控制器
│   ├── user_controller.py # 用户控制器
│   └── ...
├── services/             # 服务层
│   ├── __init__.py
│   ├── auth/             # 认证服务
│   ├── user/             # 用户服务
│   ├── testcase/         # 测试用例服务
│   ├── ai_chat/          # AI对话服务
│   └── rag/              # RAG服务
├── models/               # 数据模型层
│   ├── __init__.py
│   ├── base.py           # 基础模型
│   ├── user.py           # 用户模型
│   ├── auth.py           # 认证模型
│   └── ...
├── schemas/              # 数据验证层
│   ├── __init__.py
│   ├── base.py           # 基础Schema
│   ├── user.py           # 用户Schema
│   ├── auth.py           # 认证Schema
│   └── ...
├── api_core/             # API核心工具层
│   ├── __init__.py
│   ├── config.py         # 配置管理
│   ├── database.py       # 数据库连接
│   ├── security.py       # 安全工具
│   ├── crud.py           # CRUD基类
│   ├── response.py       # 响应处理
│   ├── exceptions.py     # 异常定义
│   ├── deps.py           # 依赖注入
│   └── middleware.py     # 中间件
├── ai_core/              # AI核心框架
│   ├── __init__.py
│   ├── agents/           # AI智能体
│   ├── memory/           # 记忆管理
│   ├── runtime/          # 运行时
│   └── message_queue.py  # 消息队列
├── rag_core/             # RAG核心框架
│   ├── __init__.py
│   ├── rag_system.py     # RAG系统
│   ├── vector_store.py   # 向量存储
│   ├── query_engine.py   # 查询引擎
│   └── embedding.py      # 嵌入生成
├── utils/                # 工具函数
│   ├── __init__.py
│   ├── helpers.py        # 辅助函数
│   ├── validators.py     # 验证器
│   └── formatters.py     # 格式化器
├── tests/                # 测试代码
│   ├── __init__.py
│   ├── conftest.py       # 测试配置
│   ├── test_api/         # API测试
│   ├── test_controllers/ # 控制器测试
│   └── test_services/    # 服务测试
├── migrations/           # 数据库迁移
├── docs/                 # 文档
├── main.py               # 应用入口
├── settings.py           # 配置文件
└── requirements.txt      # 依赖列表
```

## 🔄 分层架构详解

### 1. API层 (api/)

**职责**: 处理HTTP请求和响应，参数验证，路由管理

```python
# api/v1/users.py
from fastapi import APIRouter, Depends
from backend.controllers.user_controller import user_controller
from backend.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["用户管理"])

@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreate):
    """创建用户 - 只处理HTTP层面的事务"""
    return await user_controller.create_user(user_data)
```

**特点**:
- 薄层设计，不包含业务逻辑
- 负责参数验证和响应格式化
- 处理HTTP状态码和错误响应
- 版本控制和API文档生成

### 2. 控制器层 (controllers/)

**职责**: 业务流程控制，调用服务层，处理业务异常

```python
# controllers/user_controller.py
from backend.api_core.crud import CRUDBase
from backend.api_core.response import response
from backend.services.user.user_service import user_service


class UserController(CRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(User)

    async def create_user(self, user_data: UserCreate):
        """控制用户创建流程"""
        # 业务验证
        await self._validate_user_data(user_data)

        # 调用服务层
        user = await user_service.create_user(user_data)

        # 返回统一响应
        return response.success(data=user, msg="用户创建成功")
```

**特点**:
- 继承CRUD基类，复用通用操作
- 处理业务流程控制
- 统一响应格式
- 异常处理和转换

### 3. 服务层 (services/)

**职责**: 具体业务逻辑实现，数据处理，外部服务集成

```python
# services/user/user_service.py
class UserService:
    async def create_user(self, user_data: UserCreate) -> User:
        """用户创建业务逻辑"""
        # 密码加密
        hashed_password = get_password_hash(user_data.password)

        # 创建用户
        user = await User.create(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )

        # 发送欢迎邮件
        await self._send_welcome_email(user)

        # 创建用户资料
        await self._create_user_profile(user)

        return user
```

**特点**:
- 包含具体业务逻辑
- 处理数据转换和计算
- 集成外部服务
- 事务管理

### 4. 模型层 (models/)

**职责**: 数据模型定义，数据库表结构，关系映射

```python
# models/user.py
from backend.models.base import BaseModel

class User(BaseModel):
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=255, unique=True)
    hashed_password = fields.CharField(max_length=255)

    # 关系定义
    profile = fields.OneToOneField("models.UserProfile", related_name="user")
    articles = fields.ReverseRelation["Article"]

    class Meta:
        table = "users"
        indexes = [["username", "email"]]
```

**特点**:
- 继承基础模型
- 定义字段约束和索引
- 建立模型间关系
- 提供模型方法

### 5. Schema层 (schemas/)

**职责**: 数据验证，序列化，API文档生成

```python
# schemas/user.py
from backend.schemas.base import BaseSchema

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

**特点**:
- 继承基础Schema
- 定义验证规则
- 支持自定义验证器
- 自动生成API文档

## 🔧 核心组件

### 1. 配置管理 (api_core/config.py)

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    # 应用配置
    app_name: str = "Backend API"
    debug: bool = False
    version: str = "1.0.0"

    # 数据库配置
    database_url: str
    redis_url: str

    # 安全配置
    secret_key: str
    access_token_expire_minutes: int = 30

    # AI配置
    deepseek_api_key: str
    ollama_base_url: str = "http://localhost:11434"

    class Config:
        env_file = ".env"

settings = Settings()
```

### 2. 数据库连接 (api_core/database.py)

```python
from tortoise import Tortoise

TORTOISE_ORM = {
    "connections": {
        "default": settings.database_url
    },
    "apps": {
        "models": {
            "models": ["backend.models"],
            "default_connection": "default",
        }
    }
}

async def init_db():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()

async def close_db():
    await Tortoise.close_connections()
```

### 3. 依赖注入 (api_core/deps.py)

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)) -> User:
    """获取当前用户"""
    try:
        payload = jwt.decode(token.credentials, settings.secret_key)
        username = payload.get("sub")
        user = await User.get_or_none(username=username)
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Token无效")

def require_permissions(permissions: List[str]):
    """权限检查装饰器"""
    async def permission_checker(current_user: User = Depends(get_current_user)):
        user_permissions = await current_user.get_permissions()
        if not all(perm in user_permissions for perm in permissions):
            raise HTTPException(status_code=403, detail="权限不足")
    return Depends(permission_checker)
```

## 🚀 AI核心架构

### 1. AI Core模块

```python
# ai_core/agents/base_agent.py
class BaseAgent:
    def __init__(self, name: str, system_message: str):
        self.name = name
        self.system_message = system_message

    async def process_message(self, message: str) -> str:
        """处理消息的基础方法"""
        raise NotImplementedError

# ai_core/runtime/base_runtime.py
class BaseRuntime:
    def __init__(self):
        self.agents = {}
        self.message_queue = MessageQueue()

    async def run_conversation(self, initial_message: str):
        """运行对话流程"""
        pass
```

### 2. RAG Core模块

```python
# rag_core/rag_system.py
class RAGSystem:
    def __init__(self):
        self.vector_store = VectorStore()
        self.query_engine = QueryEngine()
        self.embedding_generator = EmbeddingGenerator()

    async def query(self, question: str, collection: str) -> QueryResult:
        """RAG查询主流程"""
        # 生成嵌入向量
        embedding = await self.embedding_generator.generate(question)

        # 向量检索
        docs = await self.vector_store.search(embedding, collection)

        # 生成回答
        answer = await self.query_engine.generate_answer(question, docs)

        return QueryResult(answer=answer, sources=docs)
```

## 🔄 数据流架构

### 1. 请求处理流程

```
Client Request
      ↓
FastAPI Router (api/)
      ↓
Parameter Validation (schemas/)
      ↓
Controller (controllers/)
      ↓
Service Layer (services/)
      ↓
Model Layer (models/)
      ↓
Database
      ↓
Response (api_core/response.py)
      ↓
Client Response
```

### 2. AI处理流程

```
User Input
      ↓
AI Chat API (api/v1/ai_chat.py)
      ↓
Chat Controller (controllers/)
      ↓
AI Service (services/ai_chat/)
      ↓
AI Core Runtime (ai_core/)
      ↓
Agent Processing
      ↓
Message Queue
      ↓
SSE Stream Response
      ↓
Frontend Display
```

### 3. RAG查询流程

```
Query Request
      ↓
RAG API (api/v1/rag.py)
      ↓
RAG Controller (controllers/)
      ↓
RAG Service (services/rag/)
      ↓
RAG Core System (rag_core/)
      ↓
Vector Search + LLM Generation
      ↓
Query Result
      ↓
Response
```

## 🔒 安全架构

### 1. 认证授权

```python
# 多层安全验证
@router.post("/admin/users")
async def admin_create_user(
    user_data: UserCreate,
    current_user = Depends(get_current_user),           # 身份验证
    _: None = Depends(require_permissions(["user:create"])),  # 权限验证
    _: None = Depends(require_roles(["admin"]))         # 角色验证
):
    pass
```

### 2. 数据安全

- **输入验证**: Pydantic Schema验证
- **SQL注入防护**: ORM参数化查询
- **XSS防护**: 输出转义
- **CSRF防护**: Token验证

### 3. API安全

- **速率限制**: 防止API滥用
- **CORS配置**: 跨域请求控制
- **HTTPS强制**: 传输加密
- **API版本控制**: 向后兼容

## 📊 监控架构

### 1. 应用监控

```python
# 性能监控中间件
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # 记录指标
    metrics.record_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=process_time
    )

    return response
```

### 2. 日志架构

```python
# 结构化日志
from loguru import logger

logger.add(
    "logs/app.log",
    rotation="1 day",
    retention="30 days",
    format="{time} | {level} | {name}:{function}:{line} - {message}",
    serialize=True  # JSON格式
)
```

## 🔧 部署架构

### 1. 容器化部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 微服务架构

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - milvus

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: backend_db

  redis:
    image: redis:7-alpine

  milvus:
    image: milvusdb/milvus:latest
```

这个架构设计确保了系统的可扩展性、可维护性和高性能，为AI编程助手提供了清晰的开发指导。
