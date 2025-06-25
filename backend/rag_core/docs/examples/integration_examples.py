"""
RAG知识库系统集成示例

本文件展示了RAG系统与其他系统组件的集成方法，包括：
- 与FastAPI的集成
- 与测试用例生成的集成
- 与AI对话系统的集成
- 与前端的集成
"""

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.rag_core.rag_system import RAGSystem

# ==================== FastAPI集成示例 ====================


class QueryRequest(BaseModel):
    """查询请求模型"""

    question: str
    collection_name: str = "general"
    top_k: Optional[int] = None


class QueryResponse(BaseModel):
    """查询响应模型"""

    answer: str
    sources: List[Dict[str, Any]]
    collection_name: str
    query_time: float
    confidence_score: float


class DocumentAddRequest(BaseModel):
    """文档添加请求模型"""

    content: str
    collection_name: str = "general"
    metadata: Optional[Dict[str, Any]] = None


# 全局RAG系统实例
rag_system: Optional[RAGSystem] = None


async def get_rag_system() -> RAGSystem:
    """获取RAG系统实例"""
    global rag_system
    if rag_system is None:
        rag_system = RAGSystem()
        await rag_system.initialize()
    return rag_system


def create_rag_api() -> FastAPI:
    """创建RAG API应用"""
    app = FastAPI(title="RAG知识库API", version="1.0.0")

    @app.on_event("startup")
    async def startup_event():
        """应用启动时初始化RAG系统"""
        await get_rag_system()
        print("✅ RAG系统初始化完成")

    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭时清理RAG系统"""
        global rag_system
        if rag_system:
            await rag_system.cleanup()
            print("✅ RAG系统清理完成")

    @app.post("/api/v1/rag/query", response_model=QueryResponse)
    async def query_knowledge(request: QueryRequest):
        """知识库查询接口"""
        try:
            rag = await get_rag_system()
            result = await rag.query(
                request.question, request.collection_name, request.top_k
            )

            # 转换为API响应格式
            sources = []
            for node in result.retrieved_nodes:
                sources.append(
                    {
                        "content": (
                            node.text[:200] + "..."
                            if len(node.text) > 200
                            else node.text
                        ),
                        "score": node.score,
                        "metadata": getattr(node, "metadata", {}),
                    }
                )

            return QueryResponse(
                answer=result.answer,
                sources=sources,
                collection_name=result.collection_name,
                query_time=result.query_time,
                confidence_score=result.confidence_score,
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

    @app.post("/api/v1/rag/documents")
    async def add_document(request: DocumentAddRequest):
        """添加文档接口"""
        try:
            rag = await get_rag_system()
            await rag.setup_collection(request.collection_name)

            count = await rag.add_text(
                request.content, request.collection_name, request.metadata
            )

            return {
                "success": True,
                "message": f"文档添加成功，生成 {count} 个节点",
                "node_count": count,
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文档添加失败: {str(e)}")

    @app.get("/api/v1/rag/collections")
    async def list_collections():
        """列出所有Collection"""
        try:
            rag = await get_rag_system()
            collections = await rag.list_collections()

            collection_info = []
            for collection_name in collections:
                info = await rag.get_collection_info(collection_name)
                collection_info.append(info)

            return {"success": True, "collections": collection_info}

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"获取Collection列表失败: {str(e)}"
            )

    return app


# ==================== 测试用例生成集成示例 ====================


class TestCaseGenerator:
    """测试用例生成器，集成RAG知识库"""

    def __init__(self):
        self.rag_system = None

    async def initialize(self):
        """初始化测试用例生成器"""
        self.rag_system = RAGSystem()
        await self.rag_system.initialize()
        await self.rag_system.setup_collection("testcase")

        # 添加测试用例相关知识
        testcase_knowledge = [
            "测试用例应该包含前置条件、测试步骤、预期结果三个基本要素。",
            "边界值测试是验证系统在输入边界条件下的行为。",
            "等价类划分可以减少测试用例数量同时保证测试覆盖率。",
            "正向测试验证系统在正常输入下的功能，负向测试验证异常处理。",
            "测试用例应该具有可重复性、独立性和可验证性。",
        ]

        await self.rag_system.add_documents(testcase_knowledge, "testcase")
        print("✅ 测试用例知识库初始化完成")

    async def generate_test_cases(
        self, requirement: str, test_type: str = "functional"
    ) -> List[Dict[str, Any]]:
        """
        基于需求生成测试用例

        Args:
            requirement: 需求描述
            test_type: 测试类型 (functional, boundary, negative)
        """
        if not self.rag_system:
            await self.initialize()

        # 构建查询问题
        query_templates = {
            "functional": f"如何为以下需求设计功能测试用例：{requirement}",
            "boundary": f"如何为以下需求设计边界值测试用例：{requirement}",
            "negative": f"如何为以下需求设计负向测试用例：{requirement}",
        }

        question = query_templates.get(test_type, query_templates["functional"])

        # 查询RAG知识库
        result = await self.rag_system.query(question, "testcase")

        # 解析生成的测试用例建议
        test_cases = self._parse_test_case_suggestions(result.answer, requirement)

        return test_cases

    def _parse_test_case_suggestions(
        self, suggestions: str, requirement: str
    ) -> List[Dict[str, Any]]:
        """解析RAG生成的测试用例建议"""
        # 这里可以使用更复杂的解析逻辑
        test_cases = [
            {
                "id": "TC001",
                "title": f"测试{requirement}的基本功能",
                "precondition": "系统正常运行",
                "steps": ["1. 输入有效数据", "2. 执行操作", "3. 验证结果"],
                "expected_result": "操作成功，返回预期结果",
                "priority": "高",
                "type": "功能测试",
                "rag_suggestion": suggestions,
            }
        ]

        return test_cases

    async def cleanup(self):
        """清理资源"""
        if self.rag_system:
            await self.rag_system.cleanup()


# ==================== AI对话系统集成示例 ====================


class AIConversationSystem:
    """AI对话系统，集成RAG知识库"""

    def __init__(self):
        self.rag_system = None
        self.conversation_history = []

    async def initialize(self):
        """初始化对话系统"""
        self.rag_system = RAGSystem()
        await self.rag_system.initialize()
        await self.rag_system.setup_collection("ai_chat")

        # 添加对话相关知识
        chat_knowledge = [
            "良好的对话系统应该能够理解上下文并保持对话连贯性。",
            "用户意图识别是对话系统的核心功能之一。",
            "对话系统应该能够处理多轮对话和话题切换。",
            "个性化回复可以提升用户体验。",
            "对话系统需要具备错误恢复和澄清机制。",
        ]

        await self.rag_system.add_documents(chat_knowledge, "ai_chat")
        print("✅ AI对话知识库初始化完成")

    async def chat(self, user_message: str, use_rag: bool = True) -> Dict[str, Any]:
        """
        处理用户对话

        Args:
            user_message: 用户消息
            use_rag: 是否使用RAG增强回复
        """
        if not self.rag_system:
            await self.initialize()

        # 记录对话历史
        self.conversation_history.append(
            {
                "role": "user",
                "content": user_message,
                "timestamp": asyncio.get_event_loop().time(),
            }
        )

        # 生成回复
        if use_rag:
            # 使用RAG增强的回复
            response = await self._generate_rag_enhanced_response(user_message)
        else:
            # 普通回复
            response = await self._generate_basic_response(user_message)

        # 记录AI回复
        self.conversation_history.append(
            {
                "role": "assistant",
                "content": response["content"],
                "timestamp": asyncio.get_event_loop().time(),
                "rag_used": use_rag,
                "sources": response.get("sources", []),
            }
        )

        return response

    async def _generate_rag_enhanced_response(
        self, user_message: str
    ) -> Dict[str, Any]:
        """生成RAG增强的回复"""
        # 构建包含对话历史的查询
        context = self._build_conversation_context()
        enhanced_query = (
            f"基于以下对话历史回答用户问题：\n{context}\n用户问题：{user_message}"
        )

        # 查询RAG知识库
        result = await self.rag_system.query(enhanced_query, "ai_chat")

        # 构建响应
        sources = [
            {"content": node.text[:100] + "...", "score": node.score}
            for node in result.retrieved_nodes[:3]
        ]

        return {
            "content": result.answer,
            "type": "rag_enhanced",
            "confidence": result.confidence_score,
            "sources": sources,
            "query_time": result.query_time,
        }

    async def _generate_basic_response(self, user_message: str) -> Dict[str, Any]:
        """生成基础回复"""
        # 这里可以集成其他对话模型
        basic_responses = [
            "我理解您的问题，让我为您查找相关信息。",
            "这是一个很好的问题，我需要更多信息来为您提供准确的答案。",
            "根据我的理解，这个问题涉及多个方面。",
        ]

        import random

        response = random.choice(basic_responses)

        return {"content": response, "type": "basic", "confidence": 0.5}

    def _build_conversation_context(self, max_turns: int = 5) -> str:
        """构建对话上下文"""
        recent_history = self.conversation_history[-max_turns * 2 :]  # 最近几轮对话

        context_parts = []
        for entry in recent_history:
            role = "用户" if entry["role"] == "user" else "助手"
            context_parts.append(f"{role}: {entry['content']}")

        return "\n".join(context_parts)

    async def get_conversation_summary(self) -> str:
        """获取对话摘要"""
        if not self.conversation_history:
            return "暂无对话历史"

        # 构建对话历史文本
        conversation_text = self._build_conversation_context(
            len(self.conversation_history)
        )

        # 使用RAG生成摘要
        summary_query = f"请总结以下对话的主要内容：\n{conversation_text}"
        result = await self.rag_system.query(summary_query, "ai_chat")

        return result.answer

    async def cleanup(self):
        """清理资源"""
        if self.rag_system:
            await self.rag_system.cleanup()


# ==================== 前端集成示例 ====================


class FrontendIntegrationHelper:
    """前端集成辅助类"""

    @staticmethod
    def format_query_response_for_frontend(result) -> Dict[str, Any]:
        """格式化查询结果供前端使用"""
        return {
            "success": True,
            "data": {
                "answer": result.answer,
                "sources": [
                    {
                        "id": i,
                        "content": (
                            node.text[:200] + "..."
                            if len(node.text) > 200
                            else node.text
                        ),
                        "score": round(node.score, 3),
                        "metadata": getattr(node, "metadata", {}),
                    }
                    for i, node in enumerate(result.retrieved_nodes)
                ],
                "metadata": {
                    "collection_name": result.collection_name,
                    "query_time": round(result.query_time, 3),
                    "confidence_score": round(result.confidence_score, 3),
                    "source_count": result.source_count,
                },
            },
        }

    @staticmethod
    def create_sse_response(result) -> str:
        """创建SSE格式的响应"""
        import json

        # 分段发送答案
        answer_chunks = [
            result.answer[i : i + 50] for i in range(0, len(result.answer), 50)
        ]

        sse_data = []
        for i, chunk in enumerate(answer_chunks):
            sse_data.append(
                f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'index': i})}\n\n"
            )

        # 发送完成信号
        sse_data.append(
            f"data: {json.dumps({'type': 'complete', 'metadata': {'query_time': result.query_time}})}\n\n"
        )

        return "".join(sse_data)


# ==================== 示例运行函数 ====================


async def run_fastapi_integration_example():
    """运行FastAPI集成示例"""
    print("🌐 FastAPI集成示例")

    # 创建FastAPI应用
    app = create_rag_api()

    # 模拟API调用
    print("✅ FastAPI应用创建成功")
    print("📡 API端点:")
    print("  POST /api/v1/rag/query - 知识库查询")
    print("  POST /api/v1/rag/documents - 添加文档")
    print("  GET /api/v1/rag/collections - 列出Collection")

    # 实际部署时使用: uvicorn main:app --reload
    print()


async def run_testcase_integration_example():
    """运行测试用例生成集成示例"""
    print("🧪 测试用例生成集成示例")

    generator = TestCaseGenerator()
    await generator.initialize()

    # 生成测试用例
    requirement = "用户登录功能"
    test_cases = await generator.generate_test_cases(requirement, "functional")

    print(f"📋 为需求 '{requirement}' 生成的测试用例:")
    for tc in test_cases:
        print(f"  ID: {tc['id']}")
        print(f"  标题: {tc['title']}")
        print(f"  步骤: {tc['steps']}")
        print(f"  预期结果: {tc['expected_result']}")

    await generator.cleanup()
    print()


async def run_ai_chat_integration_example():
    """运行AI对话系统集成示例"""
    print("💬 AI对话系统集成示例")

    chat_system = AIConversationSystem()
    await chat_system.initialize()

    # 模拟对话
    conversations = [
        "你好，我想了解对话系统的设计原则",
        "如何提升对话的自然度？",
        "能总结一下我们刚才的对话吗？",
    ]

    for user_msg in conversations:
        print(f"\n👤 用户: {user_msg}")

        response = await chat_system.chat(user_msg, use_rag=True)
        print(f"🤖 助手: {response['content']}")
        print(f"📊 置信度: {response.get('confidence', 0):.3f}")

        if response.get("sources"):
            print(f"📚 参考来源: {len(response['sources'])} 个")

    # 获取对话摘要
    summary = await chat_system.get_conversation_summary()
    print(f"\n📝 对话摘要: {summary}")

    await chat_system.cleanup()
    print()


async def main():
    """主函数 - 运行所有集成示例"""
    print("🎯 RAG知识库系统集成示例")
    print("=" * 50)

    examples = [
        run_fastapi_integration_example,
        run_testcase_integration_example,
        run_ai_chat_integration_example,
    ]

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"❌ 示例 {example.__name__} 执行失败: {e}")

        print("-" * 30)

    print("🎉 所有集成示例执行完成！")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
