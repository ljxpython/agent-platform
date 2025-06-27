"""
UI图片分析API接口
支持图片上传、UI分析、进度查询等功能
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from backend.ai_core.message_queue import get_streaming_sse_messages_from_queue
from backend.services.ui_testing.midscene_service import MidsceneService

ui_image_analysis_router = APIRouter()


class ImageUploadRequest(BaseModel):
    """图片上传请求"""

    user_requirement: str
    collection_name: str = "ui_testing"
    user_id: str = "anonymous"


@ui_image_analysis_router.post("/upload", summary="上传UI界面图片进行分析")
async def upload_ui_images(
    files: List[UploadFile] = File(...),
    user_requirement: str = Form(...),
    collection_name: str = Form("ui_testing"),
    user_id: str = Form("anonymous"),
):
    """
    上传UI界面图片，进行UI元素分析并存入RAG知识库

    功能流程：
    1. 保存上传的图片文件
    2. 启动UIAnalysisAgent进行UI元素分析
    3. 将分析结果存入RAG知识库
    4. 返回分析任务ID用于后续查询进度
    """
    try:
        logger.info(
            f"📸 [UI图片分析] 收到图片上传请求 | 文件数: {len(files)} | 用户需求: {user_requirement[:100]}..."
        )

        if not files:
            raise HTTPException(status_code=400, detail="请至少上传一个图片文件")

        # 创建上传目录
        upload_dir = Path("uploads/ui_images")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 保存上传的图片文件
        saved_files = []
        for file in files:
            if not file.content_type.startswith("image/"):
                logger.warning(f"⚠️ 跳过非图片文件: {file.filename}")
                continue

            # 生成唯一文件名
            timestamp = int(time.time() * 1000)
            file_extension = Path(file.filename).suffix
            unique_filename = f"{user_id}_{timestamp}_{file.filename}"
            file_path = upload_dir / unique_filename

            # 保存文件
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            saved_files.append(str(file_path))
            logger.info(f"✅ 图片保存成功: {file_path}")

        if not saved_files:
            raise HTTPException(status_code=400, detail="没有有效的图片文件")

        # 启动UI分析服务
        logger.info(f"🚀 [UI图片分析] 启动后台任务 | 文件数: {len(saved_files)}")
        midscene_service = MidsceneService()
        conversation_id = await midscene_service.start_analysis(
            user_id=user_id, image_paths=saved_files, user_requirement=user_requirement
        )

        logger.info(f"✅ [UI图片分析] 分析任务启动成功 | 对话ID: {conversation_id}")

        return {
            "code": 200,
            "msg": "图片上传成功，UI分析已启动",
            "data": {
                "conversation_id": conversation_id,
                "uploaded_files": len(saved_files),
                "file_paths": saved_files,
                "collection_name": collection_name,
                "user_requirement": user_requirement,
            },
        }

    except Exception as e:
        logger.error(f"❌ [UI图片分析] 上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@ui_image_analysis_router.get("/progress/{conversation_id}", summary="查询UI分析进度")
async def get_analysis_progress(conversation_id: str):
    """
    查询UI分析进度
    使用消息队列的SSE流式响应，实时显示分析进度
    """
    try:
        logger.info(f"📡 [UI图片分析-SSE] 开始流式响应 | 对话ID: {conversation_id}")

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
        logger.error(f"❌ [UI图片分析-SSE] 查询分析进度失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询进度失败: {str(e)}")


@ui_image_analysis_router.delete(
    "/cleanup/{conversation_id}", summary="清理分析产生的图片文件"
)
async def cleanup_analysis_images(conversation_id: str):
    """清理指定对话ID产生的图片文件"""
    try:
        logger.info(f"🧹 [UI图片分析] 清理分析图片 | 对话ID: {conversation_id}")

        upload_dir = Path("uploads/ui_images")
        if not upload_dir.exists():
            return {"code": 200, "msg": "无需清理", "data": {"deleted_files": 0}}

        deleted_count = 0
        # 根据对话ID模式匹配文件
        for file_path in upload_dir.glob(f"*{conversation_id}*"):
            try:
                file_path.unlink()
                deleted_count += 1
                logger.info(f"🗑️ 删除文件: {file_path}")
            except Exception as e:
                logger.warning(f"⚠️ 删除文件失败 {file_path}: {e}")

        logger.success(f"✅ [UI图片分析] 图片清理完成 | 删除文件数: {deleted_count}")

        return {
            "code": 200,
            "msg": "图片清理完成",
            "data": {"deleted_files": deleted_count},
        }

    except Exception as e:
        logger.error(f"❌ [UI图片分析] 清理图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")


@ui_image_analysis_router.get("/status/{conversation_id}", summary="获取分析任务状态")
async def get_analysis_status(conversation_id: str):
    """获取分析任务的当前状态"""
    try:
        logger.info(f"📊 [UI图片分析] 查询任务状态 | 对话ID: {conversation_id}")

        # 这里可以添加任务状态查询逻辑
        # 暂时返回基本信息
        return {
            "code": 200,
            "msg": "状态查询成功",
            "data": {
                "conversation_id": conversation_id,
                "status": "processing",  # processing, completed, failed
                "timestamp": time.time(),
            },
        }

    except Exception as e:
        logger.error(f"❌ [UI图片分析] 状态查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"状态查询失败: {str(e)}")


@ui_image_analysis_router.get("/history", summary="获取分析历史记录")
async def get_analysis_history(
    user_id: str = "anonymous", limit: int = 10, offset: int = 0
):
    """获取用户的分析历史记录"""
    try:
        logger.info(f"📚 [UI图片分析] 查询历史记录 | 用户: {user_id} | 限制: {limit}")

        # 这里可以添加历史记录查询逻辑
        # 暂时返回空列表
        return {
            "code": 200,
            "msg": "历史记录查询成功",
            "data": {
                "records": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
            },
        }

    except Exception as e:
        logger.error(f"❌ [UI图片分析] 历史记录查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"历史记录查询失败: {str(e)}")
