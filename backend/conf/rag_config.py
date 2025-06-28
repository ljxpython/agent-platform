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
    dimension: int
    business_type: str

    # 检索参数
    top_k: int
    similarity_threshold: float

    # 文档处理参数
    chunk_size: int
    chunk_overlap: int

    @classmethod
    def from_dict(cls, config_dict: dict, defaults: dict):
        """从配置字典创建CollectionConfig实例"""
        return cls(
            name=config_dict.get("name"),
            description=config_dict.get("description"),
            dimension=config_dict.get("dimension", defaults.get("dimension", 768)),
            business_type=config_dict.get("business_type", "general"),
            top_k=config_dict.get("top_k", defaults.get("top_k", 5)),
            similarity_threshold=config_dict.get(
                "similarity_threshold", defaults.get("similarity_threshold", 0.7)
            ),
            chunk_size=config_dict.get("chunk_size", defaults.get("chunk_size", 1000)),
            chunk_overlap=config_dict.get(
                "chunk_overlap", defaults.get("chunk_overlap", 200)
            ),
        )


@dataclass
class MilvusConfig:
    """Milvus向量数据库配置"""

    host: str
    port: int
    default_collection: str
    dimension: int
    collections: Dict[str, CollectionConfig]

    @classmethod
    def from_settings(cls):
        """从settings中创建配置"""
        rag_config = getattr(settings, "rag", {})
        milvus_config = rag_config.get("milvus", {})
        collection_defaults = rag_config.get("collection_defaults", {})
        collections_config = rag_config.get("collections", {})

        # 创建collections字典
        collections = {}
        for key, config_dict in collections_config.items():
            collections[key] = CollectionConfig.from_dict(
                config_dict, collection_defaults
            )

        return cls(
            host=milvus_config.get("host", "localhost"),
            port=milvus_config.get("port", 19530),
            default_collection=milvus_config.get(
                "default_collection", "general_knowledge"
            ),
            dimension=milvus_config.get(
                "dimension", collection_defaults.get("dimension", 768)
            ),
            collections=collections,
        )


@dataclass
class OllamaConfig:
    """Ollama服务配置"""

    base_url: str
    embedding_model: str

    @classmethod
    def from_settings(cls):
        """从settings中创建配置"""
        rag_config = getattr(settings, "rag", {})
        ollama_config = rag_config.get("ollama", {})

        return cls(
            base_url=ollama_config.get("base_url", "http://localhost:11434"),
            embedding_model=ollama_config.get("embedding_model", "nomic-embed-text"),
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
        rag_config = getattr(settings, "rag", {})
        deepseek_config = rag_config.get("deepseek", {})

        return cls(
            model=deepseek_config.get("model", "deepseek-chat"),
            api_key=deepseek_config.get("api_key", ""),
            base_url=deepseek_config.get("base_url", "https://api.deepseek.com/v1"),
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
