# SSE协议规范

## 📡 Server-Sent Events 概述

Server-Sent Events (SSE) 是一种服务器向客户端推送数据的技术，适用于实时数据流传输，如AI对话、进度更新、实时通知等场景。

## 🎯 SSE协议标准

### 1. 基础协议格式

SSE遵循以下标准格式：

```
data: 消息内容
event: 事件类型
id: 消息ID
retry: 重连间隔

```

**注意**: 每个字段后必须有换行符，消息结束需要额外的空行。

### 2. 标准字段说明

- **data**: 实际传输的数据内容
- **event**: 事件类型，客户端可根据类型处理不同消息
- **id**: 消息唯一标识，用于断线重连
- **retry**: 客户端重连间隔（毫秒）

## 🏗️ FastAPI SSE实现

### 1. 基础SSE响应

```python
# api_core/sse.py
from fastapi import Response
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Dict, Any, Optional
import json
import asyncio

class SSEResponse:
    """SSE响应工具类"""

    @staticmethod
    def format_sse_data(
        data: Any,
        event: Optional[str] = None,
        id: Optional[str] = None,
        retry: Optional[int] = None
    ) -> str:
        """格式化SSE数据"""
        lines = []

        # 添加事件类型
        if event:
            lines.append(f"event: {event}")

        # 添加消息ID
        if id:
            lines.append(f"id: {id}")

        # 添加重连间隔
        if retry:
            lines.append(f"retry: {retry}")

        # 添加数据内容
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, ensure_ascii=False)
        else:
            data_str = str(data)

        # 处理多行数据
        for line in data_str.split('\n'):
            lines.append(f"data: {line}")

        # 添加结束标记
        lines.append("")

        return "\n".join(lines) + "\n"

    @staticmethod
    def create_sse_response(generator: AsyncGenerator) -> StreamingResponse:
        """创建SSE响应"""
        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )

# 创建SSE工具实例
sse = SSEResponse()
```

### 2. AI对话SSE实现

```python
# api/v1/ai_chat.py
from fastapi import APIRouter, Depends
from backend.api_core.sse import sse
from backend.services.ai_chat_service import ai_chat_service
from backend.schemas.ai_chat import ChatRequest

router = APIRouter(prefix="/ai-chat", tags=["AI对话"])


@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """流式AI对话"""

    async def chat_generator():
        """聊天数据生成器"""
        try:
            # 发送开始事件
            yield sse.format_sse_data(
                data={"status": "started", "conversation_id": request.conversation_id},
                event="chat_start",
                id="start"
            )

            # 流式获取AI响应
            async for chunk in ai_chat_service.stream_chat(request):
                if chunk.get("type") == "content":
                    # 内容块
                    yield sse.format_sse_data(
                        data={
                            "type": "content",
                            "content": chunk["content"],
                            "delta": chunk.get("delta", "")
                        },
                        event="chat_content",
                        id=chunk.get("id")
                    )
                elif chunk.get("type") == "thinking":
                    # 思考过程
                    yield sse.format_sse_data(
                        data={
                            "type": "thinking",
                            "message": chunk["message"]
                        },
                        event="chat_thinking"
                    )
                elif chunk.get("type") == "tool_call":
                    # 工具调用
                    yield sse.format_sse_data(
                        data={
                            "type": "tool_call",
                            "tool": chunk["tool"],
                            "args": chunk["args"]
                        },
                        event="chat_tool"
                    )

            # 发送完成事件
            yield sse.format_sse_data(
                data={
                    "status": "completed",
                    "total_tokens": chunk.get("total_tokens", 0),
                    "finish_reason": "stop"
                },
                event="chat_complete",
                id="complete"
            )

        except Exception as e:
            # 发送错误事件
            yield sse.format_sse_data(
                data={
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                event="chat_error",
                id="error"
            )

    return sse.create_sse_response(chat_generator())
```

### 3. 测试用例生成SSE

```python
# api/v1/testcase.py
from fastapi import APIRouter
from backend.api_core.sse import sse
from backend.services.testcase_service import testcase_service

router = APIRouter(prefix="/testcase", tags=["测试用例"])


@router.post("/generate/stream")
async def stream_generate_testcase(request: TestCaseRequest):
    """流式生成测试用例"""

    async def testcase_generator():
        """测试用例生成器"""
        try:
            # 开始生成
            yield sse.format_sse_data(
                data={"status": "analyzing", "step": "需求分析"},
                event="testcase_progress"
            )

            # 流式生成过程
            async for step_data in testcase_service.stream_generate(request):
                if step_data["type"] == "analysis":
                    yield sse.format_sse_data(
                        data={
                            "type": "analysis",
                            "content": step_data["content"],
                            "progress": step_data["progress"]
                        },
                        event="testcase_analysis"
                    )

                elif step_data["type"] == "generation":
                    yield sse.format_sse_data(
                        data={
                            "type": "generation",
                            "testcase": step_data["testcase"],
                            "index": step_data["index"]
                        },
                        event="testcase_generated"
                    )

                elif step_data["type"] == "optimization":
                    yield sse.format_sse_data(
                        data={
                            "type": "optimization",
                            "suggestion": step_data["suggestion"]
                        },
                        event="testcase_optimization"
                    )

            # 生成完成
            yield sse.format_sse_data(
                data={
                    "status": "completed",
                    "total_testcases": step_data.get("total", 0)
                },
                event="testcase_complete"
            )

        except Exception as e:
            yield sse.format_sse_data(
                data={"status": "error", "error": str(e)},
                event="testcase_error"
            )

    return sse.create_sse_response(testcase_generator())
```

## 🔄 消息队列集成

### 1. 基于消息队列的SSE

```python
# api_core/message_queue.py
import asyncio
from typing import AsyncGenerator, Dict, Any
from backend.ai_core.message_queue import MessageQueue

async def stream_from_message_queue(
    queue: MessageQueue,
    timeout: int = 300
) -> AsyncGenerator[str, None]:
    """从消息队列流式获取数据"""

    start_time = asyncio.get_event_loop().time()

    try:
        while True:
            current_time = asyncio.get_event_loop().time()

            # 检查超时
            if current_time - start_time > timeout:
                yield sse.format_sse_data(
                    data={"status": "timeout", "message": "请求超时"},
                    event="timeout"
                )
                break

            try:
                # 从队列获取消息
                message = await asyncio.wait_for(
                    queue.get_message(),
                    timeout=1.0
                )

                if message is None:
                    continue

                # 处理特殊消息
                if message.get("type") == "CLOSE":
                    yield sse.format_sse_data(
                        data={"status": "closed"},
                        event="stream_close"
                    )
                    break

                # 格式化并发送消息
                yield sse.format_sse_data(
                    data=message,
                    event=message.get("event", "message"),
                    id=message.get("id")
                )

            except asyncio.TimeoutError:
                # 发送心跳
                yield sse.format_sse_data(
                    data={"type": "heartbeat", "timestamp": current_time},
                    event="heartbeat"
                )
                continue

    except asyncio.CancelledError:
        yield sse.format_sse_data(
            data={"status": "cancelled"},
            event="stream_cancelled"
        )
    except Exception as e:
        yield sse.format_sse_data(
            data={"status": "error", "error": str(e)},
            event="stream_error"
        )
```

### 2. RAG查询SSE

```python
# api/v1/rag.py
from backend.api_core.sse import sse
from backend.rag_core.message_queue import get_streaming_sse_messages_from_queue


@router.post("/query/stream")
async def stream_rag_query(request: RAGQueryRequest):
    """流式RAG查询"""

    async def rag_query_generator():
        """RAG查询生成器"""
        try:
            # 创建消息队列
            queue = MessageQueue()

            # 启动RAG查询任务
            task = asyncio.create_task(
                rag_service.stream_query(request, queue)
            )

            # 流式返回结果
            async for sse_message in get_streaming_sse_messages_from_queue(
                    queue,
                    timeout=300
            ):
                yield sse_message

            # 等待任务完成
            await task

        except Exception as e:
            yield sse.format_sse_data(
                data={"status": "error", "error": str(e)},
                event="rag_error"
            )

    return sse.create_sse_response(rag_query_generator())
```

## 🎨 前端集成示例

### 1. JavaScript客户端

```javascript
// 前端SSE客户端示例
class SSEClient {
    constructor(url, options = {}) {
        this.url = url;
        this.options = options;
        this.eventSource = null;
        this.handlers = new Map();
    }

    connect() {
        this.eventSource = new EventSource(this.url);

        // 通用消息处理
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage('message', data);
            } catch (e) {
                console.error('解析SSE消息失败:', e);
            }
        };

        // 连接打开
        this.eventSource.onopen = () => {
            console.log('SSE连接已建立');
            this.handleMessage('open', {});
        };

        // 连接错误
        this.eventSource.onerror = (error) => {
            console.error('SSE连接错误:', error);
            this.handleMessage('error', error);
        };

        // 注册自定义事件处理器
        this.registerEventHandlers();
    }

    registerEventHandlers() {
        // AI对话事件
        this.addEventListener('chat_start', (data) => {
            console.log('对话开始:', data);
        });

        this.addEventListener('chat_content', (data) => {
            this.appendContent(data.content);
        });

        this.addEventListener('chat_complete', (data) => {
            console.log('对话完成:', data);
        });

        // 测试用例生成事件
        this.addEventListener('testcase_progress', (data) => {
            this.updateProgress(data.progress);
        });

        this.addEventListener('testcase_generated', (data) => {
            this.addTestCase(data.testcase);
        });
    }

    addEventListener(eventType, handler) {
        if (!this.handlers.has(eventType)) {
            this.handlers.set(eventType, []);

            // 注册到EventSource
            this.eventSource.addEventListener(eventType, (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(eventType, data);
                } catch (e) {
                    console.error(`解析${eventType}事件失败:`, e);
                }
            });
        }

        this.handlers.get(eventType).push(handler);
    }

    handleMessage(eventType, data) {
        const handlers = this.handlers.get(eventType) || [];
        handlers.forEach(handler => {
            try {
                handler(data);
            } catch (e) {
                console.error(`处理${eventType}事件失败:`, e);
            }
        });
    }

    close() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}

// 使用示例
const chatSSE = new SSEClient('/api/v1/ai-chat/stream');
chatSSE.connect();
```

### 2. React Hook示例

```javascript
// useSSE Hook
import { useEffect, useRef, useState } from 'react';

export function useSSE(url, options = {}) {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const eventSourceRef = useRef(null);

    useEffect(() => {
        if (!url) return;

        const eventSource = new EventSource(url);
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
            setIsConnected(true);
            setError(null);
        };

        eventSource.onmessage = (event) => {
            try {
                const parsedData = JSON.parse(event.data);
                setData(parsedData);
            } catch (e) {
                setError(e);
            }
        };

        eventSource.onerror = (error) => {
            setError(error);
            setIsConnected(false);
        };

        return () => {
            eventSource.close();
        };
    }, [url]);

    const close = () => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            setIsConnected(false);
        }
    };

    return { data, error, isConnected, close };
}
```

## 🔧 SSE最佳实践

### 1. 错误处理和重连

```python
async def robust_sse_generator():
    """健壮的SSE生成器"""
    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        try:
            async for data in main_data_generator():
                yield sse.format_sse_data(data)
            break  # 成功完成

        except Exception as e:
            retry_count += 1

            if retry_count < max_retries:
                # 发送重试通知
                yield sse.format_sse_data(
                    data={
                        "status": "retrying",
                        "attempt": retry_count,
                        "error": str(e)
                    },
                    event="retry",
                    retry=5000  # 5秒后重试
                )
                await asyncio.sleep(1)
            else:
                # 最终失败
                yield sse.format_sse_data(
                    data={"status": "failed", "error": str(e)},
                    event="error"
                )
```

### 2. 性能优化

```python
async def optimized_sse_generator():
    """优化的SSE生成器"""
    buffer = []
    buffer_size = 10

    async for data in data_source():
        buffer.append(data)

        # 批量发送
        if len(buffer) >= buffer_size:
            yield sse.format_sse_data({
                "type": "batch",
                "items": buffer
            })
            buffer.clear()

    # 发送剩余数据
    if buffer:
        yield sse.format_sse_data({
            "type": "batch",
            "items": buffer
        })
```

### 3. 安全考虑

```python
from fastapi import Depends
from backend.api_core.deps import get_current_user


@router.post("/secure-stream")
async def secure_stream(
        request: StreamRequest,
        current_user=Depends(get_current_user)
):
    """安全的SSE流"""

    async def secure_generator():
        # 验证用户权限
        if not current_user.has_permission("stream_access"):
            yield sse.format_sse_data(
                data={"error": "权限不足"},
                event="error"
            )
            return

        # 限制数据访问
        async for data in filtered_data_source(current_user):
            # 过滤敏感信息
            safe_data = sanitize_data(data, current_user)
            yield sse.format_sse_data(safe_data)

    return sse.create_sse_response(secure_generator())
```
