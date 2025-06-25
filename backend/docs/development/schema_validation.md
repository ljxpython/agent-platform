# 参数校验规范

## ✅ Schema设计原则

### 基础原则

1. **继承基类** - 所有Schema都继承自 `BaseSchema`
2. **类型安全** - 使用完整的类型注解
3. **验证规则** - 设置合适的验证约束
4. **文档化** - 为字段添加清晰的描述
5. **复用性** - 合理设计Schema的继承关系

## 🏗️ 基础Schema结构

### 1. 基础Schema类

```python
# schemas/base.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any
from datetime import datetime

class BaseSchema(BaseModel):
    """基础Schema类，所有Schema都应继承此类"""

    model_config = ConfigDict(
        # 允许从ORM对象创建
        from_attributes=True,
        # 验证赋值
        validate_assignment=True,
        # 使用枚举值
        use_enum_values=True,
        # 额外字段处理
        extra='forbid'
    )

class TimestampMixin(BaseModel):
    """时间戳混入"""
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

class IDMixin(BaseModel):
    """ID混入"""
    id: int = Field(..., description="主键ID", gt=0)

class ResponseSchema(BaseSchema):
    """响应Schema基类"""
    pass

class RequestSchema(BaseSchema):
    """请求Schema基类"""
    pass
```

### 2. 用户Schema示例

```python
# schemas/user.py
from typing import Optional, List
from pydantic import Field, EmailStr, validator, root_validator
from datetime import datetime
from backend.schemas.base import BaseSchema, IDMixin, TimestampMixin

class UserBase(BaseSchema):
    """用户基础Schema"""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        regex=r'^[a-zA-Z0-9_]+$',
        description="用户名，3-50字符，只能包含字母、数字和下划线"
    )
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="全名"
    )

class UserCreate(UserBase):
    """用户创建Schema"""
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="密码，至少6字符"
    )
    confirm_password: str = Field(..., description="确认密码")

    @root_validator
    def validate_passwords_match(cls, values):
        """验证密码一致性"""
        password = values.get('password')
        confirm_password = values.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise ValueError('两次输入的密码不一致')
        return values

    @validator('password')
    def validate_password_strength(cls, v):
        """验证密码强度"""
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v

class UserUpdate(BaseSchema):
    """用户更新Schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

    @validator('full_name')
    def validate_full_name(cls, v):
        """验证全名"""
        if v is not None and len(v.strip()) == 0:
            raise ValueError('全名不能为空字符串')
        return v.strip() if v else v

class UserResponse(UserBase, IDMixin, TimestampMixin):
    """用户响应Schema"""
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否超级用户")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")

    # 排除敏感字段
    class Config:
        fields = {
            'password': {'write_only': True},
            'hashed_password': {'write_only': True}
        }

class UserListResponse(BaseSchema):
    """用户列表响应Schema"""
    users: List[UserResponse] = Field(..., description="用户列表")
    total: int = Field(..., description="总数", ge=0)
    page: int = Field(..., description="当前页", ge=1)
    page_size: int = Field(..., description="每页数量", ge=1)
```

## 🔍 验证器使用

### 1. 字段验证器

```python
from pydantic import validator, Field
import re

class ArticleSchema(BaseSchema):
    """文章Schema - 字段验证示例"""

    title: str = Field(..., min_length=1, max_length=200, description="标题")
    slug: str = Field(..., max_length=200, description="URL别名")
    content: str = Field(..., min_length=10, description="内容")
    tags: List[str] = Field(default=[], description="标签列表")

    @validator('slug')
    def validate_slug(cls, v):
        """验证URL别名格式"""
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('URL别名只能包含小写字母、数字和连字符')
        if v.startswith('-') or v.endswith('-'):
            raise ValueError('URL别名不能以连字符开头或结尾')
        return v

    @validator('tags')
    def validate_tags(cls, v):
        """验证标签"""
        if len(v) > 10:
            raise ValueError('标签数量不能超过10个')

        for tag in v:
            if len(tag) > 20:
                raise ValueError('单个标签长度不能超过20字符')
            if not re.match(r'^[a-zA-Z0-9\u4e00-\u9fa5]+$', tag):
                raise ValueError('标签只能包含字母、数字和中文')

        return list(set(v))  # 去重

    @validator('content')
    def validate_content(cls, v):
        """验证内容"""
        # 移除HTML标签进行长度验证
        import re
        clean_content = re.sub(r'<[^>]+>', '', v)
        if len(clean_content.strip()) < 10:
            raise ValueError('文章内容至少需要10个字符')
        return v
```

### 2. 根验证器

```python
from pydantic import root_validator
from datetime import datetime, date

class EventSchema(BaseSchema):
    """事件Schema - 根验证示例"""

    title: str = Field(..., description="事件标题")
    start_date: date = Field(..., description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    start_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")
    is_all_day: bool = Field(False, description="是否全天事件")

    @root_validator
    def validate_dates(cls, values):
        """验证日期逻辑"""
        start_date = values.get('start_date')
        end_date = values.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise ValueError('结束日期不能早于开始日期')

        return values

    @root_validator
    def validate_times(cls, values):
        """验证时间逻辑"""
        start_time = values.get('start_time')
        end_time = values.get('end_time')
        is_all_day = values.get('is_all_day')

        if is_all_day:
            # 全天事件不需要时间
            values['start_time'] = None
            values['end_time'] = None
        else:
            # 非全天事件需要时间
            if not start_time:
                raise ValueError('非全天事件必须设置开始时间')

        return values
```

### 3. 自定义验证器

```python
from pydantic import validator
from typing import Union

def validate_phone_number(phone: str) -> str:
    """手机号验证器"""
    import re

    # 移除所有非数字字符
    clean_phone = re.sub(r'\D', '', phone)

    # 验证中国手机号
    if not re.match(r'^1[3-9]\d{9}$', clean_phone):
        raise ValueError('请输入有效的中国手机号')

    return clean_phone

def validate_id_card(id_card: str) -> str:
    """身份证号验证器"""
    import re

    if not re.match(r'^\d{17}[\dXx]$', id_card):
        raise ValueError('身份证号格式不正确')

    # 这里可以添加更复杂的身份证校验逻辑
    return id_card.upper()

class PersonSchema(BaseSchema):
    """个人信息Schema - 自定义验证器示例"""

    name: str = Field(..., min_length=2, max_length=50, description="姓名")
    phone: str = Field(..., description="手机号")
    id_card: Optional[str] = Field(None, description="身份证号")
    age: int = Field(..., ge=0, le=150, description="年龄")

    # 使用自定义验证器
    _validate_phone = validator('phone', allow_reuse=True)(validate_phone_number)
    _validate_id_card = validator('id_card', allow_reuse=True)(validate_id_card)

    @validator('name')
    def validate_name(cls, v):
        """验证姓名"""
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z\s]+$', v):
            raise ValueError('姓名只能包含中文、英文和空格')
        return v.strip()
```

## 📊 复杂数据类型验证

### 1. 嵌套Schema

```python
from typing import List, Dict, Any

class AddressSchema(BaseSchema):
    """地址Schema"""
    province: str = Field(..., description="省份")
    city: str = Field(..., description="城市")
    district: str = Field(..., description="区县")
    street: str = Field(..., description="街道地址")
    postal_code: Optional[str] = Field(None, regex=r'^\d{6}$', description="邮政编码")

class ContactSchema(BaseSchema):
    """联系方式Schema"""
    phone: str = Field(..., description="手机号")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    wechat: Optional[str] = Field(None, description="微信号")

class UserProfileSchema(BaseSchema):
    """用户详细信息Schema - 嵌套示例"""

    user_id: int = Field(..., description="用户ID")
    address: AddressSchema = Field(..., description="地址信息")
    contacts: List[ContactSchema] = Field(..., description="联系方式列表")
    preferences: Dict[str, Any] = Field(default={}, description="用户偏好设置")

    @validator('contacts')
    def validate_contacts(cls, v):
        """验证联系方式"""
        if len(v) == 0:
            raise ValueError('至少需要一种联系方式')
        if len(v) > 5:
            raise ValueError('联系方式不能超过5个')
        return v

    @validator('preferences')
    def validate_preferences(cls, v):
        """验证偏好设置"""
        allowed_keys = {'theme', 'language', 'notifications', 'privacy'}
        invalid_keys = set(v.keys()) - allowed_keys
        if invalid_keys:
            raise ValueError(f'不支持的偏好设置: {invalid_keys}')
        return v
```

### 2. 联合类型验证

```python
from typing import Union
from pydantic import Field

class SearchSchema(BaseSchema):
    """搜索Schema - 联合类型示例"""

    query: Union[str, Dict[str, Any]] = Field(..., description="搜索条件")
    filters: Optional[Dict[str, Union[str, int, List[str]]]] = Field(
        None,
        description="过滤条件"
    )
    sort: Optional[Union[str, List[str]]] = Field(None, description="排序字段")

    @validator('query')
    def validate_query(cls, v):
        """验证搜索条件"""
        if isinstance(v, str):
            if len(v.strip()) < 2:
                raise ValueError('搜索关键词至少需要2个字符')
            return v.strip()
        elif isinstance(v, dict):
            if not v:
                raise ValueError('搜索条件不能为空')
            return v
        else:
            raise ValueError('搜索条件格式不正确')

    @validator('sort')
    def validate_sort(cls, v):
        """验证排序字段"""
        if isinstance(v, str):
            return [v]
        elif isinstance(v, list):
            allowed_fields = {'created_at', 'updated_at', 'name', 'id'}
            for field in v:
                clean_field = field.lstrip('-')  # 移除降序标记
                if clean_field not in allowed_fields:
                    raise ValueError(f'不支持的排序字段: {clean_field}')
            return v
        return v
```

## 🔄 Schema继承和复用

### 1. 基础继承模式

```python
class BaseArticleSchema(BaseSchema):
    """文章基础Schema"""
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    content: str = Field(..., min_length=10, description="内容")
    summary: Optional[str] = Field(None, max_length=500, description="摘要")

class ArticleCreateSchema(BaseArticleSchema):
    """文章创建Schema"""
    category_id: int = Field(..., gt=0, description="分类ID")
    tags: List[str] = Field(default=[], description="标签")

    @validator('tags')
    def validate_tags_count(cls, v):
        if len(v) > 10:
            raise ValueError('标签数量不能超过10个')
        return v

class ArticleUpdateSchema(BaseSchema):
    """文章更新Schema - 所有字段可选"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=10)
    summary: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = Field(None, gt=0)
    tags: Optional[List[str]] = None

    @root_validator
    def validate_at_least_one_field(cls, values):
        """至少更新一个字段"""
        if not any(v is not None for v in values.values()):
            raise ValueError('至少需要更新一个字段')
        return values

class ArticleResponseSchema(BaseArticleSchema, IDMixin, TimestampMixin):
    """文章响应Schema"""
    category_name: str = Field(..., description="分类名称")
    author_name: str = Field(..., description="作者名称")
    view_count: int = Field(..., description="浏览次数")
    status: str = Field(..., description="状态")
```

### 2. 动态Schema生成

```python
from typing import Type, TypeVar
from pydantic import create_model

T = TypeVar('T', bound=BaseSchema)

def create_partial_schema(base_schema: Type[T], exclude_fields: set = None) -> Type[T]:
    """创建部分更新Schema"""
    exclude_fields = exclude_fields or set()

    fields = {}
    for field_name, field_info in base_schema.__fields__.items():
        if field_name not in exclude_fields:
            # 将所有字段设为可选
            field_type = field_info.type_
            fields[field_name] = (Optional[field_type], None)

    return create_model(
        f"{base_schema.__name__}Partial",
        **fields,
        __base__=BaseSchema
    )

# 使用示例
UserPartialSchema = create_partial_schema(UserCreate, exclude_fields={'password'})
```

## 📝 最佳实践

### 1. Schema组织

```python
# schemas/user/__init__.py
from .create import UserCreateSchema
from .update import UserUpdateSchema
from .response import UserResponseSchema
from .list import UserListSchema

__all__ = [
    'UserCreateSchema',
    'UserUpdateSchema',
    'UserResponseSchema',
    'UserListSchema'
]
```

### 2. 错误处理

```python
from pydantic import ValidationError
from fastapi import HTTPException

def handle_validation_error(e: ValidationError):
    """处理验证错误"""
    errors = []
    for error in e.errors():
        errors.append({
            'field': '.'.join(str(x) for x in error['loc']),
            'message': error['msg'],
            'type': error['type']
        })

    raise HTTPException(
        status_code=422,
        detail={
            'message': '参数验证失败',
            'errors': errors
        }
    )
```

### 3. 性能优化

```python
class OptimizedSchema(BaseSchema):
    """性能优化的Schema"""

    class Config:
        # 验证赋值（谨慎使用）
        validate_assignment = False
        # 允许变更（提高性能）
        allow_mutation = True
        # 使用枚举值
        use_enum_values = True
        # 预编译正则表达式
        regex_engine = 'python-re'
```
