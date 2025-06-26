#!/usr/bin/env python3
"""
AI Chat RAG增强功能使用示例

展示如何使用新的RAG增强功能和消息队列流式输出
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from loguru import logger

from backend.services.ai_chat.autogen_service import autogen_service


async def example_basic_chat():
    """基础聊天示例（不使用RAG）"""
    logger.info("🔹 示例1: 基础聊天（不使用RAG）")

    try:
        # 使用流式聊天
        conversation_id = "example-basic-001"
        message = "你好，请介绍一下你自己"

        logger.info(f"发送消息: {message}")

        response_chunks = []
        async for chunk in autogen_service.chat_stream_with_rag(
            message=message, conversation_id=conversation_id, use_rag=False  # 不使用RAG
        ):
            # 解析SSE数据
            if chunk.startswith("data: "):
                import json

                try:
                    data = json.loads(chunk[6:])  # 移除"data: "前缀
                    if data.get("type") == "streaming_chunk":
                        response_chunks.append(data.get("content", ""))
                        print(data.get("content", ""), end="", flush=True)
                    elif data.get("type") == "complete":
                        print("\n")
                        logger.info("✅ 基础聊天完成")
                        break
                except json.JSONDecodeError:
                    continue

        full_response = "".join(response_chunks)
        logger.info(f"完整回答长度: {len(full_response)} 字符")

    except Exception as e:
        logger.error(f"❌ 基础聊天示例失败: {e}")


async def example_rag_enhanced_chat():
    """RAG增强聊天示例"""
    logger.info("🔹 示例2: RAG增强聊天")

    try:
        # 使用RAG增强的流式聊天
        conversation_id = "example-rag-001"
        message = "请告诉我关于人工智能的最新发展"

        logger.info(f"发送消息: {message}")
        logger.info("启用RAG增强，将查询知识库...")

        async for chunk in autogen_service.chat_stream_with_rag(
            message=message,
            conversation_id=conversation_id,
            collection_name="ai_chat",
            use_rag=True,  # 启用RAG
        ):
            # 解析SSE数据
            if chunk.startswith("data: "):
                import json

                try:
                    data = json.loads(chunk[6:])

                    # 处理不同类型的消息
                    msg_type = data.get("type")
                    content = data.get("content", "")
                    source = data.get("source", "")

                    if msg_type == "rag_start":
                        logger.info(f"🔍 {content}")
                    elif msg_type == "rag_retrieval":
                        logger.info(f"📄 {content}")
                    elif msg_type == "rag_answer_start":
                        logger.info(f"💡 {content}")
                    elif msg_type == "rag_answer_chunk":
                        print(content, end="", flush=True)
                    elif msg_type == "rag_answer_end":
                        print(content)
                    elif msg_type == "rag_no_result":
                        logger.warning(f"📚 {content}")
                    elif msg_type == "agent_start":
                        logger.info(f"🤖 {content}")
                    elif msg_type == "streaming_chunk":
                        print(content, end="", flush=True)
                    elif msg_type == "complete":
                        print("\n")
                        logger.info("✅ RAG增强聊天完成")
                        break
                    elif msg_type == "error":
                        logger.error(f"❌ {content}")
                        break

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        logger.error(f"❌ RAG增强聊天示例失败: {e}")


async def example_agent_stats():
    """获取Agent统计信息示例"""
    logger.info("🔹 示例3: 获取Agent统计信息")

    try:
        stats = await autogen_service.get_agent_stats()

        logger.info("📊 Agent统计信息:")
        logger.info(f"   总Agent数: {stats.get('total_agents', 0)}")
        logger.info(f"   活跃Agent数: {stats.get('active_agents', 0)}")
        logger.info(f"   过期Agent数: {stats.get('expired_agents', 0)}")
        logger.info(f"   RAG可用: {stats.get('rag_available', False)}")

        if stats.get("rag_available"):
            collections = stats.get("rag_collections", [])
            logger.info(f"   可用Collections: {collections}")

    except Exception as e:
        logger.error(f"❌ 获取统计信息失败: {e}")


async def main():
    """主函数"""
    logger.info("🚀 开始AI Chat RAG增强功能示例...")

    try:
        # 运行示例
        await example_basic_chat()
        print("\n" + "=" * 50 + "\n")

        await example_rag_enhanced_chat()
        print("\n" + "=" * 50 + "\n")

        await example_agent_stats()

        logger.success("🎉 所有示例运行完成!")

    except Exception as e:
        logger.error(f"❌ 示例运行失败: {e}")


if __name__ == "__main__":
    # 设置日志级别
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    # 运行示例
    asyncio.run(main())
