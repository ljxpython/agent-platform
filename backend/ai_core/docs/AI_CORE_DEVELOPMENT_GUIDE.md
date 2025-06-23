# AI核心框架开发指南

[← 返回AI核心框架](../) | [📖 文档中心](../../../docs/) | [📋 导航索引](../../../docs/DOCS_INDEX.md)

## 🎯 框架概述

AI核心框架（`backend/ai_core`）是专门为大模型应用开发设计的核心组件库，基于AutoGen 0.5.7构建，提供了完整的智能体开发、运行时管理、消息队列、内存管理等功能。

### 🏗️ 架构设计原则

1. **模块化设计**：每个组件职责单一，易于扩展和维护
2. **业务解耦**：通用组件与业务逻辑分离，提高复用性
3. **健壮性优先**：完整的错误处理和容错机制
4. **工程化友好**：简化业务代码开发，提高开发效率

## 📁 目录结构

```
backend/ai_core/
├── __init__.py              # 统一导出接口
├── factory.py               # 智能体工厂
├── llm.py                   # LLM客户端管理
├── memory.py                # 内存管理
├── runtime.py               # 运行时管理
├── message_queue.py         # 消息队列管理
└── docs/                    # 文档目录
    └── AI_CORE_DEVELOPMENT_GUIDE.md  # 本文档
```

## 🤖 核心组件详解

### 1. LLM客户端管理器 (llm.py)

#### 功能特性
- 支持多种模型：DeepSeek-Chat、Qwen-VL-Max-Latest、UI-TARS
- 统一的客户端管理和配置验证
- 智能的默认模型选择策略
- 单例模式优化性能

#### 基本使用

```python
from backend.ai_core import get_default_client, get_deepseek_client

# 获取默认客户端（自动选择最佳可用模型）
client = get_default_client()

# 获取特定模型客户端
deepseek_client = get_deepseek_client()
```

#### 配置验证

```python
from backend.ai_core import validate_model_configs

# 验证所有模型配置
configs = validate_model_configs()
print(f"DeepSeek配置: {configs['deepseek_configured']}")
print(f"Qwen-VL配置: {configs['qwen_vl_configured']}")
```

### 2. 智能体工厂 (factory.py)

#### 功能特性
- 统一的智能体创建和管理
- 支持自动内存和上下文管理
- 异步创建，优化性能
- 完整的错误处理和日志记录

#### 创建助手智能体

```python
from backend.ai_core import create_assistant_agent

# 创建带自动内存和上下文的智能体
agent = await create_assistant_agent(
    name="requirement_analyst",
    system_message="你是一位资深的需求分析师...",
    conversation_id="conv_123",
    auto_memory=True,      # 自动内存管理
    auto_context=True      # 自动上下文管理
)
```

#### 创建用户代理智能体

```python
from backend.ai_core import create_user_proxy_agent

# 创建用户代理智能体
user_agent = create_user_proxy_agent(
    name="user_feedback",
    input_func=lambda prompt: get_user_input(prompt)
)
```

### 3. 内存管理器 (memory.py)

#### 功能特性
- 对话历史记录和管理
- 自动内存初始化
- 支持结构化数据存储
- 完整的容错机制

#### 基本使用

```python
from backend.ai_core.memory import save_to_memory, get_conversation_history

# 保存数据到内存
await save_to_memory("conv_123", {
    "type": "user_input",
    "content": "用户需求内容",
    "metadata": {"source": "web"}
})

# 获取对话历史
history = await get_conversation_history("conv_123")
```

#### 获取智能体内存

```python
from backend.ai_core.memory import get_agent_memory

# 获取智能体内存（自动初始化）
memory = await get_agent_memory("conv_123")
if memory:
    await memory.add_message("system", "系统消息")
```

### 4. 消息队列管理 (message_queue.py)

#### 功能特性
- 独立的消息队列管理
- 支持流式输出到前端
- 用户反馈队列
- SSE格式化输出
- 完整的超时和错误处理

#### 基本消息操作

```python
from backend.ai_core.message_queue import (
    put_message_to_queue,
    get_message_from_queue
)

# 放入消息
await put_message_to_queue("conv_123", "智能体输出内容")

# 获取消息（支持超时）
message = await get_message_from_queue("conv_123", timeout=30.0)
```

#### 用户反馈处理

```python
from backend.ai_core.message_queue import (
    put_feedback_to_queue,
    get_feedback_from_queue
)

# 放入用户反馈
await put_feedback_to_queue("conv_123", "用户反馈内容")

# 获取用户反馈
feedback = await get_feedback_from_queue("conv_123", timeout=60.0)
```

#### SSE流式输出

```python
from backend.ai_core.message_queue import get_streaming_sse_messages_from_queue

# 获取SSE格式的流式消息（用于API接口）
async def stream_messages(conversation_id: str):
    async for sse_message in get_streaming_sse_messages_from_queue(conversation_id):
        yield sse_message
```

### 5. 运行时管理器 (runtime.py)

#### 功能特性
- 智能体运行时生命周期管理
- 状态跟踪和监控
- 资源清理和优化
- 完整的错误处理

#### 基本使用

```python
from backend.ai_core.runtime import BaseRuntime

class MyRuntime(BaseRuntime):
    async def register_agents(self, runtime, conversation_id):
        # 注册智能体到运行时
        await MyAgent.register(runtime, "my_topic", lambda: MyAgent())

    async def start_processing(self, conversation_id, data):
        # 启动处理流程
        runtime = await self.get_runtime(conversation_id)
        # 发布消息到智能体
```

## 🚀 完整开发示例

以下以测试用例生成服务为例，展示如何使用AI核心框架开发完整的智能体系统。

### 示例：测试用例生成智能体

#### 1. 智能体定义

```python
from autogen_core import RoutedAgent, message_handler, type_subscription
from backend.ai_core import create_assistant_agent

@type_subscription(topic_type="requirement_analysis")
class RequirementAnalysisAgent(RoutedAgent):
    def __init__(self):
        super().__init__(description="需求分析智能体")

    def get_system_prompt(self) -> str:
        return """
        你是一位资深的软件需求分析师，拥有超过10年的需求分析经验。
        你的任务是分析用户提供的需求文档，提取关键信息...
        """

    @message_handler
    async def handle_requirement_analysis(self, message, ctx):
        conversation_id = message.conversation_id

        # 创建智能体（自动内存和上下文）
        agent = await create_assistant_agent(
            name="requirement_analyst",
            system_message=self.get_system_prompt(),
            conversation_id=conversation_id,
            auto_memory=True,
            auto_context=True
        )

        # 处理需求分析
        result = await agent.run(message.text_content)

        # 输出到消息队列
        await put_message_to_queue(conversation_id, result)
```

#### 2. 运行时实现

```python
from backend.ai_core.runtime import BaseRuntime

class TestCaseRuntime(BaseRuntime):
    async def register_agents(self, runtime, conversation_id):
        # 注册需求分析智能体
        await RequirementAnalysisAgent.register(
            runtime, "requirement_analysis",
            lambda: RequirementAnalysisAgent()
        )

        # 注册其他智能体...

    async def start_requirement_analysis(self, conversation_id, data):
        runtime = await self.get_runtime(conversation_id)

        # 发布需求分析消息
        message = RequirementAnalysisMessage(**data)
        await runtime.publish_message(message, topic_id="requirement_analysis")
```

#### 3. 服务层实现

```python
from backend.ai_core.message_queue import get_streaming_sse_messages_from_queue

class TestCaseService:
    def __init__(self):
        self.runtime = TestCaseRuntime()

    async def start_streaming_generation(self, requirement):
        conversation_id = requirement.conversation_id

        # 初始化运行时
        await self.runtime.initialize_runtime(conversation_id)

        # 启动需求分析
        await self.runtime.start_requirement_analysis(
            conversation_id, requirement.dict()
        )

    async def get_streaming_response(self, conversation_id):
        # 返回SSE流式响应
        return get_streaming_sse_messages_from_queue(conversation_id)
```

#### 4. API接口实现

```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

@router.post("/generate/streaming")
async def generate_testcase_streaming(request: GenerateRequest):
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # 启动后台任务
    asyncio.create_task(
        testcase_service.start_streaming_generation(request)
    )

    # 返回流式响应
    return StreamingResponse(
        testcase_service.get_streaming_response(conversation_id),
        media_type="text/event-stream"
    )
```

## 📋 开发最佳实践

### 1. 错误处理
- 所有异步操作都要有try-catch
- 使用loguru记录详细的调试信息
- 失败时返回合理的默认值

### 2. 内存管理
- 使用auto_memory=True自动管理内存
- 定期清理不活跃的对话资源
- 避免内存泄漏

### 3. 消息队列
- 设置合理的超时时间
- 处理CLOSE信号优雅关闭
- 使用SSE格式化函数统一输出格式

### 4. 智能体设计
- 系统提示词要清晰具体
- 使用type_subscription正确订阅消息
- 实现完整的消息处理逻辑

## 🔗 相关文档

- [AutoGen官方文档](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/index.html)
- [后端架构文档](../../../docs/architecture/BACKEND_ARCHITECTURE.md)
- [测试用例服务实现](../../services/testcase/)

## 📞 技术支持

如有问题，请参考：
1. 查看日志输出（使用loguru详细记录）
2. 检查模型配置是否正确
3. 验证消息队列状态
4. 确认智能体注册成功
