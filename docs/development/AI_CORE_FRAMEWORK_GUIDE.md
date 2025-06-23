# AI核心框架完整开发指南

[← 返回开发文档](../) | [📖 文档中心](../) | [📋 导航索引](../DOCS_INDEX.md)

## 🎯 概述

本文档是AI核心框架的完整开发指南，基于AutoGen 0.5.7构建，提供了智能体系统开发的全套解决方案。框架位于`backend/ai_core`目录，包含LLM客户端管理、智能体工厂、消息队列、内存管理、运行时管理等核心组件。

## 📁 框架结构

```
backend/ai_core/
├── __init__.py              # 统一导出接口
├── factory.py               # 智能体工厂
├── llm.py                   # LLM客户端管理
├── memory.py                # 内存管理
├── runtime.py               # 运行时管理
├── message_queue.py         # 消息队列管理
└── docs/                    # 详细文档
    ├── README.md                           # 文档中心
    ├── AI_CORE_DEVELOPMENT_GUIDE.md       # 开发指南
    ├── TESTCASE_SERVICE_EXAMPLE.md        # 实现案例
    ├── SSE_AND_FEEDBACK_GUIDE.md          # SSE与反馈指南
    ├── AUTOGEN_RUNTIME_GUIDE.md           # 运行时指南
    └── FRAMEWORK_INTEGRATION_GUIDE.md     # 集成指南
```

## 🚀 快速开始

### 1. 基础使用

#### 创建智能体
```python
from backend.ai_core import create_assistant_agent

# 创建带自动内存和上下文的智能体
agent = await create_assistant_agent(
    name="my_agent",
    system_message="你是一个智能助手",
    conversation_id="conv_123",
    auto_memory=True,      # 自动内存管理
    auto_context=True      # 自动上下文管理
)
```

#### 消息队列操作
```python
from backend.ai_core.message_queue import (
    put_message_to_queue,
    get_message_from_queue,
    get_streaming_sse_messages_from_queue
)

# 发送消息到队列
await put_message_to_queue("conv_123", "智能体输出内容")

# 获取消息
message = await get_message_from_queue("conv_123", timeout=30.0)

# SSE流式输出
async for sse_message in get_streaming_sse_messages_from_queue("conv_123"):
    print(sse_message)
```

#### 内存管理
```python
from backend.ai_core.memory import save_to_memory, get_conversation_history

# 保存数据到内存
await save_to_memory("conv_123", {
    "type": "user_input",
    "content": "用户输入内容",
    "metadata": {"source": "web"}
})

# 获取对话历史
history = await get_conversation_history("conv_123")
```

### 2. 完整业务实现

以测试用例生成服务为例，展示完整的业务实现：

#### 智能体定义
```python
from autogen_core import RoutedAgent, message_handler, type_subscription

@type_subscription(topic_type="requirement_analysis")
class RequirementAnalysisAgent(RoutedAgent):
    def __init__(self):
        super().__init__(description="需求分析智能体")

    @message_handler
    async def handle_requirement_analysis(self, message, ctx):
        # 创建智能体实例
        agent = await create_assistant_agent(
            name="requirement_analyst",
            system_message=self.get_system_prompt(),
            conversation_id=message.conversation_id,
            auto_memory=True,
            auto_context=True
        )

        # 处理业务逻辑
        result = await agent.run(message.text_content)

        # 输出到消息队列
        await put_message_to_queue(message.conversation_id, result)
```

#### 运行时实现
```python
from backend.ai_core.runtime import BaseRuntime

class TestCaseRuntime(BaseRuntime):
    async def register_agents(self, runtime, conversation_id):
        # 注册智能体
        await RequirementAnalysisAgent.register(
            runtime, "requirement_analysis",
            lambda: RequirementAnalysisAgent()
        )

    async def start_requirement_analysis(self, conversation_id, data):
        runtime = await self.get_runtime(conversation_id)
        message = RequirementAnalysisMessage(**data)
        await runtime.publish_message(message, topic_id="requirement_analysis")
```

#### API接口实现
```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

@router.post("/generate/streaming")
async def generate_streaming(request):
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # 启动后台任务
    asyncio.create_task(service.start_generation(request))

    # 返回SSE流式响应
    return StreamingResponse(
        get_streaming_sse_messages_from_queue(conversation_id),
        media_type="text/event-stream"
    )
```

## 🌊 SSE流式输出与用户反馈

### SSE技术实现

#### 后端SSE输出
```python
# 消息队列自动转换为SSE格式
async def get_streaming_sse_messages_from_queue(conversation_id: str):
    queue = get_message_queue(conversation_id)
    while True:
        message = await queue.get_message(timeout=300.0)
        if message == "CLOSE":
            break
        yield f"data: {message}\n\n"
```

#### 前端SSE接收
```typescript
// 健壮的SSE解析
function parseSSEData(buffer: string) {
  const chunks = buffer.split('\n\n');
  const remainingBuffer = chunks.pop() || '';
  const results = [];

  for (const chunk of chunks) {
    const lines = chunk.split('\n');
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          results.push(data);
        } catch (e) {
          console.error('JSON解析失败:', e);
        }
      }
    }
  }

  return { data: results, remainingBuffer };
}
```

### 用户反馈机制

#### 智能体请求反馈
```python
async def get_user_feedback(prompt: str) -> str:
    # 发送反馈请求到前端
    await put_message_to_queue(conversation_id, {
        "type": "user_feedback_request",
        "content": prompt
    })

    # 等待用户反馈
    feedback = await get_feedback_from_queue(conversation_id, timeout=300.0)
    return feedback or "继续"

# 在UserProxyAgent中使用
user_agent = UserProxyAgent(
    name="user_feedback",
    input_func=get_user_feedback
)
```

#### API反馈接口
```python
@router.get("/feedback")
async def submit_feedback(conversation_id: str, message: str):
    await put_feedback_to_queue(conversation_id, message)
    return {"message": "ok"}
```

## 🏗️ AutoGen运行时管理

### 运行时生命周期

```
初始化 → 智能体注册 → 运行时启动 → 消息处理 → 资源清理
```

#### 运行时初始化
```python
async def initialize_runtime(self, conversation_id: str):
    # 1. 创建运行时实例
    runtime = SingleThreadedAgentRuntime()

    # 2. 注册智能体
    await self.register_agents(runtime, conversation_id)

    # 3. 启动运行时
    runtime.start()

    # 4. 保存实例和状态
    self.runtimes[conversation_id] = runtime
    self.states[conversation_id] = RuntimeState(conversation_id)
```

#### 消息发布订阅
```python
# 发布消息
await runtime.publish_message(
    message,
    topic_id=DefaultTopicId(type="requirement_analysis")
)

# 订阅消息
@type_subscription(topic_type="requirement_analysis")
class MyAgent(RoutedAgent):
    @message_handler
    async def handle_message(self, message, ctx):
        # 处理消息
        pass
```

## 🔧 框架集成最佳实践

### 1. 分层架构
```
API接口层 → 业务服务层 → AI核心框架层 → AutoGen运行时层
```

### 2. 业务服务封装
```python
class BaseAIService:
    def __init__(self):
        self.memory_manager = get_memory_manager()
        self.message_queue = BusinessMessageQueue()

    async def validate_prerequisites(self) -> bool:
        configs = validate_model_configs()
        return any(configs.values())

    async def handle_error(self, conversation_id: str, error: Exception):
        await self.message_queue.send_error_message(conversation_id, str(error))
```

### 3. 统一错误处理
```python
class ErrorHandler:
    @staticmethod
    async def handle_error(conversation_id: str, error: Exception):
        # 记录错误日志
        logger.error(f"处理失败: {error}")

        # 发送错误消息
        await put_message_to_queue(conversation_id, {
            "type": "error",
            "content": f"处理失败: {str(error)}"
        })

        # 保存错误到内存
        await save_to_memory(conversation_id, {
            "type": "error_log",
            "content": str(error)
        })
```

### 4. 性能优化
```python
# 连接池管理
class ConnectionPoolManager:
    def __init__(self):
        self.runtime_pool = {}
        self.max_pool_size = 10

    async def get_runtime(self, service_type: str):
        if service_type not in self.runtime_pool:
            self.runtime_pool[service_type] = self._create_runtime(service_type)
        return self.runtime_pool[service_type]

# 并发控制
class ConcurrencyManager:
    def __init__(self):
        self.semaphore = Semaphore(10)  # 最大并发数

    async def process_with_limit(self, coro):
        async with self.semaphore:
            return await coro
```

## 📊 监控与调试

### 1. 健康检查
```python
async def check_system_health():
    health_status = {
        "status": "healthy",
        "components": {}
    }

    # 检查模型配置
    configs = validate_model_configs()
    health_status["components"]["models"] = {
        "status": "healthy" if any(configs.values()) else "unhealthy"
    }

    # 检查消息队列
    queue_manager = get_queue_manager()
    health_status["components"]["message_queue"] = {
        "status": "healthy",
        "active_queues": len(queue_manager.queues)
    }

    return health_status
```

### 2. 性能监控
```python
def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"执行完成，耗时: {duration:.2f}秒")
            return result
        except Exception as e:
            logger.error(f"执行失败，耗时: {time.time() - start_time:.2f}秒")
            raise
    return wrapper
```

## 🔗 详细文档链接

### 核心文档
- [AI核心框架开发指南](../backend/ai_core/docs/AI_CORE_DEVELOPMENT_GUIDE.md) - 框架基础和组件详解
- [测试用例生成服务实现案例](../backend/ai_core/docs/TESTCASE_SERVICE_EXAMPLE.md) - 完整业务实现示例
- [SSE流式输出与用户反馈指南](../backend/ai_core/docs/SSE_AND_FEEDBACK_GUIDE.md) - 前后端交互技术
- [AutoGen运行时与业务封装指南](../backend/ai_core/docs/AUTOGEN_RUNTIME_GUIDE.md) - 运行时深入解析
- [框架集成与最佳实践指南](../backend/ai_core/docs/FRAMEWORK_INTEGRATION_GUIDE.md) - 集成和优化策略

### 相关资源
- [AutoGen官方文档](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/index.html)
- [后端架构文档](./architecture/BACKEND_ARCHITECTURE.md)
- [API文档](./api/)

## 🚀 开发建议

### 新手开发者
1. 先阅读框架开发指南了解基础概念
2. 参考测试用例服务案例学习实际应用
3. 查看SSE和反馈指南了解前后端交互

### 业务开发者
1. 重点学习测试用例服务实现案例
2. 参考框架集成指南的业务服务开发模式
3. 使用SSE和反馈指南实现用户交互

### 架构师
1. 全面了解框架集成与最佳实践指南
2. 深入学习AutoGen运行时与业务封装指南
3. 参考测试用例服务案例的架构设计

通过这套完整的AI核心框架，可以快速构建出高质量、高性能的智能体系统，大大简化大模型应用的开发复杂度。
