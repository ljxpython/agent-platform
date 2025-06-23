"""
AI测试用例生成服务 - 基于AI核心框架的重构版本
使用抽象的智能体框架，简化业务逻辑，专注于接口对接
"""

import asyncio
import json
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from backend.ai_core import get_memory_manager, validate_model_configs
from backend.ai_core.message_queue import (
    get_message_from_queue,
    get_streaming_messages_from_queue,
    put_feedback_to_queue,
    put_message_to_queue,
)
from backend.services.testcase.testcase_runtime import get_testcase_runtime


# 消息模型定义
class RequirementMessage(BaseModel):
    """需求分析消息"""

    text_content: Optional[str] = Field(default="", description="文本内容")
    files: Optional[List[Any]] = Field(default=None, description="上传的文件")
    file_paths: Optional[List[str]] = Field(default=None, description="文件路径列表")
    conversation_id: str = Field(..., description="对话ID")
    round_number: int = Field(default=1, description="轮次")


class FeedbackMessage(BaseModel):
    """用户反馈消息"""

    feedback: str = Field(..., description="用户反馈内容")
    conversation_id: str = Field(..., description="对话ID")
    round_number: int = Field(..., description="轮次")
    previous_testcases: Optional[str] = Field(default="", description="之前的测试用例")


class TestCaseService:
    """AI测试用例生成服务 - 重构版本"""

    def __init__(self):
        """初始化服务"""
        self.runtime = get_testcase_runtime()
        self.memory_manager = get_memory_manager()

        logger.info("🧪 [测试用例服务] 基于AI核心框架的服务初始化完成")

    async def start_streaming_generation(self, requirement: RequirementMessage) -> None:
        """
        启动流式测试用例生成

        Args:
            requirement: 需求分析消息对象
        """
        conversation_id = requirement.conversation_id
        logger.info(f"🌊 [测试用例服务] 启动流式生成 | 对话ID: {conversation_id}")

        try:
            # 验证模型配置
            configs = validate_model_configs()
            if not any(configs.values()):
                error_msg = "没有可用的模型配置"
                logger.error(f"❌ [测试用例服务] {error_msg}")
                await put_message_to_queue(
                    conversation_id,
                    json.dumps(
                        {
                            "type": "error",
                            "source": "system",
                            "content": error_msg,
                            "conversation_id": conversation_id,
                            "timestamp": datetime.now().isoformat(),
                        },
                        ensure_ascii=False,
                    ),
                )
                return

            # 消息队列已在运行时初始化中创建

            # 检查是否为反馈监听模式
            if requirement.text_content == "FEEDBACK_LISTENING":
                logger.info(
                    f"🎧 [测试用例服务] 反馈监听模式 | 对话ID: {conversation_id}"
                )
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

            await self.runtime.start_requirement_analysis(
                conversation_id, requirement_data
            )

            logger.success(
                f"✅ [测试用例服务] 流式生成启动成功 | 对话ID: {conversation_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ [测试用例服务] 流式生成失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            # 将错误信息放入队列
            error_message = {
                "type": "error",
                "source": "system",
                "content": f"流式生成失败: {str(e)}",
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
            }
            await put_message_to_queue(
                conversation_id, json.dumps(error_message, ensure_ascii=False)
            )

    async def process_user_feedback(self, feedback: FeedbackMessage) -> None:
        """
        处理用户反馈

        Args:
            feedback: 用户反馈消息对象
        """
        conversation_id = feedback.conversation_id
        logger.info(f"💬 [测试用例服务] 处理用户反馈 | 对话ID: {conversation_id}")

        try:
            # 将反馈放入队列
            await put_feedback_to_queue(conversation_id, feedback.feedback)

            # 使用运行时处理反馈
            feedback_data = {
                "conversation_id": conversation_id,
                "feedback": feedback.feedback,
                "round_number": feedback.round_number,
                "previous_testcases": feedback.previous_testcases,
            }

            await self.runtime.process_user_feedback(conversation_id, feedback_data)

            logger.success(
                f"✅ [测试用例服务] 用户反馈处理完成 | 对话ID: {conversation_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ [测试用例服务] 用户反馈处理失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            raise

    async def get_streaming_messages(
        self, conversation_id: str
    ) -> AsyncGenerator[str, None]:
        """
        获取流式消息生成器 - 直接使用message_queue的流式接口

        Args:
            conversation_id: 对话ID

        Yields:
            str: 流式消息
        """
        logger.info(f"📡 [测试用例服务] 开始流式消息传输 | 对话ID: {conversation_id}")

        try:
            # 直接使用message_queue的流式消息获取方法
            async for message in get_streaming_messages_from_queue(conversation_id):
                yield message

        except Exception as e:
            logger.error(
                f"❌ [测试用例服务] 流式消息传输失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            error_message = json.dumps(
                {
                    "type": "error",
                    "source": "system",
                    "content": f"流式传输失败: {str(e)}",
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat(),
                },
                ensure_ascii=False,
            )
            yield f"data: {error_message}\n\n"

    async def get_conversation_history(
        self, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """
        获取对话历史

        Args:
            conversation_id: 对话ID

        Returns:
            List[Dict]: 历史消息列表
        """
        return await self.memory_manager.get_conversation_history(conversation_id)

    async def cleanup_conversation(self, conversation_id: str) -> None:
        """
        清理对话资源

        Args:
            conversation_id: 对话ID
        """
        logger.info(f"🗑️ [测试用例服务] 清理对话资源 | 对话ID: {conversation_id}")

        try:
            # 清理运行时（包括队列）
            await self.runtime.cleanup_runtime(conversation_id)

            logger.success(
                f"✅ [测试用例服务] 对话资源清理完成 | 对话ID: {conversation_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ [测试用例服务] 对话资源清理失败 | 对话ID: {conversation_id} | 错误: {e}"
            )


# 创建全局服务实例
testcase_service = TestCaseService()

# 导出接口
__all__ = [
    "RequirementMessage",
    "FeedbackMessage",
    "TestCaseService",
    "testcase_service",
]
