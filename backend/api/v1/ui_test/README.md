# UI测试API接口文档

## 📋 概述

UI测试API提供了完整的UI界面分析、RAG知识库查询和Collection管理功能。所有接口都使用标准的消息队列SSE流式输出方式，确保实时性和一致性。

## 🏗️ 目录结构

```
backend/api/v1/ui_test/
├── __init__.py              # 主路由注册
├── image_analysis.py        # 图片分析相关接口
├── rag_query.py            # RAG查询相关接口
├── collections.py          # Collection管理接口
└── README.md               # 本文档
```

## 🔗 API路由

### 主路由
- **基础路径**: `/api/v1/ui-test`

### 子模块路由

#### 1. 图片分析模块 (`/image-analysis`)
- `POST /upload` - 上传UI界面图片进行分析
- `GET /progress/{conversation_id}` - 查询分析进度（SSE流式）
- `DELETE /cleanup/{conversation_id}` - 清理分析产生的图片文件
- `GET /status/{conversation_id}` - 获取分析任务状态
- `GET /history` - 获取分析历史记录

#### 2. RAG查询模块 (`/rag-query`)
- `POST /query` - 基于RAG知识库的UI测试查询
- `POST /streaming-query` - 基于RAG的流式UI测试查询
- `GET /streaming-result/{conversation_id}` - 获取流式查询结果（SSE流式）

#### 3. Collection管理模块 (`/collections`)
- `GET /` - 获取UI测试相关的Collection列表
- `GET /{collection_name}` - 获取指定Collection的详细信息
- `GET /{collection_name}/documents` - 获取Collection中的文档列表
- `GET /stats/summary` - 获取UI测试Collection统计摘要
- `GET /{collection_name}/stats` - 获取指定Collection的详细统计

## 🌊 SSE流式输出

### 消息队列集成
所有流式接口都使用 `backend/ai_core/message_queue.py` 中的消息队列系统：

```python
# 发送消息到队列
from backend.ai_core.message_queue import put_message_to_queue

queue_message = {
    "type": "streaming_chunk",
    "source": "UI分析智能体",
    "content": "分析内容",
    "message_type": "streaming",
    "conversation_id": conversation_id,
    "timestamp": datetime.now().isoformat(),
}

await put_message_to_queue(
    conversation_id,
    json.dumps(queue_message, ensure_ascii=False)
)
```

### SSE响应
```python
# 返回SSE流式响应
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

## 📝 消息格式

### 标准消息格式
```json
{
    "type": "streaming_chunk|agent_start|agent_complete|rag_save|agent_error",
    "source": "智能体名称",
    "content": "消息内容",
    "step": "当前步骤描述",
    "conversation_id": "对话ID",
    "timestamp": "2024-06-27T10:30:00.000Z"
}
```

### 消息类型说明
- `agent_start` - 智能体开始处理
- `streaming_chunk` - 流式内容块
- `agent_complete` - 智能体处理完成
- `rag_save` - RAG保存操作
- `rag_query` - RAG查询操作
- `agent_error` - 处理错误
- `query_start` - 查询开始
- `retrieval_progress` - 检索进度
- `retrieval_complete` - 检索完成
- `rag_answer` - RAG回答
- `retrieved_docs` - 检索到的文档
- `query_complete` - 查询完成

## 🔧 使用示例

### 1. 图片上传和分析
```python
# 1. 上传图片
response = await upload_ui_images(
    files=[image_file],
    user_requirement="测试登录页面功能",
    collection_name="ui_testing"
)
conversation_id = response["data"]["conversation_id"]

# 2. 监听分析进度
async for message in get_streaming_sse_messages_from_queue(conversation_id):
    data = json.loads(message.replace("data: ", ""))
    print(f"收到消息: {data['type']} - {data['content']}")
```

### 2. RAG查询
```python
# 1. 启动流式查询
response = await streaming_query_ui_testing_with_rag({
    "user_requirement": "如何测试表单验证功能？",
    "collection_name": "ui_testing"
})
conversation_id = response["data"]["conversation_id"]

# 2. 获取查询结果
async for message in get_streaming_sse_messages_from_queue(conversation_id):
    data = json.loads(message.replace("data: ", ""))
    if data["type"] == "rag_answer":
        print(f"RAG回答: {data['content']}")
```

## 🚀 部署和配置

### 依赖要求
- FastAPI
- 消息队列系统 (`backend/ai_core/message_queue.py`)
- RAG核心系统 (`backend/rag_core`)
- UI测试服务 (`backend/services/ui_testing`)

### 环境配置
确保以下服务正常运行：
- Milvus向量数据库
- RAG知识库系统
- ui_testing Collection已创建

### 路由注册
在 `backend/api/v1/__init__.py` 中已自动注册：
```python
from .ui_test import ui_test_router
v1_router.include_router(ui_test_router, prefix="/ui-test", tags=["UI测试"])
```

## 🔍 调试和监控

### 日志级别
- `DEBUG` - 详细的消息队列操作
- `INFO` - 关键业务操作
- `SUCCESS` - 操作成功确认
- `WARNING` - 异常情况警告
- `ERROR` - 错误信息

### 监控指标
- 消息队列大小
- SSE连接数量
- 分析任务完成率
- RAG查询响应时间

## 📚 相关文档

- [RAG核心系统文档](../../../rag_core/docs/)
- [UI测试服务文档](../../../services/ui_testing/)
- [消息队列系统文档](../../../ai_core/message_queue.py)
- [前端API接口文档](../../../../frontend/src/api/ui-testing.ts)

---

*本文档描述了UI测试API的完整结构和使用方法，为开发和维护提供参考。*
