"""
Midscene 管理 API 路由
提供 Midscene 系统的管理功能
"""

from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel

from backend.models.midscene import (
    MidsceneAgentLog,
    MidsceneSession,
    MidsceneStatistics,
    MidsceneUploadedFile,
)
from backend.services.midscene_service import midscene_service

# 创建路由器
router = APIRouter(prefix="/api/midscene/admin", tags=["midscene-admin"])


# ==================== 数据模型 ====================


class SessionListResponse(BaseModel):
    """会话列表响应"""

    total: int
    sessions: List[dict]


class SessionDetailResponse(BaseModel):
    """会话详情响应"""

    session: dict
    agent_logs: List[dict]
    uploaded_files: List[dict]


class StatisticsResponse(BaseModel):
    """统计响应"""

    daily_stats: List[dict]
    summary: dict


class DeleteResponse(BaseModel):
    """删除响应"""

    success: bool
    message: str
    deleted_count: int


# ==================== 会话管理 ====================


@router.get("/sessions", response_model=SessionListResponse)
async def get_sessions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
):
    """
    获取会话列表
    """
    logger.info(f"📋 获取会话列表 - 页码: {page}, 每页: {page_size}")

    try:
        # 构建查询
        query = MidsceneSession.all()

        # 状态筛选
        if status:
            query = query.filter(status=status)

        # 用户筛选
        if user_id:
            query = query.filter(user_id=user_id)

        # 日期筛选
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(created_at__gte=start_dt)

        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(created_at__lt=end_dt)

        # 获取总数
        total = await query.count()

        # 分页查询
        offset = (page - 1) * page_size
        sessions = await query.order_by("-created_at").offset(offset).limit(page_size)

        # 转换为字典
        session_list = []
        for session in sessions:
            session_dict = {
                "id": session.id,
                "session_id": session.session_id,
                "user_id": session.user_id,
                "user_requirement": (
                    session.user_requirement[:100] + "..."
                    if len(session.user_requirement) > 100
                    else session.user_requirement
                ),
                "status": session.status,
                "file_count": session.file_count,
                "processing_time": session.processing_time,
                "created_at": (
                    session.created_at.isoformat() if session.created_at else None
                ),
                "completed_at": (
                    session.completed_at.isoformat() if session.completed_at else None
                ),
            }
            session_list.append(session_dict)

        return SessionListResponse(total=total, sessions=session_list)

    except Exception as e:
        logger.error(f"❌ 获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(session_id: str):
    """
    获取会话详情
    """
    logger.info(f"📖 获取会话详情: {session_id}")

    try:
        # 获取会话信息
        session = await MidsceneSession.get_or_none(session_id=session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 获取智能体日志
        agent_logs = await MidsceneAgentLog.filter(session_id=session_id).order_by(
            "started_at"
        )

        # 获取上传文件
        uploaded_files = await MidsceneUploadedFile.filter(
            session_id=session_id
        ).order_by("uploaded_at")

        # 转换为字典
        session_dict = {
            "id": session.id,
            "session_id": session.session_id,
            "user_id": session.user_id,
            "user_requirement": session.user_requirement,
            "status": session.status,
            "uploaded_files": session.uploaded_files,
            "file_count": session.file_count,
            "ui_analysis_result": session.ui_analysis_result,
            "interaction_analysis_result": session.interaction_analysis_result,
            "midscene_generation_result": session.midscene_generation_result,
            "script_generation_result": session.script_generation_result,
            "yaml_script": session.yaml_script,
            "playwright_script": session.playwright_script,
            "script_info": session.script_info,
            "processing_time": session.processing_time,
            "agent_count": session.agent_count,
            "total_tokens": session.total_tokens,
            "created_at": (
                session.created_at.isoformat() if session.created_at else None
            ),
            "updated_at": (
                session.updated_at.isoformat() if session.updated_at else None
            ),
            "completed_at": (
                session.completed_at.isoformat() if session.completed_at else None
            ),
        }

        agent_logs_list = []
        for log in agent_logs:
            log_dict = {
                "id": log.id,
                "agent_name": log.agent_name,
                "agent_type": log.agent_type,
                "step": log.step,
                "status": log.status,
                "input_content": log.input_content,
                "output_content": log.output_content,
                "error_message": log.error_message,
                "processing_time": log.processing_time,
                "token_count": log.token_count,
                "chunk_count": log.chunk_count,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "completed_at": (
                    log.completed_at.isoformat() if log.completed_at else None
                ),
            }
            agent_logs_list.append(log_dict)

        uploaded_files_list = []
        for file_record in uploaded_files:
            file_dict = {
                "id": file_record.id,
                "original_filename": file_record.original_filename,
                "stored_filename": file_record.stored_filename,
                "file_path": file_record.file_path,
                "file_size": file_record.file_size,
                "file_type": file_record.file_type,
                "mime_type": file_record.mime_type,
                "image_width": file_record.image_width,
                "image_height": file_record.image_height,
                "image_format": file_record.image_format,
                "status": file_record.status,
                "uploaded_at": (
                    file_record.uploaded_at.isoformat()
                    if file_record.uploaded_at
                    else None
                ),
            }
            uploaded_files_list.append(file_dict)

        return SessionDetailResponse(
            session=session_dict,
            agent_logs=agent_logs_list,
            uploaded_files=uploaded_files_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取会话详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话详情失败: {str(e)}")


@router.delete("/sessions/{session_id}", response_model=DeleteResponse)
async def delete_session(session_id: str):
    """
    删除会话
    """
    logger.info(f"🗑️ 删除会话: {session_id}")

    try:
        # 检查会话是否存在
        session = await MidsceneSession.get_or_none(session_id=session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 删除会话及相关数据
        await midscene_service.delete_session(session_id)

        return DeleteResponse(success=True, message="会话删除成功", deleted_count=1)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


# ==================== 统计分析 ====================


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(days: int = Query(30, ge=1, le=365, description="统计天数")):
    """
    获取统计数据
    """
    logger.info(f"📊 获取统计数据 - 天数: {days}")

    try:
        # 计算日期范围
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # 获取每日统计
        daily_stats = await MidsceneStatistics.filter(
            date__gte=start_date, date__lte=end_date
        ).order_by("date")

        # 转换为字典列表
        daily_stats_list = []
        for stat in daily_stats:
            stat_dict = {
                "date": stat.date.isoformat(),
                "total_sessions": stat.total_sessions,
                "completed_sessions": stat.completed_sessions,
                "failed_sessions": stat.failed_sessions,
                "total_files": stat.total_files,
                "total_file_size": stat.total_file_size,
                "avg_processing_time": stat.avg_processing_time,
                "total_tokens": stat.total_tokens,
                "success_rate": stat.success_rate,
            }
            daily_stats_list.append(stat_dict)

        # 计算汇总数据
        total_sessions = sum(stat.total_sessions for stat in daily_stats)
        total_completed = sum(stat.completed_sessions for stat in daily_stats)
        total_failed = sum(stat.failed_sessions for stat in daily_stats)
        total_files = sum(stat.total_files for stat in daily_stats)
        total_file_size = sum(stat.total_file_size for stat in daily_stats)
        total_tokens = sum(stat.total_tokens for stat in daily_stats)

        summary = {
            "period_days": days,
            "total_sessions": total_sessions,
            "completed_sessions": total_completed,
            "failed_sessions": total_failed,
            "success_rate": (
                total_completed / total_sessions if total_sessions > 0 else 0.0
            ),
            "total_files": total_files,
            "total_file_size": total_file_size,
            "total_tokens": total_tokens,
            "avg_sessions_per_day": total_sessions / days,
        }

        return StatisticsResponse(daily_stats=daily_stats_list, summary=summary)

    except Exception as e:
        logger.error(f"❌ 获取统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")


@router.post("/statistics/update")
async def update_statistics():
    """
    更新统计数据
    """
    logger.info("🔄 手动更新统计数据")

    try:
        stats = await midscene_service.update_daily_statistics()

        return {
            "success": True,
            "message": "统计数据更新成功",
            "date": stats.date.isoformat(),
            "total_sessions": stats.total_sessions,
            "success_rate": stats.success_rate,
        }

    except Exception as e:
        logger.error(f"❌ 更新统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新统计数据失败: {str(e)}")


# ==================== 系统管理 ====================


@router.post("/cleanup")
async def cleanup_old_data(days: int = Query(30, ge=1, description="保留天数")):
    """
    清理旧数据
    """
    logger.info(f"🧹 清理旧数据 - 保留 {days} 天")

    try:
        # 计算清理日期
        cleanup_date = datetime.now() - timedelta(days=days)

        # 获取要清理的会话
        old_sessions = await MidsceneSession.filter(
            created_at__lt=cleanup_date, status__in=["completed", "failed"]
        )

        deleted_count = 0
        for session in old_sessions:
            await midscene_service.delete_session(session.session_id)
            deleted_count += 1

        # 清理旧的统计数据
        old_stats_date = date.today() - timedelta(days=365)  # 保留一年的统计数据
        await MidsceneStatistics.filter(date__lt=old_stats_date).delete()

        return DeleteResponse(
            success=True,
            message=f"清理完成，删除了 {deleted_count} 个会话",
            deleted_count=deleted_count,
        )

    except Exception as e:
        logger.error(f"❌ 清理旧数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理旧数据失败: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查
    """
    try:
        # 检查数据库连接
        session_count = await MidsceneSession.all().count()

        # 检查队列状态
        active_connections = (
            midscene_service.queue_manager.getActiveSSEConnectionsCount()
            if hasattr(midscene_service.queue_manager, "getActiveSSEConnectionsCount")
            else 0
        )

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "total_sessions": session_count,
            "active_connections": active_connections,
            "version": "1.0.0",
        }

    except Exception as e:
        logger.error(f"❌ 健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")
