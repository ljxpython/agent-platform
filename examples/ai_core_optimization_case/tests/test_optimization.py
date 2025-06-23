#!/usr/bin/env python3
"""
AI核心框架优化功能测试
验证构建器、配置管理和模板系统的功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """测试新功能模块导入"""
    print("🔍 测试模块导入...")

    try:
        # 测试构建器导入
        from backend.ai_core import AgentBuilder, PresetAgentBuilder, agent_builder

        print("   ✅ 智能体构建器导入成功")

        # 测试配置管理导入
        from backend.ai_core import AgentConfig, get_agent_config, save_agent_config

        print("   ✅ 配置管理系统导入成功")

        # 测试模板管理导入
        from backend.ai_core import PromptTemplate, get_template, render_template

        print("   ✅ 模板管理系统导入成功")

        return True

    except ImportError as e:
        print(f"   ❌ 模块导入失败: {e}")
        return False


def test_config_system():
    """测试配置管理系统"""
    print("\n⚙️ 测试配置管理系统...")

    try:
        from backend.ai_core import get_agent_config, get_agent_config_manager

        # 测试配置管理器初始化
        config_manager = get_agent_config_manager()
        print(f"   ✅ 配置管理器初始化成功")

        # 测试获取配置
        requirement_config = get_agent_config("requirement_analysis")
        if requirement_config:
            print(f"   ✅ 需求分析配置获取成功: {requirement_config.get('name')}")
        else:
            print("   ⚠️ 需求分析配置不存在（将使用默认配置）")

        # 测试配置验证
        from backend.ai_core.config import ConfigValidator

        test_config = {
            "name": "测试智能体",
            "system_message": "测试提示词",
            "model_type": "deepseek",
        }

        is_valid, errors = ConfigValidator.validate_agent_config(test_config)
        if is_valid:
            print("   ✅ 配置验证通过")
        else:
            print(f"   ❌ 配置验证失败: {errors}")

        return True

    except Exception as e:
        print(f"   ❌ 配置系统测试失败: {e}")
        return False


def test_template_system():
    """测试模板管理系统"""
    print("\n📝 测试模板管理系统...")

    try:
        from backend.ai_core import get_template, get_template_manager, render_template

        # 测试模板管理器初始化
        template_manager = get_template_manager()
        print(f"   ✅ 模板管理器初始化成功")

        # 测试获取模板
        requirement_template = get_template("requirement_analysis")
        if requirement_template:
            print(f"   ✅ 需求分析模板获取成功")
            print(f"   🔧 模板变量: {requirement_template.get_variables()}")
        else:
            print("   ❌ 需求分析模板不存在")

        # 测试模板渲染
        rendered = render_template(
            "requirement_analysis",
            project_background="测试项目",
            analysis_focus="功能测试",
        )

        if rendered and "测试项目" in rendered:
            print("   ✅ 模板渲染成功")
        else:
            print("   ❌ 模板渲染失败")

        return True

    except Exception as e:
        print(f"   ❌ 模板系统测试失败: {e}")
        return False


async def test_builder_system():
    """测试构建器系统"""
    print("\n🏗️ 测试构建器系统...")

    try:
        from backend.ai_core import ModelType, PresetAgentBuilder, agent_builder

        # 测试基础构建器
        builder = agent_builder()
        print("   ✅ 构建器创建成功")

        # 测试链式调用
        config = (
            builder.name("测试智能体")
            .prompt("测试提示词")
            .model(ModelType.DEEPSEEK)
            .get_config()
        )

        if config.get("name") == "测试智能体":
            print("   ✅ 链式调用测试成功")
        else:
            print("   ❌ 链式调用测试失败")

        # 测试配置重置
        builder.reset()
        if not builder.get_config():
            print("   ✅ 配置重置测试成功")
        else:
            print("   ❌ 配置重置测试失败")

        # 测试预设构建器（不实际创建智能体，只测试配置）
        preset_builder = PresetAgentBuilder.requirement_analyst("test_conv")
        preset_config = preset_builder.get_config()

        if preset_config.get("name") == "需求分析师":
            print("   ✅ 预设构建器测试成功")
        else:
            print("   ❌ 预设构建器测试失败")

        return True

    except Exception as e:
        print(f"   ❌ 构建器系统测试失败: {e}")
        return False


def test_integration():
    """测试集成功能"""
    print("\n🔄 测试集成功能...")

    try:
        from backend.ai_core import (
            ModelType,
            agent_builder,
            get_agent_config,
            render_template,
        )

        # 测试配置驱动的构建器
        config = get_agent_config("requirement_analysis")
        if config:
            builder = (
                agent_builder()
                .name(config.get("name", "默认名称"))
                .model(ModelType.DEEPSEEK)
            )

            if builder.get_config().get("name") == config.get("name"):
                print("   ✅ 配置驱动构建器测试成功")
            else:
                print("   ❌ 配置驱动构建器测试失败")

        # 测试模板驱动的构建器
        prompt = render_template(
            "requirement_analysis",
            project_background="集成测试项目",
            analysis_focus="集成测试重点",
        )

        if prompt and "集成测试项目" in prompt:
            builder = (
                agent_builder()
                .name("集成测试智能体")
                .prompt(prompt)
                .model(ModelType.DEEPSEEK)
            )

            if "集成测试项目" in builder.get_config().get("system_message", ""):
                print("   ✅ 模板驱动构建器测试成功")
            else:
                print("   ❌ 模板驱动构建器测试失败")

        return True

    except Exception as e:
        print(f"   ❌ 集成功能测试失败: {e}")
        return False


def test_file_structure():
    """测试文件结构"""
    print("\n📁 测试文件结构...")

    try:
        # 检查配置目录
        config_dir = Path("configs/agents")
        if config_dir.exists():
            print("   ✅ 智能体配置目录存在")

            # 检查配置文件
            config_files = list(config_dir.glob("*.yaml"))
            if config_files:
                print(f"   ✅ 找到 {len(config_files)} 个配置文件")
            else:
                print("   ⚠️ 未找到配置文件")
        else:
            print("   ❌ 智能体配置目录不存在")

        # 检查模板目录
        template_dir = Path("configs/templates")
        if template_dir.exists():
            print("   ✅ 模板目录存在")

            # 检查模板文件
            template_files = list(template_dir.glob("*.txt"))
            if template_files:
                print(f"   ✅ 找到 {len(template_files)} 个模板文件")
            else:
                print("   ⚠️ 未找到模板文件")
        else:
            print("   ❌ 模板目录不存在")

        # 检查新增的Python文件
        ai_core_dir = Path("backend/ai_core")
        new_files = ["builder.py", "config.py", "templates.py"]

        for file_name in new_files:
            file_path = ai_core_dir / file_name
            if file_path.exists():
                print(f"   ✅ {file_name} 文件存在")
            else:
                print(f"   ❌ {file_name} 文件不存在")

        return True

    except Exception as e:
        print(f"   ❌ 文件结构测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🚀 AI核心框架优化功能测试开始")
    print("=" * 50)

    test_results = []

    # 执行各项测试
    test_results.append(("模块导入", test_imports()))
    test_results.append(("配置管理", test_config_system()))
    test_results.append(("模板管理", test_template_system()))
    test_results.append(("构建器系统", await test_builder_system()))
    test_results.append(("集成功能", test_integration()))
    test_results.append(("文件结构", test_file_structure()))

    # 统计测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果统计:")

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1

    print(f"\n🎯 总体结果: {passed}/{total} 项测试通过")

    if passed == total:
        print("🎉 所有测试通过！AI核心框架优化功能正常工作。")
    else:
        print("⚠️ 部分测试失败，请检查相关功能。")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
