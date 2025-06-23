# SSE流式输出与用户反馈完整指南

[← 返回开发指南](./AI_CORE_DEVELOPMENT_GUIDE.md) | [📖 文档中心](../../../docs/) | [📋 导航索引](../../../docs/DOCS_INDEX.md)

## 🎯 概述

本文档详细介绍如何使用AI核心框架实现SSE（Server-Sent Events）流式输出和用户反馈机制。这是构建实时智能体交互系统的核心技术。

## 🌊 SSE流式输出技术

### 1. SSE技术原理

SSE（Server-Sent Events）是一种服务器向客户端推送数据的技术，特别适合实时流式输出场景：

- **单向通信**：服务器向客户端推送数据
- **自动重连**：客户端自动处理连接断开和重连
- **事件驱动**：支持不同类型的事件消息
- **轻量级**：比WebSocket更简单，适合单向数据流

### 2. AI核心框架中的SSE实现

#### 消息队列到SSE的转换

```python
async def get_streaming_sse_messages_from_queue(
    conversation_id: str,
) -> AsyncGenerator[str, None]:
    """
    从独立消息队列获取SSE格式的流式消息

    特性：
    - 支持300秒超时机制
    - 处理CLOSE信号优雅关闭
    - 完整的错误处理和CancelledError支持
    - 自动SSE格式化
    """
    try:
        logger.info(f"🌊 [队列管理-SSE] 开始SSE流式输出 | 对话ID: {conversation_id}")

        queue = get_message_queue(conversation_id, create_if_not_exists=True)
        if queue:
            try:
                while True:
                    # 从队列获取消息，设置超时
                    message = await queue.get_message(timeout=300.0)

                    if message and message != "CLOSE":
                        # 格式化为SSE标准格式
                        yield f"data: {message}\n\n"
                    elif message == "CLOSE":
                        logger.debug(f"   📦 队列关闭，结束SSE流式输出")
                        break
                    else:
                        logger.debug(f"   ⏰ 消息获取超时")

            except asyncio.CancelledError:
                logger.info(f"   ⏹️ SSE流式输出任务取消")
            except Exception as e:
                logger.error(f"   ❌ SSE流式输出异常: {e}")
```

#### SSE格式标准

```
data: {"type": "agent_message", "content": "智能体输出内容", "source": "requirement_analyst"}

data: {"type": "user_feedback_request", "content": "请提供您的反馈意见"}

data: {"type": "process_complete", "content": "处理完成"}

```

### 3. API接口层SSE实现

#### 流式生成接口

```python
@testcase_router.post("/generate/streaming")
async def generate_testcase_streaming(request: StreamingGenerateRequest):
    """
    流式生成测试用例接口 - 队列模式

    采用队列模式：
    1. 启动后台任务处理智能体流程
    2. 返回队列消费者的流式响应
    3. 智能体将消息放入队列，消费者从队列取出并流式返回
    """
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # 创建需求消息对象
    requirement = RequirementMessage(
        text_content=request.text_content or "",
        files=[],
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
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )
```

#### 关键配置说明

1. **媒体类型**：`text/plain` 或 `text/event-stream`
2. **缓存控制**：`no-cache` 禁用缓存
3. **连接保持**：`keep-alive` 保持连接
4. **跨域支持**：CORS头部配置

### 4. 前端SSE接收实现

#### 标准SSE解析逻辑

```typescript
// 健壮的SSE解析函数
function parseSSEData(buffer: string): { data: any[], remainingBuffer: string } {
  const results: any[] = [];

  // 使用 \n\n 分割消息块（SSE标准）
  const chunks = buffer.split('\n\n');
  const remainingBuffer = chunks.pop() || '';

  for (const chunk of chunks) {
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.trim() === '' || !line.startsWith('data: ')) {
        continue; // 跳过空行和非数据行
      }

      let jsonStr = line.slice(6); // 移除 'data: ' 前缀

      // 处理重复的 'data:' 前缀
      if (jsonStr.startsWith('data: ')) {
        console.warn('检测到重复的data:前缀，自动移除');
        jsonStr = jsonStr.slice(6);
      }

      // 验证JSON格式
      if (!jsonStr.trim() || !jsonStr.startsWith('{')) {
        continue;
      }

      try {
        const data = JSON.parse(jsonStr);
        if (data && typeof data === 'object') {
          results.push(data);
        }
      } catch (e) {
        console.error('JSON解析失败:', e, '原始数据:', jsonStr);
      }
    }
  }

  return { data: results, remainingBuffer };
}
```

#### 使用示例

```typescript
async function handleSSEStream(conversationId: string) {
  const response = await fetch('/api/v1/testcase/generate/streaming', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_id: conversationId, text_content: '需求内容' })
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const { data, remainingBuffer } = parseSSEData(buffer);
    buffer = remainingBuffer;

    // 处理解析出的数据
    for (const item of data) {
      handleAgentMessage(item);
    }
  }
}
```

## 💬 用户反馈机制

### 1. 反馈队列系统

#### 反馈消息放入队列

```python
async def put_feedback_to_queue(conversation_id: str, feedback: str) -> None:
    """
    将用户反馈放入独立消息队列（全局便捷函数，完整容错）

    Args:
        conversation_id: 对话ID
        feedback: 用户反馈内容
    """
    try:
        logger.debug(f"💬 [队列管理] 开始放入用户反馈 | 对话ID: {conversation_id}")

        # 获取独立消息队列
        queue = get_message_queue(conversation_id, create_if_not_exists=True)
        if queue:
            logger.debug(f"   📦 队列获取成功，开始放入反馈")

            # 放入反馈到队列
            await queue.put_feedback(feedback)
            logger.debug(f"   ✅ 反馈放入队列成功 | 对话ID: {conversation_id}")

        else:
            logger.error(f"❌ [队列管理] 无法获取消息队列 | 对话ID: {conversation_id}")

    except Exception as e:
        logger.error(f"❌ [队列管理] 放入反馈异常 | 对话ID: {conversation_id} | 错误: {e}")
```

#### 智能体获取用户反馈

```python
async def get_feedback_from_queue(
    conversation_id: str, timeout: Optional[float] = 60.0
) -> str:
    """
    从独立消息队列获取用户反馈（全局便捷函数，支持超时）

    Args:
        conversation_id: 对话ID
        timeout: 超时时间（秒）

    Returns:
        str: 用户反馈内容，超时或失败时返回空字符串
    """
    try:
        logger.debug(f"👂 [队列管理] 开始获取用户反馈 | 对话ID: {conversation_id}")

        # 获取独立消息队列
        queue = get_message_queue(conversation_id, create_if_not_exists=False)
        if queue:
            logger.debug(f"   📦 队列获取成功，开始获取反馈")

            # 从队列获取反馈
            feedback = await queue.get_feedback(timeout=timeout)
            if feedback:
                logger.debug(f"   ✅ 反馈获取成功 | 对话ID: {conversation_id}")
                return feedback
            else:
                logger.debug(f"   ⏰ 反馈获取超时 | 对话ID: {conversation_id}")
                return ""
```

### 2. 智能体中的用户交互实现

#### UserProxyAgent集成

```python
# 步骤2: 创建用户反馈智能体
async def get_user_feedback(prompt: str) -> str:
    """获取用户反馈的异步函数"""
    logger.info(f"👤 [用户反馈] 请求用户反馈: {prompt[:100]}...")

    # 将提示信息发送到前端
    feedback_request = {
        "type": "user_feedback_request",
        "content": prompt,
        "source": "testcase_generator",
        "conversation_id": conversation_id,
        "timestamp": datetime.now().isoformat(),
    }

    await put_message_to_queue(
        conversation_id, json.dumps(feedback_request, ensure_ascii=False)
    )

    # 等待用户反馈
    logger.info(f"⏳ [用户反馈] 等待用户反馈...")
    feedback = await get_feedback_from_queue(conversation_id, timeout=300.0)

    if feedback:
        logger.info(f"✅ [用户反馈] 收到用户反馈: {feedback[:100]}...")
        return feedback
    else:
        logger.warning(f"⏰ [用户反馈] 用户反馈超时，使用默认响应")
        return "继续"

user_feedback_agent = UserProxyAgent(
    name="user_feedback",
    input_func=get_user_feedback,
)
```

### 3. API接口层反馈处理

#### 简单反馈接口

```python
@testcase_router.get("/feedback")
async def submit_feedback_simple(conversation_id: str, message: str):
    """
    简单用户反馈接口 - 直接使用message_queue

    功能：接收用户反馈并放入队列，立即返回确认
    - 直接调用put_feedback_to_queue放入队列
    - 立即返回确认消息，不处理流式响应
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

### 4. 前端反馈提交实现

#### 反馈提交函数

```typescript
async function submitFeedback(conversationId: string, feedback: string) {
  try {
    console.log('🔄 提交反馈:', feedback.trim());

    // 提交反馈到简单接口
    const response = await fetch(
      `/api/v1/testcase/feedback?conversation_id=${encodeURIComponent(conversationId)}&message=${encodeURIComponent(feedback.trim())}`,
      { method: 'GET' }
    );

    if (!response.ok) {
      throw new Error(`反馈提交失败: ${response.status}`);
    }

    const result = await response.json();
    console.log('✅ 反馈提交成功:', result);

  } catch (error) {
    console.error('❌ 反馈提交失败:', error);
    throw error;
  }
}
```

## 🔄 完整交互流程

### 1. 智能体请求用户反馈

```
智能体处理 → 需要用户输入 → 发送反馈请求到队列 → SSE推送到前端 → 显示反馈界面
```

### 2. 用户提供反馈

```
用户输入 → 前端提交 → 反馈接口 → 反馈队列 → 智能体获取 → 继续处理
```

### 3. 超时处理

```
智能体等待 → 超时检测 → 使用默认响应 → 继续流程 → 记录超时日志
```

## 🛠️ 高级特性

### 1. 反馈类型分类

```python
# 不同类型的反馈请求
feedback_types = {
    "approval": "请确认是否同意当前结果",
    "optimization": "请提供优化建议",
    "clarification": "请澄清以下问题",
    "selection": "请从以下选项中选择"
}
```

### 2. 超时策略

```python
# 不同场景的超时设置
timeout_configs = {
    "quick_feedback": 30.0,    # 快速反馈
    "detailed_review": 300.0,  # 详细评审
    "complex_decision": 600.0  # 复杂决策
}
```

### 3. 错误恢复

```python
async def robust_feedback_collection(conversation_id: str, prompt: str, max_retries: int = 3):
    """健壮的反馈收集机制"""
    for attempt in range(max_retries):
        try:
            feedback = await get_feedback_from_queue(conversation_id, timeout=60.0)
            if feedback:
                return feedback
        except Exception as e:
            logger.warning(f"反馈收集失败，尝试 {attempt + 1}/{max_retries}: {e}")

    return "继续"  # 默认响应
```

## 📊 性能优化

### 1. 连接管理
- 合理设置SSE连接超时
- 实现客户端自动重连
- 优雅处理连接断开

### 2. 内存控制
- 限制消息队列大小
- 定期清理过期消息
- 避免内存泄漏

### 3. 并发处理
- 支持多个对话并发
- 避免阻塞主线程
- 合理分配资源

## 🔍 调试技巧

### 1. SSE调试
```bash
# 使用curl测试SSE接口
curl -N -H "Accept: text/event-stream" "http://localhost:8000/api/v1/testcase/generate/streaming"
```

### 2. 队列状态监控
```python
# 监控队列状态
info = await get_queue_info(conversation_id)
logger.info(f"队列状态: {info}")
```

### 3. 反馈流程跟踪
```python
# 跟踪反馈流程
logger.info(f"反馈请求发送: {prompt}")
logger.info(f"等待反馈中...")
logger.info(f"收到反馈: {feedback}")
```

## ✅ 最佳实践

1. **错误处理**：完整的异常捕获和日志记录
2. **超时设置**：合理的超时时间和默认响应
3. **用户体验**：清晰的反馈提示和状态显示
4. **性能优化**：避免阻塞和资源泄漏
5. **调试友好**：详细的日志和状态监控

通过这套完整的SSE和反馈机制，可以构建出响应迅速、交互友好的智能体系统。
