"""
RAG知识库服务 - 重写版本
基于 backend/rag_core 的薄封装，为 AI 测试系统提供 RAG 功能
支持项目隔离的知识库管理
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from backend.conf.rag_config import RAGConfig, get_rag_config
from backend.models.rag import RAGCollection, RAGDocument
from backend.rag_core.rag_system import QueryResult, RAGSystem


class RAGService:
    """
    RAG知识库服务 - 重写版本

    设计原则：
    1. 薄封装 backend/rag_core.RAGSystem
    2. 添加项目隔离支持
    3. 保持与现有 API 的兼容性
    4. 专注于业务逻辑，技术实现交给 rag_core
    """

    def __init__(
        self, config: Optional[RAGConfig] = None, project_id: Optional[str] = None
    ):
        """
        初始化RAG服务

        Args:
            config: RAG配置，如果不提供则使用默认配置
            project_id: 项目ID，用于知识库隔离（可选）
        """
        self.config = config or get_rag_config()
        self.project_id = project_id or "default"  # 默认项目
        self.rag_system: Optional[RAGSystem] = None
        self._initialized = False

        logger.info(f"🔧 RAG服务初始化 | 项目: {self.project_id}")

    async def initialize(self):
        """初始化RAG服务"""
        if self._initialized:
            return

        logger.info(f"🚀 正在初始化RAG服务... | 项目: {self.project_id}")

        try:
            # 使用 RAGSystem 作为核心引擎
            self.rag_system = RAGSystem(self.config)
            await self.rag_system.initialize()

            self._initialized = True
            logger.success(f"✅ RAG服务初始化完成 | 项目: {self.project_id}")

        except Exception as e:
            logger.error(f"❌ RAG服务初始化失败 | 项目: {self.project_id} | 错误: {e}")
            raise

    async def ensure_initialized(self):
        """确保服务已初始化"""
        if not self._initialized:
            await self.initialize()

    def _get_project_collection_name(self, collection_name: str) -> str:
        """
        获取项目级别的 collection 名称
        格式: {project_id}_{collection_name}

        Args:
            collection_name: 原始 collection 名称

        Returns:
            str: 项目级别的 collection 名称
        """
        if self.project_id == "default":
            return collection_name
        return f"{self.project_id}_{collection_name}"

    # ==================== Collection 管理方法 ====================

    async def setup_collection(
        self, collection_name: str, overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        设置 collection（支持项目隔离）

        Args:
            collection_name: collection名称
            overwrite: 是否覆盖现有collection

        Returns:
            Dict[str, Any]: 操作结果
        """
        await self.ensure_initialized()

        # 获取项目级别的 collection 名称
        project_collection_name = self._get_project_collection_name(collection_name)

        try:
            logger.info(
                f"🔧 设置Collection | 原名: {collection_name} | 项目名: {project_collection_name}"
            )

            # 直接使用 rag_core 的功能
            await self.rag_system.setup_collection(project_collection_name, overwrite)

            # 同步数据库记录
            await self._sync_collection_to_db(collection_name, project_collection_name)

            logger.success(f"✅ Collection设置成功 | {project_collection_name}")
            return {
                "success": True,
                "message": f"Collection {collection_name} 设置成功",
                "collection_name": collection_name,
                "project_collection_name": project_collection_name,
                "project_id": self.project_id,
            }

        except Exception as e:
            logger.error(f"❌ Collection设置失败 | {project_collection_name}: {e}")
            return {
                "success": False,
                "message": f"Collection {collection_name} 设置失败: {str(e)}",
                "collection_name": collection_name,
                "error": str(e),
            }

    async def _sync_collection_to_db(
        self, original_name: str, project_collection_name: str
    ):
        """同步 collection 信息到数据库"""
        try:
            # 检查数据库中是否已存在记录
            existing = await RAGCollection.get_or_none(name=project_collection_name)
            if existing:
                logger.info(f"📋 Collection数据库记录已存在: {project_collection_name}")
                return

            # 获取默认配置
            from backend.conf.rag_config import get_rag_config

            rag_config = get_rag_config()

            # 创建数据库记录
            await RAGCollection.create(
                name=project_collection_name,
                display_name=f"{original_name} ({self.project_id})",
                description=f"项目 {self.project_id} 的 {original_name} 知识库",
                business_type=original_name,  # 使用原始名称作为业务类型
                dimension=rag_config.milvus.dimension,
                chunk_size=rag_config.chunk_size,
                chunk_overlap=rag_config.chunk_overlap,
                top_k=rag_config.top_k,
                similarity_threshold=rag_config.similarity_threshold,
                metadata={
                    "project_id": self.project_id,
                    "original_name": original_name,
                },
            )

            logger.success(
                f"✅ Collection数据库记录创建成功: {project_collection_name}"
            )

        except Exception as e:
            logger.warning(f"⚠️ 同步Collection到数据库失败: {e}")

    def list_collections(self) -> List[str]:
        """列出当前项目的所有 collections（基于配置）"""
        if not self._initialized:
            return []

        # 获取所有 collections，然后过滤出当前项目的
        all_collections = self.rag_system.list_collections()

        if self.project_id == "default":
            # 默认项目返回不带前缀的 collections
            return [name for name in all_collections if "_" not in name]
        else:
            # 其他项目返回去掉项目前缀的 collections
            project_prefix = f"{self.project_id}_"
            return [
                name[len(project_prefix) :]
                for name in all_collections
                if name.startswith(project_prefix)
            ]

    async def list_milvus_collections(self) -> Dict[str, Any]:
        """
        列出Milvus向量数据库中实际存在的所有collections

        Returns:
            Dict[str, Any]: 包含Milvus中collections信息的结果
        """
        await self.ensure_initialized()

        try:
            logger.info(f"🔍 查询Milvus中的Collections | 项目: {self.project_id}")

            # 获取Milvus中所有collections
            all_milvus_collections = (
                self.rag_system.collection_manager.list_milvus_collections()
            )

            # 过滤出当前项目的collections
            project_collections = []

            if self.project_id == "default":
                # 默认项目：不带下划线前缀的collections
                for collection_name in all_milvus_collections:
                    if "_" not in collection_name:
                        project_collections.append(
                            {
                                "name": collection_name,
                                "project_collection_name": collection_name,
                                "project_id": self.project_id,
                            }
                        )
            else:
                # 其他项目：带有项目前缀的collections
                project_prefix = f"{self.project_id}_"
                for collection_name in all_milvus_collections:
                    if collection_name.startswith(project_prefix):
                        original_name = collection_name[len(project_prefix) :]
                        project_collections.append(
                            {
                                "name": original_name,
                                "project_collection_name": collection_name,
                                "project_id": self.project_id,
                            }
                        )

            logger.success(
                f"✅ 查询Milvus Collections成功 | 项目: {self.project_id} | 数量: {len(project_collections)}"
            )

            return {
                "success": True,
                "project_id": self.project_id,
                "total_collections": len(project_collections),
                "collections": project_collections,
                "all_milvus_collections": all_milvus_collections,  # 用于调试
            }

        except Exception as e:
            logger.error(
                f"❌ 查询Milvus Collections失败 | 项目: {self.project_id} | 错误: {e}"
            )
            return {
                "success": False,
                "project_id": self.project_id,
                "message": f"查询失败: {str(e)}",
                "error": str(e),
            }

    async def get_milvus_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        获取Milvus中collection的详细信息

        Args:
            collection_name: collection名称（原始名称）

        Returns:
            Dict[str, Any]: collection详细信息
        """
        await self.ensure_initialized()

        project_collection_name = self._get_project_collection_name(collection_name)

        try:
            logger.info(
                f"🔍 获取Milvus Collection信息 | {collection_name} -> {project_collection_name}"
            )

            # 获取Milvus中的collection信息
            milvus_info = self.rag_system.collection_manager.get_milvus_collection_info(
                project_collection_name
            )

            if not milvus_info:
                return {
                    "success": False,
                    "message": f"Collection '{collection_name}' 在Milvus中不存在",
                    "collection_name": collection_name,
                    "project_collection_name": project_collection_name,
                    "project_id": self.project_id,
                }

            # 添加项目信息
            milvus_info.update(
                {
                    "success": True,
                    "original_name": collection_name,
                    "project_collection_name": project_collection_name,
                    "project_id": self.project_id,
                }
            )

            logger.success(
                f"✅ 获取Milvus Collection信息成功 | {project_collection_name}"
            )
            return milvus_info

        except Exception as e:
            logger.error(
                f"❌ 获取Milvus Collection信息失败 | {project_collection_name} | 错误: {e}"
            )
            return {
                "success": False,
                "message": f"获取信息失败: {str(e)}",
                "collection_name": collection_name,
                "project_id": self.project_id,
                "error": str(e),
            }

    async def get_collection_info(
        self, collection_name: str
    ) -> Optional[Dict[str, Any]]:
        """获取 collection 信息"""
        await self.ensure_initialized()

        project_collection_name = self._get_project_collection_name(collection_name)
        info = self.rag_system.get_collection_info(project_collection_name)

        if info:
            # 添加项目信息
            info["project_id"] = self.project_id
            info["original_name"] = collection_name
            info["project_collection_name"] = project_collection_name

        return info

    async def get_all_collections_info(self) -> Dict[str, Any]:
        """获取当前项目所有 collections 信息"""
        await self.ensure_initialized()

        collections_info = {}
        for collection_name in self.list_collections():
            info = await self.get_collection_info(collection_name)
            if info:
                collections_info[collection_name] = info

        return {
            "project_id": self.project_id,
            "total_collections": len(collections_info),
            "collections": collections_info,
        }

    # ==================== 文档添加方法 ====================

    async def add_text(
        self,
        text: str,
        collection_name: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        添加文本到知识库（支持项目隔离）

        Args:
            text: 文本内容
            collection_name: collection名称
            metadata: 元数据

        Returns:
            Dict[str, Any]: 添加结果
        """
        await self.ensure_initialized()

        project_collection_name = self._get_project_collection_name(collection_name)
        operation_id = f"add_text_{hash(text[:100])}_{project_collection_name}"

        try:
            logger.info(f"🚀 [操作开始] {operation_id}")
            logger.info(
                f"📝 [文本信息] 长度: {len(text)} 字符 | Collection: {collection_name} -> {project_collection_name}"
            )
            logger.info(f"🏷️ [元数据] {metadata}")

            # 添加项目信息到元数据
            enhanced_metadata = metadata or {}
            enhanced_metadata.update(
                {
                    "project_id": self.project_id,
                    "original_collection": collection_name,
                    "added_by": "rag_service",
                }
            )

            # 使用 rag_core 添加文本
            logger.info(f"⚙️ [处理阶段] 开始向量化和存储...")
            node_count = await self.rag_system.add_text(
                text=text,
                collection_name=project_collection_name,
                metadata=enhanced_metadata,
            )

            # 更新数据库记录
            await self._update_collection_document_count(project_collection_name)

            logger.success(f"🎉 [操作完成] {operation_id}")
            logger.info(f"📊 [结果详情] 节点数: {node_count} | 文本长度: {len(text)}")

            return {
                "success": True,
                "message": "文本添加成功",
                "collection_name": collection_name,
                "project_collection_name": project_collection_name,
                "project_id": self.project_id,
                "node_count": node_count,
                "text_length": len(text),
            }

        except Exception as e:
            logger.error(f"💥 [操作失败] {operation_id} | 错误: {str(e)}")
            logger.error(f"🔍 [错误详情] 异常类型: {type(e).__name__}")
            return {
                "success": False,
                "message": f"文本添加失败: {str(e)}",
                "collection_name": collection_name,
                "project_id": self.project_id,
                "error": str(e),
            }

    async def _update_collection_document_count(self, project_collection_name: str):
        """更新数据库中的文档数量"""
        try:
            collection = await RAGCollection.get_or_none(name=project_collection_name)
            if collection:
                # 这里可以实现更精确的计数逻辑
                collection.document_count += 1
                await collection.save()
                logger.debug(f"📊 更新Collection文档数量: {project_collection_name}")
        except Exception as e:
            logger.warning(f"⚠️ 更新文档数量失败: {e}")

    async def add_text_to_collection(
        self,
        text: str,
        collection_name: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        添加文本到指定collection（add_text的别名方法，保持API兼容性）

        Args:
            text: 要添加的文本内容
            collection_name: 集合名称
            metadata: 元数据

        Returns:
            Dict: 添加结果，包含vector_count和chunk_count
        """
        result = await self.add_text(text, collection_name, metadata)

        # 为了兼容性，添加vector_count和chunk_count字段
        if result.get("success", False):
            node_count = result.get("node_count", 0)
            result["vector_count"] = node_count
            result["chunk_count"] = node_count

        return result

    async def add_file(
        self, file_path: Union[str, Path], collection_name: str = "general"
    ) -> Dict[str, Any]:
        """
        添加文件到知识库（支持项目隔离）

        Args:
            file_path: 文件路径
            collection_name: collection名称

        Returns:
            Dict[str, Any]: 添加结果
        """
        await self.ensure_initialized()

        project_collection_name = self._get_project_collection_name(collection_name)

        try:
            logger.info(
                f"📁 添加文件 | 路径: {file_path} | Collection: {collection_name} -> {project_collection_name}"
            )

            # 使用 rag_core 添加文件
            node_count = await self.rag_system.add_file(
                file_path, project_collection_name
            )

            # 更新数据库记录
            await self._update_collection_document_count(project_collection_name)

            logger.success(f"✅ 文件添加成功 | 节点数: {node_count}")
            return {
                "success": True,
                "message": "文件添加成功",
                "collection_name": collection_name,
                "project_collection_name": project_collection_name,
                "project_id": self.project_id,
                "node_count": node_count,
                "file_path": str(file_path),
            }

        except Exception as e:
            logger.error(
                f"❌ 文件添加失败 | Collection: {project_collection_name} | 错误: {e}"
            )
            return {
                "success": False,
                "message": f"文件添加失败: {str(e)}",
                "collection_name": collection_name,
                "project_id": self.project_id,
                "file_path": str(file_path),
                "error": str(e),
            }

    # ==================== 查询方法 ====================

    async def query(
        self, question: str, collection_name: str = "general", **kwargs
    ) -> Dict[str, Any]:
        """
        执行RAG查询（支持项目隔离）

        Args:
            question: 查询问题
            collection_name: collection名称
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 查询结果
        """
        await self.ensure_initialized()

        project_collection_name = self._get_project_collection_name(collection_name)

        try:
            logger.info(
                f"🔍 RAG查询 | 问题: {question[:50]}... | Collection: {collection_name} -> {project_collection_name}"
            )

            # 使用 rag_core 执行查询
            result: QueryResult = await self.rag_system.query(
                question, project_collection_name, **kwargs
            )

            # 记录查询日志到数据库
            await self._log_query(question, result, collection_name)

            logger.success(
                f"✅ RAG查询成功 | 检索到 {len(result.retrieved_nodes)} 个文档"
            )
            return {
                "success": True,
                "query": result.query,
                "answer": result.answer,
                "collection_name": collection_name,
                "project_collection_name": project_collection_name,
                "project_id": self.project_id,
                "business_type": result.business_type,
                "response_time": result.response_time,
                "retrieved_count": len(result.retrieved_nodes),
                "metadata": result.metadata,
                "retrieved_nodes": [
                    {
                        "text": (
                            node.node.text[:200] + "..."
                            if len(node.node.text) > 200
                            else node.node.text
                        ),
                        "score": node.score,
                        "metadata": node.node.metadata,
                    }
                    for node in result.retrieved_nodes
                ],
            }

        except Exception as e:
            logger.error(
                f"❌ RAG查询失败 | Collection: {project_collection_name} | 错误: {e}"
            )
            return {
                "success": False,
                "message": f"RAG查询失败: {str(e)}",
                "collection_name": collection_name,
                "project_id": self.project_id,
                "query": question,
                "error": str(e),
            }

    async def _log_query(
        self, question: str, result: QueryResult, original_collection: str
    ):
        """记录查询日志到数据库"""
        try:
            # 这里可以实现查询日志记录逻辑
            # 暂时跳过，避免复杂化
            pass
        except Exception as e:
            logger.warning(f"⚠️ 记录查询日志失败: {e}")

    async def query_multiple_collections(
        self, question: str, collection_names: List[str], **kwargs
    ) -> Dict[str, Any]:
        """
        在多个collections中查询（支持项目隔离）

        Args:
            question: 查询问题
            collection_names: collection名称列表
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 查询结果
        """
        await self.ensure_initialized()

        try:
            # 转换为项目级别的 collection 名称
            project_collection_names = [
                self._get_project_collection_name(name) for name in collection_names
            ]

            logger.info(
                f"🔍 多Collection查询 | 问题: {question[:50]}... | Collections: {collection_names}"
            )

            # 使用 rag_core 执行多Collection查询
            results = await self.rag_system.query_multiple_collections(
                question, project_collection_names, **kwargs
            )

            formatted_results = []
            for i, result in enumerate(results):
                original_name = (
                    collection_names[i] if i < len(collection_names) else "unknown"
                )
                formatted_results.append(
                    {
                        "collection_name": original_name,
                        "project_collection_name": result.collection_name,
                        "business_type": result.business_type,
                        "answer": result.answer,
                        "response_time": result.response_time,
                        "retrieved_count": len(result.retrieved_nodes),
                    }
                )

            logger.success(
                f"✅ 多Collection查询成功 | 查询了 {len(formatted_results)} 个Collection"
            )
            return {
                "success": True,
                "query": question,
                "project_id": self.project_id,
                "total_collections": len(formatted_results),
                "results": formatted_results,
            }

        except Exception as e:
            logger.error(f"❌ 多Collection查询失败 | 错误: {e}")
            return {
                "success": False,
                "message": f"多Collection查询失败: {str(e)}",
                "query": question,
                "collection_names": collection_names,
                "project_id": self.project_id,
                "error": str(e),
            }

    async def query_business_type(
        self, question: str, business_type: str, **kwargs
    ) -> Dict[str, Any]:
        """
        根据业务类型查询（支持项目隔离）

        Args:
            question: 查询问题
            business_type: 业务类型
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 查询结果
        """
        await self.ensure_initialized()

        try:
            logger.info(
                f"🔍 业务类型查询 | 问题: {question[:50]}... | 业务类型: {business_type}"
            )

            # 对于项目隔离，我们需要找到当前项目中属于指定业务类型的collections
            # 这里简化处理，直接查询对应的collection
            collection_name = business_type
            project_collection_name = self._get_project_collection_name(collection_name)

            # 使用单个collection查询代替业务类型查询
            result = await self.rag_system.query(
                question, project_collection_name, **kwargs
            )

            formatted_results = [
                {
                    "collection_name": collection_name,
                    "project_collection_name": project_collection_name,
                    "answer": result.answer,
                    "response_time": result.response_time,
                    "retrieved_count": len(result.retrieved_nodes),
                }
            ]

            logger.success(f"✅ 业务类型查询成功 | 业务类型: {business_type}")
            return {
                "success": True,
                "query": question,
                "business_type": business_type,
                "project_id": self.project_id,
                "total_results": len(formatted_results),
                "results": formatted_results,
            }

        except Exception as e:
            logger.error(f"❌ 业务类型查询失败 | 业务类型: {business_type} | 错误: {e}")
            return {
                "success": False,
                "message": f"业务类型查询失败: {str(e)}",
                "query": question,
                "business_type": business_type,
                "project_id": self.project_id,
                "error": str(e),
            }

    async def chat(
        self, message: str, collection_name: str = "general"
    ) -> Dict[str, Any]:
        """
        简单聊天接口（支持项目隔离）

        Args:
            message: 聊天消息
            collection_name: collection名称

        Returns:
            Dict[str, Any]: 聊天结果
        """
        await self.ensure_initialized()

        project_collection_name = self._get_project_collection_name(collection_name)

        try:
            logger.info(
                f"💬 RAG聊天 | 消息: {message[:50]}... | Collection: {collection_name} -> {project_collection_name}"
            )

            # 使用 rag_core 的聊天功能
            answer = await self.rag_system.chat(message, project_collection_name)

            logger.success(f"✅ RAG聊天成功")
            return {
                "success": True,
                "message": message,
                "answer": answer,
                "collection_name": collection_name,
                "project_collection_name": project_collection_name,
                "project_id": self.project_id,
            }

        except Exception as e:
            logger.error(
                f"❌ 聊天失败 | Collection: {project_collection_name} | 错误: {e}"
            )
            return {
                "success": False,
                "message": f"聊天失败: {str(e)}",
                "collection_name": collection_name,
                "project_id": self.project_id,
                "user_message": message,
                "error": str(e),
            }

    # ==================== 系统管理方法 ====================

    async def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息（项目级别）"""
        await self.ensure_initialized()

        try:
            # 获取 rag_core 的统计信息
            core_stats = self.rag_system.get_stats()

            # 添加项目级别的统计信息
            project_collections = self.list_collections()

            return {
                "project_id": self.project_id,
                "project_collections": project_collections,
                "project_collection_count": len(project_collections),
                "core_stats": core_stats,
            }
        except Exception as e:
            logger.error(f"❌ 获取系统统计失败 | 项目: {self.project_id} | 错误: {e}")
            return {
                "project_id": self.project_id,
                "error": str(e),
            }

    async def clear_collection(self, collection_name: str) -> Dict[str, Any]:
        """清空collection数据（支持项目隔离）"""
        await self.ensure_initialized()

        project_collection_name = self._get_project_collection_name(collection_name)

        try:
            logger.warning(
                f"🗑️ 清空Collection数据 | Collection: {collection_name} -> {project_collection_name}"
            )

            # 使用 rag_core 清空数据
            await self.rag_system.clear_collection(project_collection_name)

            # 更新数据库记录
            collection = await RAGCollection.get_or_none(name=project_collection_name)
            if collection:
                collection.document_count = 0
                await collection.save()

            logger.success(f"✅ Collection数据清空成功 | {project_collection_name}")
            return {
                "success": True,
                "message": f"Collection {collection_name} 数据清空成功",
                "collection_name": collection_name,
                "project_collection_name": project_collection_name,
                "project_id": self.project_id,
            }

        except Exception as e:
            logger.error(
                f"❌ Collection数据清空失败 | {project_collection_name} | 错误: {e}"
            )
            return {
                "success": False,
                "message": f"Collection {collection_name} 数据清空失败: {str(e)}",
                "collection_name": collection_name,
                "project_id": self.project_id,
                "error": str(e),
            }

    async def clear_all_data(self) -> Dict[str, Any]:
        """清空当前项目的所有数据"""
        await self.ensure_initialized()

        try:
            logger.warning(f"🗑️ 清空项目所有数据 | 项目: {self.project_id}")

            # 获取当前项目的所有collections
            project_collections = self.list_collections()
            cleared_collections = []

            for collection_name in project_collections:
                try:
                    result = await self.clear_collection(collection_name)
                    if result.get("success"):
                        cleared_collections.append(collection_name)
                except Exception as e:
                    logger.error(
                        f"❌ 清空Collection失败: {collection_name} | 错误: {e}"
                    )

            logger.success(
                f"✅ 项目数据清空完成 | 项目: {self.project_id} | 清空了 {len(cleared_collections)} 个Collection"
            )
            return {
                "success": True,
                "message": f"项目 {self.project_id} 所有数据清空成功",
                "project_id": self.project_id,
                "cleared_collections": cleared_collections,
                "total_cleared": len(cleared_collections),
            }

        except Exception as e:
            logger.error(f"❌ 项目数据清空失败 | 项目: {self.project_id} | 错误: {e}")
            return {
                "success": False,
                "message": f"项目 {self.project_id} 数据清空失败: {str(e)}",
                "project_id": self.project_id,
                "error": str(e),
            }

    async def close(self):
        """关闭服务"""
        try:
            if self.rag_system:
                await self.rag_system.cleanup()

            self._initialized = False
            logger.info(f"🔄 RAG服务关闭完成 | 项目: {self.project_id}")
        except Exception as e:
            logger.error(f"❌ RAG服务关闭失败 | 项目: {self.project_id} | 错误: {e}")


# ==================== 服务实例管理 ====================

# 项目级别的RAG服务实例缓存
_rag_services: Dict[str, RAGService] = {}


async def get_rag_service(project_id: Optional[str] = None) -> RAGService:
    """
    获取RAG服务实例（支持项目隔离）

    Args:
        project_id: 项目ID，如果不提供则使用默认项目

    Returns:
        RAGService: RAG服务实例
    """
    global _rag_services

    project_id = project_id or "default"

    if project_id not in _rag_services:
        logger.info(f"🔧 创建新的RAG服务实例 | 项目: {project_id}")
        _rag_services[project_id] = RAGService(project_id=project_id)
        await _rag_services[project_id].initialize()

    return _rag_services[project_id]


async def close_all_rag_services():
    """关闭所有RAG服务实例"""
    global _rag_services

    logger.info(f"🔄 关闭所有RAG服务实例 | 总数: {len(_rag_services)}")

    for project_id, service in _rag_services.items():
        try:
            await service.close()
            logger.info(f"✅ RAG服务关闭成功 | 项目: {project_id}")
        except Exception as e:
            logger.error(f"❌ RAG服务关闭失败 | 项目: {project_id} | 错误: {e}")

    _rag_services.clear()
    logger.success("🎉 所有RAG服务实例关闭完成")


if __name__ == "__main__":
    # 测试代码 - 重写版本
    import asyncio

    async def test_rag_service():
        """测试重写后的RAG服务"""
        print("🧪 测试重写后的RAG服务")

        # 测试默认项目
        print("\n=== 测试默认项目 ===")
        service_default = await get_rag_service("default")

        # 设置collection
        setup_result = await service_default.setup_collection("general", overwrite=True)
        print(f"设置结果: {setup_result}")

        # 添加测试文本
        add_result = await service_default.add_text(
            "人工智能是计算机科学的一个分支，致力于创建智能机器。",
            "general",
            {"source": "test", "topic": "AI"},
        )
        print(f"添加结果: {add_result}")

        # 测试查询
        query_result = await service_default.query("什么是人工智能？", "general")
        print(f"查询结果: {query_result}")

        # 测试项目隔离
        print("\n=== 测试项目隔离 ===")
        service_project1 = await get_rag_service("project1")

        # 在project1中添加不同的内容
        add_result_p1 = await service_project1.add_text(
            "机器学习是人工智能的一个子集。",
            "general",
            {"source": "project1", "topic": "ML"},
        )
        print(f"项目1添加结果: {add_result_p1}")

        # 在project1中查询
        query_result_p1 = await service_project1.query("什么是机器学习？", "general")
        print(f"项目1查询结果: {query_result_p1}")

        # 获取统计信息
        stats_default = await service_default.get_system_stats()
        stats_project1 = await service_project1.get_system_stats()
        print(f"默认项目统计: {stats_default}")
        print(f"项目1统计: {stats_project1}")

        # 关闭所有服务
        await close_all_rag_services()
        print("✅ 测试完成")

    asyncio.run(test_rag_service())
