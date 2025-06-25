"""
RAG系统配置管理
基于项目现有配置系统，为RAG系统提供统一的配置管理
支持多collection架构，为不同业务提供专业知识库
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from backend.conf.config import settings


@dataclass
class CollectionConfig:
    """单个Collection配置"""

    name: str
    description: str
    dimension: int = 768  # nomic-embed-text的向量维度
    business_type: str = "general"  # 业务类型：general, testcase, ui_testing, ai_chat等

    # 检索参数
    top_k: int = 5
    similarity_threshold: float = 0.7

    # 文档处理参数
    chunk_size: int = 1000
    chunk_overlap: int = 200


@dataclass
class MilvusConfig:
    """Milvus向量数据库配置"""

    host: str
    port: int
    default_collection: str
    dimension: int = 768  # nomic-embed-text的向量维度
    collections: Dict[str, CollectionConfig] = None

    def __post_init__(self):
        """初始化默认collections"""
        if self.collections is None:
            self.collections = {
                "general": CollectionConfig(
                    name="general_knowledge",
                    description="通用知识库",
                    business_type="general",
                ),
                "testcase": CollectionConfig(
                    name="testcase_knowledge",
                    description="测试用例专业知识库",
                    business_type="testcase",
                    chunk_size=800,
                    chunk_overlap=150,
                ),
                "ui_testing": CollectionConfig(
                    name="ui_testing_knowledge",
                    description="UI测试专业知识库",
                    business_type="ui_testing",
                    chunk_size=1200,
                    chunk_overlap=200,
                ),
                "ai_chat": CollectionConfig(
                    name="ai_chat_knowledge",
                    description="AI对话专业知识库",
                    business_type="ai_chat",
                ),
            }

    @classmethod
    def from_settings(cls):
        """从settings中创建配置"""
        return cls(
            host=getattr(settings, "milvus_host", "localhost"),
            port=getattr(settings, "milvus_port", 19530),
            default_collection="general_knowledge",
            dimension=768,
        )


@dataclass
class OllamaConfig:
    """Ollama服务配置"""

    base_url: str
    embedding_model: str

    @classmethod
    def from_settings(cls):
        """从settings中创建配置"""
        return cls(
            base_url=getattr(settings, "ollama_base_url", "http://localhost:11434"),
            embedding_model=getattr(
                settings, "ollama_embedding_model", "nomic-embed-text"
            ),
        )


@dataclass
class DeepSeekConfig:
    """DeepSeek大语言模型配置"""

    model: str
    api_key: str
    base_url: str

    @classmethod
    def from_settings(cls):
        """从settings中创建配置"""
        return cls(
            model=getattr(settings, "deepseek_model", "deepseek-chat"),
            api_key=getattr(settings, "deepseek_api_key", ""),
            base_url=getattr(settings, "deepseek_base_url", "https://api.deepseek.com"),
        )


@dataclass
class RAGConfig:
    """RAG系统总配置"""

    milvus: MilvusConfig
    ollama: OllamaConfig
    deepseek: DeepSeekConfig

    @classmethod
    def from_settings(cls):
        """从settings中创建完整配置"""
        return cls(
            milvus=MilvusConfig.from_settings(),
            ollama=OllamaConfig.from_settings(),
            deepseek=DeepSeekConfig.from_settings(),
        )

    def get_collection_config(self, collection_name: str) -> Optional[CollectionConfig]:
        """获取指定collection的配置"""
        return self.milvus.collections.get(collection_name)

    def get_business_collections(self, business_type: str) -> List[CollectionConfig]:
        """获取指定业务类型的所有collections"""
        return [
            config
            for config in self.milvus.collections.values()
            if config.business_type == business_type
        ]


def get_rag_config() -> RAGConfig:
    """获取RAG系统配置"""
    return RAGConfig.from_settings()


def get_collection_config(collection_name: str) -> Optional[CollectionConfig]:
    """获取指定collection的配置"""
    config = get_rag_config()
    return config.get_collection_config(collection_name)


if __name__ == "__main__":
    # 测试配置
    config = get_rag_config()
    print("RAG系统配置:")
    print(f"Milvus: {config.milvus.host}:{config.milvus.port}")
    print(f"Ollama: {config.ollama.base_url}")
    print(f"DeepSeek: {config.deepseek.model}")
    print(f"嵌入模型: {config.ollama.embedding_model}")
