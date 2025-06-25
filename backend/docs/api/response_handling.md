# 响应处理规范

## 📤 统一响应系统

### 核心响应工具类

系统提供了 `backend.api_core.response` 模块来统一处理所有API响应：

```python
from backend.api_core.response import response, rag_response
```

## 🎯 基础响应方法

### 1. 成功响应

```python
from backend.api_core.response import response


# 基础成功响应
@router.get("/users")
async def get_users():
    users = await User.all()
    return response.success(
        data=users,
        msg="获取用户列表成功"
    )


# 响应格式
{
    "code": 200,
    "msg": "获取用户列表成功",
    "data": [...]
}
```

### 2. 失败响应

```python
# 通过异常处理自动生成失败响应
from backend.api_core.exceptions import BusinessError


@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise BusinessError("用户不存在", code=404)
    return response.success(data=user)


# 自动生成的错误响应格式
{
    "code": 404,
    "msg": "用户不存在",
    "data": null
}
```

### 3. 分页响应

```python
@router.get("/users")
async def get_users_paginated(page: int = 1, page_size: int = 20):
    total = await User.all().count()
    users = await User.all().offset((page - 1) * page_size).limit(page_size)

    return response.success_with_pagination(
        data=users,
        total=total,
        page=page,
        page_size=page_size,
        msg="获取用户列表成功"
    )

# 分页响应格式
{
    "code": 200,
    "msg": "获取用户列表成功",
    "data": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
}
```

## 🔧 专用响应工具

### RAG专用响应

```python
from backend.api_core.response import rag_response


# Collection相关响应
@router.get("/rag/collections")
async def get_collections():
    collections = await get_all_collections()
    return rag_response.collection_success(collections)


@router.post("/rag/collections")
async def create_collection(data: CollectionCreate):
    collection = await create_collection(data)
    return rag_response.collection_created(collection)


@router.delete("/rag/collections/{name}")
async def delete_collection(name: str):
    doc_count = await delete_collection_and_docs(name)
    return rag_response.collection_deleted(doc_count)


# 文档相关响应
@router.get("/rag/documents")
async def get_documents(page: int = 1, page_size: int = 20):
    documents, total = await get_documents_paginated(page, page_size)
    return rag_response.documents_success(documents, total, page, page_size)


@router.post("/rag/documents")
async def create_document(data: DocumentCreate):
    document_id = await create_document(data)
    return rag_response.document_created(document_id)


# 查询相关响应
@router.post("/rag/query")
async def rag_query(request: QueryRequest):
    result = await execute_rag_query(request)
    return rag_response.query_success(result)


# 统计相关响应
@router.get("/rag/stats")
async def get_rag_stats():
    stats = await get_system_stats()
    return rag_response.stats_success(stats)
```

## 🚨 异常处理与响应

### 1. 业务异常

```python
from backend.api_core.exceptions import BusinessError


# 抛出业务异常
@router.post("/users")
async def create_user(user_data: UserCreate):
    if await User.exists(username=user_data.username):
        raise BusinessError("用户名已存在", code=409)

    if await User.exists(email=user_data.email):
        raise BusinessError("邮箱已被注册", code=409)

    user = await User.create(**user_data.dict())
    return response.success(data=user, msg="用户创建成功")
```

### 2. 数据库异常

```python
from tortoise.exceptions import DoesNotExist, IntegrityError

# 系统自动处理数据库异常
@router.get("/users/{user_id}")
async def get_user(user_id: int):
    # DoesNotExist异常会自动转换为404响应
    user = await User.get(id=user_id)
    return response.success(data=user)

@router.post("/users")
async def create_user(user_data: UserCreate):
    # IntegrityError异常会自动转换为500响应
    user = await User.create(**user_data.dict())
    return response.success(data=user)
```

### 3. 参数验证异常

```python
from pydantic import ValidationError

# Pydantic验证异常自动处理
@router.post("/users")
async def create_user(user_data: UserCreate):
    # 参数验证失败会自动返回422响应
    user = await User.create(**user_data.dict())
    return response.success(data=user)

# 自动生成的验证错误响应
{
    "code": 422,
    "msg": "请求参数验证失败",
    "data": {
        "errors": [
            {
                "loc": ["username"],
                "msg": "ensure this value has at least 3 characters",
                "type": "value_error.any_str.min_length"
            }
        ]
    }
}
```

## 📊 响应格式标准

### 1. 标准成功响应

```json
{
    "code": 200,
    "msg": "操作成功",
    "data": {
        // 具体数据内容
    }
}
```

### 2. 分页响应

```json
{
    "code": 200,
    "msg": "操作成功",
    "data": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
}
```

### 3. 错误响应

```json
{
    "code": 400,
    "msg": "错误描述",
    "data": null
}
```

### 4. 验证错误响应

```json
{
    "code": 422,
    "msg": "参数验证失败",
    "data": {
        "errors": [
            {
                "loc": ["field_name"],
                "msg": "error message",
                "type": "error_type"
            }
        ]
    }
}
```

## 🎨 自定义响应方法

### 1. 扩展响应工具类

```python
# 在具体业务中扩展响应方法
class UserResponseUtil:
    @staticmethod
    def user_created(user_data: dict) -> Success:
        return response.success(
            data=user_data,
            msg="用户创建成功",
            code=201
        )

    @staticmethod
    def user_login_success(user_data: dict, token: str) -> Success:
        return response.success(
            data={
                "user": user_data,
                "token": token,
                "expires_in": 3600
            },
            msg="登录成功"
        )

    @staticmethod
    def user_not_found() -> Fail:
        return response.fail(
            msg="用户不存在",
            code=404
        )

# 使用自定义响应
user_response = UserResponseUtil()

@router.post("/login")
async def login(credentials: LoginRequest):
    user, token = await authenticate_user(credentials)
    return user_response.user_login_success(user, token)
```

### 2. 条件响应

```python
@router.get("/users/{user_id}")
async def get_user(user_id: int, include_posts: bool = False):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise BusinessError("用户不存在", code=404)

    user_data = UserResponse.from_orm(user).dict()

    if include_posts:
        posts = await Post.filter(user=user).all()
        user_data["posts"] = [PostResponse.from_orm(post).dict() for post in posts]
        return response.success(
            data=user_data,
            msg="获取用户详情（包含文章）成功"
        )

    return response.success(
        data=user_data,
        msg="获取用户详情成功"
    )
```

## 🔄 响应中间件

### 1. 响应时间记录

```python
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

### 2. 响应格式统一

```python
from fastapi.responses import JSONResponse

@app.middleware("http")
async def ensure_response_format(request: Request, call_next):
    response = await call_next(request)

    # 确保所有响应都是JSON格式
    if not isinstance(response, JSONResponse):
        return JSONResponse(
            content={
                "code": 200,
                "msg": "操作成功",
                "data": response
            }
        )

    return response
```

## 📝 响应文档化

### 1. 响应模型定义

```python
from pydantic import BaseModel

class UserListResponse(BaseModel):
    """用户列表响应模型"""
    code: int = 200
    msg: str = "获取用户列表成功"
    data: List[UserResponse]
    total: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None

@router.get("/users", response_model=UserListResponse)
async def get_users():
    """获取用户列表，自动生成响应文档"""
    pass
```

### 2. 响应示例

```python
@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    responses={
        200: {
            "description": "成功获取用户信息",
            "content": {
                "application/json": {
                    "example": {
                        "code": 200,
                        "msg": "获取用户信息成功",
                        "data": {
                            "id": 1,
                            "username": "john_doe",
                            "email": "john@example.com",
                            "full_name": "John Doe",
                            "is_active": True,
                            "created_at": "2024-01-01T00:00:00"
                        }
                    }
                }
            }
        },
        404: {
            "description": "用户不存在",
            "content": {
                "application/json": {
                    "example": {
                        "code": 404,
                        "msg": "用户不存在",
                        "data": None
                    }
                }
            }
        }
    }
)
async def get_user(user_id: int):
    """获取用户详情"""
    pass
```

## 🎯 最佳实践

### 1. 响应一致性

- 所有API都使用统一的响应格式
- 错误信息要清晰明确
- 状态码要符合HTTP标准

### 2. 性能优化

- 避免在响应中包含敏感信息
- 大数据量使用分页
- 合理使用缓存

### 3. 安全考虑

- 不在响应中暴露内部错误详情
- 敏感数据要脱敏处理
- 合理设置响应头
