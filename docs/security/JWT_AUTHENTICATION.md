# JWT认证系统详解

## 📋 概述

本项目采用JWT (JSON Web Token) 作为用户认证的核心技术，提供安全、无状态的用户身份验证机制。

## 🔧 技术实现

### JWT库选择

我们使用 `python-jose` 库来处理JWT令牌：

```python
from jose import JWTError, jwt
```

**选择原因**：
- ✅ 成熟稳定的JWT实现
- ✅ 完整的JWT标准支持
- ✅ 良好的错误处理机制
- ✅ 活跃的社区维护

### 核心配置

```python
# backend/conf/config.py
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

## 🏗️ JWT令牌结构

### 标准JWT格式

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcm5hbWUiOiJ0ZXN0IiwidXNlcl9pZCI6MSwiZXhwIjoxNzUwNjQyOTMyfQ.1X9j8TfLWhYt4r3M2GbZWhqreBzuu7hHnp8fGAzhVz0
```

### 令牌组成

```
Header.Payload.Signature
```

#### Header（头部）
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

#### Payload（载荷）
```json
{
  "sub": "1",           // 用户ID（字符串格式，JWT标准要求）
  "username": "test",   // 用户名
  "user_id": 1,        // 用户ID（整数格式，向后兼容）
  "exp": 1750642932    // 过期时间戳
}
```

#### Signature（签名）
```
HMACSHA256(
  base64UrlEncode(header) + "." +
  base64UrlEncode(payload),
  secret
)
```

## 🔐 认证流程

### 1. 用户登录

```mermaid
sequenceDiagram
    participant C as 客户端
    participant A as 认证服务
    participant D as 数据库

    C->>A: POST /auth/login {username, password}
    A->>D: 查询用户信息
    D-->>A: 返回用户数据
    A->>A: 验证密码（Argon2）
    A->>A: 生成JWT令牌
    A-->>C: 返回 {access_token, user_info}
```

#### 登录实现

```python
async def login(self, username: str, password: str) -> LoginResponse:
    # 1. 查询用户
    user = await User.get_or_none(username=username)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 2. 验证密码
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 3. 检查用户状态
    if not user.is_active:
        raise HTTPException(status_code=401, detail="用户已被禁用")

    # 4. 生成JWT令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "user_id": user.id},
        expires_delta=access_token_expires,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )
```

### 2. 令牌验证

```mermaid
sequenceDiagram
    participant C as 客户端
    participant M as 中间件
    participant A as 认证服务
    participant D as 数据库

    C->>M: API请求 + Authorization Header
    M->>M: 提取JWT令牌
    M->>A: 验证令牌
    A->>A: 解码JWT
    A->>D: 查询用户信息
    D-->>A: 返回用户数据
    A->>A: 检查用户状态
    A-->>M: 返回用户信息
    M->>M: 设置用户上下文
    M-->>C: 继续处理请求
```

#### 验证实现

```python
async def is_authed(authorization: str = Header(None)) -> Optional[User]:
    try:
        # 1. 检查Authorization头
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="缺少认证令牌")

        # 2. 提取令牌
        token = authorization.replace("Bearer ", "")

        # 3. 解码JWT
        decode_data = decode_access_token(token)
        if not decode_data:
            raise HTTPException(status_code=401, detail="无效的令牌")

        # 4. 获取用户信息
        user_id = decode_data.get("sub") or decode_data.get("user_id")
        user = await User.get_or_none(id=int(user_id))
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="用户不存在或已禁用")

        # 5. 设置上下文
        CTX_USER_ID.set(int(user_id))
        CTX_CURRENT_USER.set(user)

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"认证过程中发生错误: {e}")
        raise HTTPException(status_code=500, detail="认证服务异常")
```

## 🛡️ 安全特性

### 1. 令牌安全

#### 密钥管理
```python
# 使用强密钥
SECRET_KEY = "your-256-bit-secret-key-here"

# 密钥轮换（推荐定期更换）
def rotate_secret_key():
    # 实现密钥轮换逻辑
    pass
```

#### 令牌过期
```python
# 设置合理的过期时间
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30分钟

# 自动过期检查
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### 2. 字段验证

#### Sub字段标准化
```python
# JWT标准要求sub字段必须是字符串
def create_access_token(data: dict):
    # 确保sub字段是字符串
    if "sub" in data and not isinstance(data["sub"], str):
        data["sub"] = str(data["sub"])

    # 同时保留user_id字段用于兼容性
    if "user_id" in data:
        data["sub"] = str(data["user_id"])
```

#### 载荷验证
```python
def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # 验证必要字段
        sub = payload.get("sub")
        username = payload.get("username")

        if not sub or not username:
            logger.warning(f"JWT载荷缺少必要字段: sub={sub}, username={username}")
            return None

        # 转换sub为整数
        try:
            user_id = int(sub)
        except (ValueError, TypeError):
            logger.warning(f"无法转换sub为整数: {sub}")
            return None

        return {
            "user_id": user_id,
            "username": username,
            "sub": user_id
        }

    except JWTError as e:
        logger.error(f"JWT解码失败: {e}")
        return None
```

### 3. 错误处理

#### 统一异常处理
```python
class JWTAuthenticationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=401, detail=detail)

# 具体异常类型
class TokenExpiredError(JWTAuthenticationError):
    def __init__(self):
        super().__init__("令牌已过期")

class TokenInvalidError(JWTAuthenticationError):
    def __init__(self):
        super().__init__("无效的令牌")

class UserNotFoundError(JWTAuthenticationError):
    def __init__(self):
        super().__init__("用户不存在")
```

## 🔍 调试和监控

### 1. 详细日志

```python
def decode_access_token(token: str) -> Optional[dict]:
    try:
        logger.debug(f"[JWT] 开始解码令牌: {token[:20]}...")
        logger.debug(f"[JWT] 使用密钥: {SECRET_KEY[:10]}...")
        logger.debug(f"[JWT] 使用算法: {ALGORITHM}")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"[JWT] 解码成功，载荷: {payload}")

        # ... 处理逻辑

        logger.debug(f"[JWT] 提取的用户信息: user_id={user_id}, username={username}")
        return result

    except JWTError as e:
        logger.error(f"[JWT] 解码失败: {type(e).__name__}: {str(e)}")
        return None
```

### 2. 性能监控

```python
import time
from functools import wraps

def monitor_jwt_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"JWT操作 {func.__name__} 耗时: {duration:.3f}秒")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"JWT操作 {func.__name__} 失败，耗时: {duration:.3f}秒，错误: {e}")
            raise
    return wrapper

@monitor_jwt_performance
async def is_authed(authorization: str = Header(None)):
    # JWT验证逻辑
    pass
```

## 🚀 最佳实践

### 1. 前端集成

#### 令牌存储
```typescript
// 安全存储JWT令牌
class TokenManager {
    private static readonly TOKEN_KEY = 'access_token';

    static setToken(token: string): void {
        localStorage.setItem(this.TOKEN_KEY, token);
    }

    static getToken(): string | null {
        return localStorage.getItem(this.TOKEN_KEY);
    }

    static removeToken(): void {
        localStorage.removeItem(this.TOKEN_KEY);
    }
}
```

#### 请求拦截器
```typescript
// Axios请求拦截器
axios.interceptors.request.use(
    (config) => {
        const token = TokenManager.getToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// 响应拦截器处理401
axios.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            TokenManager.removeToken();
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);
```

### 2. 令牌刷新

```python
# 实现令牌刷新机制
@router.post("/auth/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    # 生成新的访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(current_user.id), "username": current_user.username},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}
```

### 3. 开发模式支持

```python
# 开发模式下的便捷认证
async def is_authed(authorization: str = Header(None)):
    # 开发模式支持
    if token == "dev" and settings.get("DEBUG", False):
        user = await User.filter().first()
        if not user:
            raise HTTPException(status_code=401, detail="开发模式下未找到用户")
        return user

    # 正常JWT验证流程
    # ...
```

## 📋 故障排查

### 常见问题

#### 1. "Subject must be a string" 错误
**原因**: JWT标准要求`sub`字段必须是字符串
**解决**: 确保创建JWT时将用户ID转换为字符串

```python
# 错误
data = {"sub": user.id}  # user.id是整数

# 正确
data = {"sub": str(user.id)}  # 转换为字符串
```

#### 2. "Invalid token" 错误
**原因**: 令牌格式错误或密钥不匹配
**解决**: 检查密钥配置和令牌格式

#### 3. 前端401错误
**原因**: 令牌未正确发送或已过期
**解决**: 检查请求拦截器和令牌存储

### 调试步骤

1. **检查令牌格式**: 确保Bearer前缀正确
2. **验证密钥配置**: 确保前后端使用相同密钥
3. **查看详细日志**: 启用DEBUG级别日志
4. **测试令牌解码**: 使用在线JWT工具验证

## 📚 相关文档

- [权限管理系统](./PERMISSION_SYSTEM.md)
- [用户系统架构](../architecture/USER_SYSTEM.md)
- [API文档](../development/API_DOCUMENTATION.md)
- [故障排查指南](../troubleshooting/PERMISSION_TROUBLESHOOTING.md)

---

## 📞 技术支持

如果在JWT认证过程中遇到问题，请：
1. 查看详细的调试日志
2. 参考故障排查文档
3. 提交Issue描述具体问题
