"""
Milvus向量数据库模块
基于LlamaIndex的Milvus向量存储实现，支持多collection架构
"""

from typing import Any, Dict, List, Optional

from llama_index.core.schema import BaseNode, TextNode
from llama_index.core.vector_stores import VectorStoreQuery, VectorStoreQueryResult
from llama_index.vector_stores.milvus import MilvusVectorStore
from loguru import logger

from backend.conf.rag_config import CollectionConfig, RAGConfig


class MilvusVectorDB:
    """Milvus向量数据库管理器，支持多collection"""

    def __init__(self, config: RAGConfig, collection_config: CollectionConfig):
        """
        初始化Milvus向量数据库

        Args:
            config: RAG总配置
            collection_config: 单个collection配置
        """
        self.config = config.milvus
        self.collection_config = collection_config
        self.vector_store: MilvusVectorStore = None
        self._initialized = False

        logger.info(f"🗄️ Milvus向量数据库初始化 - Collection: {collection_config.name}")

    def initialize(self):
        """初始化向量存储"""
        if self._initialized:
            return

        logger.info(
            f"🚀 正在连接Milvus向量数据库 - Collection: {self.collection_config.name}"
        )

        try:
            # 创建Milvus向量存储，确保连接到远程数据库
            self.vector_store = MilvusVectorStore(
                uri=f"http://{self.config.host}:{self.config.port}",  # 使用完整URI
                collection_name=self.collection_config.name,
                dim=self.collection_config.dimension,
                overwrite=False,  # 不覆盖现有集合
                # 确保不使用本地存储
                enable_sparse=False,
                hybrid_ranker="RRFRanker",
                hybrid_ranker_params={},
            )

            self._initialized = True
            logger.success(
                f"✅ Milvus向量数据库连接成功 - Collection: {self.collection_config.name}"
            )
            logger.info(f"🔗 连接URI: http://{self.config.host}:{self.config.port}")

        except Exception as e:
            logger.error(
                f"❌ Milvus向量数据库连接失败 - Collection: {self.collection_config.name}: {e}"
            )
            raise

    def create_collection(self, overwrite: bool = False):
        """
        创建集合

        Args:
            overwrite: 是否覆盖现有集合
        """
        if not self._initialized:
            self.initialize()

        logger.info(f"📦 创建集合: {self.collection_config.name}")

        try:
            if overwrite:
                # 重新创建向量存储以覆盖集合
                self.vector_store = MilvusVectorStore(
                    uri=f"http://{self.config.host}:{self.config.port}",
                    collection_name=self.collection_config.name,
                    dim=self.collection_config.dimension,
                    overwrite=True,
                    enable_sparse=False,
                    hybrid_ranker="RRFRanker",
                    hybrid_ranker_params={},
                )

            logger.success(f"✅ 集合创建完成: {self.collection_config.name}")

        except Exception as e:
            logger.error(f"❌ 集合创建失败 - {self.collection_config.name}: {e}")
            raise

    def add_nodes(self, nodes: List[BaseNode]) -> List[str]:
        """
        添加节点到向量数据库

        Args:
            nodes: 节点列表

        Returns:
            List[str]: 节点ID列表
        """
        if not self._initialized:
            self.initialize()

        if not nodes:
            logger.warning("⚠️ 节点列表为空，跳过添加")
            return []

        logger.info(
            f"📝 添加 {len(nodes)} 个节点到向量数据库 - Collection: {self.collection_config.name}"
        )

        try:
            # 使用向量存储添加节点
            node_ids = self.vector_store.add(nodes)

            logger.success(
                f"✅ 节点添加完成: {len(node_ids)} 个 - Collection: {self.collection_config.name}"
            )
            return node_ids

        except Exception as e:
            logger.error(
                f"❌ 节点添加失败 - Collection: {self.collection_config.name}: {e}"
            )
            raise

    def query(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> VectorStoreQueryResult:
        """
        查询相似向量

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            filters: 过滤条件

        Returns:
            VectorStoreQueryResult: 查询结果
        """
        if not self._initialized:
            self.initialize()

        top_k = top_k or self.collection_config.top_k
        logger.info(
            f"🔍 向量查询 - Collection: {self.collection_config.name}, top_k: {top_k}"
        )

        try:
            # 创建查询对象
            query_obj = VectorStoreQuery(
                query_embedding=query_embedding, similarity_top_k=top_k, filters=filters
            )

            # 执行查询
            result = self.vector_store.query(query_obj)

            logger.success(
                f"✅ 查询完成: 返回 {len(result.nodes)} 个结果 - Collection: {self.collection_config.name}"
            )
            return result

        except Exception as e:
            logger.error(
                f"❌ 向量查询失败 - Collection: {self.collection_config.name}: {e}"
            )
            raise

    def delete_collection(self):
        """删除集合"""
        if not self._initialized:
            self.initialize()

        logger.warning(f"🗑️ 删除集合: {self.collection_config.name}")

        try:
            # 通过重新创建并覆盖来删除集合
            self.vector_store = MilvusVectorStore(
                uri=f"http://{self.config.host}:{self.config.port}",
                collection_name=self.collection_config.name,
                dim=self.collection_config.dimension,
                overwrite=True,
                enable_sparse=False,
                hybrid_ranker="RRFRanker",
                hybrid_ranker_params={},
            )

            logger.success(f"✅ 集合删除完成: {self.collection_config.name}")

        except Exception as e:
            logger.error(f"❌ 集合删除失败 - {self.collection_config.name}: {e}")
            raise

    def verify_connection(self) -> bool:
        """
        验证与远程Milvus的连接状态

        Returns:
            bool: 连接是否正常
        """
        if not self._initialized:
            return False

        try:
            # 尝试获取collection信息来验证连接
            if hasattr(self.vector_store, "_milvus_client"):
                # 检查是否真的连接到远程Milvus
                client = self.vector_store._milvus_client
                if hasattr(client, "server_address"):
                    server_address = client.server_address
                    is_remote = not (
                        server_address.startswith("file://")
                        or server_address.endswith(".db")
                    )
                    logger.info(f"🔗 Milvus连接地址: {server_address}")
                    logger.info(
                        f"📡 远程连接状态: {'是' if is_remote else '否（本地文件）'}"
                    )
                    return is_remote
            return True
        except Exception as e:
            logger.error(f"❌ 连接验证失败: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        获取集合统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        if not self._initialized:
            self.initialize()

        try:
            # 验证连接状态
            is_remote_connected = self.verify_connection()

            # 基本统计信息
            stats = {
                "collection_name": self.collection_config.name,
                "description": self.collection_config.description,
                "business_type": self.collection_config.business_type,
                "dimension": self.collection_config.dimension,
                "host": self.config.host,
                "port": self.config.port,
                "uri": f"http://{self.config.host}:{self.config.port}",
                "initialized": self._initialized,
                "remote_connected": is_remote_connected,
                "chunk_size": self.collection_config.chunk_size,
                "chunk_overlap": self.collection_config.chunk_overlap,
                "top_k": self.collection_config.top_k,
                "similarity_threshold": self.collection_config.similarity_threshold,
            }

            return stats

        except Exception as e:
            logger.error(
                f"❌ 获取统计信息失败 - Collection: {self.collection_config.name}: {e}"
            )
            return {"error": str(e)}

    def close(self):
        """关闭连接"""
        if self.vector_store:
            # LlamaIndex的MilvusVectorStore通常不需要显式关闭
            pass

        self._initialized = False
        logger.info(
            f"🔄 Milvus向量数据库连接关闭 - Collection: {self.collection_config.name}"
        )


def create_vector_db(
    config: RAGConfig, collection_config: CollectionConfig
) -> MilvusVectorDB:
    """
    创建并初始化向量数据库

    Args:
        config: RAG配置
        collection_config: Collection配置

    Returns:
        MilvusVectorDB: 初始化后的向量数据库
    """
    vector_db = MilvusVectorDB(config, collection_config)
    vector_db.initialize()
    return vector_db


if __name__ == "__main__":
    # 测试代码
    from backend.conf.rag_config import get_rag_config

    config = get_rag_config()
    collection_config = config.get_collection_config("general")

    if collection_config:
        vector_db = create_vector_db(config, collection_config)

        # 创建测试节点
        test_nodes = [
            TextNode(
                text="人工智能是计算机科学的一个分支",
                metadata={"source": "test", "topic": "AI"},
            ),
            TextNode(
                text="机器学习是人工智能的子集",
                metadata={"source": "test", "topic": "ML"},
            ),
        ]

        # 测试添加节点
        try:
            # 创建集合
            vector_db.create_collection(overwrite=True)

            # 获取统计信息
            stats = vector_db.get_stats()
            print(f"统计信息: {stats}")

        except Exception as e:
            print(f"测试失败: {e}")

        finally:
            vector_db.close()
    else:
        print("未找到general collection配置")
