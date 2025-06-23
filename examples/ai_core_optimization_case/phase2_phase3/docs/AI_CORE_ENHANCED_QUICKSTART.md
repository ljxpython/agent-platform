# AI核心框架增强功能快速开始指南

[← 返回指南目录](../) | [📖 文档中心](../) | [📋 导航索引](../DOCS_INDEX.md)

## 🚀 概述

本指南将帮助你快速上手AI核心框架的增强功能，包括监控观测系统和扩展性增强功能。

## 📦 功能导入

```python
from backend.ai_core import (
    # 监控观测系统
    get_agent_monitor,
    get_agent_debugger,
    get_structured_logger,
    TraceLevel,

    # 扩展性增强系统
    get_plugin_manager,
    get_middleware_manager,
    BasePlugin,
    BaseMiddleware,

    # 装饰器系统
    agent_operation,
    smart_agent_operation,
    monitor_performance,
    cache_result,
    retry_on_failure,
)
```

## 🎯 快速使用

### 1. 智能体操作监控

最简单的方式是使用装饰器：

```python
class MyAgent:
    @agent_operation("process_message", enable_monitoring=True, enable_debug=True)
    async def process_message(self, message: str) -> str:
        # 自动记录性能指标和调试信息
        await asyncio.sleep(0.1)  # 模拟处理
        return f"处理结果: {message}"

# 使用
agent = MyAgent()
result = await agent.process_message("测试消息")

# 查看监控数据
monitor = get_agent_monitor()
stats = monitor.get_agent_stats("MyAgent")
print(f"调用次数: {stats.total_calls}")
print(f"平均耗时: {stats.avg_duration:.3f}s")
```

### 2. 性能监控

```python
@monitor_performance("data_analysis", tags={"type": "ml"})
async def analyze_data(data: str) -> dict:
    # 自动记录性能指标和内存使用
    await asyncio.sleep(0.2)
    return {"result": f"分析了 {len(data)} 个字符"}

# 使用
result = await analyze_data("测试数据")

# 查看性能日志
performance_logger = get_performance_logger()
# 性能指标会自动记录到 logs/performance.log
```

### 3. 结果缓存

```python
@cache_result(ttl=300)  # 5分钟缓存
async def expensive_operation(input_data: str) -> str:
    await asyncio.sleep(1.0)  # 模拟昂贵操作
    return f"昂贵操作结果: {input_data.upper()}"

# 第一次调用会执行完整操作
result1 = await expensive_operation("test")  # 耗时 1s

# 第二次调用从缓存获取
result2 = await expensive_operation("test")  # 耗时 < 1ms
```

### 4. 失败重试

```python
@retry_on_failure(max_retries=3, delay=0.1)
async def unreliable_operation(should_fail: bool = False) -> str:
    if should_fail:
        raise Exception("模拟操作失败")
    return "操作成功"

# 使用
try:
    result = await unreliable_operation(should_fail=True)
except Exception as e:
    print(f"最终失败: {e}")  # 会重试3次后失败
```

### 5. 组合装饰器

```python
@smart_agent_operation(
    "complex_task",
    enable_cache=True,      # 启用缓存
    cache_ttl=60,          # 1分钟缓存
    enable_retry=True,      # 启用重试
    max_retries=2,         # 最多重试2次
    enable_monitoring=True  # 启用监控
)
async def complex_task(self, task_data: str) -> dict:
    # 自动集成：缓存、重试、监控、调试
    await asyncio.sleep(0.3)
    return {
        "task": "complex_task",
        "input": task_data,
        "result": f"处理了复杂任务: {task_data}"
    }
```

## 🔧 自定义扩展

### 1. 自定义中间件

```python
class ValidationMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__("validation", priority=10)

    async def before_operation(self, context, *args, **kwargs) -> bool:
        # 操作前验证
        if not args or not args[0]:
            print(f"参数验证失败: {context.operation}")
            return False
        return True

    async def after_operation(self, context, result, *args, **kwargs):
        # 操作后处理
        print(f"操作完成: {context.operation}")
        return result

    async def on_error(self, context, error, *args, **kwargs) -> bool:
        # 错误处理
        print(f"操作失败: {context.operation} | 错误: {error}")
        return False

# 注册中间件
middleware_manager = get_middleware_manager()
middleware_manager.add_middleware(ValidationMiddleware())
```

### 2. 自定义插件

```python
class MyPlugin(BasePlugin):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="my_plugin",
            version="1.0.0",
            description="我的自定义插件",
            author="开发者",
            dependencies=[]
        )

    async def initialize(self) -> bool:
        print("插件初始化")
        # 注册钩子处理器
        self.register_hook("agent_created", self.on_agent_created)
        return True

    async def cleanup(self) -> None:
        print("插件清理")

    async def on_agent_created(self, agent_name: str, **kwargs):
        print(f"智能体已创建: {agent_name}")

# 加载插件
plugin_manager = get_plugin_manager()
await plugin_manager.load_plugin("my_plugin", MyPlugin)
```

## 📊 监控和调试

### 1. 启用调试模式

```python
# 启用调试
debugger = get_agent_debugger()
debugger.enable_debug(TraceLevel.INFO)

# 执行操作后查看调试信息
traces = debugger.get_traces(limit=5)
for trace in traces:
    print(f"{trace.timestamp}: {trace.event_type} | {trace.message}")
```

### 2. 查看性能统计

```python
# 获取性能摘要
monitor = get_agent_monitor()
summary = monitor.get_performance_summary()

print(f"总调用次数: {summary['total_calls']}")
print(f"成功率: {summary['success_rate']:.2%}")
print(f"平均耗时: {summary['avg_duration']:.3f}s")

# 获取最近的性能指标
recent_metrics = monitor.get_recent_metrics(limit=10)
for metric in recent_metrics:
    print(f"{metric.agent_name}.{metric.operation}: {metric.duration:.3f}s")
```

### 3. 结构化日志

```python
# 记录结构化日志
structured_logger = get_structured_logger()

# 记录智能体操作
structured_logger.log_agent_operation(
    "MyAgent", "process_data", "completed",
    duration=0.5, conversation_id="conv_123"
)

# 记录性能指标
structured_logger.log_performance("response_time", 0.3, "seconds")

# 记录结构化事件
structured_logger.log_structured("user_action", {
    "action": "login",
    "user_id": "user_123",
    "success": True
})
```

## 🎯 实际业务集成

### 增强现有服务

```python
class EnhancedTestCaseService:
    def __init__(self):
        # 设置中间件
        middleware_manager = get_middleware_manager()
        middleware_manager.add_middleware(ValidationMiddleware())

        # 启用调试
        debugger = get_agent_debugger()
        debugger.enable_debug(TraceLevel.INFO)

    @smart_agent_operation(
        "analyze_requirement",
        enable_cache=True,
        enable_retry=True,
        enable_monitoring=True
    )
    async def analyze_requirement(self, conversation_id: str, text: str) -> str:
        # 业务逻辑，自动集成所有增强功能
        agent = await self.create_agent(conversation_id)
        return await agent.analyze(text)

    @cache_result(ttl=300)
    async def get_service_stats(self) -> dict:
        # 获取服务统计信息（带缓存）
        monitor = get_agent_monitor()
        return monitor.get_performance_summary()
```

## 📁 日志文件说明

增强功能会自动创建以下日志文件：

```
logs/
├── agent_operations.log    # 智能体操作日志
├── performance.log         # 性能指标日志
├── errors.log             # 错误日志
└── structured.jsonl       # 结构化JSON日志
```

## ⚠️ 注意事项

### 1. 性能考虑
- 生产环境适当调整监控级别
- 合理设置缓存TTL避免内存泄漏
- 避免过度重试造成系统负载

### 2. 调试模式
- 开发环境启用详细调试
- 生产环境使用WARNING级别以上
- 定期清理调试数据

### 3. 中间件顺序
- 验证中间件优先级设置较高（数字较小）
- 日志中间件优先级设置较低（数字较大）
- 缓存中间件在验证之后

## 🔗 相关文档

- [AI核心框架Phase 2&3总结](../architecture/AI_CORE_PHASE2_PHASE3_SUMMARY.md)
- [后端架构文档](../architecture/BACKEND_ARCHITECTURE.md)
- [API文档](../api/)

## 🎉 开始使用

1. **运行演示**：`python examples/ai_core_phase2_phase3_demo.py`
2. **查看业务集成**：`python examples/enhanced_testcase_service.py`
3. **查看日志**：检查 `logs/` 目录下的日志文件
4. **自定义扩展**：参考上述示例创建自己的中间件和插件

---

**提示**：如果遇到问题，请查看日志文件获取详细信息，或参考演示代码了解正确用法。
