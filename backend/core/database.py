import os

from fastapi import FastAPI
from loguru import logger
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from backend.conf.config import settings
from backend.conf.constants import backend_path

# 数据库配置 - 使用constants.py中定义的路径
data_dir = backend_path / "data"
db_file = data_dir / "aitestlab.db"
DATABASE_URL = f"sqlite://{db_file}"

# Tortoise ORM 配置
TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": [
                "backend.models.user",
                "backend.models.chat",
                "backend.models.testcase",
                "backend.models.midscene",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}


async def init_db():
    """初始化数据库"""
    try:
        # 确保数据目录存在
        logger.info(f"数据目录: {data_dir}")
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建数据目录: {data_dir}")

        # 初始化 Tortoise ORM
        await Tortoise.init(config=TORTOISE_ORM)
        logger.info("Tortoise ORM 初始化成功")

        # 生成数据库表
        await Tortoise.generate_schemas()
        logger.info("数据库表生成成功")

        # 创建默认用户
        await create_default_user()

        logger.success("🚀 数据库初始化完成")

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def init_data():
    """初始化应用数据 - 从init_app.py迁移过来"""
    logger.info("开始初始化应用数据...")

    try:
        # 初始化数据库
        logger.debug("初始化数据库连接...")
        await init_db()

        # 预热缓存
        logger.debug("预热应用缓存...")
        # 这里可以添加缓存预热逻辑

        # 检查外部服务连接
        logger.debug("检查外部服务连接...")
        # 这里可以添加外部服务检查逻辑

        logger.success("🚀 应用数据初始化完成")
    except Exception as e:
        logger.error(f"应用数据初始化失败: {e}")
        raise


async def create_default_user():
    """创建默认用户"""
    try:
        from backend.models.user import User

        # 检查是否已存在默认用户
        existing_user = await User.get_or_none(username="test")
        if existing_user:
            logger.info("默认用户已存在")
            return

        # 创建默认用户
        default_user = User(
            username="test",
            email="test@example.com",
            full_name="测试用户",
            is_active=True,
            is_superuser=True,
        )
        default_user.set_password("test")
        await default_user.save()

        logger.success("默认用户创建成功:")
        logger.info("  用户名: test")
        logger.info("  密码: test")
        logger.info("  邮箱: test@example.com")

    except Exception as e:
        logger.error(f"创建默认用户失败: {e}")
        raise


async def close_db():
    """关闭数据库连接"""
    try:
        await Tortoise.close_connections()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {e}")


def setup_database(app: FastAPI):
    """设置数据库"""
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
        add_exception_handlers=True,
    )
