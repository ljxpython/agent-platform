"""
CRUD操作示例

展示如何使用backend/api_core/crud.py中的CRUDBase类进行数据库操作
"""

import asyncio
from typing import List, Optional

from tortoise import fields

from backend.api_core.crud import CRUDBase
from backend.api_core.exceptions import BusinessError
from backend.api_core.response import response
from backend.models.base import BaseModel
from backend.schemas.base import BaseSchema

# ==================== 模型定义示例 ====================


class User(BaseModel):
    """用户模型示例"""

    username = fields.CharField(max_length=50, unique=True, description="用户名")
    email = fields.CharField(max_length=255, unique=True, description="邮箱")
    full_name = fields.CharField(max_length=100, null=True, description="全名")
    is_active = fields.BooleanField(default=True, description="是否激活")

    class Meta:
        table = "users"


class Article(BaseModel):
    """文章模型示例"""

    title = fields.CharField(max_length=200, description="标题")
    content = fields.TextField(description="内容")
    author = fields.ForeignKeyField("models.User", related_name="articles")
    is_published = fields.BooleanField(default=False, description="是否发布")
    view_count = fields.IntField(default=0, description="浏览次数")

    class Meta:
        table = "articles"


# ==================== Schema定义示例 ====================

from pydantic import EmailStr, Field


class UserCreate(BaseSchema):
    """用户创建Schema"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(...)
    full_name: Optional[str] = Field(None, max_length=100)


class UserUpdate(BaseSchema):
    """用户更新Schema"""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class ArticleCreate(BaseSchema):
    """文章创建Schema"""

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)
    author_id: int = Field(..., gt=0)


class ArticleUpdate(BaseSchema):
    """文章更新Schema"""

    title: Optional[str] = None
    content: Optional[str] = None
    is_published: Optional[bool] = None


# ==================== 基础CRUD控制器 ====================


class UserController(CRUDBase[User, UserCreate, UserUpdate]):
    """用户控制器 - 基础CRUD示例"""

    def __init__(self):
        super().__init__(User)

    async def create_user(self, user_data: UserCreate):
        """创建用户"""
        # 检查用户名是否存在
        if await self.model.exists(username=user_data.username):
            raise BusinessError("用户名已存在", code=409)

        # 检查邮箱是否存在
        if await self.model.exists(email=user_data.email):
            raise BusinessError("邮箱已被注册", code=409)

        # 创建用户
        user = await self.create(user_data)
        return response.success(data=user, msg="用户创建成功", code=201)

    async def get_user_by_id(self, user_id: int):
        """根据ID获取用户"""
        user = await self.get(user_id)
        if not user:
            raise BusinessError("用户不存在", code=404)

        return response.success(data=user, msg="获取用户成功")

    async def get_users_paginated(self, page: int = 1, page_size: int = 20):
        """获取用户列表（分页）"""
        # 计算偏移量
        skip = (page - 1) * page_size

        # 获取用户列表和总数
        users = await self.get_multi(skip=skip, limit=page_size)
        total = await self.model.all().count()

        return response.success_with_pagination(
            data=users,
            total=total,
            page=page,
            page_size=page_size,
            msg="获取用户列表成功",
        )

    async def update_user(self, user_id: int, user_data: UserUpdate):
        """更新用户"""
        # 获取现有用户
        user = await self.get(user_id)
        if not user:
            raise BusinessError("用户不存在", code=404)

        # 如果更新邮箱，检查是否重复
        if user_data.email and user_data.email != user.email:
            if await self.model.exists(email=user_data.email):
                raise BusinessError("邮箱已被使用", code=409)

        # 更新用户
        updated_user = await self.update(user, user_data)
        return response.success(data=updated_user, msg="用户更新成功")

    async def delete_user(self, user_id: int):
        """删除用户"""
        user = await self.get(user_id)
        if not user:
            raise BusinessError("用户不存在", code=404)

        await self.delete(user_id)
        return response.success(msg="用户删除成功")

    async def get_active_users(self):
        """获取活跃用户"""
        users = await self.model.filter(is_active=True).all()
        return response.success(data=users, msg="获取活跃用户成功")


# ==================== 高级CRUD控制器 ====================


class ArticleController(CRUDBase[Article, ArticleCreate, ArticleUpdate]):
    """文章控制器 - 高级CRUD示例"""

    def __init__(self):
        super().__init__(Article)

    async def create_article(self, article_data: ArticleCreate):
        """创建文章"""
        # 验证作者是否存在
        author = await User.get_or_none(id=article_data.author_id)
        if not author:
            raise BusinessError("作者不存在", code=404)

        # 创建文章
        article = await self.create(article_data)

        # 预加载关联数据
        await article.fetch_related("author")

        return response.success(data=article, msg="文章创建成功", code=201)

    async def get_articles_by_author(
        self, author_id: int, page: int = 1, page_size: int = 10
    ):
        """获取作者的文章列表"""
        # 验证作者是否存在
        author = await User.get_or_none(id=author_id)
        if not author:
            raise BusinessError("作者不存在", code=404)

        # 计算偏移量
        skip = (page - 1) * page_size

        # 获取文章列表
        query = self.model.filter(author_id=author_id).select_related("author")
        total = await query.count()
        articles = await query.offset(skip).limit(page_size).all()

        return response.success_with_pagination(
            data=articles,
            total=total,
            page=page,
            page_size=page_size,
            msg="获取作者文章列表成功",
        )

    async def publish_article(self, article_id: int):
        """发布文章"""
        article = await self.get(article_id)
        if not article:
            raise BusinessError("文章不存在", code=404)

        if article.is_published:
            raise BusinessError("文章已发布", code=400)

        # 更新发布状态
        update_data = ArticleUpdate(is_published=True)
        updated_article = await self.update(article, update_data)

        return response.success(data=updated_article, msg="文章发布成功")

    async def increment_view_count(self, article_id: int):
        """增加文章浏览次数"""
        article = await self.get(article_id)
        if not article:
            raise BusinessError("文章不存在", code=404)

        # 直接更新数据库
        await self.model.filter(id=article_id).update(view_count=article.view_count + 1)

        # 重新获取更新后的文章
        updated_article = await self.get(article_id)
        return response.success(data=updated_article, msg="浏览次数更新成功")

    async def search_articles(self, keyword: str, page: int = 1, page_size: int = 10):
        """搜索文章"""
        from tortoise.expressions import Q

        # 构建搜索条件
        search_query = Q(title__icontains=keyword) | Q(content__icontains=keyword)

        # 计算偏移量
        skip = (page - 1) * page_size

        # 执行搜索
        query = self.model.filter(search_query, is_published=True).select_related(
            "author"
        )
        total = await query.count()
        articles = await query.offset(skip).limit(page_size).all()

        return response.success_with_pagination(
            data=articles,
            total=total,
            page=page,
            page_size=page_size,
            msg=f"搜索到 {total} 篇相关文章",
        )


# ==================== 批量操作示例 ====================


class BatchOperationController:
    """批量操作控制器"""

    def __init__(self):
        self.user_controller = UserController()
        self.article_controller = ArticleController()

    async def batch_create_users(self, users_data: List[UserCreate]):
        """批量创建用户"""
        created_users = []
        errors = []

        for i, user_data in enumerate(users_data):
            try:
                # 检查重复
                if await User.exists(username=user_data.username):
                    errors.append(f"第{i+1}个用户: 用户名已存在")
                    continue

                if await User.exists(email=user_data.email):
                    errors.append(f"第{i+1}个用户: 邮箱已被注册")
                    continue

                # 创建用户
                user = await self.user_controller.create(user_data)
                created_users.append(user)

            except Exception as e:
                errors.append(f"第{i+1}个用户: {str(e)}")

        return response.success(
            data={
                "created_count": len(created_users),
                "created_users": created_users,
                "errors": errors,
            },
            msg=f"批量创建完成，成功 {len(created_users)} 个，失败 {len(errors)} 个",
        )

    async def batch_update_user_status(self, user_ids: List[int], is_active: bool):
        """批量更新用户状态"""
        # 验证用户是否存在
        existing_users = await User.filter(id__in=user_ids).all()
        existing_ids = {user.id for user in existing_users}
        missing_ids = set(user_ids) - existing_ids

        if missing_ids:
            raise BusinessError(f"用户不存在: {missing_ids}", code=404)

        # 批量更新
        updated_count = await User.filter(id__in=user_ids).update(is_active=is_active)

        status_text = "激活" if is_active else "停用"
        return response.success(
            data={"updated_count": updated_count},
            msg=f"批量{status_text}用户成功，共 {updated_count} 个",
        )

    async def batch_delete_articles(self, article_ids: List[int]):
        """批量删除文章"""
        # 验证文章是否存在
        existing_articles = await Article.filter(id__in=article_ids).all()
        existing_ids = {article.id for article in existing_articles}
        missing_ids = set(article_ids) - existing_ids

        if missing_ids:
            raise BusinessError(f"文章不存在: {missing_ids}", code=404)

        # 批量删除
        deleted_count = await Article.filter(id__in=article_ids).delete()

        return response.success(
            data={"deleted_count": deleted_count},
            msg=f"批量删除文章成功，共 {deleted_count} 篇",
        )


# ==================== 使用示例 ====================


async def crud_examples():
    """CRUD操作示例"""

    # 创建控制器实例
    user_controller = UserController()
    article_controller = ArticleController()
    batch_controller = BatchOperationController()

    print("🚀 CRUD操作示例")

    try:
        # 1. 创建用户
        print("\n1. 创建用户")
        user_data = UserCreate(
            username="john_doe", email="john@example.com", full_name="John Doe"
        )
        result = await user_controller.create_user(user_data)
        print(f"创建用户结果: {result}")

        # 2. 获取用户列表
        print("\n2. 获取用户列表")
        users_result = await user_controller.get_users_paginated(page=1, page_size=10)
        print(f"用户列表: {users_result}")

        # 3. 创建文章
        print("\n3. 创建文章")
        article_data = ArticleCreate(
            title="Python编程入门",
            content="这是一篇关于Python编程的入门文章...",
            author_id=1,  # 假设用户ID为1
        )
        article_result = await article_controller.create_article(article_data)
        print(f"创建文章结果: {article_result}")

        # 4. 搜索文章
        print("\n4. 搜索文章")
        search_result = await article_controller.search_articles("Python")
        print(f"搜索结果: {search_result}")

        # 5. 批量操作
        print("\n5. 批量操作")
        batch_users = [
            UserCreate(username="user1", email="user1@example.com"),
            UserCreate(username="user2", email="user2@example.com"),
        ]
        batch_result = await batch_controller.batch_create_users(batch_users)
        print(f"批量创建结果: {batch_result}")

    except Exception as e:
        print(f"❌ 操作失败: {e}")


# ==================== 高级查询示例 ====================


class AdvancedQueryController:
    """高级查询控制器"""

    async def get_user_statistics(self):
        """获取用户统计信息"""
        total_users = await User.all().count()
        active_users = await User.filter(is_active=True).count()
        inactive_users = total_users - active_users

        return response.success(
            data={
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "active_rate": (
                    round(active_users / total_users * 100, 2) if total_users > 0 else 0
                ),
            },
            msg="获取用户统计成功",
        )

    async def get_article_statistics(self):
        """获取文章统计信息"""
        from tortoise.functions import Count, Sum

        # 基础统计
        total_articles = await Article.all().count()
        published_articles = await Article.filter(is_published=True).count()

        # 聚合查询
        stats = await Article.annotate(total_views=Sum("view_count")).values(
            "total_views"
        )

        total_views = stats[0]["total_views"] if stats else 0

        return response.success(
            data={
                "total_articles": total_articles,
                "published_articles": published_articles,
                "draft_articles": total_articles - published_articles,
                "total_views": total_views,
                "avg_views": (
                    round(total_views / total_articles, 2) if total_articles > 0 else 0
                ),
            },
            msg="获取文章统计成功",
        )

    async def get_top_authors(self, limit: int = 10):
        """获取发文最多的作者"""
        from tortoise.functions import Count

        authors = (
            await User.annotate(article_count=Count("articles"))
            .filter(article_count__gt=0)
            .order_by("-article_count")
            .limit(limit)
        )

        return response.success(data=authors, msg=f"获取前{limit}名作者成功")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(crud_examples())
