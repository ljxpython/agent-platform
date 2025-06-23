# AutoGen运行时与业务封装指南

[← 返回开发指南](./AI_CORE_DEVELOPMENT_GUIDE.md) | [📖 文档中心](../../../docs/) | [📋 导航索引](../../../docs/DOCS_INDEX.md)

## 🎯 概述

本文档详细介绍如何使用AutoGen 0.5.7的运行时系统，以及如何在AI核心框架中进行业务封装。涵盖运行时生命周期管理、智能体注册、消息发布订阅、业务类封装等核心内容。

## 🏗️ AutoGen运行时架构

### 1. 核心组件

#### SingleThreadedAgentRuntime
AutoGen的核心运行时，负责：
- 智能体生命周期管理
- 消息路由和分发
- 主题订阅管理
- 资源清理

#### RoutedAgent
基于消息路由的智能体基类：
- 支持消息订阅和处理
- 自动消息路由
- 类型安全的消息处理

#### 消息系统
- **消息类型**：使用Pydantic模型定义
- **主题订阅**：通过装饰器声明订阅关系
- **消息处理**：异步消息处理机制

### 2. AI核心框架的运行时封装

```python
class BaseRuntime(ABC):
    """智能体运行时基类"""

    def __init__(self):
        self.runtimes: Dict[str, SingleThreadedAgentRuntime] = {}
        self.states: Dict[str, RuntimeState] = {}
        self.queues: Dict[str, MessageQueue] = {}
        self.agent_factory: AgentFactory = get_agent_factory()
        self.memory_manager = get_memory_manager()

    async def initialize_runtime(self, conversation_id: str) -> None:
        """
        初始化运行时（增强版，完整容错机制）

        功能：
        1. 创建SingleThreadedAgentRuntime实例
        2. 注册所有相关智能体
        3. 启动运行时
        4. 初始化状态和队列
        """
        try:
            logger.info(f"🏗️ [运行时管理] 开始初始化运行时 | 对话ID: {conversation_id}")

            # 检查是否已存在
            if conversation_id in self.runtimes:
                logger.info(f"♻️ [运行时管理] 运行时已存在，跳过初始化 | 对话ID: {conversation_id}")
                return

            # 创建运行时实例
            runtime = SingleThreadedAgentRuntime()
            logger.debug(f"   ✅ SingleThreadedAgentRuntime创建成功")

            # 注册智能体
            await self.register_agents(runtime, conversation_id)
            logger.debug(f"   ✅ 智能体注册完成")

            # 启动运行时
            runtime.start()
            logger.debug(f"   ✅ 运行时启动成功")

            # 保存运行时实例
            self.runtimes[conversation_id] = runtime

            # 初始化状态
            self.states[conversation_id] = RuntimeState(conversation_id)

            # 初始化消息队列
            queue_manager = get_queue_manager()
            self.queues[conversation_id] = queue_manager.get_or_create_queue(conversation_id)

            logger.success(f"✅ [运行时管理] 运行时初始化完成 | 对话ID: {conversation_id}")

        except Exception as e:
            logger.error(f"❌ [运行时管理] 初始化失败 | 对话ID: {conversation_id} | 错误: {str(e)}")
            # 确保清理资源
            await self.cleanup_runtime(conversation_id)
            raise
```

## 🤖 智能体注册与管理

### 1. 智能体注册模式

#### 抽象注册方法

```python
@abstractmethod
async def register_agents(
    self, runtime: SingleThreadedAgentRuntime, conversation_id: str
) -> None:
    """
    注册智能体到运行时（抽象方法，子类必须实现）

    Args:
        runtime: 运行时实例
        conversation_id: 对话ID
    """
    pass
```

#### 具体实现示例

```python
class TestCaseRuntime(BaseRuntime):
    """测试用例生成专用运行时"""

    async def register_agents(
        self, runtime: SingleThreadedAgentRuntime, conversation_id: str
    ) -> None:
        """注册测试用例生成相关的智能体"""
        logger.info(f"🤖 [测试用例运行时] 注册智能体 | 对话ID: {conversation_id}")

        try:
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

            # 注册测试用例优化智能体
            await TestCaseOptimizationAgent.register(
                runtime,
                self.topic_types["testcase_optimization"],
                lambda: TestCaseOptimizationAgent(),
            )

            logger.success(f"✅ [测试用例运行时] 智能体注册完成 | 对话ID: {conversation_id}")

        except Exception as e:
            logger.error(f"❌ [测试用例运行时] 智能体注册失败 | 对话ID: {conversation_id} | 错误: {e}")
            raise
```

### 2. 智能体定义规范

#### 基本结构

```python
from autogen_core import RoutedAgent, message_handler, type_subscription
from pydantic import BaseModel

# 1. 定义消息模型
class MyMessage(BaseModel):
    conversation_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

# 2. 定义智能体
@type_subscription(topic_type="my_topic")
class MyAgent(RoutedAgent):
    def __init__(self):
        super().__init__(description="我的智能体")

    @message_handler
    async def handle_message(self, message: MyMessage, ctx: MessageContext):
        # 处理消息逻辑
        pass
```

#### 智能体注册

```python
# 在运行时中注册
await MyAgent.register(
    runtime,
    "my_topic",           # 主题类型
    lambda: MyAgent()     # 智能体工厂函数
)
```

## 📨 消息发布与订阅

### 1. 消息发布

#### 基本发布

```python
async def start_requirement_analysis(
    self, conversation_id: str, requirement_data: Dict[str, Any]
) -> None:
    """启动需求分析流程"""
    try:
        runtime = await self.get_runtime(conversation_id)
        if not runtime:
            raise RuntimeError(f"运行时不存在: {conversation_id}")

        # 更新状态
        await self.update_state(conversation_id, "requirement_analysis", "processing")

        # 创建需求分析消息
        requirement_msg = RequirementAnalysisMessage(**requirement_data)

        # 发布消息到智能体
        await runtime.publish_message(
            requirement_msg,
            topic_id=DefaultTopicId(type=self.topic_types["requirement_analysis"]),
        )

        logger.info(f"📤 [测试用例运行时] 需求分析消息已发布 | 对话ID: {conversation_id}")

    except Exception as e:
        logger.error(f"❌ [测试用例运行时] 启动需求分析失败 | 对话ID: {conversation_id} | 错误: {e}")
        raise
```

#### 消息路由

```python
from autogen_core import DefaultTopicId

# 发布到特定主题
await runtime.publish_message(
    message,
    topic_id=DefaultTopicId(type="requirement_analysis")
)

# 发布到特定智能体
await runtime.publish_message(
    message,
    topic_id=TopicId(type="my_topic", source="specific_agent")
)
```

### 2. 消息订阅

#### 类型订阅

```python
@type_subscription(topic_type="requirement_analysis")
class RequirementAnalysisAgent(RoutedAgent):
    # 自动订阅 "requirement_analysis" 类型的消息
    pass
```

#### 多主题订阅

```python
@type_subscription(topic_type="topic1")
@type_subscription(topic_type="topic2")
class MultiTopicAgent(RoutedAgent):
    # 订阅多个主题
    pass
```

### 3. 消息处理

#### 消息处理器

```python
@message_handler
async def handle_requirement_analysis(
    self, message: RequirementAnalysisMessage, ctx: MessageContext
) -> None:
    conversation_id = message.conversation_id
    logger.info(f"📋 [需求分析智能体] 收到需求分析任务 | 对话ID: {conversation_id}")

    try:
        # 创建智能体实例
        analyst_agent = await create_assistant_agent(
            name="requirement_analyst",
            system_message=self.get_system_prompt(),
            conversation_id=conversation_id,
            auto_memory=True,
            auto_context=True,
        )

        # 处理业务逻辑
        result = await self.process_requirement(analyst_agent, message)

        # 发布下游消息
        await self.publish_downstream_message(conversation_id, result)

    except Exception as e:
        logger.error(f"❌ [需求分析智能体] 处理失败 | 对话ID: {conversation_id} | 错误: {e}")
        await self.handle_error(conversation_id, e)
```

## 🏢 业务类封装模式

### 1. 服务层封装

#### 服务基类设计

```python
class TestCaseService:
    """AI测试用例生成服务 - 重构版本"""

    def __init__(self):
        """初始化服务"""
        self.runtime = get_testcase_runtime()
        self.memory_manager = get_memory_manager()

    async def start_streaming_generation(self, requirement: RequirementMessage) -> None:
        """启动流式测试用例生成"""
        conversation_id = requirement.conversation_id
        logger.info(f"🌊 [测试用例服务] 启动流式生成 | 对话ID: {conversation_id}")

        try:
            # 验证模型配置
            configs = validate_model_configs()
            if not any(configs.values()):
                await self.handle_config_error(conversation_id)
                return

            # 检查反馈监听模式
            if requirement.text_content == "FEEDBACK_LISTENING":
                logger.info(f"🎧 [测试用例服务] 反馈监听模式 | 对话ID: {conversation_id}")
                return

            # 初始化运行时
            await self.runtime.initialize_runtime(conversation_id)

            # 启动需求分析
            requirement_data = {
                "conversation_id": conversation_id,
                "text_content": requirement.text_content,
                "files": requirement.files or [],
                "round_number": requirement.round_number,
            }

            await self.runtime.start_requirement_analysis(conversation_id, requirement_data)

            logger.success(f"✅ [测试用例服务] 流式生成启动成功 | 对话ID: {conversation_id}")

        except Exception as e:
            logger.error(f"❌ [测试用例服务] 启动失败 | 对话ID: {conversation_id} | 错误: {e}")
            await self.handle_service_error(conversation_id, e)
```

### 2. 运行时封装

#### 专用运行时类

```python
class TestCaseRuntime(BaseRuntime):
    """测试用例生成专用运行时"""

    def __init__(self):
        super().__init__()
        # 定义主题类型映射
        self.topic_types = {
            "requirement_analysis": "requirement_analysis",
            "testcase_generation": "testcase_generation",
            "testcase_optimization": "testcase_optimization",
            "testcase_finalization": "testcase_finalization",
        }

    # 业务特定的方法
    async def start_requirement_analysis(self, conversation_id: str, data: Dict[str, Any]):
        """启动需求分析"""
        pass

    async def process_user_feedback(self, conversation_id: str, feedback_data: Dict[str, Any]):
        """处理用户反馈"""
        pass

    async def finalize_testcases(self, conversation_id: str, testcases: str):
        """最终化测试用例"""
        pass
```

### 3. 智能体封装

#### 智能体基类模式

```python
class BaseTestCaseAgent(RoutedAgent):
    """测试用例智能体基类"""

    def __init__(self, description: str):
        super().__init__(description=description)

    async def create_agent_instance(self, conversation_id: str, system_message: str):
        """创建智能体实例的通用方法"""
        return await create_assistant_agent(
            name=self.__class__.__name__.lower(),
            system_message=system_message,
            conversation_id=conversation_id,
            auto_memory=True,
            auto_context=True,
        )

    async def save_result_to_memory(self, conversation_id: str, result: str, result_type: str):
        """保存结果到内存的通用方法"""
        await save_to_memory(conversation_id, {
            "type": result_type,
            "content": result,
            "agent": self.__class__.__name__,
            "timestamp": datetime.now().isoformat()
        })

    async def output_to_queue(self, conversation_id: str, content: str, message_type: str = "agent_message"):
        """输出到消息队列的通用方法"""
        message = {
            "type": message_type,
            "content": content,
            "source": self.__class__.__name__.lower(),
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
        }
        await put_message_to_queue(conversation_id, json.dumps(message, ensure_ascii=False))
```

## 🔄 生命周期管理

### 1. 运行时生命周期

```
初始化 → 智能体注册 → 运行时启动 → 消息处理 → 资源清理
```

#### 初始化阶段

```python
async def initialize_runtime(self, conversation_id: str):
    # 1. 创建运行时实例
    runtime = SingleThreadedAgentRuntime()

    # 2. 注册智能体
    await self.register_agents(runtime, conversation_id)

    # 3. 启动运行时
    runtime.start()

    # 4. 保存实例
    self.runtimes[conversation_id] = runtime
```

#### 清理阶段

```python
async def cleanup_runtime(self, conversation_id: str) -> None:
    """
    清理运行时资源（增强版，完整容错机制）

    功能：
    1. 停止运行时
    2. 清理状态
    3. 关闭消息队列
    4. 释放内存资源
    """
    try:
        logger.info(f"🗑️ [运行时管理] 开始清理运行时 | 对话ID: {conversation_id}")

        # 停止运行时
        if conversation_id in self.runtimes:
            runtime = self.runtimes[conversation_id]
            try:
                await runtime.stop()
                logger.debug(f"   ✅ 运行时停止成功")
            except Exception as e:
                logger.warning(f"   ⚠️ 运行时停止异常: {e}")

            del self.runtimes[conversation_id]

        # 清理状态
        if conversation_id in self.states:
            del self.states[conversation_id]
            logger.debug(f"   ✅ 状态清理完成")

        # 关闭消息队列
        if conversation_id in self.queues:
            queue = self.queues[conversation_id]
            try:
                await queue.close()
                logger.debug(f"   ✅ 消息队列关闭成功")
            except Exception as e:
                logger.warning(f"   ⚠️ 消息队列关闭异常: {e}")

            del self.queues[conversation_id]

        logger.success(f"✅ [运行时管理] 运行时清理完成 | 对话ID: {conversation_id}")

    except Exception as e:
        logger.error(f"❌ [运行时管理] 清理失败 | 对话ID: {conversation_id} | 错误: {e}")
```

### 2. 智能体生命周期

```
注册 → 实例化 → 消息处理 → 结果输出 → 资源释放
```

### 3. 消息生命周期

```
创建 → 发布 → 路由 → 处理 → 响应 → 清理
```

## 📊 状态管理

### 1. 运行时状态

```python
class RuntimeState:
    """运行时状态管理"""

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.stage = "initialized"
        self.status = "ready"
        self.round_number = 1
        self.last_update = datetime.now().isoformat()
        self.metadata: Dict[str, Any] = {}

    def update_stage(self, stage: str, status: str = "processing") -> None:
        """更新阶段和状态"""
        self.stage = stage
        self.status = status
        self.last_update = datetime.now().isoformat()

    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        self.metadata[key] = value
        self.last_update = datetime.now().isoformat()
```

### 2. 状态查询和更新

```python
# 获取状态
state = runtime.get_state(conversation_id)
print(f"当前阶段: {state.stage}")
print(f"当前状态: {state.status}")

# 更新状态
await runtime.update_state(conversation_id, "testcase_generation", "processing")

# 设置元数据
state.set_metadata("user_feedback_count", 3)
```

## 🛠️ 高级特性

### 1. 错误处理和恢复

```python
async def robust_message_processing(self, message, ctx):
    """健壮的消息处理"""
    try:
        # 正常处理逻辑
        result = await self.process_message(message)
        return result
    except Exception as e:
        # 错误处理
        logger.error(f"消息处理失败: {e}")

        # 尝试恢复
        if self.can_recover(e):
            return await self.recover_and_retry(message)
        else:
            # 发送错误消息
            await self.send_error_message(message.conversation_id, str(e))
            raise
```

### 2. 性能监控

```python
async def monitored_message_handler(self, message, ctx):
    """带性能监控的消息处理"""
    start_time = time.time()

    try:
        result = await self.handle_message(message, ctx)

        # 记录性能指标
        duration = time.time() - start_time
        logger.info(f"消息处理完成，耗时: {duration:.2f}秒")

        return result
    except Exception as e:
        # 记录错误指标
        logger.error(f"消息处理失败，耗时: {time.time() - start_time:.2f}秒")
        raise
```

### 3. 资源优化

```python
async def optimized_runtime_management(self):
    """优化的运行时管理"""
    # 定期清理不活跃的运行时
    inactive_conversations = []

    for conversation_id, state in self.states.items():
        last_update = datetime.fromisoformat(state.last_update)
        if (datetime.now() - last_update).total_seconds() > 3600:  # 1小时
            inactive_conversations.append(conversation_id)

    for conversation_id in inactive_conversations:
        await self.cleanup_runtime(conversation_id)
        logger.info(f"清理不活跃运行时: {conversation_id}")
```

## ✅ 最佳实践

1. **运行时管理**：及时清理资源，避免内存泄漏
2. **错误处理**：完整的异常捕获和恢复机制
3. **状态跟踪**：详细的状态管理和监控
4. **性能优化**：合理的资源分配和并发控制
5. **日志记录**：详细的操作日志便于调试

通过这套完整的AutoGen运行时和业务封装体系，可以构建出高效、稳定、易维护的智能体系统。
