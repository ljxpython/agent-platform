# UI测试服务消息队列重构总结

## 📋 重构概述

根据要求，对UI测试服务进行了全面重构，主要包括：
1. **修正SSE流式输出方式** - 使用标准的消息队列实现
2. **重新组织API目录结构** - 在v1目录下创建ui_test子目录
3. **统一消息格式** - 复用backend/ai_core/message_queue.py的功能

## 🔄 主要变更

### 1. API目录结构重组

#### 原结构
```
backend/api/v1/ui_testing.py  # 单文件包含所有接口
```

#### 新结构
```
backend/api/v1/ui_test/
├── __init__.py              # 主路由注册
├── image_analysis.py        # 图片分析相关接口
├── rag_query.py            # RAG查询相关接口
├── collections.py          # Collection管理接口
└── README.md               # API文档
```

### 2. 消息队列SSE流式输出修正

#### 原实现（错误）
```python
def generate_progress():
    """自定义生成器"""
    try:
        message_gen = get_message_generator(conversation_id)
        for message in message_gen:
            yield f"data: {json.dumps(message)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

return StreamingResponse(generate_progress(), ...)
```

#### 新实现（正确）
```python
# 直接使用message_queue的SSE流式函数
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

### 3. 消息格式标准化

#### 原格式
```python
await put_message_to_queue(
    conversation_id,
    json.dumps({
        "type": "agent_start",
        "agent": "UI分析智能体",
        "step": "开始分析",
        "content": "...",
        "timestamp": "..."
    })
)
```

#### 新格式（标准化）
```python
queue_message = {
    "type": "streaming_chunk",
    "source": "UI分析智能体",           # 统一使用source字段
    "content": item.content,
    "message_type": "streaming",
    "conversation_id": conversation_id,  # 添加conversation_id
    "timestamp": datetime.now().isoformat(),
}

await put_message_to_queue(
    conversation_id,
    json.dumps(queue_message, ensure_ascii=False)
)
```

## 🛠️ 具体修改内容

### 1. 后端API接口重构

#### `backend/api/v1/ui_test/__init__.py`
- 创建UI测试主路由
- 注册三个子模块路由
- 统一标签管理

#### `backend/api/v1/ui_test/image_analysis.py`
- **图片上传接口**: `POST /upload`
- **分析进度查询**: `GET /progress/{conversation_id}` (SSE流式)
- **资源清理**: `DELETE /cleanup/{conversation_id}`
- **任务状态查询**: `GET /status/{conversation_id}`
- **历史记录**: `GET /history`

#### `backend/api/v1/ui_test/rag_query.py`
- **标准RAG查询**: `POST /query`
- **流式RAG查询**: `POST /streaming-query`
- **流式结果获取**: `GET /streaming-result/{conversation_id}` (SSE流式)
- **后台任务处理**: `_process_streaming_rag_query()`

#### `backend/api/v1/ui_test/collections.py`
- **Collection列表**: `GET /`
- **Collection详情**: `GET /{collection_name}`
- **文档列表**: `GET /{collection_name}/documents`
- **统计摘要**: `GET /stats/summary`
- **详细统计**: `GET /{collection_name}/stats`

### 2. 服务层消息队列修正

#### `backend/services/ui_testing/agents.py`
修正了所有智能体的消息队列使用方式：

**UIAnalysisAgent修改**:
- 统一消息格式，使用`source`字段
- 添加`conversation_id`到消息中
- 正确的流式消息构建
- 添加`CLOSE`信号发送

**MidsceneGenerationAgent修改**:
- RAG查询消息标准化
- 流式输出消息格式统一
- 错误处理消息规范化

### 3. 前端API接口更新

#### `frontend/src/api/ui-testing.ts`
更新所有API端点路径：
- `/ui-testing/upload-images` → `/ui-test/image-analysis/upload`
- `/ui-testing/analysis-progress/` → `/ui-test/image-analysis/progress/`
- `/ui-testing/query-with-rag` → `/ui-test/rag-query/query`
- `/ui-testing/collections` → `/ui-test/collections/`
- `/ui-testing/images/` → `/ui-test/image-analysis/cleanup/`

### 4. 路由注册更新

#### `backend/api/v1/__init__.py`
```python
# 原注册
from .ui_testing import ui_testing_router
v1_router.include_router(ui_testing_router, prefix="/ui-testing", tags=["UI测试"])

# 新注册
from .ui_test import ui_test_router
v1_router.include_router(ui_test_router, prefix="/ui-test", tags=["UI测试"])
```

## 🎯 核心改进

### 1. 消息队列使用规范化
- **复用现有功能**: 完全使用`backend/ai_core/message_queue.py`的功能
- **标准化消息格式**: 遵循testcase服务的消息格式规范
- **正确的SSE实现**: 使用`get_streaming_sse_messages_from_queue`函数

### 2. API结构模块化
- **清晰的职责分离**: 图片分析、RAG查询、Collection管理分别独立
- **统一的错误处理**: 所有接口使用一致的错误响应格式
- **完整的文档**: 每个模块都有详细的API文档

### 3. 流式输出优化
- **实时性**: 使用消息队列确保消息的实时传递
- **可靠性**: 内置超时和错误处理机制
- **一致性**: 与其他服务（如testcase）保持一致的流式输出方式

## 🔧 使用示例

### 后台任务启动模式
```python
# API层写法
logger.info(f"🚀 [API-流式生成-队列模式] 启动后台任务 | 对话ID: {conversation_id}")
asyncio.create_task(process_ui_analysis(conversation_id, request))

# 返回队列消费者的流式响应
logger.info(f"📡 [API-流式生成-队列模式] 返回队列消费者流式响应 | 对话ID: {conversation_id}")
return StreamingResponse(
    get_streaming_sse_messages_from_queue(conversation_id),
    media_type="text/plain",
    headers={...}
)
```

### 服务层消息发送
```python
# 构建标准化消息
queue_message = {
    "type": "streaming_chunk",
    "source": "UI分析智能体",
    "content": chunk_content,
    "message_type": "streaming",
    "conversation_id": conversation_id,
    "timestamp": datetime.now().isoformat(),
}

# 发送到队列
await put_message_to_queue(
    conversation_id,
    json.dumps(queue_message, ensure_ascii=False)
)

# 发送关闭信号
await put_message_to_queue(conversation_id, "CLOSE")
```

## 📊 测试验证

### 1. API接口测试
- 所有新的API端点都需要测试
- 验证SSE流式输出的正确性
- 确认消息格式的一致性

### 2. 消息队列测试
- 验证消息的正确发送和接收
- 测试超时和错误处理
- 确认CLOSE信号的正确处理

### 3. 集成测试
- 端到端的UI分析流程测试
- RAG查询功能验证
- 前后端集成测试

## 🚀 部署注意事项

1. **路由更新**: 确保前端API调用使用新的路径
2. **消息队列**: 确保消息队列服务正常运行
3. **RAG系统**: 确保RAG核心系统和ui_testing Collection可用
4. **日志监控**: 关注新的日志格式和错误信息

## 📚 相关文档

- [UI测试API文档](../../../api/v1/ui_test/README.md)
- [消息队列系统文档](../../../ai_core/message_queue.py)
- [RAG集成文档](./README_RAG_INTEGRATION.md)
- [测试用例服务参考](../testcase/agents.py)

---

*本次重构确保了UI测试服务与整个系统的消息队列架构保持一致，提供了更可靠和标准化的流式输出功能。*
