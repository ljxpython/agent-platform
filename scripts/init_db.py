#!/usr/bin/env python3
"""
数据库初始化脚本
使用Aerich进行数据库迁移管理
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from tortoise import Tortoise

from backend.api_core.database import TORTOISE_ORM, init_data


async def init_aerich():
    """初始化Aerich"""
    logger.info("🔧 初始化Aerich...")

    try:
        # 检查是否已经初始化过
        migrations_dir = project_root / "migrations"
        if migrations_dir.exists():
            logger.info("Aerich已经初始化过，跳过初始化步骤")
            return

        # 运行aerich init命令
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "aerich",
                "init",
                "-t",
                "backend.core.database.TORTOISE_ORM",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.success("✅ Aerich初始化成功")
        else:
            logger.error(f"❌ Aerich初始化失败: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"❌ Aerich初始化异常: {e}")
        return False

    return True


async def create_initial_migration():
    """创建初始迁移"""
    logger.info("📝 创建初始迁移...")

    try:
        import subprocess

        result = subprocess.run(
            [sys.executable, "-m", "aerich", "init-db"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.success("✅ 初始迁移创建成功")
            logger.info(result.stdout)
        else:
            logger.error(f"❌ 初始迁移创建失败: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"❌ 创建初始迁移异常: {e}")
        return False

    return True


async def run_migrations():
    """运行数据库迁移"""
    logger.info("🚀 运行数据库迁移...")

    try:
        import subprocess

        result = subprocess.run(
            [sys.executable, "-m", "aerich", "upgrade"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.success("✅ 数据库迁移完成")
            if result.stdout:
                logger.info(result.stdout)
        else:
            logger.error(f"❌ 数据库迁移失败: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"❌ 数据库迁移异常: {e}")
        return False

    return True


async def create_default_data():
    """创建默认数据"""
    logger.info("📊 创建默认数据...")

    try:
        # 初始化Tortoise ORM
        await Tortoise.init(config=TORTOISE_ORM)

        # 创建默认用户
        from backend.models.user import User

        existing_user = await User.get_or_none(username="admin")
        if not existing_user:
            admin_user = User(
                username="admin",
                email="admin@aitestlab.com",
                full_name="系统管理员",
                is_active=True,
                is_superuser=True,
            )
            admin_user.set_password("admin123")
            await admin_user.save()
            logger.success("✅ 创建默认管理员用户: admin/admin123")

        # 创建测试用例模板
        from backend.models.testcase import TestCaseTemplate

        existing_template = await TestCaseTemplate.get_or_none(name="标准功能测试模板")
        if not existing_template:
            template = TestCaseTemplate(
                name="标准功能测试模板",
                description="适用于一般功能测试的标准模板",
                category="功能测试",
                template_content="""
## 测试用例模板

### 用例编号: TC_{序号}
### 用例标题: {功能名称}测试
### 测试类型: 功能测试
### 优先级: 高/中/低
### 前置条件:
- 系统正常运行
- 用户已登录

### 测试步骤:
1. 步骤1描述
2. 步骤2描述
3. 步骤3描述

### 预期结果:
- 期望的结果描述

### 后置条件:
- 清理测试数据
                """.strip(),
                is_active=True,
                is_default=True,
                sort_order=1,
            )
            await template.save()
            logger.success("✅ 创建默认测试用例模板")

        await Tortoise.close_connections()
        logger.success("✅ 默认数据创建完成")

    except Exception as e:
        logger.error(f"❌ 创建默认数据失败: {e}")
        return False

    return True


async def main():
    """主函数"""
    logger.info("🚀 开始数据库初始化...")

    try:
        # 1. 初始化Aerich
        if not await init_aerich():
            return False

        # 2. 创建初始迁移
        if not await create_initial_migration():
            return False

        # 3. 运行迁移
        if not await run_migrations():
            return False

        # 4. 创建默认数据
        if not await create_default_data():
            return False

        logger.success("🎉 数据库初始化完成！")
        logger.info("默认管理员账户: admin/admin123")
        return True

    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
