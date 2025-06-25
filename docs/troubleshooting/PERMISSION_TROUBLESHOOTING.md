# 权限管理故障排查指南

## 📋 概述

本文档提供权限管理系统常见问题的诊断和解决方案，帮助快速定位和修复权限相关问题。

## 🔍 常见问题诊断

### 1. JWT认证问题

#### 问题：前端收到401 "无效的令牌"错误

**症状**：
```
❌ [响应拦截器] 请求错误: {status: 401, data: {detail: "无效的令牌"}}
```

**诊断步骤**：

1. **检查令牌是否正确发送**
```javascript
// 浏览器控制台检查
console.log('Token:', localStorage.getItem('token'));
console.log('Authorization Header:', request.headers.Authorization);
```

2. **检查令牌格式**
```bash
# 正确格式
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# 错误格式
Authorization: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # 缺少Bearer前缀
```

3. **检查后端JWT解码日志**
```
2025-06-22 09:32:01 | DEBUG | [JWT] 开始解码令牌: eyJhbGciOiJIUzI1NiIsInR5...
2025-06-22 09:32:01 | ERROR | [JWT] 解码失败: JWTClaimsError: Subject must be a string.
```

**解决方案**：

- **Sub字段类型错误**：
```python
# 修复JWT创建
data = {"sub": str(user.id), "username": user.username}  # 确保sub是字符串
```

- **密钥不匹配**：
```python
# 检查配置文件
SECRET_KEY = "your-secret-key-here"  # 确保前后端使用相同密钥
```

#### 问题：令牌过期

**症状**：
```
❌ JWT解码失败: ExpiredSignatureError: Signature has expired
```

**解决方案**：
```python
# 调整令牌过期时间
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 增加到60分钟

# 或实现令牌刷新机制
@router.post("/auth/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    # 生成新令牌
    pass
```

### 2. 权限检查问题

#### 问题：有效用户仍然收到403权限不足

**症状**：
```
❌ 权限检查失败: 用户 test 无权访问 GET /api/v1/system/users
```

**诊断步骤**：

1. **检查用户角色**
```sql
-- 查询用户角色
SELECT u.username, r.name as role_name
FROM user u
JOIN user_role ur ON u.id = ur.user_id
JOIN role r ON ur.role_id = r.id
WHERE u.username = 'test';
```

2. **检查角色权限**
```sql
-- 查询角色权限
SELECT r.name as role_name, a.method, a.path
FROM role r
JOIN role_api ra ON r.id = ra.role_id
JOIN api a ON ra.api_id = a.id
WHERE r.name = '管理员';
```

3. **检查API权限同步**
```bash
# 检查API是否已同步
curl -X GET "http://localhost:8000/api/v1/system/apis" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**解决方案**：

- **重新同步API权限**：
```bash
curl -X POST "http://localhost:8000/api/v1/system/apis/sync" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

- **手动分配权限**：
```python
# 为角色分配权限
await permission_service.assign_role_permissions(role_id=1, api_ids=[1,2,3])
```

### 3. 数据库相关问题

#### 问题：用户表为空或默认用户不存在

**症状**：
```
❌ 登录失败: 用户名或密码错误
```

**诊断**：
```bash
# 检查用户表
sqlite3 backend/data/db.sqlite3 "SELECT * FROM user;"
```

**解决方案**：
```bash
# 重新初始化数据库
cd backend
aerich upgrade
python3 -c "
from backend.core.database import create_default_user
import asyncio
asyncio.run(create_default_user())
"
```

#### 问题：数据库迁移失败

**症状**：
```
❌ tortoise.exceptions.OperationalError: no such table: user
```

**解决方案**：
```bash
# 重新初始化迁移
cd backend
rm -rf migrations/
aerich init -t backend.conf.database.TORTOISE_ORM
aerich init-db
aerich upgrade
```

### 4. 前端集成问题

#### 问题：登录成功但后续请求仍然401

**诊断步骤**：

1. **检查token存储**
```javascript
// 登录成功后检查
console.log('Login response:', response);
console.log('Token saved:', localStorage.getItem('token'));
```

2. **检查请求拦截器**
```javascript
// 检查拦截器是否正确添加Authorization头
axios.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    console.log('Request interceptor - Token:', !!token);
    console.log('Request interceptor - Auth header:', config.headers.Authorization);
    return config;
});
```

**解决方案**：

- **修复token存储**：
```typescript
// 确保登录成功后正确存储token
const handleLogin = async (credentials) => {
    const response = await authService.login(credentials);
    localStorage.setItem('token', response.access_token);  // 注意字段名
    localStorage.setItem('user', JSON.stringify(response.user));
};
```

- **修复请求拦截器**：
```typescript
// 确保正确添加Authorization头
axiosInstance.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});
```

## 🛠️ 调试工具

### 1. 后端调试

#### 启用详细日志
```python
# backend/conf/config.py
LOGGING = {
    "level": "DEBUG",  # 启用DEBUG级别
    "format": "%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
}
```

#### JWT调试工具
```python
# 临时调试函数
async def debug_jwt_token(token: str):
    try:
        # 不验证签名，仅解码查看内容
        unverified_payload = jwt.get_unverified_claims(token)
        print(f"JWT载荷: {unverified_payload}")

        # 验证解码
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"验证成功: {payload}")

    except Exception as e:
        print(f"JWT调试失败: {e}")
```

### 2. 前端调试

#### 网络请求监控
```javascript
// 监控所有axios请求
axios.interceptors.request.use((config) => {
    console.group(`📤 ${config.method?.toUpperCase()} ${config.url}`);
    console.log('Headers:', config.headers);
    console.log('Data:', config.data);
    console.groupEnd();
    return config;
});

axios.interceptors.response.use(
    (response) => {
        console.group(`✅ ${response.status} ${response.config.url}`);
        console.log('Data:', response.data);
        console.groupEnd();
        return response;
    },
    (error) => {
        console.group(`❌ ${error.response?.status} ${error.config?.url}`);
        console.log('Error:', error.response?.data);
        console.groupEnd();
        return Promise.reject(error);
    }
);
```

#### 权限状态检查
```javascript
// 权限状态检查工具
const checkAuthStatus = () => {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');

    console.log('🔍 认证状态检查:');
    console.log('Token存在:', !!token);
    console.log('Token长度:', token?.length || 0);
    console.log('用户信息:', user ? JSON.parse(user) : null);

    if (token) {
        // 解码JWT查看内容（仅用于调试）
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            console.log('Token载荷:', payload);
            console.log('Token过期时间:', new Date(payload.exp * 1000));
        } catch (e) {
            console.error('Token解码失败:', e);
        }
    }
};

// 在控制台调用
window.checkAuthStatus = checkAuthStatus;
```

## 🔧 修复脚本

### 1. 权限重置脚本

```python
# scripts/reset_permissions.py
import asyncio
from backend.api_core.database import init_db
from backend.services.permission_service import permission_service
from backend.models.user import User
from backend.models.role import Role


async def reset_permissions():
    """重置权限系统"""
    await init_db()

    # 1. 创建默认角色
    admin_role, created = await Role.get_or_create(
        name="管理员",
        defaults={"description": "系统管理员", "is_active": True}
    )

    # 2. 同步API权限
    from fastapi import FastAPI
    app = FastAPI()  # 临时应用实例
    result = await permission_service.sync_apis_from_app(app)
    print(f"API同步完成: {result}")

    # 3. 分配权限
    await permission_service.init_default_permissions()
    print("默认权限初始化完成")


if __name__ == "__main__":
    asyncio.run(reset_permissions())
```

### 2. 用户修复脚本

```python
# scripts/fix_user.py
import asyncio
from backend.api_core.database import init_db, create_default_user


async def fix_user_system():
    """修复用户系统"""
    await init_db()
    await create_default_user()
    print("用户系统修复完成")


if __name__ == "__main__":
    asyncio.run(fix_user_system())
```

## 📋 检查清单

### 登录问题检查清单

- [ ] 用户是否存在于数据库
- [ ] 密码哈希是否正确
- [ ] 用户状态是否激活
- [ ] JWT密钥配置是否正确
- [ ] JWT过期时间是否合理

### 权限问题检查清单

- [ ] 用户是否有相应角色
- [ ] 角色是否有相应权限
- [ ] API权限是否已同步
- [ ] 权限检查逻辑是否正确
- [ ] 超级用户权限是否正常

### 前端集成检查清单

- [ ] 登录响应是否正确处理
- [ ] Token是否正确存储
- [ ] 请求拦截器是否正确配置
- [ ] Authorization头是否正确添加
- [ ] 错误处理是否完善

## 🚨 紧急修复

### 快速恢复访问

如果系统完全无法访问，可以使用开发模式：

```python
# backend/core/dependency.py
async def is_authed(authorization: str = Header(None)):
    # 紧急开发模式
    if authorization == "Bearer dev":
        user = await User.filter().first()
        if user:
            return user

    # 正常认证流程
    # ...
```

然后使用：
```bash
curl -X GET "http://localhost:8000/api/v1/system/users" \
  -H "Authorization: Bearer dev"
```

### 重置整个权限系统

```bash
# 完全重置
cd backend
rm -f data/db.sqlite3
rm -rf migrations/
aerich init -t backend.conf.database.TORTOISE_ORM
aerich init-db
python3 run.py  # 重新启动，会自动初始化
```

## 📞 获取帮助

如果以上方法都无法解决问题：

1. **收集日志信息**：
   - 后端完整日志
   - 前端控制台错误
   - 网络请求详情

2. **提供环境信息**：
   - Python版本
   - 依赖库版本
   - 操作系统信息

3. **描述复现步骤**：
   - 具体操作步骤
   - 预期结果
   - 实际结果

4. **提交Issue**：
   - 包含完整的错误信息
   - 提供最小复现示例
   - 说明已尝试的解决方案
