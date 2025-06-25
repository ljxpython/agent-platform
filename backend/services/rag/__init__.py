"""
RAG知识库服务模块
基于Milvus向量数据库、Ollama大模型服务、llama_index框架
支持多collection架构，为不同业务提供专业知识库
"""

from .rag_service import RAGService

__all__ = ["RAGService"]
