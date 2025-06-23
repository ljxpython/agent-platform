#!/usr/bin/env python3
"""
AI核心框架优化演示
展示新的构建器、配置管理和模板系统的使用方法
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.ai_core import (
    AgentBuilder,
    ModelType,
    PresetAgentBuilder,
    agent_builder,
    get_agent_config,
    get_template,
    render_template,
)


async def demo_agent_builder():
    """演示智能体构建器的使用"""
    print("\n🏗️ === 智能体构建器演示 ===")

    # 方式1: 链式API构建智能体
    print("\n1. 使用链式API构建智能体:")
    agent = await (
        agent_builder()
        .name("演示智能体")
        .prompt("你是一个演示用的AI助手，请友好地回应用户。")
        .model(ModelType.DEEPSEEK)
        .memory("demo_conversation_123")
        .build()
    )

    if agent:
        print(f"   ✅ 智能体创建成功: {agent.name}")
    else:
        print("   ❌ 智能体创建失败")

    # 方式2: 使用预设构建器
    print("\n2. 使用预设构建器:")
    requirement_agent = await PresetAgentBuilder.requirement_analyst(
        "demo_conv_456"
    ).build()

    if requirement_agent:
        print(f"   ✅ 需求分析师创建成功: {requirement_agent.name}")
    else:
        print("   ❌ 需求分析师创建失败")

    # 方式3: 批量配置
    print("\n3. 使用批量配置:")
    config = {
        "name": "批量配置智能体",
        "system_message": "你是通过批量配置创建的智能体。",
        "model_type": ModelType.DEEPSEEK,
        "conversation_id": "batch_conv_789",
    }

    batch_agent = await agent_builder().config_dict(config).build()

    if batch_agent:
        print(f"   ✅ 批量配置智能体创建成功: {batch_agent.name}")
    else:
        print("   ❌ 批量配置智能体创建失败")


def demo_config_management():
    """演示配置管理系统的使用"""
    print("\n⚙️ === 配置管理系统演示 ===")

    # 获取智能体配置
    print("\n1. 获取智能体配置:")
    requirement_config = get_agent_config("requirement_analysis")
    if requirement_config:
        print(f"   ✅ 需求分析配置: {requirement_config.get('name', '未知')}")
        print(f"   📝 模型类型: {requirement_config.get('model_type', '未知')}")
    else:
        print("   ⚠️ 需求分析配置不存在，将使用默认配置")

    testcase_config = get_agent_config("testcase_generation")
    if testcase_config:
        print(f"   ✅ 测试用例配置: {testcase_config.get('name', '未知')}")
        print(f"   📝 模型类型: {testcase_config.get('model_type', '未知')}")
    else:
        print("   ⚠️ 测试用例配置不存在，将使用默认配置")


def demo_template_system():
    """演示模板系统的使用"""
    print("\n📝 === 模板系统演示 ===")

    # 获取模板
    print("\n1. 获取和渲染模板:")
    requirement_template = get_template("requirement_analysis")
    if requirement_template:
        print(f"   ✅ 需求分析模板加载成功")
        print(f"   🔧 模板变量: {requirement_template.get_variables()}")

        # 渲染模板
        rendered_prompt = requirement_template.render(
            project_background="电商平台用户管理系统",
            analysis_focus="用户注册和登录流程的安全性",
        )
        print(f"   🎨 渲染结果预览: {rendered_prompt[:100]}...")
    else:
        print("   ❌ 需求分析模板不存在")

    # 使用便捷函数渲染模板
    print("\n2. 使用便捷函数渲染模板:")
    testcase_prompt = render_template(
        "testcase_generation",
        test_objective="验证用户注册功能",
        test_scope="用户注册表单和验证逻辑",
        quality_requirements="覆盖正常流程、异常流程和边界条件",
    )

    if testcase_prompt:
        print(f"   ✅ 测试用例模板渲染成功")
        print(f"   🎨 渲染结果预览: {testcase_prompt[:100]}...")
    else:
        print("   ❌ 测试用例模板渲染失败")


async def demo_integrated_usage():
    """演示集成使用场景"""
    print("\n🔄 === 集成使用演示 ===")

    # 场景：基于配置和模板创建智能体
    print("\n1. 基于配置和模板创建智能体:")

    # 获取配置
    config = get_agent_config("requirement_analysis")
    if not config:
        print("   ⚠️ 配置不存在，使用默认配置")
        config = {
            "name": "需求分析师",
            "model_type": "deepseek",
            "auto_memory": True,
            "auto_context": True,
        }

    # 渲染模板
    system_prompt = render_template(
        "requirement_analysis",
        project_background="移动端购物应用",
        analysis_focus="支付流程的用户体验和安全性",
    )

    if not system_prompt:
        system_prompt = "你是一位专业的需求分析师。"

    # 创建智能体
    agent = await (
        agent_builder()
        .name(config.get("name", "智能体"))
        .prompt(system_prompt)
        .model(ModelType.DEEPSEEK)
        .memory("integrated_demo_conv")
        .build()
    )

    if agent:
        print(f"   ✅ 集成智能体创建成功: {agent.name}")
        print(f"   📝 提示词长度: {len(system_prompt)} 字符")
    else:
        print("   ❌ 集成智能体创建失败")


def demo_builder_features():
    """演示构建器的高级功能"""
    print("\n🔧 === 构建器高级功能演示 ===")

    # 创建构建器
    builder = agent_builder()

    # 获取当前配置
    print("\n1. 构建器配置管理:")
    print(f"   📋 初始配置: {builder.get_config()}")

    # 设置配置
    builder.name("高级功能演示").prompt("演示提示词")
    print(f"   📋 设置后配置: {list(builder.get_config().keys())}")

    # 重置构建器
    builder.reset()
    print(f"   📋 重置后配置: {builder.get_config()}")

    # 链式调用演示
    print("\n2. 链式调用演示:")
    final_config = (
        builder.name("链式调用智能体")
        .prompt("通过链式调用创建的智能体")
        .model(ModelType.DEEPSEEK)
        .memory("chain_demo_conv")
        .kwargs(custom_param="自定义参数")
        .get_config()
    )

    print(f"   📋 最终配置: {list(final_config.keys())}")


async def main():
    """主函数"""
    print("🚀 AI核心框架优化演示开始")
    print("=" * 50)

    try:
        # 演示各个功能模块
        await demo_agent_builder()
        demo_config_management()
        demo_template_system()
        await demo_integrated_usage()
        demo_builder_features()

        print("\n" + "=" * 50)
        print("🎉 AI核心框架优化演示完成！")

        print("\n📊 优化效果总结:")
        print("   ✅ 智能体创建更加简洁和直观")
        print("   ✅ 配置管理统一和标准化")
        print("   ✅ 模板系统支持动态参数")
        print("   ✅ 链式API提升开发体验")
        print("   ✅ 预设构建器减少重复代码")

    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        print(f"   🐛 错误类型: {type(e).__name__}")


if __name__ == "__main__":
    asyncio.run(main())
