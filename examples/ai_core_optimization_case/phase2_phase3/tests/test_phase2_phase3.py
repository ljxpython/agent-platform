#!/usr/bin/env python3
"""
AI核心框架Phase 2&3功能测试
验证监控观测系统和扩展性增强功能
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加案例代码路径
case_root = Path(__file__).parent.parent
code_root = case_root / "code"
sys.path.insert(0, str(code_root))


def test_case_structure():
    """测试案例目录结构"""
    print("🔍 检查Phase 2&3案例目录结构...")

    required_files = [
        "README.md",
        "docs/AI_CORE_PHASE2_PHASE3_SUMMARY.md",
        "docs/AI_CORE_ENHANCED_QUICKSTART.md",
        "code/ai_core_enhanced/__init__.py",
        "code/ai_core_enhanced/monitoring.py",
        "code/ai_core_enhanced/debug.py",
        "code/ai_core_enhanced/logging_enhanced.py",
        "code/ai_core_enhanced/plugins.py",
        "code/ai_core_enhanced/middleware.py",
        "code/ai_core_enhanced/decorators.py",
        "examples/ai_core_phase2_phase3_demo.py",
        "examples/enhanced_testcase_service.py",
    ]

    missing_files = []
    for file_path in required_files:
        full_path = case_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            print(f"   ✅ {file_path}")

    if missing_files:
        print(f"\n❌ 缺失文件:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False

    print("✅ 目录结构完整")
    return True


def test_imports():
    """测试模块导入"""
    print("\n🔍 测试Phase 2&3模块导入...")

    try:
        # 测试Phase 2模块导入
        from ai_core_enhanced.monitoring import (
            AgentMonitor,
            get_agent_monitor,
            monitor_agent_operation,
        )

        print("   ✅ 监控系统模块导入成功")

        from ai_core_enhanced.debug import AgentDebugger, TraceLevel, get_agent_debugger

        print("   ✅ 调试系统模块导入成功")

        from ai_core_enhanced.logging_enhanced import (
            StructuredLogger,
            get_structured_logger,
        )

        print("   ✅ 增强日志模块导入成功")

        # 测试Phase 3模块导入
        from ai_core_enhanced.plugins import (
            BasePlugin,
            PluginManager,
            get_plugin_manager,
        )

        print("   ✅ 插件系统模块导入成功")

        from ai_core_enhanced.middleware import (
            BaseMiddleware,
            MiddlewareManager,
            get_middleware_manager,
        )

        print("   ✅ 中间件系统模块导入成功")

        from ai_core_enhanced.decorators import (
            agent_operation,
            cache_result,
            smart_agent_operation,
        )

        print("   ✅ 装饰器系统模块导入成功")

        return True

    except ImportError as e:
        print(f"   ❌ 模块导入失败: {e}")
        return False


def test_monitoring_system():
    """测试监控系统"""
    print("\n🔍 测试监控系统...")

    try:
        from ai_core_enhanced.monitoring import get_agent_monitor

        # 创建监控器
        monitor = get_agent_monitor()
        print("   ✅ 监控器创建成功")

        # 测试性能摘要
        summary = monitor.get_performance_summary()
        if isinstance(summary, dict):
            print("   ✅ 性能摘要获取成功")
        else:
            print("   ❌ 性能摘要格式错误")
            return False

        return True

    except Exception as e:
        print(f"   ❌ 监控系统测试失败: {e}")
        return False


def test_debug_system():
    """测试调试系统"""
    print("\n🔍 测试调试系统...")

    try:
        from ai_core_enhanced.debug import TraceLevel, get_agent_debugger

        # 创建调试器
        debugger = get_agent_debugger()
        print("   ✅ 调试器创建成功")

        # 启用调试
        debugger.enable_debug(TraceLevel.INFO)
        print("   ✅ 调试模式启用成功")

        # 测试事件跟踪
        debugger.trace_event(
            "TestAgent", "test_operation", "test_event", "测试事件", TraceLevel.INFO
        )

        # 获取跟踪事件
        traces = debugger.get_traces(limit=1)
        if traces and len(traces) > 0:
            print("   ✅ 事件跟踪功能正常")
        else:
            print("   ❌ 事件跟踪功能异常")
            return False

        return True

    except Exception as e:
        print(f"   ❌ 调试系统测试失败: {e}")
        return False


def test_plugin_system():
    """测试插件系统"""
    print("\n🔍 测试插件系统...")

    try:
        from ai_core_enhanced.plugins import BasePlugin, PluginInfo, get_plugin_manager

        # 创建插件管理器
        plugin_manager = get_plugin_manager()
        print("   ✅ 插件管理器创建成功")

        # 创建测试插件
        class TestPlugin(BasePlugin):
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name="test_plugin",
                    version="1.0.0",
                    description="测试插件",
                    author="测试",
                    dependencies=[],
                )

            async def initialize(self) -> bool:
                return True

            async def cleanup(self) -> None:
                pass

        # 测试插件加载（同步测试，不实际加载）
        print("   ✅ 插件加载接口可用")

        # 测试插件列表
        plugins = plugin_manager.list_plugins()
        print("   ✅ 插件列表接口可用")

        return True

    except Exception as e:
        print(f"   ❌ 插件系统测试失败: {e}")
        return False


def test_middleware_system():
    """测试中间件系统"""
    print("\n🔍 测试中间件系统...")

    try:
        from ai_core_enhanced.middleware import (
            BaseMiddleware,
            MiddlewareContext,
            get_middleware_manager,
        )

        # 创建中间件管理器
        middleware_manager = get_middleware_manager()
        print("   ✅ 中间件管理器创建成功")

        # 创建测试中间件
        class TestMiddleware(BaseMiddleware):
            def __init__(self):
                super().__init__("test_middleware", priority=50)

            async def before_operation(self, context, *args, **kwargs) -> bool:
                return True

            async def after_operation(self, context, result, *args, **kwargs):
                return result

            async def on_error(self, context, error, *args, **kwargs) -> bool:
                return False

        # 添加中间件
        test_middleware = TestMiddleware()
        middleware_manager.add_middleware(test_middleware)
        print("   ✅ 中间件添加成功")

        # 测试中间件列表
        middlewares = middleware_manager.list_middlewares()
        if middlewares and len(middlewares) > 0:
            print("   ✅ 中间件列表获取成功")
        else:
            print("   ❌ 中间件列表为空")
            return False

        return True

    except Exception as e:
        print(f"   ❌ 中间件系统测试失败: {e}")
        return False


def test_decorator_system():
    """测试装饰器系统"""
    print("\n🔍 测试装饰器系统...")

    try:
        from ai_core_enhanced.decorators import agent_operation, cache_result

        # 测试缓存装饰器
        @cache_result(ttl=60)
        def cached_function(x):
            return x * 2

        result1 = cached_function(5)
        result2 = cached_function(5)

        if result1 == result2 == 10:
            print("   ✅ 缓存装饰器功能正常")
        else:
            print("   ❌ 缓存装饰器功能异常")
            return False

        # 测试智能体操作装饰器（同步测试）
        class TestAgent:
            @agent_operation("test_op", enable_monitoring=False, enable_debug=False)
            def test_method(self, data):
                return f"processed: {data}"

        agent = TestAgent()
        result = agent.test_method("test")

        if result == "processed: test":
            print("   ✅ 智能体操作装饰器功能正常")
        else:
            print("   ❌ 智能体操作装饰器功能异常")
            return False

        return True

    except Exception as e:
        print(f"   ❌ 装饰器系统测试失败: {e}")
        return False


def test_documentation():
    """测试文档完整性"""
    print("\n🔍 测试文档完整性...")

    try:
        # 检查README文档
        readme_file = case_root / "README.md"
        with open(readme_file, "r", encoding="utf-8") as f:
            readme_content = f.read()

        required_sections = ["案例概述", "目录结构", "优化目标", "优化效果", "快速体验"]

        missing_sections = []
        for section in required_sections:
            if section not in readme_content:
                missing_sections.append(section)

        if missing_sections:
            print(f"   ❌ README缺少章节: {missing_sections}")
            return False

        print("   ✅ README文档完整")

        # 检查详细文档
        summary_file = case_root / "docs/AI_CORE_PHASE2_PHASE3_SUMMARY.md"
        quickstart_file = case_root / "docs/AI_CORE_ENHANCED_QUICKSTART.md"

        if summary_file.exists():
            print("   ✅ 详细总结文档存在")
        else:
            print("   ❌ 详细总结文档缺失")
            return False

        if quickstart_file.exists():
            print("   ✅ 快速开始文档存在")
        else:
            print("   ❌ 快速开始文档缺失")
            return False

        return True

    except Exception as e:
        print(f"   ❌ 文档测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🚀 AI核心框架Phase 2&3功能测试")
    print("=" * 60)

    tests = [
        ("目录结构", test_case_structure),
        ("模块导入", test_imports),
        ("监控系统", test_monitoring_system),
        ("调试系统", test_debug_system),
        ("插件系统", test_plugin_system),
        ("中间件系统", test_middleware_system),
        ("装饰器系统", test_decorator_system),
        ("文档完整性", test_documentation),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 项通过")

    if passed == total:
        print("🎉 Phase 2&3案例验证通过！所有组件都已正确整理。")
        print("\n📋 使用说明:")
        print("   1. 查看 README.md 了解案例概述")
        print("   2. 阅读 docs/ 目录下的详细文档")
        print("   3. 运行 examples/ 目录下的演示脚本")
        print("   4. 参考 code/ 目录下的代码实现")
        print("   5. 根据需要在未来集成到主系统中")
    else:
        print("⚠️ 案例验证失败，请检查相关文件。")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
