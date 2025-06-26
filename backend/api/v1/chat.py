import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from backend.ai_core.message_queue import get_streaming_sse_messages_from_queue
from backend.models.chat import ChatRequest, ChatResponse, StreamChunk
from backend.services.ai_chat.autogen_service import autogen_service

chat_router = APIRouter()


# 新的请求模型
class RAGChatRequest(BaseModel):
    """RAG增强聊天请求"""

    message: str
    conversation_id: Optional[str] = None
    system_message: Optional[str] = "你是一个有用的AI助手，请用中文回答问题。"
    collection_name: str = "ai_chat"
    use_rag: bool = True


class FileUploadRequest(BaseModel):
    """文件上传请求"""

    collection_name: str = "ai_chat"


@chat_router.post("/stream/rag")
async def chat_stream_rag(request: RAGChatRequest):
    """
    RAG增强流式聊天接口 - 队列模式，参考testcase.py

    功能：启动RAG增强聊天处理，返回流式输出
    流程：用户输入 → RAG检索 → AutoGen Assistant → 队列消费者 → 流式SSE返回

    采用队列模式：
    1. 启动后台任务处理RAG和Agent流程
    2. 返回队列消费者的流式响应
    3. RAG和Agent将消息放入队列，消费者从队列取出并流式返回

    Args:
        request: RAG聊天请求对象

    Returns:
        StreamingResponse: SSE流式响应，实时返回RAG和Agent处理结果
    """
    # 生成或使用提供的对话ID
    conversation_id = request.conversation_id or str(uuid.uuid4())

    logger.info(f"🚀 [API-RAG流式聊天-队列模式] 收到RAG增强流式聊天请求")
    logger.info(f"   📋 对话ID: {conversation_id}")
    logger.info(f"   📝 消息: {request.message[:100]}...")
    logger.info(f"   📚 Collection: {request.collection_name}")
    logger.info(f"   🔍 使用RAG: {request.use_rag}")
    logger.info(f"   🌐 请求方法: POST /api/chat/stream/rag (队列模式)")

    try:
        # 启动后台任务处理RAG和Agent流程 - 参考testcase.py
        logger.info(
            f"🚀 [API-RAG流式聊天-队列模式] 启动后台任务 | 对话ID: {conversation_id}"
        )

        # 创建后台任务处理RAG增强聊天
        async def process_rag_chat():
            try:
                # 调用autogen_service的start_rag_chat_stream方法
                # 该方法将消息放入队列，不返回流式内容
                await autogen_service.start_rag_chat_stream(
                    message=request.message,
                    conversation_id=conversation_id,
                    system_message=request.system_message,
                    collection_name=request.collection_name,
                    use_rag=request.use_rag,
                )

            except Exception as e:
                logger.error(
                    f"❌ [API-RAG流式聊天-队列模式] 后台任务失败 | 对话ID: {conversation_id} | 错误: {e}"
                )
                # 发送错误信息到队列
                import json

                from backend.ai_core.message_queue import put_message_to_queue

                error_message = json.dumps(
                    {
                        "type": "error",
                        "source": "系统",
                        "content": f"❌ 处理失败: {str(e)}",
                        "timestamp": datetime.now().isoformat(),
                    },
                    ensure_ascii=False,
                )
                await put_message_to_queue(conversation_id, error_message)
                await put_message_to_queue(conversation_id, "CLOSE")

        asyncio.create_task(process_rag_chat())

        # 返回队列消费者的流式响应 - 直接使用message_queue的SSE函数
        logger.info(
            f"📡 [API-RAG流式聊天-队列模式] 返回队列消费者流式响应 | 对话ID: {conversation_id}"
        )

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

    except Exception as e:
        logger.error(
            f"❌ [API-RAG流式聊天-队列模式] 接口异常 | 对话ID: {conversation_id} | 错误: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/stream")
async def chat_stream(request: ChatRequest):
    """流式聊天接口（兼容旧版本）"""
    conversation_id = request.conversation_id or str(uuid.uuid4())
    logger.info(
        f"收到流式聊天请求 | 对话ID: {conversation_id} | 消息: {request.message[:50]}..."
    )

    try:

        async def generate():
            try:
                logger.debug(f"开始生成流式响应 | 对话ID: {conversation_id}")
                chunk_count = 0

                async for chunk in autogen_service.chat_stream(
                    message=request.message,
                    conversation_id=conversation_id,
                    system_message=request.system_message or "你是一个有用的AI助手",
                ):
                    chunk_count += 1
                    logger.debug(
                        f"生成第 {chunk_count} 个数据块 | 内容长度: {len(chunk)}"
                    )

                    # 发送内容块
                    chunk_data = StreamChunk(
                        content=chunk,
                        is_complete=False,
                        conversation_id=conversation_id,
                    )
                    yield f"data: {chunk_data.model_dump_json()}\n\n"

                # 发送完成信号
                final_chunk = StreamChunk(
                    content="", is_complete=True, conversation_id=conversation_id
                )
                yield f"data: {final_chunk.model_dump_json()}\n\n"
                logger.success(
                    f"流式响应完成 | 对话ID: {conversation_id} | 总块数: {chunk_count}"
                )

            except Exception as e:
                logger.error(
                    f"流式响应生成失败 | 对话ID: {conversation_id} | 错误: {e}"
                )
                error_chunk = StreamChunk(
                    content=f"错误: {str(e)}",
                    is_complete=True,
                    conversation_id=conversation_id,
                )
                yield f"data: {error_chunk.model_dump_json()}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            },
        )

    except Exception as e:
        logger.error(f"流式聊天接口异常 | 对话ID: {conversation_id} | 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """普通聊天接口"""
    conversation_id = request.conversation_id or str(uuid.uuid4())
    logger.info(
        f"收到普通聊天请求 | 对话ID: {conversation_id} | 消息: {request.message[:50]}..."
    )

    try:
        response_message, conv_id = await autogen_service.chat(
            message=request.message,
            conversation_id=conversation_id,
            system_message=request.system_message,
        )

        logger.success(
            f"普通聊天响应完成 | 对话ID: {conv_id} | 响应长度: {len(response_message)}"
        )

        return ChatResponse(
            message=response_message, conversation_id=conv_id, timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"普通聊天接口异常 | 对话ID: {conversation_id} | 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.delete("/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """清除对话历史"""
    logger.info(f"收到清除对话请求 | 对话ID: {conversation_id}")

    try:
        autogen_service.clear_conversation(conversation_id)
        logger.success(f"对话清除成功 | 对话ID: {conversation_id}")
        return {"message": "对话已清除", "conversation_id": conversation_id}
    except Exception as e:
        logger.error(f"清除对话失败 | 对话ID: {conversation_id} | 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/upload")
async def upload_file_to_rag(
    files: List[UploadFile] = File(...), collection_name: str = Form("ai_chat")
):
    """上传文件到RAG知识库"""
    logger.info(
        f"收到文件上传请求 | 文件数量: {len(files)} | Collection: {collection_name}"
    )

    try:
        results = []
        upload_dir = Path("backend/data/uploads/chat")
        upload_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            # 保存上传的文件
            file_path = upload_dir / file.filename
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            # 添加到RAG知识库
            result = await autogen_service.add_file_to_rag(
                str(file_path), collection_name
            )

            # 清理临时文件
            file_path.unlink()

            results.append({"filename": file.filename, "result": result})

        logger.success(
            f"文件上传完成 | 成功: {sum(1 for r in results if r['result']['success'])}/{len(results)}"
        )

        return {
            "success": True,
            "message": f"处理了 {len(files)} 个文件",
            "results": results,
            "collection_name": collection_name,
        }

    except Exception as e:
        logger.error(f"文件上传失败 | 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.get("/collections")
async def get_rag_collections():
    """获取可用的RAG collections"""
    logger.debug("收到获取RAG collections请求")

    try:
        from backend.services.rag.collection_service import collection_service

        # 从数据库获取Collections
        collections = await collection_service.get_collection_names()
        logger.debug(f"可用RAG collections: {collections}")

        return {"success": True, "collections": collections}
    except Exception as e:
        logger.error(f"获取RAG collections失败 | 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.get("/stats")
async def get_agent_stats():
    """获取 Agent 统计信息，包括RAG状态"""
    logger.debug("收到 Agent 统计信息请求")

    try:
        stats = await autogen_service.get_agent_stats()
        logger.debug(f"Agent 统计信息: {stats}")
        return stats
    except Exception as e:
        logger.error(f"获取 Agent 统计信息失败 | 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/cleanup")
async def force_cleanup():
    """强制清理过期的 Agent"""
    logger.info("收到强制清理请求")

    try:
        autogen_service.force_cleanup()
        stats = autogen_service.get_agent_stats()
        logger.success("强制清理完成")
        return {"message": "清理完成", "stats": stats}
    except Exception as e:
        logger.error(f"强制清理失败 | 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
