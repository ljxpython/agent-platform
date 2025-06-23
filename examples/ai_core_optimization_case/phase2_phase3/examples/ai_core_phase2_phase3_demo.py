#!/usr/bin/env python3
"""
AI核心框架Phase 2&3功能演示
展示监控观测系统和扩展性增强功能
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.ai_core import (  # 监控观测系统; 扩展性增强系统; 装饰器系统
    BaseMiddleware,
    BasePlugin,
    MiddlewareContext,
    PluginInfo,
    TraceLevel,
    agent_operation,
    cache_result,
    debug_trace_decorator,
    get_agent_debugger,
    get_agent_monitor,
    get_middleware_manager,
    get_performance_logger,
    get_plugin_manager,
    get_structured_logger,
    monitor_performance,
    retry_on_failure,
    smart_agent_operation,
)


# ===== 演示智能体类 =====
class DemoAgent:
    """演示智能体"""

    def __init__(self, name: str):
        self.name = name
        self.conversation_id = "demo_conv_123"

    @agent_operation("process_message", enable_monitoring=True, enable_debug=True)
    async def process_message(self, message: str) -> str:
        """处理消息（带监控和调试）"""
        await asyncio.sleep(0.1)  # 模拟处理时间
        return f"[{self.name}] 处理结果: {message}"

    @monitor_performance("analyze_performance", tags={"agent_type": "demo"})
    async def analyze_data(self, data: str) -> dict:
        """分析数据（带性能监控）"""
        await asyncio.sleep(0.2)  # 模拟分析时间
        return {"analysis": f"分析了 {len(data)} 个字符", "status": "completed"}

    @cache_result(ttl=60)
    async def expensive_operation(self, input_data: str) -> str:
        """昂贵操作（带缓存）"""
        await asyncio.sleep(0.5)  # 模拟昂贵操作
        return f"昂贵操作结果: {input_data.upper()}"

    @retry_on_failure(max_retries=3, delay=0.1)
    async def unreliable_operation(self, should_fail: bool = False) -> str:
        """不可靠操作（带重试）"""
        if should_fail:
            raise Exception("模拟操作失败")
        return "操作成功"

    @smart_agent_operation(
        "complex_task",
        enable_cache=True,
        cache_ttl=30,
        enable_retry=True,
        max_retries=2,
    )
    async def complex_task(self, task_data: str) -> dict:
        """复杂任务（组合装饰器）"""
        await asyncio.sleep(0.3)
        return {
            "task": "complex_task",
            "input": task_data,
            "result": f"处理了复杂任务: {task_data}",
            "timestamp": time.time(),
        }


# ===== 演示插件 =====
class DemoPlugin(BasePlugin):
    """演示插件"""

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="demo_plugin",
            version="1.0.0",
            description="演示插件，展示插件系统功能",
            author="AI Core Team",
            dependencies=[],
        )

    async def initialize(self) -> bool:
        print("🔌 [演示插件] 插件初始化")

        # 注册钩子处理器
        self.register_hook("agent_created", self.on_agent_created)
        self.register_hook("operation_completed", self.on_operation_completed)

        return True

    async def cleanup(self) -> None:
        print("🔌 [演示插件] 插件清理")

    async def on_agent_created(self, agent_name: str, **kwargs):
        """智能体创建钩子"""
        print(f"🔌 [演示插件] 智能体已创建: {agent_name}")

    async def on_operation_completed(self, operation: str, **kwargs):
        """操作完成钩子"""
        print(f"🔌 [演示插件] 操作已完成: {operation}")


# ===== 演示中间件 =====
class DemoMiddleware(BaseMiddleware):
    """演示中间件"""

    def __init__(self):
        super().__init__("demo_middleware", priority=50)
        self.operation_count = 0

    async def before_operation(
        self, context: MiddlewareContext, *args, **kwargs
    ) -> bool:
        self.operation_count += 1
        print(
            f"🔧 [演示中间件] 操作前处理: {context.agent_name}.{context.operation} | 计数: {self.operation_count}"
        )
        context.metadata["demo_start_time"] = time.time()
        return True

    async def after_operation(
        self, context: MiddlewareContext, result, *args, **kwargs
    ):
        duration = time.time() - context.metadata.get("demo_start_time", 0)
        print(
            f"🔧 [演示中间件] 操作后处理: {context.agent_name}.{context.operation} | 耗时: {duration:.3f}s"
        )
        return result

    async def on_error(
        self, context: MiddlewareContext, error: Exception, *args, **kwargs
    ) -> bool:
        print(
            f"🔧 [演示中间件] 错误处理: {context.agent_name}.{context.operation} | 错误: {error}"
        )
        return False


# ===== 演示函数 =====
async def demo_monitoring_system():
    """演示监控观测系统"""
    print("\n📊 === 监控观测系统演示 ===")

    # 创建演示智能体
    agent = DemoAgent("MonitoringAgent")

    # 演示监控功能
    print("\n1. 智能体操作监控:")
    result1 = await agent.process_message("测试消息1")
    result2 = await agent.process_message("测试消息2")
    print(f"   结果1: {result1}")
    print(f"   结果2: {result2}")

    # 演示性能监控
    print("\n2. 性能监控:")
    analysis_result = await agent.analyze_data("这是一些测试数据")
    print(f"   分析结果: {analysis_result}")

    # 获取监控统计
    monitor = get_agent_monitor()
    stats = monitor.get_agent_stats("DemoAgent")
    if stats:
        print(f"\n📈 监控统计:")
        print(f"   总调用次数: {stats.total_calls}")
        print(f"   成功次数: {stats.successful_calls}")
        print(f"   平均耗时: {stats.avg_duration:.3f}s")
        print(f"   错误率: {stats.error_rate:.2%}")

    # 演示调试功能
    print("\n3. 调试跟踪:")
    debugger = get_agent_debugger()
    debugger.enable_debug(TraceLevel.INFO)

    await agent.process_message("调试测试消息")

    # 获取调试跟踪
    traces = debugger.get_traces(agent_name="DemoAgent", limit=3)
    print(f"   调试跟踪数量: {len(traces)}")
    for trace in traces:
        print(f"   - {trace.timestamp}: {trace.event_type} | {trace.message}")


async def demo_caching_and_retry():
    """演示缓存和重试功能"""
    print("\n💾 === 缓存和重试功能演示 ===")

    agent = DemoAgent("CacheAgent")

    # 演示缓存功能
    print("\n1. 缓存功能:")
    print("   第一次调用（会缓存）:")
    start_time = time.time()
    result1 = await agent.expensive_operation("测试数据")
    duration1 = time.time() - start_time
    print(f"   结果: {result1}")
    print(f"   耗时: {duration1:.3f}s")

    print("   第二次调用（从缓存获取）:")
    start_time = time.time()
    result2 = await agent.expensive_operation("测试数据")
    duration2 = time.time() - start_time
    print(f"   结果: {result2}")
    print(f"   耗时: {duration2:.3f}s")

    # 演示重试功能
    print("\n2. 重试功能:")
    print("   成功操作:")
    success_result = await agent.unreliable_operation(should_fail=False)
    print(f"   结果: {success_result}")

    print("   失败操作（会重试）:")
    try:
        await agent.unreliable_operation(should_fail=True)
    except Exception as e:
        print(f"   最终失败: {e}")


async def demo_plugin_system():
    """演示插件系统"""
    print("\n🔌 === 插件系统演示 ===")

    # 获取插件管理器
    plugin_manager = get_plugin_manager()

    # 加载演示插件
    print("\n1. 加载插件:")
    success = await plugin_manager.load_plugin("demo_plugin", DemoPlugin)
    print(f"   插件加载结果: {'成功' if success else '失败'}")

    # 列出插件
    plugins = plugin_manager.list_plugins()
    print(f"\n2. 已加载插件: {len(plugins)} 个")
    for plugin_info in plugins:
        print(
            f"   - {plugin_info['name']} v{plugin_info['version']}: {plugin_info['description']}"
        )

    # 触发钩子
    print("\n3. 触发插件钩子:")
    await plugin_manager.execute_hook("agent_created", "TestAgent")
    await plugin_manager.execute_hook("operation_completed", "test_operation")

    # 卸载插件
    print("\n4. 卸载插件:")
    unload_success = await plugin_manager.unload_plugin("demo_plugin")
    print(f"   插件卸载结果: {'成功' if unload_success else '失败'}")


async def demo_middleware_system():
    """演示中间件系统"""
    print("\n🔧 === 中间件系统演示 ===")

    # 获取中间件管理器
    middleware_manager = get_middleware_manager()

    # 添加演示中间件
    print("\n1. 添加中间件:")
    demo_middleware = DemoMiddleware()
    middleware_manager.add_middleware(demo_middleware)

    # 列出中间件
    middlewares = middleware_manager.list_middlewares()
    print(f"\n2. 已注册中间件: {len(middlewares)} 个")
    for mw in middlewares:
        print(f"   - {mw['name']} (优先级: {mw['priority']}, 启用: {mw['enabled']})")

    # 演示中间件执行
    print("\n3. 中间件执行演示:")
    agent = DemoAgent("MiddlewareAgent")

    # 执行带中间件的操作
    result = await agent.process_message("中间件测试消息")
    print(f"   操作结果: {result}")

    # 移除演示中间件
    print("\n4. 移除中间件:")
    remove_success = middleware_manager.remove_middleware("demo_middleware")
    print(f"   中间件移除结果: {'成功' if remove_success else '失败'}")


async def demo_complex_scenarios():
    """演示复杂场景"""
    print("\n🎯 === 复杂场景演示 ===")

    agent = DemoAgent("ComplexAgent")

    # 演示组合装饰器
    print("\n1. 组合装饰器（缓存+重试+监控）:")

    # 第一次调用
    print("   第一次调用:")
    result1 = await agent.complex_task("复杂任务数据")
    print(f"   结果: {result1}")

    # 第二次调用（应该从缓存获取）
    print("   第二次调用（缓存）:")
    result2 = await agent.complex_task("复杂任务数据")
    print(f"   结果: {result2}")

    # 获取性能摘要
    print("\n2. 性能摘要:")
    monitor = get_agent_monitor()
    summary = monitor.get_performance_summary()
    print(f"   总调用次数: {summary.get('total_calls', 0)}")
    print(f"   成功率: {summary.get('success_rate', 0):.2%}")
    print(f"   平均耗时: {summary.get('avg_duration', 0):.3f}s")

    # 获取调试摘要
    print("\n3. 调试摘要:")
    debugger = get_agent_debugger()
    debug_summary = debugger.get_debug_summary()
    print(f"   调试启用: {debug_summary['debug_enabled']}")
    print(f"   跟踪事件数: {debug_summary['total_traces']}")
    print(f"   活跃智能体数: {debug_summary['active_agents']}")


async def main():
    """主演示函数"""
    print("🚀 AI核心框架Phase 2&3功能演示")
    print("=" * 60)
    print("展示监控观测系统和扩展性增强功能")
    print("=" * 60)

    try:
        # 演示各个功能模块
        await demo_monitoring_system()
        await demo_caching_and_retry()
        await demo_plugin_system()
        await demo_middleware_system()
        await demo_complex_scenarios()

        print("\n" + "=" * 60)
        print("🎉 AI核心框架Phase 2&3功能演示完成！")

        print("\n📋 新功能特点总结:")
        print("   ✅ 智能体性能监控和统计")
        print("   ✅ 调试跟踪和错误诊断")
        print("   ✅ 结构化日志和性能日志")
        print("   ✅ 插件系统支持功能扩展")
        print("   ✅ 中间件系统处理横切关注点")
        print("   ✅ 装饰器简化开发和集成")
        print("   ✅ 缓存和重试机制提升可靠性")

        print("\n🔮 工程化收益:")
        print("   📊 完整的可观测性支持")
        print("   🔧 灵活的扩展机制")
        print("   🎯 简化的开发体验")
        print("   🛡️ 增强的系统可靠性")

    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        print(f"   🐛 错误类型: {type(e).__name__}")


if __name__ == "__main__":
    asyncio.run(main())
