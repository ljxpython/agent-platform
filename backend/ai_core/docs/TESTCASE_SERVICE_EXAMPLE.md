# 测试用例生成服务详细实现案例

[← 返回开发指南](./AI_CORE_DEVELOPMENT_GUIDE.md) | [📖 文档中心](../../../docs/) | [📋 导航索引](../../../docs/DOCS_INDEX.md)

## 🎯 案例概述

本文档以测试用例生成服务为例，详细展示如何使用AI核心框架开发完整的智能体系统。该案例涵盖了框架的所有核心功能：智能体工厂、消息队列、内存管理、运行时管理、SSE流式输出等。

## 📁 项目结构

```
backend/services/testcase/
├── __init__.py              # 模块导出
├── agents.py                # 智能体实现
├── testcase_runtime.py      # 专用运行时
├── testcase_service.py      # 服务层
└── README.md               # 服务说明

backend/api/v1/
└── testcase.py             # API接口层
```

## 🤖 智能体实现详解

### 1. 需求分析智能体

```python
@type_subscription(topic_type="requirement_analysis")
class RequirementAnalysisAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__(description="需求分析智能体")

    def get_system_prompt(self) -> str:
        return """
        你是一位资深的软件需求分析师，拥有超过10年的需求分析和软件测试经验。

        你的任务是：
        1. 深入分析用户提供的需求文档或描述
        2. 识别核心功能点、业务流程和关键场景
        3. 提取测试重点和风险点
        4. 为后续测试用例生成提供结构化的分析结果
        """

    @message_handler
    async def handle_requirement_analysis(
        self, message: RequirementAnalysisMessage, ctx: MessageContext
    ) -> None:
        conversation_id = message.conversation_id
        logger.info(f"📋 [需求分析智能体] 收到需求分析任务 | 对话ID: {conversation_id}")

        try:
            # 步骤1: 创建需求分析智能体 - 使用优化后的factory函数
            analyst_agent = await create_assistant_agent(
                name="requirement_analyst",
                system_message=self.get_system_prompt(),
                conversation_id=conversation_id,
                auto_memory=True,      # 自动内存管理
                auto_context=True     # 自动上下文管理
            )
```

#### 关键实现要点

1. **智能体创建**：使用`create_assistant_agent`创建智能体，启用自动内存和上下文管理
2. **消息订阅**：使用`@type_subscription`装饰器订阅特定主题
3. **消息处理**：使用`@message_handler`装饰器处理消息
4. **错误处理**：完整的try-catch机制和详细日志记录

### 2. 测试用例生成智能体（团队协作模式）

```python
@type_subscription(topic_type="testcase_generation")
class TestCaseGenerationAgent(RoutedAgent):
    @message_handler
    async def handle_testcase_generation(
        self, message: TestCaseGenerationMessage, ctx: MessageContext
    ) -> None:
        conversation_id = message.conversation_id

        try:
            # 步骤1: 创建测试用例生成智能体
            generator_agent = await create_assistant_agent(
                name="testcase_generator",
                system_message=self.get_system_prompt(),
                conversation_id=conversation_id,
                auto_memory=True,
                auto_context=True,
            )

            # 步骤2: 创建用户反馈智能体
            async def get_user_feedback(prompt: str) -> str:
                await put_message_to_queue(conversation_id, prompt)
                feedback = await get_feedback_from_queue(conversation_id, timeout=300.0)
                return feedback or "继续"

            user_feedback_agent = UserProxyAgent(
                name="user_feedback",
                input_func=get_user_feedback,
            )

            # 步骤3: 创建RoundRobinGroupChat团队
            team = RoundRobinGroupChat(
                [generator_agent, user_feedback_agent],
                termination_condition=TextMentionTermination("同意"),
            )

            # 步骤4: 执行团队协作流式输出
            generation_task = f"请为以下需求生成测试用例：\n\n{message.content}"

            async for chunk in team.run_stream(task=generation_task):
                if isinstance(chunk, ModelClientStreamingChunkEvent):
                    await put_message_to_queue(conversation_id, chunk.content)
```

#### 团队协作特性

1. **多智能体协作**：使用`RoundRobinGroupChat`实现智能体团队协作
2. **用户交互**：通过`UserProxyAgent`实现用户反馈收集
3. **流式输出**：使用`run_stream`实现实时流式输出
4. **终止条件**：使用`TextMentionTermination`设置协作终止条件

## 🏗️ 运行时管理实现

### 专用运行时类

```python
class TestCaseRuntime(BaseRuntime):
    """测试用例生成专用运行时"""

    def __init__(self):
        super().__init__()
        self.topic_types = {
            "requirement_analysis": "requirement_analysis",
            "testcase_generation": "testcase_generation",
            "testcase_optimization": "testcase_optimization",
            "testcase_finalization": "testcase_finalization",
        }

    async def register_agents(
        self, runtime: SingleThreadedAgentRuntime, conversation_id: str
    ) -> None:
        """注册测试用例生成相关的智能体"""

        # 注册需求分析智能体
        await RequirementAnalysisAgent.register(
            runtime,
            self.topic_types["requirement_analysis"],
            lambda: RequirementAnalysisAgent(),
        )

        # 注册测试用例生成智能体
        await TestCaseGenerationAgent.register(
            runtime,
            self.topic_types["testcase_generation"],
            lambda: TestCaseGenerationAgent(),
        )
```

#### 运行时管理特性

1. **智能体注册**：统一注册所有相关智能体
2. **主题管理**：定义和管理消息主题类型
3. **生命周期管理**：继承BaseRuntime的完整生命周期管理
4. **状态跟踪**：自动跟踪运行时状态和元数据

## 📡 消息队列使用详解

### 1. 基本消息操作

```python
from backend.ai_core.message_queue import (
    put_message_to_queue,
    get_message_from_queue,
    put_feedback_to_queue,
    get_feedback_from_queue
)

# 智能体输出消息
await put_message_to_queue(conversation_id, "智能体分析结果...")

# 获取用户反馈
feedback = await get_feedback_from_queue(conversation_id, timeout=300.0)
if feedback:
    logger.info(f"收到用户反馈: {feedback}")
```

### 2. SSE流式输出

```python
async def get_streaming_sse_messages_from_queue(
    conversation_id: str,
) -> AsyncGenerator[str, None]:
    """
    从独立消息队列获取SSE格式的流式消息（全局便捷函数，专用于SSE输出）

    特性：
    - 支持300秒超时
    - 处理CLOSE信号优雅关闭
    - 完整的错误处理和CancelledError支持
    - 详细的调试日志
    """
    try:
        logger.info(f"🌊 [队列管理-SSE] 开始SSE流式输出 | 对话ID: {conversation_id}")

        # 获取独立消息队列
        queue = get_message_queue(conversation_id, create_if_not_exists=True)
        if queue:
            try:
                while True:
                    message = await queue.get_message(timeout=300.0)

                    if message and message != "CLOSE":
                        # 直接返回SSE格式
                        yield f"data: {message}\n\n"
                    elif message == "CLOSE":
                        logger.debug(f"   📦 队列关闭，结束SSE流式输出")
                        break
            except asyncio.CancelledError:
                logger.info(f"   ⏹️ SSE流式输出任务取消")
            except Exception as e:
                logger.error(f"   ❌ SSE流式输出异常: {e}")
```

### 3. 队列状态管理

```python
from backend.ai_core.message_queue import get_queue_info, close_message_queue

# 获取队列信息
info = await get_queue_info(conversation_id)
logger.info(f"队列状态: {info}")

# 优雅关闭队列
await close_message_queue(conversation_id)
```

## 🧠 内存管理使用

### 1. 自动内存管理

```python
# 在智能体创建时启用自动内存
agent = await create_assistant_agent(
    name="my_agent",
    system_message="系统提示词",
    conversation_id=conversation_id,
    auto_memory=True,      # 自动内存管理
    auto_context=True      # 自动上下文管理
)
```

### 2. 手动内存操作

```python
from backend.ai_core.memory import save_to_memory, get_conversation_history

# 保存结构化数据
await save_to_memory(conversation_id, {
    "type": "requirement_analysis",
    "content": "分析结果...",
    "metadata": {
        "agent": "requirement_analyst",
        "timestamp": datetime.now().isoformat()
    }
})

# 获取对话历史
history = await get_conversation_history(conversation_id)
for item in history:
    logger.info(f"历史记录: {item['type']} - {item['content'][:100]}...")
```

## 🌐 API接口实现

### 1. 流式生成接口

```python
@testcase_router.post("/generate/streaming")
async def generate_testcase_streaming(request: StreamingGenerateRequest):
    """
    流式生成测试用例接口 - 队列模式

    功能：启动需求分析和初步用例生成，返回流式输出
    流程：用户输入 → 需求分析智能体 → 测试用例生成智能体 → 队列消费者 → 流式SSE返回
    """
    # 生成或使用提供的对话ID
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # 创建需求消息对象
    requirement = RequirementMessage(
        text_content=request.text_content or "",
        files=[],
        file_paths=[],
        conversation_id=conversation_id,
        round_number=request.round_number,
    )

    # 启动后台任务处理智能体流程
    asyncio.create_task(testcase_service.start_streaming_generation(requirement))

    # 返回队列消费者的流式响应
    from backend.ai_core.message_queue import get_streaming_sse_messages_from_queue

    return StreamingResponse(
        get_streaming_sse_messages_from_queue(conversation_id),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )
```

### 2. 用户反馈接口

```python
@testcase_router.get("/feedback")
async def submit_feedback_simple(conversation_id: str, message: str):
    """
    简单用户反馈接口 - 直接使用message_queue

    功能：接收用户反馈并放入队列，立即返回确认
    """
    logger.info(f"💬 [API-简单反馈] 收到用户反馈")
    logger.info(f"   📋 对话ID: {conversation_id}")
    logger.info(f"   💭 反馈内容: {message}")

    # 直接使用message_queue中的函数
    from backend.ai_core.message_queue import put_feedback_to_queue

    await put_feedback_to_queue(conversation_id, message)

    logger.success(f"✅ [API-简单反馈] 反馈已放入队列")
    return {"message": "ok"}
```

## 🔄 完整业务流程

### 1. 初始生成流程

```
用户请求 → API接口 → 服务层 → 运行时 → 需求分析智能体 → 测试用例生成智能体 → 消息队列 → SSE流式返回
```

### 2. 用户反馈流程

```
用户反馈 → 反馈接口 → 反馈队列 → 智能体获取反馈 → 优化处理 → 结果输出 → SSE流式返回
```

### 3. 资源清理流程

```
对话结束 → 清理接口 → 运行时清理 → 队列关闭 → 内存清理 → 资源释放
```

## 📊 性能优化建议

### 1. 内存优化
- 使用auto_memory避免重复创建内存实例
- 定期清理不活跃的对话资源
- 合理设置队列大小限制

### 2. 并发优化
- 使用asyncio.create_task启动后台任务
- 避免阻塞主线程
- 合理设置超时时间

### 3. 错误处理
- 完整的try-catch机制
- 详细的日志记录
- 优雅的降级策略

## 🔍 调试技巧

### 1. 日志分析
```python
# 查看详细的调试日志
logger.debug(f"智能体状态: {agent.name}")
logger.debug(f"队列信息: {await get_queue_info(conversation_id)}")
logger.debug(f"内存状态: {len(await get_conversation_history(conversation_id))}")
```

### 2. 状态监控
```python
# 监控运行时状态
runtime_stats = runtime.get_runtime_stats()
logger.info(f"运行时统计: {runtime_stats}")
```

### 3. 错误排查
- 检查模型配置是否正确
- 验证智能体注册是否成功
- 确认消息队列状态正常
- 查看内存使用情况

## 🎯 总结

通过测试用例生成服务的完整实现案例，我们可以看到AI核心框架提供了：

1. **简化的智能体开发**：通过工厂模式和自动管理简化创建过程
2. **强大的消息队列**：支持流式输出、用户交互、SSE格式化
3. **完善的内存管理**：自动初始化、结构化存储、历史记录
4. **健壮的运行时**：生命周期管理、状态跟踪、资源清理
5. **工程化友好**：详细日志、错误处理、性能优化

这个框架大大简化了智能体系统的开发复杂度，让开发者可以专注于业务逻辑的实现。
