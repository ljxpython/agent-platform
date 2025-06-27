"""
UI测试RAG查询API接口
基于RAG知识库的UI测试查询和智能助手功能
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from backend.ai_core.message_queue import (
    get_streaming_sse_messages_from_queue,
    put_message_to_queue,
)
from backend.services.rag.rag_service import RAGService, get_rag_service

ui_rag_query_router = APIRouter()


class UITestingQueryRequest(BaseModel):
    """UI测试查询请求"""

    user_requirement: str
    collection_name: str = "ui_testing"
    user_id: str = "anonymous"
    enable_streaming: bool = False  # 是否启用流式响应


class UITestingStreamingQueryRequest(BaseModel):
    """UI测试流式查询请求"""

    user_requirement: str
    collection_name: str = "ui_testing"
    user_id: str = "anonymous"


@ui_rag_query_router.post("/query", summary="基于RAG知识库的UI测试查询")
async def query_ui_testing_with_rag(request: UITestingQueryRequest):
    """
    基于RAG知识库进行UI测试查询

    功能流程：
    1. 从RAG知识库检索相关UI测试经验
    2. 使用LLM生成增强的测试建议
    3. 返回完整的查询结果和相关文档
    """
    try:
        logger.info(
            f"🔍 [UI测试RAG查询] 收到查询请求 | 用户需求: {request.user_requirement[:100]}..."
        )

        # 使用RAG服务查询相关经验
        rag_service = await get_rag_service()
        await rag_service.initialize()

        query_result = await rag_service.query_collection(
            question=f"UI自动化测试相关经验，用户需求：{request.user_requirement}",
            collection_name=request.collection_name,
            top_k=5,
        )

        if not query_result.get("success", False):
            logger.warning(
                f"⚠️ [UI测试RAG查询] RAG查询失败: {query_result.get('error', '未知错误')}"
            )
            return {
                "code": 400,
                "msg": "知识库查询失败",
                "data": {
                    "error": query_result.get("error", "未知错误"),
                    "user_requirement": request.user_requirement,
                },
            }

        # 生成对话ID
        conversation_id = f"rag_query_{request.user_id}_{int(time.time() * 1000)}"

        logger.success(f"✅ [UI测试RAG查询] 查询成功 | 对话ID: {conversation_id}")

        return {
            "code": 200,
            "msg": "RAG查询成功",
            "data": {
                "conversation_id": conversation_id,
                "rag_answer": query_result.get("answer", ""),
                "retrieved_docs": query_result.get("retrieved_docs", []),
                "user_requirement": request.user_requirement,
                "collection_name": request.collection_name,
                "query_time": datetime.now().isoformat(),
            },
        }

    except Exception as e:
        logger.error(f"❌ [UI测试RAG查询] 查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@ui_rag_query_router.post("/streaming-query", summary="基于RAG的流式UI测试查询")
async def streaming_query_ui_testing_with_rag(request: UITestingStreamingQueryRequest):
    """
    基于RAG知识库进行流式UI测试查询
    启动后台任务进行RAG增强查询，返回对话ID用于SSE流式获取结果
    """
    try:
        logger.info(
            f"🌊 [UI测试RAG流式查询] 收到流式查询请求 | 用户需求: {request.user_requirement[:100]}..."
        )

        # 生成对话ID
        conversation_id = f"rag_streaming_{request.user_id}_{int(time.time() * 1000)}"

        # 启动后台任务处理RAG流式查询
        logger.info(f"🚀 [UI测试RAG流式查询] 启动后台任务 | 对话ID: {conversation_id}")
        asyncio.create_task(_process_streaming_rag_query(conversation_id, request))

        return {
            "code": 200,
            "msg": "流式查询已启动",
            "data": {
                "conversation_id": conversation_id,
                "user_requirement": request.user_requirement,
                "collection_name": request.collection_name,
                "start_time": datetime.now().isoformat(),
            },
        }

    except Exception as e:
        logger.error(f"❌ [UI测试RAG流式查询] 启动失败: {e}")
        raise HTTPException(status_code=500, detail=f"流式查询启动失败: {str(e)}")


@ui_rag_query_router.get(
    "/streaming-result/{conversation_id}", summary="获取流式查询结果"
)
async def get_streaming_query_result(conversation_id: str):
    """
    获取流式查询结果
    使用消息队列的SSE流式响应
    """
    try:
        logger.info(
            f"📡 [UI测试RAG流式查询-SSE] 开始流式响应 | 对话ID: {conversation_id}"
        )

        # 直接使用message_queue的SSE流式函数
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
        logger.error(f"❌ [UI测试RAG流式查询-SSE] 获取流式结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取流式结果失败: {str(e)}")


async def _process_streaming_rag_query(
    conversation_id: str, request: UITestingStreamingQueryRequest
) -> None:
    """
    处理流式RAG查询的后台任务
    """
    try:
        logger.info(f"🔄 [UI测试RAG流式查询-后台] 开始处理 | 对话ID: {conversation_id}")

        # 发送开始消息
        start_message = {
            "type": "query_start",
            "source": "UI测试RAG查询",
            "content": "开始从知识库检索相关UI测试经验...",
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
        }
        await put_message_to_queue(
            conversation_id, json.dumps(start_message, ensure_ascii=False)
        )

        # 使用RAG服务查询
        rag_service = await get_rag_service()
        await rag_service.initialize()

        # 发送检索消息
        retrieval_message = {
            "type": "retrieval_progress",
            "source": "UI测试RAG查询",
            "content": f"正在检索与'{request.user_requirement[:50]}...'相关的UI测试经验",
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
        }
        await put_message_to_queue(
            conversation_id, json.dumps(retrieval_message, ensure_ascii=False)
        )

        query_result = await rag_service.query_collection(
            question=f"UI自动化测试相关经验，用户需求：{request.user_requirement}",
            collection_name=request.collection_name,
            top_k=5,
        )

        if query_result.get("success", False):
            # 发送检索完成消息
            retrieval_complete_message = {
                "type": "retrieval_complete",
                "source": "UI测试RAG查询",
                "content": f"检索完成，找到{len(query_result.get('retrieved_docs', []))}个相关文档",
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
            }
            await put_message_to_queue(
                conversation_id,
                json.dumps(retrieval_complete_message, ensure_ascii=False),
            )

            # 发送RAG回答
            answer_message = {
                "type": "rag_answer",
                "source": "UI测试RAG查询",
                "content": query_result.get("answer", ""),
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
            }
            await put_message_to_queue(
                conversation_id, json.dumps(answer_message, ensure_ascii=False)
            )

            # 发送检索文档
            docs_message = {
                "type": "retrieved_docs",
                "source": "UI测试RAG查询",
                "content": json.dumps(
                    query_result.get("retrieved_docs", []), ensure_ascii=False
                ),
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
            }
            await put_message_to_queue(
                conversation_id, json.dumps(docs_message, ensure_ascii=False)
            )

        else:
            # 发送错误消息
            error_message = {
                "type": "query_error",
                "source": "UI测试RAG查询",
                "content": f"查询失败: {query_result.get('error', '未知错误')}",
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
            }
            await put_message_to_queue(
                conversation_id, json.dumps(error_message, ensure_ascii=False)
            )

        # 发送完成消息
        complete_message = {
            "type": "query_complete",
            "source": "UI测试RAG查询",
            "content": "RAG查询处理完成",
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
        }
        await put_message_to_queue(
            conversation_id, json.dumps(complete_message, ensure_ascii=False)
        )

        # 发送关闭信号
        await put_message_to_queue(conversation_id, "CLOSE")

        logger.success(
            f"✅ [UI测试RAG流式查询-后台] 处理完成 | 对话ID: {conversation_id}"
        )

    except Exception as e:
        logger.error(f"❌ [UI测试RAG流式查询-后台] 处理失败: {e}")

        # 发送错误消息
        error_message = {
            "type": "system_error",
            "source": "UI测试RAG查询",
            "content": f"系统错误: {str(e)}",
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
        }
        await put_message_to_queue(
            conversation_id, json.dumps(error_message, ensure_ascii=False)
        )

        # 发送关闭信号
        await put_message_to_queue(conversation_id, "CLOSE")
