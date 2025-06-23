"""
消息队列管理模块

提供独立的消息队列功能，支持流式输出到前端，与运行时解耦。
"""

import asyncio
import json
from asyncio import Queue
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from loguru import logger


class MessageQueue:
    """
    增强的消息队列管理器

    支持：
    - 消息队列管理
    - 用户反馈队列
    - 流式输出到前端
    - 队列状态监控
    - 完整的容错机制
    """

    def __init__(self, conversation_id: str, max_size: int = 1000):
        """
        初始化消息队列

        Args:
            conversation_id: 对话ID
            max_size: 队列最大大小
        """
        try:
            if not conversation_id or not conversation_id.strip():
                raise ValueError("对话ID不能为空")

            self.conversation_id = conversation_id.strip()
            self.max_size = max_size

            # 主消息队列 - 用于流式输出
            self.message_queue: Queue = Queue(maxsize=max_size)

            # 用户反馈队列 - 用于用户交互
            self.feedback_queue: Queue = Queue()

            # 流式输出队列 - 用于SSE流式输出
            self.streaming_queue: Queue = Queue()

            # 队列状态
            self.created_at = datetime.now().isoformat()
            self.last_activity = datetime.now().isoformat()
            self.total_messages = 0
            self.total_feedback = 0
            self.is_closed = False

            logger.debug(
                f"📦 [消息队列] 创建队列成功 | 对话ID: {self.conversation_id} | 最大大小: {max_size}"
            )

        except Exception as e:
            logger.error(
                f"❌ [消息队列] 初始化失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            raise

    async def put_message(self, message: str) -> None:
        """
        放入消息到队列（增强版，完整容错机制）

        Args:
            message: 消息内容
        """
        try:
            if self.is_closed:
                logger.warning(
                    f"⚠️ [消息队列] 队列已关闭，无法放入消息 | 对话ID: {self.conversation_id}"
                )
                return

            if not message:
                logger.warning(
                    f"⚠️ [消息队列] 消息为空，跳过放入 | 对话ID: {self.conversation_id}"
                )
                return

            # 检查队列是否已满
            if self.message_queue.full():
                logger.warning(
                    f"⚠️ [消息队列] 队列已满，等待空间 | 对话ID: {self.conversation_id}"
                )

            await self.message_queue.put(message)
            self.total_messages += 1
            self.last_activity = datetime.now().isoformat()

            logger.debug(
                f"📤 [消息队列] 消息入队成功 | 对话ID: {self.conversation_id} | 总消息数: {self.total_messages}"
            )
            logger.debug(
                f"   📄 消息内容: {message[:200]}..."
                if len(message) > 200
                else f"   📄 消息内容: {message}"
            )

        except Exception as e:
            logger.error(
                f"❌ [消息队列] 消息入队失败 | 对话ID: {self.conversation_id} | 错误: {e}"
            )
            logger.error(f"   🐛 错误类型: {type(e).__name__}")

    async def get_message(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        从队列获取消息（增强版，支持超时）

        Args:
            timeout: 超时时间（秒），None表示无限等待

        Returns:
            str: 消息内容，超时或错误时返回None
        """
        try:
            if self.is_closed and self.message_queue.empty():
                logger.debug(
                    f"📝 [消息队列] 队列已关闭且为空 | 对话ID: {self.conversation_id}"
                )
                return None

            if timeout:
                message = await asyncio.wait_for(
                    self.message_queue.get(), timeout=timeout
                )
            else:
                message = await self.message_queue.get()

            self.last_activity = datetime.now().isoformat()

            logger.debug(f"📥 [消息队列] 消息出队成功 | 对话ID: {self.conversation_id}")
            logger.debug(
                f"   📄 消息内容: {message[:200]}..."
                if len(message) > 200
                else f"   📄 消息内容: {message}"
            )

            return message

        except asyncio.TimeoutError:
            logger.debug(
                f"⏰ [消息队列] 获取消息超时 | 对话ID: {self.conversation_id} | 超时: {timeout}s"
            )
            return None
        except Exception as e:
            logger.error(
                f"❌ [消息队列] 消息出队失败 | 对话ID: {self.conversation_id} | 错误: {e}"
            )
            return None

    async def put_feedback(self, feedback: str) -> None:
        """
        放入用户反馈到队列（增强版）

        Args:
            feedback: 用户反馈内容
        """
        try:
            if self.is_closed:
                logger.warning(
                    f"⚠️ [消息队列] 队列已关闭，无法放入反馈 | 对话ID: {self.conversation_id}"
                )
                return

            if not feedback:
                logger.warning(
                    f"⚠️ [消息队列] 反馈为空，跳过放入 | 对话ID: {self.conversation_id}"
                )
                return

            await self.feedback_queue.put(feedback)
            self.total_feedback += 1
            self.last_activity = datetime.now().isoformat()

            logger.info(
                f"💬 [消息队列] 用户反馈入队成功 | 对话ID: {self.conversation_id} | 总反馈数: {self.total_feedback}"
            )
            logger.debug(f"   💭 反馈内容: {feedback}")

        except Exception as e:
            logger.error(
                f"❌ [消息队列] 反馈入队失败 | 对话ID: {self.conversation_id} | 错误: {e}"
            )

    async def get_feedback(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        从队列获取用户反馈（增强版，支持超时）

        Args:
            timeout: 超时时间（秒），None表示无限等待

        Returns:
            str: 用户反馈内容，超时或错误时返回None
        """
        try:
            if timeout:
                feedback = await asyncio.wait_for(
                    self.feedback_queue.get(), timeout=timeout
                )
            else:
                feedback = await self.feedback_queue.get()

            self.last_activity = datetime.now().isoformat()

            logger.info(
                f"💬 [消息队列] 用户反馈出队成功 | 对话ID: {self.conversation_id}"
            )
            logger.debug(f"   💭 反馈内容: {feedback}")

            return feedback

        except asyncio.TimeoutError:
            logger.debug(
                f"⏰ [消息队列] 获取反馈超时 | 对话ID: {self.conversation_id} | 超时: {timeout}s"
            )
            return None
        except Exception as e:
            logger.error(
                f"❌ [消息队列] 反馈出队失败 | 对话ID: {self.conversation_id} | 错误: {e}"
            )
            return None

    async def put_streaming_message(self, message: Dict[str, Any]) -> None:
        """
        放入流式消息到队列（用于SSE流式输出）

        Args:
            message: 流式消息字典
        """
        try:
            if self.is_closed:
                logger.warning(
                    f"⚠️ [消息队列] 队列已关闭，无法放入流式消息 | 对话ID: {self.conversation_id}"
                )
                return

            if not message:
                logger.warning(
                    f"⚠️ [消息队列] 流式消息为空，跳过放入 | 对话ID: {self.conversation_id}"
                )
                return

            # 添加时间戳
            if "timestamp" not in message:
                message["timestamp"] = datetime.now().isoformat()

            # 序列化消息
            serialized_message = json.dumps(message, ensure_ascii=False)

            await self.streaming_queue.put(serialized_message)
            self.last_activity = datetime.now().isoformat()

            logger.debug(
                f"🌊 [消息队列] 流式消息入队成功 | 对话ID: {self.conversation_id}"
            )
            logger.debug(
                f"   📄 消息类型: {message.get('type', 'unknown')} | 来源: {message.get('source', 'unknown')}"
            )

        except Exception as e:
            logger.error(
                f"❌ [消息队列] 流式消息入队失败 | 对话ID: {self.conversation_id} | 错误: {e}"
            )

    async def get_streaming_messages(self) -> AsyncGenerator[str, None]:
        """
        获取流式消息生成器（用于SSE流式输出）

        Yields:
            str: 格式化的SSE消息
        """
        try:
            logger.info(f"🌊 [消息队列] 开始流式输出 | 对话ID: {self.conversation_id}")

            while True:
                try:
                    # 获取消息，设置超时避免无限等待
                    message = await asyncio.wait_for(
                        self.streaming_queue.get(), timeout=1.0
                    )

                    # 格式化为SSE格式
                    sse_message = f"data: {message}\n\n"

                    logger.debug(
                        f"🌊 [消息队列] 流式消息输出 | 对话ID: {self.conversation_id}"
                    )
                    yield sse_message

                except asyncio.TimeoutError:
                    # 超时时检查队列是否已关闭
                    if self.is_closed and self.streaming_queue.empty():
                        logger.info(
                            f"🏁 [消息队列] 流式输出结束 | 对话ID: {self.conversation_id}"
                        )
                        break
                    continue

        except Exception as e:
            logger.error(
                f"❌ [消息队列] 流式输出异常 | 对话ID: {self.conversation_id} | 错误: {e}"
            )

    def get_queue_sizes(self) -> Dict[str, int]:
        """
        获取队列大小信息（增强版）

        Returns:
            Dict: 队列大小统计
        """
        try:
            sizes = {
                "message_queue_size": self.message_queue.qsize(),
                "feedback_queue_size": self.feedback_queue.qsize(),
                "streaming_queue_size": self.streaming_queue.qsize(),
                "total_messages": self.total_messages,
                "total_feedback": self.total_feedback,
                "is_closed": self.is_closed,
            }

            logger.debug(
                f"📊 [消息队列] 队列状态 | 对话ID: {self.conversation_id} | 状态: {sizes}"
            )
            return sizes

        except Exception as e:
            logger.error(
                f"❌ [消息队列] 获取队列状态失败 | 对话ID: {self.conversation_id} | 错误: {e}"
            )
            return {
                "message_queue_size": 0,
                "feedback_queue_size": 0,
                "streaming_queue_size": 0,
                "total_messages": 0,
                "total_feedback": 0,
                "is_closed": True,
                "error": str(e),
            }

    def get_queue_info(self) -> Dict[str, Any]:
        """
        获取队列详细信息

        Returns:
            Dict: 队列详细信息
        """
        try:
            info = {
                "conversation_id": self.conversation_id,
                "max_size": self.max_size,
                "created_at": self.created_at,
                "last_activity": self.last_activity,
                "is_closed": self.is_closed,
                **self.get_queue_sizes(),
            }

            return info

        except Exception as e:
            logger.error(
                f"❌ [消息队列] 获取队列信息失败 | 对话ID: {self.conversation_id} | 错误: {e}"
            )
            return {"error": str(e)}

    async def close(self) -> None:
        """
        关闭队列（优雅关闭）
        """
        try:
            self.is_closed = True
            self.last_activity = datetime.now().isoformat()

            # 发送关闭信号到流式队列
            close_message = {
                "type": "close",
                "source": "system",
                "content": "队列已关闭",
                "timestamp": datetime.now().isoformat(),
            }

            await self.put_streaming_message(close_message)

            logger.info(f"🔒 [消息队列] 队列已关闭 | 对话ID: {self.conversation_id}")

        except Exception as e:
            logger.error(
                f"❌ [消息队列] 关闭队列失败 | 对话ID: {self.conversation_id} | 错误: {e}"
            )

    def is_empty(self) -> bool:
        """
        检查所有队列是否为空

        Returns:
            bool: 所有队列都为空时返回True
        """
        try:
            return (
                self.message_queue.empty()
                and self.feedback_queue.empty()
                and self.streaming_queue.empty()
            )
        except Exception as e:
            logger.error(
                f"❌ [消息队列] 检查队列状态失败 | 对话ID: {self.conversation_id} | 错误: {e}"
            )
            return True


class MessageQueueManager:
    """
    消息队列管理器

    管理多个对话的消息队列，提供统一的队列访问接口
    """

    def __init__(self):
        """初始化消息队列管理器"""
        self.queues: Dict[str, MessageQueue] = {}
        self.created_at = datetime.now().isoformat()

        logger.info("🏗️ [队列管理器] 初始化完成")

    def get_or_create_queue(
        self, conversation_id: str, max_size: int = 1000
    ) -> MessageQueue:
        """
        获取或创建消息队列

        Args:
            conversation_id: 对话ID
            max_size: 队列最大大小

        Returns:
            MessageQueue: 消息队列实例
        """
        try:
            if not conversation_id or not conversation_id.strip():
                raise ValueError("对话ID不能为空")

            conversation_id = conversation_id.strip()

            if conversation_id not in self.queues:
                logger.debug(f"🆕 [队列管理器] 创建新队列 | 对话ID: {conversation_id}")
                self.queues[conversation_id] = MessageQueue(conversation_id, max_size)
            else:
                logger.debug(f"♻️ [队列管理器] 使用现有队列 | 对话ID: {conversation_id}")

            return self.queues[conversation_id]

        except Exception as e:
            logger.error(
                f"❌ [队列管理器] 获取队列失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            raise

    def get_queue(self, conversation_id: str) -> Optional[MessageQueue]:
        """
        获取消息队列（不创建新队列）

        Args:
            conversation_id: 对话ID

        Returns:
            MessageQueue: 消息队列实例，不存在时返回None
        """
        try:
            if not conversation_id:
                return None

            queue = self.queues.get(conversation_id.strip())
            if queue:
                logger.debug(
                    f"🔍 [队列管理器] 获取队列成功 | 对话ID: {conversation_id}"
                )
            else:
                logger.debug(f"📝 [队列管理器] 队列不存在 | 对话ID: {conversation_id}")

            return queue

        except Exception as e:
            logger.error(
                f"❌ [队列管理器] 获取队列失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            return None

    async def remove_queue(self, conversation_id: str) -> None:
        """
        移除消息队列

        Args:
            conversation_id: 对话ID
        """
        try:
            if not conversation_id:
                return

            conversation_id = conversation_id.strip()

            if conversation_id in self.queues:
                # 优雅关闭队列
                await self.queues[conversation_id].close()
                del self.queues[conversation_id]
                logger.info(f"🗑️ [队列管理器] 队列已移除 | 对话ID: {conversation_id}")
            else:
                logger.debug(
                    f"📝 [队列管理器] 队列不存在，无需移除 | 对话ID: {conversation_id}"
                )

        except Exception as e:
            logger.error(
                f"❌ [队列管理器] 移除队列失败 | 对话ID: {conversation_id} | 错误: {e}"
            )

    def get_all_queue_info(self) -> Dict[str, Any]:
        """
        获取所有队列信息

        Returns:
            Dict: 所有队列的信息
        """
        try:
            info = {
                "total_queues": len(self.queues),
                "active_conversations": list(self.queues.keys()),
                "created_at": self.created_at,
                "timestamp": datetime.now().isoformat(),
                "queues": {},
            }

            for conversation_id, queue in self.queues.items():
                info["queues"][conversation_id] = queue.get_queue_info()

            logger.debug(f"📊 [队列管理器] 队列统计: 总数={info['total_queues']}")
            return info

        except Exception as e:
            logger.error(f"❌ [队列管理器] 获取队列信息失败: {e}")
            return {"error": str(e)}

    async def cleanup_inactive_queues(self, max_inactive_hours: int = 24) -> int:
        """
        清理不活跃的队列

        Args:
            max_inactive_hours: 最大不活跃时间（小时）

        Returns:
            int: 清理的队列数量
        """
        try:
            from datetime import datetime, timedelta

            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=max_inactive_hours)

            inactive_queues = []

            for conversation_id, queue in self.queues.items():
                try:
                    last_activity = datetime.fromisoformat(queue.last_activity)
                    if last_activity < cutoff_time:
                        inactive_queues.append(conversation_id)
                except Exception as e:
                    logger.warning(
                        f"⚠️ [队列管理器] 检查队列活跃度失败 | 对话ID: {conversation_id} | 错误: {e}"
                    )

            # 清理不活跃的队列
            cleaned_count = 0
            for conversation_id in inactive_queues:
                await self.remove_queue(conversation_id)
                cleaned_count += 1

            if cleaned_count > 0:
                logger.info(
                    f"🧹 [队列管理器] 清理不活跃队列完成 | 清理数量: {cleaned_count}"
                )

            return cleaned_count

        except Exception as e:
            logger.error(f"❌ [队列管理器] 清理不活跃队列失败: {e}")
            return 0


# 全局消息队列管理器实例
_queue_manager: Optional[MessageQueueManager] = None


def get_queue_manager() -> MessageQueueManager:
    """获取全局消息队列管理器实例（单例模式）"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = MessageQueueManager()
    return _queue_manager


# 便捷函数
def get_message_queue(
    conversation_id: str, create_if_not_exists: bool = True
) -> Optional[MessageQueue]:
    """
    获取消息队列的便捷函数

    Args:
        conversation_id: 对话ID
        create_if_not_exists: 如果不存在是否创建

    Returns:
        MessageQueue: 消息队列实例
    """
    try:
        manager = get_queue_manager()

        if create_if_not_exists:
            return manager.get_or_create_queue(conversation_id)
        else:
            return manager.get_queue(conversation_id)

    except Exception as e:
        logger.error(
            f"❌ [便捷函数] 获取消息队列失败 | 对话ID: {conversation_id} | 错误: {e}"
        )
        return None


# 全局便捷函数 - 业务层直接使用
async def put_message_to_queue(conversation_id: str, message: str) -> None:
    """
    将消息放入独立消息队列（全局便捷函数，完整容错）

    Args:
        conversation_id: 对话ID
        message: 消息内容
    """
    try:
        logger.debug(f"📤 [队列管理] 开始放入消息 | 对话ID: {conversation_id}")

        # 获取独立消息队列
        queue = get_message_queue(conversation_id, create_if_not_exists=True)
        if queue:
            logger.debug(f"   📦 队列获取成功，开始放入消息")

            # 放入消息到队列
            await queue.put_message(message)
            logger.debug(f"   ✅ 消息放入队列成功 | 对话ID: {conversation_id}")

        else:
            logger.error(f"❌ [队列管理] 无法获取消息队列 | 对话ID: {conversation_id}")

    except Exception as e:
        logger.error(
            f"❌ [队列管理] 放入消息异常 | 对话ID: {conversation_id} | 错误: {e}"
        )
        logger.error(f"   🐛 错误类型: {type(e).__name__}")


async def get_message_from_queue(
    conversation_id: str, timeout: Optional[float] = 30.0
) -> str:
    """
    从独立消息队列获取消息（全局便捷函数，支持超时）

    Args:
        conversation_id: 对话ID
        timeout: 超时时间（秒）

    Returns:
        str: 消息内容，超时或失败时返回空字符串
    """
    try:
        logger.debug(f"📥 [队列管理] 开始获取消息 | 对话ID: {conversation_id}")

        # 获取独立消息队列
        queue = get_message_queue(conversation_id, create_if_not_exists=False)
        if queue:
            logger.debug(f"   📦 队列获取成功，开始获取消息")

            # 从队列获取消息
            message = await queue.get_message(timeout=timeout)
            if message:
                logger.debug(f"   ✅ 消息获取成功 | 对话ID: {conversation_id}")
                return message
            else:
                logger.debug(f"   ⏰ 消息获取超时 | 对话ID: {conversation_id}")
                return ""

        else:
            logger.warning(f"⚠️ [队列管理] 队列不存在 | 对话ID: {conversation_id}")
            return ""

    except Exception as e:
        logger.error(
            f"❌ [队列管理] 获取消息异常 | 对话ID: {conversation_id} | 错误: {e}"
        )
        logger.error(f"   🐛 错误类型: {type(e).__name__}")
        return ""


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
            logger.info(f"   ✅ 用户反馈放入队列成功 | 对话ID: {conversation_id}")

        else:
            logger.error(f"❌ [队列管理] 无法获取消息队列 | 对话ID: {conversation_id}")

    except Exception as e:
        logger.error(
            f"❌ [队列管理] 放入反馈异常 | 对话ID: {conversation_id} | 错误: {e}"
        )
        logger.error(f"   🐛 错误类型: {type(e).__name__}")


async def get_feedback_from_queue(
    conversation_id: str, timeout: Optional[float] = 300.0
) -> str:
    """
    从独立消息队列获取用户反馈（全局便捷函数，支持超时）

    Args:
        conversation_id: 对话ID
        timeout: 超时时间（秒），默认5分钟

    Returns:
        str: 用户反馈内容，超时或失败时返回空字符串
    """
    try:
        logger.debug(f"💬 [队列管理] 开始获取用户反馈 | 对话ID: {conversation_id}")

        # 获取独立消息队列
        queue = get_message_queue(conversation_id, create_if_not_exists=True)
        if queue:
            logger.debug(f"   📦 队列获取成功，开始等待用户反馈")

            # 从反馈队列获取用户反馈（设置超时）
            feedback = await queue.get_feedback(timeout=timeout)

            if feedback:
                logger.info(
                    f"💬 [队列管理] 用户反馈获取成功 | 对话ID: {conversation_id} | 反馈: {feedback}"
                )
                return feedback
            else:
                logger.warning(
                    f"⏰ [队列管理] 用户反馈获取超时 | 对话ID: {conversation_id}"
                )
                return ""
        else:
            logger.error(f"❌ [队列管理] 无法获取消息队列 | 对话ID: {conversation_id}")
            return ""

    except Exception as e:
        logger.error(
            f"❌ [队列管理] 获取用户反馈异常 | 对话ID: {conversation_id} | 错误: {e}"
        )
        logger.error(f"   🐛 错误类型: {type(e).__name__}")
        return ""


async def put_streaming_message_to_queue(
    conversation_id: str, message: Dict[str, Any]
) -> None:
    """
    将流式消息放入独立消息队列（全局便捷函数，用于SSE流式输出）

    Args:
        conversation_id: 对话ID
        message: 流式消息字典
    """
    try:
        logger.debug(f"🌊 [队列管理] 开始放入流式消息 | 对话ID: {conversation_id}")

        # 获取独立消息队列
        queue = get_message_queue(conversation_id, create_if_not_exists=True)
        if queue:
            logger.debug(f"   📦 队列获取成功，开始放入流式消息")

            # 放入流式消息到队列
            await queue.put_streaming_message(message)
            logger.debug(f"   ✅ 流式消息放入队列成功 | 对话ID: {conversation_id}")

        else:
            logger.error(f"❌ [队列管理] 无法获取消息队列 | 对话ID: {conversation_id}")

    except Exception as e:
        logger.error(
            f"❌ [队列管理] 放入流式消息异常 | 对话ID: {conversation_id} | 错误: {e}"
        )
        logger.error(f"   🐛 错误类型: {type(e).__name__}")


async def get_streaming_messages_from_queue(
    conversation_id: str,
) -> AsyncGenerator[str, None]:
    """
    从独立消息队列获取流式消息生成器（全局便捷函数，用于SSE流式输出）

    Args:
        conversation_id: 对话ID

    Yields:
        str: 格式化的SSE消息
    """
    logger.info(f"🌊 [队列管理] 开始流式输出 | 对话ID: {conversation_id}")

    # 获取独立消息队列
    queue = get_message_queue(conversation_id, create_if_not_exists=True)
    if queue:
        logger.debug(f"   📦 队列获取成功，开始流式输出")
        try:
            while True:
                message = await queue.get_message(timeout=300.0)

                if message and message != "CLOSE":
                    logger.debug(f"   ✅ 消息获取成功 | 对话ID: {conversation_id}")
                    yield message
                elif message == "CLOSE":
                    logger.debug(
                        f"   📦 队列关闭，结束流式输出 | 对话ID: {conversation_id}"
                    )
                    break
                else:
                    logger.debug(f"   ⏰ 消息获取超时 | 对话ID: {conversation_id}")
        except asyncio.CancelledError:
            logger.info(f"   ⏹️ 流式输出任务取消 | 对话ID: {conversation_id}")
        except Exception as e:
            logger.error(f"   ❌ 流式输出异常 | 对话ID: {conversation_id} | 错误: {e}")
            logger.error(f"   🐛 错误类型: {type(e).__name__}")
    else:
        logger.error(f"❌ [队列管理] 无法获取消息队列 | 对话ID: {conversation_id}")


async def get_streaming_sse_messages_from_queue(
    conversation_id: str,
) -> AsyncGenerator[str, None]:
    """
    从独立消息队列获取SSE格式的流式消息生成器（全局便捷函数，直接返回SSE格式）

    Args:
        conversation_id: 对话ID

    Yields:
        str: SSE格式的消息 "data: {message}\n\n"
    """
    logger.info(f"🌊 [队列管理-SSE] 开始SSE流式输出 | 对话ID: {conversation_id}")

    # 获取独立消息队列
    queue = get_message_queue(conversation_id, create_if_not_exists=True)
    if queue:
        logger.debug(f"   📦 队列获取成功，开始SSE流式输出")
        try:
            while True:
                message = await queue.get_message(timeout=300.0)

                if message and message != "CLOSE":
                    logger.debug(
                        f"   ✅ 消息获取成功，格式化为SSE | 对话ID: {conversation_id}"
                    )
                    # 直接返回SSE格式
                    yield f"data: {message}\n\n"
                elif message == "CLOSE":
                    logger.debug(
                        f"   📦 队列关闭，结束SSE流式输出 | 对话ID: {conversation_id}"
                    )
                    break
                else:
                    logger.debug(f"   ⏰ 消息获取超时 | 对话ID: {conversation_id}")
        except asyncio.CancelledError:
            logger.info(f"   ⏹️ SSE流式输出任务取消 | 对话ID: {conversation_id}")
        except Exception as e:
            logger.error(
                f"   ❌ SSE流式输出异常 | 对话ID: {conversation_id} | 错误: {e}"
            )
            logger.error(f"   🐛 错误类型: {type(e).__name__}")
            # 返回错误消息的SSE格式
            error_message = {
                "type": "error",
                "source": "system",
                "content": f"SSE流式输出异常: {str(e)}",
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
            }
            yield f"data: {json.dumps(error_message, ensure_ascii=False)}\n\n"
    else:
        logger.error(f"❌ [队列管理-SSE] 无法获取消息队列 | 对话ID: {conversation_id}")
        # 返回错误消息的SSE格式
        error_message = {
            "type": "error",
            "source": "system",
            "content": "无法获取消息队列",
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
        }
        yield f"data: {json.dumps(error_message, ensure_ascii=False)}\n\n"


async def close_message_queue(conversation_id: str) -> None:
    """
    关闭独立消息队列（全局便捷函数，优雅关闭）

    Args:
        conversation_id: 对话ID
    """
    try:
        logger.debug(f"🔒 [队列管理] 开始关闭队列 | 对话ID: {conversation_id}")

        # 获取独立消息队列
        queue = get_message_queue(conversation_id, create_if_not_exists=False)
        if queue:
            logger.debug(f"   📦 队列获取成功，开始关闭")

            # 关闭队列
            await queue.close()
            logger.info(f"   ✅ 队列关闭成功 | 对话ID: {conversation_id}")

        else:
            logger.debug(f"   📝 队列不存在，无需关闭 | 对话ID: {conversation_id}")

    except Exception as e:
        logger.error(
            f"❌ [队列管理] 关闭队列异常 | 对话ID: {conversation_id} | 错误: {e}"
        )


def get_queue_info(conversation_id: str) -> Dict[str, Any]:
    """
    获取独立消息队列信息（全局便捷函数）

    Args:
        conversation_id: 对话ID

    Returns:
        Dict: 队列信息，失败时返回错误信息
    """
    try:
        logger.debug(f"📊 [队列管理] 获取队列信息 | 对话ID: {conversation_id}")

        # 获取独立消息队列
        queue = get_message_queue(conversation_id, create_if_not_exists=False)
        if queue:
            info = queue.get_queue_info()
            logger.debug(f"   ✅ 队列信息获取成功 | 对话ID: {conversation_id}")
            return info
        else:
            logger.debug(f"   📝 队列不存在 | 对话ID: {conversation_id}")
            return {"error": "队列不存在"}

    except Exception as e:
        logger.error(
            f"❌ [队列管理] 获取队列信息异常 | 对话ID: {conversation_id} | 错误: {e}"
        )
        return {"error": str(e)}


# 导出接口
__all__ = [
    "MessageQueue",
    "MessageQueueManager",
    "get_queue_manager",
    "get_message_queue",
    # 全局便捷函数
    "put_message_to_queue",
    "get_message_from_queue",
    "put_feedback_to_queue",
    "get_feedback_from_queue",
    "put_streaming_message_to_queue",
    "get_streaming_messages_from_queue",
    "get_streaming_sse_messages_from_queue",
    "close_message_queue",
    "get_queue_info",
]
