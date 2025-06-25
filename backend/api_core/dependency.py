"""
权限依赖注入管理
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, Request
from loguru import logger

from backend.api_core.ctx import CTX_CURRENT_USER, CTX_USER_ID
from backend.conf.config import settings
from backend.models.api import Api
from backend.models.role import Role
from backend.models.user import User


class AuthControl:
    """认证控制"""

    @classmethod
    async def is_authed(
        cls, authorization: str = Header(None, description="Bearer token")
    ) -> Optional[User]:
        """验证用户是否已认证"""
        try:
            # 检查Authorization头
            if not authorization:
                raise HTTPException(status_code=401, detail="缺少认证令牌")

            # 检查Bearer格式
            if not authorization.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="无效的认证令牌格式")

            # 提取token
            token = authorization.replace("Bearer ", "")

            # 开发模式支持
            if token == "dev" and settings.get("DEBUG", False):
                user = await User.filter().first()
                if not user:
                    raise HTTPException(status_code=401, detail="开发模式下未找到用户")
                user_id = user.id
            else:
                # 使用现有的JWT工具进行解码
                try:
                    from backend.api_core.security import decode_access_token

                    logger.debug(f"开始解码JWT令牌: {token[:20]}...")
                    decode_data = decode_access_token(token)
                    logger.debug(f"JWT解码成功: {decode_data}")

                    # 检查解码结果
                    if not decode_data:
                        logger.warning("JWT解码返回空结果")
                        raise HTTPException(status_code=401, detail="令牌解码失败")

                    # 获取用户ID，兼容不同的字段名
                    user_id = (
                        decode_data.get("sub")
                        or decode_data.get("user_id")
                        or decode_data.get("id")
                    )
                    logger.debug(f"从JWT中提取的用户ID: {user_id}")

                    if not user_id:
                        logger.warning(f"JWT中缺少用户ID信息: {decode_data}")
                        raise HTTPException(
                            status_code=401, detail="令牌中缺少用户信息"
                        )

                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"JWT解码失败: {e}")
                    logger.debug(f"JWT解码异常详情: {type(e).__name__}: {str(e)}")
                    raise HTTPException(status_code=401, detail="无效的令牌")

            # 获取用户信息
            user = (
                await User.filter(id=user_id).prefetch_related("dept", "roles").first()
            )
            if not user:
                raise HTTPException(status_code=401, detail="用户不存在")

            if not user.is_active:
                raise HTTPException(status_code=401, detail="用户已被禁用")

            # 设置上下文
            CTX_USER_ID.set(int(user_id))
            CTX_CURRENT_USER.set(user)

            logger.debug(f"用户认证成功: {user.username} (ID: {user.id})")
            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"认证过程中发生错误: {e}")
            raise HTTPException(status_code=500, detail="认证服务异常")


class PermissionControl:
    """权限控制"""

    @classmethod
    async def has_permission(
        cls, request: Request, current_user: User = Depends(AuthControl.is_authed)
    ) -> None:
        """检查用户是否有权限访问当前接口"""
        try:
            # 超级用户跳过权限检查
            if current_user.is_superuser:
                logger.debug(f"超级用户 {current_user.username} 跳过权限检查")
                return

            method = request.method
            path = request.url.path

            logger.debug(f"权限检查: {method} {path} - 用户: {current_user.username}")

            # 获取用户角色
            roles = await current_user.roles.all()
            if not roles:
                logger.warning(f"用户 {current_user.username} 未绑定任何角色")
                raise HTTPException(status_code=403, detail="用户未绑定角色，无法访问")

            # 获取所有角色的API权限
            permission_apis = set()
            for role in roles:
                if not role.is_active:
                    continue
                apis = await role.apis.all()
                for api in apis:
                    if api.is_active:
                        permission_apis.add((api.method, api.path))

            logger.debug(
                f"用户 {current_user.username} 拥有的API权限: {permission_apis}"
            )

            # 检查当前请求是否在权限列表中
            if (method, path) not in permission_apis:
                logger.warning(
                    f"用户 {current_user.username} 无权限访问: {method} {path}"
                )
                raise HTTPException(
                    status_code=403, detail=f"权限不足，无法访问 {method} {path}"
                )

            logger.debug(f"用户 {current_user.username} 权限检查通过: {method} {path}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"权限检查过程中发生错误: {e}")
            raise HTTPException(status_code=500, detail="权限检查服务异常")


class AdminPermissionControl:
    """管理员权限控制"""

    @classmethod
    async def is_admin(
        cls, current_user: User = Depends(AuthControl.is_authed)
    ) -> User:
        """检查用户是否为管理员"""
        if not current_user.is_superuser:
            logger.warning(f"非管理员用户 {current_user.username} 尝试访问管理员接口")
            raise HTTPException(status_code=403, detail="需要管理员权限")

        logger.debug(f"管理员 {current_user.username} 权限检查通过")
        return current_user


# 依赖注入实例
DependAuth = Depends(AuthControl.is_authed)
DependPermission = Depends(PermissionControl.has_permission)
DependAdmin = Depends(AdminPermissionControl.is_admin)

# 仅认证，不检查权限
DependAuthOnly = Depends(AuthControl.is_authed)
