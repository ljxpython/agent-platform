"""
系统管理控制器
"""

from typing import List, Optional, Tuple

from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q

from backend.core.crud import CRUDBase
from backend.models import Api, Department, Role, User
from backend.schemas.system import (
    ApiCreate,
    ApiUpdate,
    DepartmentCreate,
    DepartmentUpdate,
    RoleCreate,
    RoleUpdate,
    UserCreate,
    UserUpdate,
)
from backend.utils.password import hash_password


class UserController(CRUDBase[User, UserCreate, UserUpdate]):
    """用户控制器"""

    def __init__(self):
        super().__init__(User)

    async def create_user(self, obj_in: UserCreate) -> User:
        """创建用户"""
        obj_data = obj_in.model_dump(exclude={"password", "role_ids"})
        obj_data["password_hash"] = hash_password(obj_in.password)

        user = await self.model.create(**obj_data)
        return user

    async def update_roles(self, user: User, role_ids: List[int]):
        """更新用户角色"""
        await user.roles.clear()
        if role_ids:
            roles = await Role.filter(id__in=role_ids)
            await user.roles.add(*roles)

    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        try:
            return await self.model.get(email=email)
        except DoesNotExist:
            return None

    async def reset_password(self, user_id: int, new_password: str = "123456"):
        """重置密码"""
        user = await self.get(id=user_id)
        user.password_hash = hash_password(new_password)
        await user.save()
        return user

    async def list_with_dept_roles(
        self, page: int = 1, page_size: int = 10, search: Q = None
    ) -> Tuple[int, List[User]]:
        """获取用户列表（包含部门和角色信息）"""
        query = self.model.all()
        if search:
            query = query.filter(search)

        total = await query.count()
        users = (
            await query.prefetch_related("dept", "roles")
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        return total, users


class RoleController(CRUDBase[Role, RoleCreate, RoleUpdate]):
    """角色控制器"""

    def __init__(self):
        super().__init__(Role)

    async def update_apis(self, role: Role, api_ids: List[int]):
        """更新角色API权限"""
        await role.apis.clear()
        if api_ids:
            apis = await Api.filter(id__in=api_ids)
            await role.apis.add(*apis)

    async def is_exist(self, name: str) -> bool:
        """检查角色名是否存在"""
        return await self.model.filter(name=name).exists()

    async def list_with_apis(
        self, page: int = 1, page_size: int = 10, search: Q = None
    ) -> Tuple[int, List[Role]]:
        """获取角色列表（包含API权限）"""
        query = self.model.all()
        if search:
            query = query.filter(search)

        total = await query.count()
        roles = (
            await query.prefetch_related("apis")
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        return total, roles


class DepartmentController(CRUDBase[Department, DepartmentCreate, DepartmentUpdate]):
    """部门控制器"""

    def __init__(self):
        super().__init__(Department)

    async def list_tree(self) -> List[Department]:
        """获取部门树形结构"""
        departments = await self.model.all().prefetch_related("children", "users")

        # 构建树形结构
        dept_dict = {dept.id: dept for dept in departments}
        root_depts = []

        for dept in departments:
            if dept.parent_id is None:
                root_depts.append(dept)
            else:
                parent = dept_dict.get(dept.parent_id)
                if parent:
                    if not hasattr(parent, "_children"):
                        parent._children = []
                    parent._children.append(dept)

        return root_depts

    async def get_children(self, dept_id: int) -> List[Department]:
        """获取子部门"""
        return await self.model.filter(parent_id=dept_id)

    async def get_users_count(self, dept_id: int) -> int:
        """获取部门用户数量"""
        return await User.filter(dept_id=dept_id).count()


class ApiController(CRUDBase[Api, ApiCreate, ApiUpdate]):
    """API控制器"""

    def __init__(self):
        super().__init__(Api)

    async def is_exist(self, path: str, method: str) -> bool:
        """检查API是否存在"""
        return await self.model.filter(path=path, method=method).exists()

    async def sync_apis(self, api_list: List[dict]):
        """同步API列表"""
        # 获取现有API
        existing_apis = await self.model.all()
        existing_set = {(api.path, api.method) for api in existing_apis}

        # 新增API
        new_apis = []
        for api_info in api_list:
            key = (api_info["path"], api_info["method"])
            if key not in existing_set:
                new_apis.append(Api(**api_info))

        if new_apis:
            await Api.bulk_create(new_apis)

        # 删除不存在的API
        current_set = {(api["path"], api["method"]) for api in api_list}
        to_delete = existing_set - current_set

        if to_delete:
            for path, method in to_delete:
                await self.model.filter(path=path, method=method).delete()


# 创建全局实例
user_controller = UserController()
role_controller = RoleController()
department_controller = DepartmentController()
api_controller = ApiController()
