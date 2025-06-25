import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import ModelClientStreamingChunkEvent
from loguru import logger

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(project_root)

# 使用 AI 核心模块的配置
from backend.ai_core.llm import get_default_client
from backend.ai_core.message_queue import (
    MessageQueueManager,
    get_streaming_sse_messages_from_queue,
)
from backend.services.rag.rag_service import get_rag_service


class AutoGenService:
    """AutoGen 服务类"""

    def __init__(
        self, max_agents: int = 100, cleanup_interval: int = 3600, agent_ttl: int = 7200
    ):
        """
        初始化 AutoGen 服务，集成RAG知识库功能

        Args:
            max_agents: 最大 Agent 数量
            cleanup_interval: 清理检查间隔（秒）
            agent_ttl: Agent 生存时间（秒）
        """
        self.agents = {}
        self.max_agents = max_agents
        self.cleanup_interval = cleanup_interval
        self.agent_ttl = agent_ttl
        self._last_cleanup = asyncio.get_event_loop().time()
        self.rag_service = None  # RAG服务实例，延迟初始化
        self.message_queue_manager = MessageQueueManager()  # 消息队列管理器
        logger.info(
            f"AutoGen 服务初始化 | 最大Agent数: {max_agents} | TTL: {agent_ttl}s | 支持RAG知识库"
        )

    def create_agent(
        self, conversation_id: str, system_message: str = "你是一个有用的AI助手"
    ) -> AssistantAgent:
        """创建或获取 Agent"""
        if conversation_id not in self.agents:
            logger.debug(f"创建新的 Agent | 对话ID: {conversation_id}")
            # 将 UUID 中的连字符替换为下划线，确保是有效的 Python 标识符
            safe_name = f"assistant_{conversation_id.replace('-', '_')}"
            agent = AssistantAgent(
                name=safe_name,
                model_client=get_default_client(),
                system_message=system_message,
                model_client_stream=True,
            )
            self.agents[conversation_id] = {
                "agent": agent,
                "created_at": asyncio.get_event_loop().time(),
                "last_used": asyncio.get_event_loop().time(),
            }
            logger.success(
                f"Agent 创建成功 | 对话ID: {conversation_id} | 名称: {safe_name}"
            )
        else:
            logger.debug(f"复用现有 Agent | 对话ID: {conversation_id}")
            # 更新最后使用时间
            self.agents[conversation_id]["last_used"] = asyncio.get_event_loop().time()
        return self.agents[conversation_id]["agent"]

    def _cleanup_expired_agents(self):
        """清理过期的 Agent"""
        current_time = asyncio.get_event_loop().time()
        expired_ids = []

        for conv_id, agent_info in self.agents.items():
            if current_time - agent_info["last_used"] > self.agent_ttl:
                expired_ids.append(conv_id)

        for conv_id in expired_ids:
            del self.agents[conv_id]
            logger.info(f"清理过期 Agent | 对话ID: {conv_id}")

        if expired_ids:
            logger.info(
                f"清理完成 | 清理数量: {len(expired_ids)} | 剩余数量: {len(self.agents)}"
            )

    def _cleanup_oldest_agents(self, target_count: int):
        """清理最旧的 Agent 到目标数量"""
        if len(self.agents) <= target_count:
            return

        # 按最后使用时间排序，清理最旧的
        sorted_agents = sorted(self.agents.items(), key=lambda x: x[1]["last_used"])

        cleanup_count = len(self.agents) - target_count
        for i in range(cleanup_count):
            conv_id = sorted_agents[i][0]
            del self.agents[conv_id]
            logger.info(f"清理最旧 Agent | 对话ID: {conv_id}")

        logger.info(
            f"容量清理完成 | 清理数量: {cleanup_count} | 剩余数量: {len(self.agents)}"
        )

    def _auto_cleanup(self):
        """自动清理检查"""
        current_time = asyncio.get_event_loop().time()

        # 检查是否需要清理
        if current_time - self._last_cleanup < self.cleanup_interval:
            return

        logger.debug("开始自动清理检查...")

        # 清理过期的 Agent
        self._cleanup_expired_agents()

        # 如果数量仍然超过限制，清理最旧的
        if len(self.agents) > self.max_agents:
            logger.warning(
                f"Agent 数量超过限制 | 当前: {len(self.agents)} | 限制: {self.max_agents}"
            )
            self._cleanup_oldest_agents(self.max_agents // 2)  # 清理到一半容量

        self._last_cleanup = current_time

    async def _ensure_rag_service(self):
        """确保RAG服务已初始化"""
        if self.rag_service is None:
            try:
                self.rag_service = await get_rag_service()
                logger.info("RAG服务初始化成功")
            except Exception as e:
                logger.error(f"RAG服务初始化失败: {e}")
                self.rag_service = None

    async def add_file_to_rag(
        self, file_path: str, collection_name: str = "ai_chat"
    ) -> Dict:
        """
        添加文件到RAG知识库

        Args:
            file_path: 文件路径
            collection_name: collection名称

        Returns:
            Dict: 添加结果
        """
        await self._ensure_rag_service()
        if self.rag_service is None:
            return {"success": False, "message": "RAG服务不可用"}

        try:
            result = await self.rag_service.add_file(file_path, collection_name)
            logger.info(f"文件添加到RAG成功: {file_path} -> {collection_name}")
            return result
        except Exception as e:
            logger.error(f"文件添加到RAG失败: {e}")
            return {"success": False, "message": str(e)}

    async def add_text_to_rag(
        self,
        text: str,
        collection_name: str = "ai_chat",
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        添加文本到RAG知识库

        Args:
            text: 文本内容
            collection_name: collection名称
            metadata: 元数据

        Returns:
            Dict: 添加结果
        """
        await self._ensure_rag_service()
        if self.rag_service is None:
            return {"success": False, "message": "RAG服务不可用"}

        try:
            result = await self.rag_service.add_text(text, collection_name, metadata)
            logger.info(f"文本添加到RAG成功: {collection_name}")
            return result
        except Exception as e:
            logger.error(f"文本添加到RAG失败: {e}")
            return {"success": False, "message": str(e)}

    async def query_rag(
        self, question: str, collection_name: str = "ai_chat"
    ) -> Optional[Dict]:
        """
        查询RAG知识库

        Args:
            question: 查询问题
            collection_name: collection名称

        Returns:
            Optional[Dict]: 查询结果
        """
        await self._ensure_rag_service()
        if self.rag_service is None:
            return None

        try:
            result = await self.rag_service.query(question, collection_name)
            if result.get("success"):
                logger.info(f"RAG查询成功: {collection_name}")
                return result
            else:
                logger.warning(f"RAG查询失败: {result.get('message')}")
                return None
        except Exception as e:
            logger.error(f"RAG查询异常: {e}")
            return None

    async def get_rag_collections(self) -> List[str]:
        """获取可用的RAG collections"""
        await self._ensure_rag_service()
        if self.rag_service is None:
            return []

        try:
            return self.rag_service.list_collections()
        except Exception as e:
            logger.error(f"获取RAG collections失败: {e}")
            return []

    async def chat_stream_with_rag(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        system_message: str = "你是一个有用的AI助手",
        collection_name: str = "ai_chat",
        use_rag: bool = True,
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天，支持RAG知识库增强

        Args:
            message: 用户消息
            conversation_id: 对话ID
            system_message: 系统消息
            collection_name: RAG collection名称
            use_rag: 是否使用RAG增强

        Yields:
            str: 流式响应内容
        """
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        logger.info(
            f"开始RAG增强流式聊天 | 对话ID: {conversation_id} | 消息: {message[:100]}... | 使用RAG: {use_rag} | Collection: {collection_name}"
        )

        # 执行自动清理
        self._auto_cleanup()

        try:
            enhanced_message = message
            rag_context = ""

            # 如果启用RAG，先查询知识库
            if use_rag:
                # 发送RAG查询开始信息
                rag_start_message = {
                    "type": "rag_start",
                    "source": "RAG知识库",
                    "content": f"🔍 正在查询 {collection_name} 知识库...",
                    "collection_name": collection_name,
                    "timestamp": datetime.now().isoformat(),
                }
                yield f"data: {json.dumps(rag_start_message, ensure_ascii=False)}\n\n"

                logger.info(f"🔍 查询RAG知识库 | Collection: {collection_name}")
                rag_result = await self.query_rag(message, collection_name)

                if rag_result and rag_result.get("success"):
                    rag_context = rag_result.get("answer", "")
                    retrieved_nodes = rag_result.get("retrieved_nodes", [])

                    logger.info(
                        f"✅ RAG查询成功 | 检索到 {len(retrieved_nodes)} 个相关文档"
                    )

                    # 发送检索结果信息
                    retrieval_message = {
                        "type": "rag_retrieval",
                        "source": "RAG知识库",
                        "content": f"📄 检索到 {len(retrieved_nodes)} 个相关文档",
                        "retrieved_count": len(retrieved_nodes),
                        "collection_name": collection_name,
                        "timestamp": datetime.now().isoformat(),
                    }
                    yield f"data: {json.dumps(retrieval_message, ensure_ascii=False)}\n\n"

                    # 构建增强的提示
                    if rag_context:
                        enhanced_message = f"""基于以下知识库信息回答用户问题：

知识库信息：
{rag_context}

用户问题：{message}

请结合知识库信息和你的知识来回答用户问题。如果知识库信息不足以回答问题，请说明并提供你的最佳建议。"""

                        # 流式发送RAG回答内容
                        rag_answer_start = {
                            "type": "rag_answer_start",
                            "source": "RAG知识库",
                            "content": "💡 知识库回答：",
                            "collection_name": collection_name,
                            "timestamp": datetime.now().isoformat(),
                        }
                        yield f"data: {json.dumps(rag_answer_start, ensure_ascii=False)}\n\n"

                        # 将RAG回答分块流式输出
                        chunk_size = 50  # 每块字符数
                        for i in range(0, len(rag_context), chunk_size):
                            chunk = rag_context[i : i + chunk_size]
                            rag_chunk_message = {
                                "type": "rag_answer_chunk",
                                "source": "RAG知识库",
                                "content": chunk,
                                "collection_name": collection_name,
                                "timestamp": datetime.now().isoformat(),
                            }
                            yield f"data: {json.dumps(rag_chunk_message, ensure_ascii=False)}\n\n"
                            # 添加小延迟模拟流式效果
                            await asyncio.sleep(0.05)

                        # RAG回答结束
                        rag_answer_end = {
                            "type": "rag_answer_end",
                            "source": "RAG知识库",
                            "content": "\n\n---\n",
                            "collection_name": collection_name,
                            "timestamp": datetime.now().isoformat(),
                        }
                        yield f"data: {json.dumps(rag_answer_end, ensure_ascii=False)}\n\n"

                else:
                    logger.info("❌ RAG查询无结果，使用原始消息")
                    # 发送RAG查询无结果的信息
                    no_rag_message = {
                        "type": "rag_no_result",
                        "source": "RAG知识库",
                        "content": f"📚 在 {collection_name} 知识库中未找到相关信息，将基于通用知识回答",
                        "collection_name": collection_name,
                        "timestamp": datetime.now().isoformat(),
                    }
                    yield f"data: {json.dumps(no_rag_message, ensure_ascii=False)}\n\n"

            # 创建Agent
            agent = self.create_agent(conversation_id, system_message)

            # 发送Agent开始处理的信息
            agent_start_message = {
                "type": "agent_start",
                "source": "AI智能体",
                "content": "🤖 AI智能体开始处理您的问题...",
                "timestamp": datetime.now().isoformat(),
            }

            yield f"data: {json.dumps(agent_start_message, ensure_ascii=False)}\n\n"

            # 获取流式响应
            logger.debug(f"调用 Agent 流式响应 | 对话ID: {conversation_id}")
            result = agent.run_stream(task=enhanced_message)

            chunk_count = 0
            async for item in result:
                if isinstance(item, ModelClientStreamingChunkEvent):
                    if item.content:
                        chunk_count += 1
                        logger.debug(
                            f"收到流式数据块 {chunk_count} | 对话ID: {conversation_id} | 内容: {item.content[:50]}..."
                        )

                        # 发送流式内容
                        chunk_message = {
                            "type": "streaming_chunk",
                            "source": "AI智能体",
                            "content": item.content,
                            "timestamp": datetime.now().isoformat(),
                        }

                        yield f"data: {json.dumps(chunk_message, ensure_ascii=False)}\n\n"

            # 发送完成信号
            complete_message = {
                "type": "complete",
                "source": "AI智能体",
                "content": "✅ 回答完成",
                "timestamp": datetime.now().isoformat(),
            }

            yield f"data: {json.dumps(complete_message, ensure_ascii=False)}\n\n"

            logger.success(
                f"RAG增强流式聊天完成 | 对话ID: {conversation_id} | 总块数: {chunk_count} | 使用RAG: {use_rag}"
            )

        except Exception as e:
            logger.error(f"RAG增强流式聊天失败 | 对话ID: {conversation_id} | 错误: {e}")
            error_message = {
                "type": "error",
                "source": "系统",
                "content": f"❌ 处理失败: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }

            yield f"data: {json.dumps(error_message, ensure_ascii=False)}\n\n"

    async def chat_stream(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        system_message: str = "你是一个有用的AI助手",
    ) -> AsyncGenerator[str, None]:
        """流式聊天（兼容旧接口）"""
        async for chunk in self.chat_stream_with_rag(
            message=message,
            conversation_id=conversation_id,
            system_message=system_message,
            use_rag=False,  # 默认不使用RAG，保持兼容性
        ):
            # 提取content字段，保持旧接口兼容性
            try:
                data = json.loads(chunk.replace("data: ", "").strip())
                if data.get("type") == "streaming_chunk":
                    yield data.get("content", "")
            except:
                continue

    async def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        system_message: str = "你是一个有用的AI助手",
    ) -> tuple[str, str]:
        """非流式聊天"""
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        logger.info(
            f"开始普通聊天 | 对话ID: {conversation_id} | 消息: {message[:100]}..."
        )

        # 执行自动清理
        self._auto_cleanup()

        agent = self.create_agent(conversation_id, system_message)

        try:
            logger.debug(f"调用 Agent 普通响应 | 对话ID: {conversation_id}")
            result = await agent.run(task=message)
            response = str(result)
            logger.success(
                f"普通聊天完成 | 对话ID: {conversation_id} | 响应长度: {len(response)}"
            )
            return response, conversation_id
        except Exception as e:
            logger.error(f"普通聊天失败 | 对话ID: {conversation_id} | 错误: {e}")
            return f"错误: {str(e)}", conversation_id

    def clear_conversation(self, conversation_id: str):
        """清除对话"""
        if conversation_id in self.agents:
            logger.info(f"清除对话 | 对话ID: {conversation_id}")
            del self.agents[conversation_id]
            logger.success(f"对话清除成功 | 对话ID: {conversation_id}")
        else:
            logger.warning(f"尝试清除不存在的对话 | 对话ID: {conversation_id}")

    async def get_agent_stats(self) -> dict:
        """获取 Agent 统计信息，包括RAG状态"""
        current_time = asyncio.get_event_loop().time()
        active_count = 0
        expired_count = 0

        for agent_info in self.agents.values():
            if current_time - agent_info["last_used"] <= self.agent_ttl:
                active_count += 1
            else:
                expired_count += 1

        # 获取RAG统计信息
        rag_stats = {}
        try:
            await self._ensure_rag_service()
            if self.rag_service:
                rag_system_stats = await self.rag_service.get_system_stats()
                rag_collections = await self.get_rag_collections()
                rag_stats = {
                    "rag_available": True,
                    "rag_collections": rag_collections,
                    "rag_system_stats": rag_system_stats,
                }
            else:
                rag_stats = {"rag_available": False}
        except Exception as e:
            logger.error(f"获取RAG统计信息失败: {e}")
            rag_stats = {"rag_available": False, "rag_error": str(e)}

        return {
            "total_agents": len(self.agents),
            "active_agents": active_count,
            "expired_agents": expired_count,
            "max_agents": self.max_agents,
            "agent_ttl": self.agent_ttl,
            "cleanup_interval": self.cleanup_interval,
            **rag_stats,
        }

    def force_cleanup(self):
        """强制执行清理"""
        logger.info("执行强制清理...")
        self._cleanup_expired_agents()
        if len(self.agents) > self.max_agents:
            self._cleanup_oldest_agents(self.max_agents // 2)
        logger.info("强制清理完成")


# 全局服务实例
def create_autogen_service():
    """创建 AutoGen 服务实例"""
    try:
        # 尝试导入配置
        from backend.conf.config import settings

        # 使用配置中的参数，如果没有则使用默认值
        max_agents = getattr(settings, "autogen", {}).get("max_agents", 100)
        cleanup_interval = getattr(settings, "autogen", {}).get(
            "cleanup_interval", 3600
        )
        agent_ttl = getattr(settings, "autogen", {}).get("agent_ttl", 7200)

        return AutoGenService(
            max_agents=max_agents,
            cleanup_interval=cleanup_interval,
            agent_ttl=agent_ttl,
        )
    except ImportError:
        logger.warning("无法导入配置，使用默认参数")
        return AutoGenService()


autogen_service = create_autogen_service()
