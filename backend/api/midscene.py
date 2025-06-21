"""
Midscene API 路由
提供 Midscene 智能体系统的 API 接口
"""

import os
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from backend.services.midscene_service import midscene_service

# 创建路由器
router = APIRouter(prefix="/api/midscene", tags=["midscene"])

# 上传目录配置
UPLOAD_DIR = Path("uploads/midscene")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ==================== 数据模型 ====================


class MidsceneGenerateRequest(BaseModel):
    """Midscene 生成请求"""

    user_requirement: str
    conversation_id: Optional[str] = None


class MidsceneUploadResponse(BaseModel):
    """文件上传响应"""

    success: bool
    message: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None


class MidsceneAnalysisResponse(BaseModel):
    """分析响应"""

    success: bool
    user_id: str
    message: str


# ==================== 工具函数 ====================


def save_uploaded_file(file: UploadFile, user_id: str) -> str:
    """保存上传的文件"""
    try:
        # 创建用户目录
        user_dir = UPLOAD_DIR / user_id
        user_dir.mkdir(exist_ok=True)

        # 生成文件名
        file_extension = Path(file.filename).suffix if file.filename else ""
        file_name = f"{uuid.uuid4()}{file_extension}"
        file_path = user_dir / file_name

        # 保存文件
        with open(file_path, "wb") as buffer:
            content = file.file.read()
            buffer.write(content)

        logger.info(f"✅ 文件保存成功: {file_path}")
        return str(file_path)

    except Exception as e:
        logger.error(f"❌ 文件保存失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")


def validate_image_file(file: UploadFile) -> bool:
    """验证图片文件"""
    if not file.filename:
        return False

    # 检查文件扩展名
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        return False

    # 检查文件大小（限制为 10MB）
    if file.size and file.size > 10 * 1024 * 1024:
        return False

    return True


# ==================== API 端点 ====================


@router.post("/upload", response_model=MidsceneUploadResponse)
async def upload_image(file: UploadFile = File(...), user_id: str = Form(...)):
    """
    上传图片文件

    Args:
        file: 上传的图片文件
        user_id: 用户ID

    Returns:
        上传结果
    """
    logger.info(f"📤 接收文件上传请求 - 用户ID: {user_id}")
    logger.info(f"📁 文件名: {file.filename}, 大小: {file.size} bytes")

    try:
        # 验证文件
        if not validate_image_file(file):
            raise HTTPException(
                status_code=400, detail="不支持的文件格式或文件过大（限制10MB）"
            )

        # 保存文件
        file_path = save_uploaded_file(file, user_id)

        return MidsceneUploadResponse(
            success=True,
            message="文件上传成功",
            file_path=file_path,
            file_size=file.size,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/generate/streaming")
async def generate_midscene_streaming(
    request: MidsceneGenerateRequest,
    user_id: str = Form(...),
    files: List[UploadFile] = File(...),
):
    """
    生成 Midscene 测试脚本（流式输出）

    Args:
        request: 生成请求
        user_id: 用户ID
        files: 上传的图片文件列表

    Returns:
        SSE 流式响应
    """
    logger.info(f"🚀 接收 Midscene 生成请求 - 用户ID: {user_id}")
    logger.info(f"📝 用户需求: {request.user_requirement[:100]}...")
    logger.info(f"📷 图片数量: {len(files)}")

    try:
        # 保存上传的文件
        image_paths = []
        for file in files:
            if not validate_image_file(file):
                logger.warning(f"⚠️ 跳过无效文件: {file.filename}")
                continue

            file_path = save_uploaded_file(file, user_id)
            image_paths.append(file_path)

        if not image_paths:
            raise HTTPException(status_code=400, detail="没有有效的图片文件")

        logger.info(f"✅ 保存了 {len(image_paths)} 个图片文件")

        # 启动分析流程
        result_user_id = await midscene_service.start_analysis(
            user_id, image_paths, request.user_requirement
        )

        # 返回流式响应
        return StreamingResponse(
            midscene_service.get_stream_response(result_user_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Midscene 生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/analyze", response_model=MidsceneAnalysisResponse)
async def start_midscene_analysis(
    user_id: str, user_requirement: str, image_paths: List[str]
):
    """
    启动 Midscene 分析（非流式）

    Args:
        user_id: 用户ID
        user_requirement: 用户需求
        image_paths: 图片路径列表

    Returns:
        分析启动结果
    """
    logger.info(f"🔍 启动 Midscene 分析 - 用户ID: {user_id}")

    try:
        # 验证图片文件
        valid_paths = []
        for path in image_paths:
            if Path(path).exists():
                valid_paths.append(path)
            else:
                logger.warning(f"⚠️ 图片文件不存在: {path}")

        if not valid_paths:
            raise HTTPException(status_code=400, detail="没有有效的图片文件")

        # 启动分析
        result_user_id = await midscene_service.start_analysis(
            user_id, valid_paths, user_requirement
        )

        return MidsceneAnalysisResponse(
            success=True, user_id=result_user_id, message="分析已启动"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 启动分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动分析失败: {str(e)}")


@router.get("/stream/{user_id}")
async def get_midscene_stream(user_id: str):
    """
    获取 Midscene 分析的流式输出

    Args:
        user_id: 用户ID

    Returns:
        SSE 流式响应
    """
    logger.info(f"📡 获取流式输出 - 用户ID: {user_id}")

    try:
        return StreamingResponse(
            midscene_service.get_stream_response(user_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            },
        )

    except Exception as e:
        logger.error(f"❌ 获取流式输出失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取流式输出失败: {str(e)}")


@router.delete("/session/{user_id}")
async def cleanup_midscene_session(user_id: str):
    """
    清理 Midscene 会话

    Args:
        user_id: 用户ID

    Returns:
        清理结果
    """
    logger.info(f"🧹 清理会话 - 用户ID: {user_id}")

    try:
        # 清理服务资源
        midscene_service.cleanup_session(user_id)

        # 清理上传的文件（可选）
        user_dir = UPLOAD_DIR / user_id
        if user_dir.exists():
            import shutil

            shutil.rmtree(user_dir)
            logger.info(f"🗑️ 已删除用户文件: {user_dir}")

        return {"success": True, "message": "会话已清理"}

    except Exception as e:
        logger.error(f"❌ 清理会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理会话失败: {str(e)}")


@router.post("/upload_and_analyze")
async def upload_and_analyze(
    files: List[UploadFile] = File(...),
    user_id: str = Form(...),
    user_requirement: str = Form(...),
):
    """
    上传多张图片并开始协作分析，返回流式响应

    Args:
        files: 上传的图片文件列表
        user_id: 用户ID
        user_requirement: 用户需求描述

    Returns:
        SSE 流式响应
    """
    logger.info(f"📤 接收上传请求 - 用户: {user_id}, 文件数量: {len(files)}")
    logger.info(f"📝 用户需求: {user_requirement[:100]}...")

    try:
        # 保存上传的文件
        image_paths = []
        for i, file in enumerate(files):
            if not validate_image_file(file):
                logger.warning(f"⚠️ 跳过无效文件: {file.filename}")
                continue

            file_path = save_uploaded_file(file, user_id)
            image_paths.append(file_path)
            logger.info(f"💾 保存文件 {i+1}/{len(files)}: {file.filename}")

        if not image_paths:
            raise HTTPException(status_code=400, detail="没有有效的图片文件")

        logger.info(f"✅ 保存了 {len(image_paths)} 个图片文件")

        # 启动分析流程
        result_user_id = await midscene_service.start_analysis(
            user_id, image_paths, user_requirement
        )

        # 返回流式响应
        return StreamingResponse(
            midscene_service.get_stream_response(result_user_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 上传分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传分析失败: {str(e)}")


@router.get("/test")
async def test_midscene_api():
    """
    测试 Midscene API

    Returns:
        测试结果
    """
    return {
        "success": True,
        "message": "Midscene API 正常运行",
        "version": "1.0.0",
        "upload_dir": str(UPLOAD_DIR),
        "supported_formats": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
    }
