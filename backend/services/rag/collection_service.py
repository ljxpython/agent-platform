"""
RAG Collection管理服务 - 重写版本
专注于数据库记录管理，向量数据库操作交给 rag_core 处理
支持项目隔离的知识库管理
"""

from typing import Any, Dict, List, Optional

from loguru import logger
from tortoise.exceptions import DoesNotExist, IntegrityError

from backend.conf.rag_config import get_rag_config
from backend.models.rag import RAGCollection, RAGDocument


class RAGCollectionService:
    """
    RAG Collection管理服务 - 重写版本

    设计原则：
    1. 专注于数据库记录的 CRUD 操作
    2. 向量数据库操作交给 rag_core 处理
    3. 支持项目隔离
    4. 避免与 rag_core 功能重复
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        初始化Collection服务

        Args:
            project_id: 项目ID，用于知识库隔离
        """
        self.project_id = project_id or "default"
        logger.info(f"🔧 Collection服务初始化 | 项目: {self.project_id}")

    def _get_project_collection_name(self, collection_name: str) -> str:
        """
        获取项目级别的 collection 名称
        格式: {project_id}_{collection_name}
        """
        if self.project_id == "default":
            return collection_name
        return f"{self.project_id}_{collection_name}"

    async def initialize_default_collections(self):
        """
        初始化默认的Collections（仅在数据库中创建记录）
        支持项目隔离，为当前项目创建默认collections
        """
        logger.info(f"🚀 初始化默认RAG Collections | 项目: {self.project_id}")

        # 获取当前配置的维度
        rag_config = get_rag_config()
        default_dimension = rag_config.milvus.dimension

        # 定义默认的collection模板
        default_collection_templates = [
            {
                "name": "general",
                "display_name": "通用知识库",
                "description": "通用知识和常见问题解答",
                "business_type": "general",
            },
            {
                "name": "testcase",
                "display_name": "测试用例知识库",
                "description": "测试用例生成和测试方法相关知识",
                "business_type": "testcase",
            },
            {
                "name": "ui_testing",
                "display_name": "UI测试知识库",
                "description": "UI自动化测试和脚本生成相关知识",
                "business_type": "ui_testing",
            },
            {
                "name": "ai_chat",
                "display_name": "AI对话知识库",
                "description": "AI对话和智能助手相关知识",
                "business_type": "ai_chat",
            },
        ]

        created_count = 0
        for template in default_collection_templates:
            try:
                # 生成项目级别的collection名称
                project_collection_name = self._get_project_collection_name(
                    template["name"]
                )

                # 检查是否已存在
                existing = await RAGCollection.get_or_none(name=project_collection_name)
                if existing:
                    logger.info(f"Collection已存在: {project_collection_name}")
                    continue

                # 创建数据库记录
                collection_data = {
                    "name": project_collection_name,
                    "display_name": f"{template['display_name']} ({self.project_id})",
                    "description": f"项目 {self.project_id} 的{template['description']}",
                    "business_type": template["business_type"],
                    "dimension": default_dimension,
                    "chunk_size": rag_config.chunk_size,
                    "chunk_overlap": rag_config.chunk_overlap,
                    "top_k": rag_config.top_k,
                    "similarity_threshold": rag_config.similarity_threshold,
                    "metadata": {
                        "project_id": self.project_id,
                        "original_name": template["name"],
                        "created_by": "collection_service",
                    },
                }

                collection = await RAGCollection.create(**collection_data)
                logger.success(f"✅ 创建Collection记录: {collection.name}")
                created_count += 1

            except Exception as e:
                logger.error(f"❌ 创建Collection失败 {template['name']}: {e}")

        logger.success(
            f"🎉 项目默认Collections初始化完成 | 项目: {self.project_id} | 新创建: {created_count} 个"
        )
        logger.info("💡 向量数据库Collection将在首次使用时由RAGService自动创建")
        return created_count

    async def ensure_default_collections(self):
        """确保默认Collections存在，如果不存在则创建"""
        try:
            existing_collections = await self.get_all_collections()
            if len(existing_collections) == 0:
                logger.info(
                    f"🔧 检测到项目 {self.project_id} 没有Collections，开始创建默认Collections..."
                )
                created_count = await self.initialize_default_collections()
                logger.success(f"✅ 自动创建了 {created_count} 个默认Collections")
                return created_count
            else:
                logger.info(
                    f"📋 项目 {self.project_id} 已有 {len(existing_collections)} 个Collections"
                )
                return 0
        except Exception as e:
            logger.error(
                f"❌ 确保默认Collections失败 | 项目: {self.project_id} | 错误: {e}"
            )
            return 0

    async def ensure_collection_exists(self, collection_name: str) -> Dict:
        """
        确保Collection在数据库中存在
        注意：向量数据库操作由RAGService负责

        Args:
            collection_name: 原始collection名称

        Returns:
            Dict: 操作结果
        """
        try:
            project_collection_name = self._get_project_collection_name(collection_name)
            logger.info(
                f"🔍 检查Collection数据库记录: {collection_name} -> {project_collection_name}"
            )

            # 检查数据库记录是否存在
            collection = await RAGCollection.get_or_none(name=project_collection_name)
            if collection:
                logger.info(f"✅ Collection数据库记录已存在: {project_collection_name}")
                return {
                    "success": True,
                    "message": "Collection数据库记录已存在",
                    "collection_name": collection_name,
                    "project_collection_name": project_collection_name,
                    "action": "already_exists",
                }

            # 如果不存在，创建数据库记录
            logger.info(f"📝 创建Collection数据库记录: {project_collection_name}")

            rag_config = get_rag_config()
            collection_data = {
                "name": project_collection_name,
                "display_name": f"{collection_name} ({self.project_id})",
                "description": f"项目 {self.project_id} 的 {collection_name} 知识库",
                "business_type": collection_name,
                "dimension": rag_config.milvus.dimension,
                "chunk_size": rag_config.chunk_size,
                "chunk_overlap": rag_config.chunk_overlap,
                "top_k": rag_config.top_k,
                "similarity_threshold": rag_config.similarity_threshold,
                "metadata": {
                    "project_id": self.project_id,
                    "original_name": collection_name,
                    "created_by": "collection_service",
                },
            }

            new_collection = await RAGCollection.create(**collection_data)
            logger.success(
                f"✅ Collection数据库记录创建成功: {project_collection_name}"
            )

            return {
                "success": True,
                "message": "Collection数据库记录创建成功",
                "collection_name": collection_name,
                "project_collection_name": project_collection_name,
                "action": "created",
                "collection_id": new_collection.id,
            }

        except Exception as e:
            logger.error(f"❌ 确保Collection存在失败 {collection_name}: {e}")
            return {
                "success": False,
                "message": f"操作失败: {str(e)}",
                "collection_name": collection_name,
                "error": str(e),
            }

    async def get_all_collections(self) -> List[Dict]:
        """获取当前项目的所有Collections"""
        try:
            # 获取所有collections，然后在Python中过滤
            all_collections = await RAGCollection.all().order_by("created_at")

            # 根据项目ID过滤collections
            if self.project_id == "default":
                # 默认项目：获取不带项目前缀的collections（不包含下划线的）
                collections = [col for col in all_collections if "_" not in col.name]
            else:
                # 其他项目：获取带有项目前缀的collections
                project_prefix = f"{self.project_id}_"
                collections = [
                    col
                    for col in all_collections
                    if col.name.startswith(project_prefix)
                ]

            # 如果没有Collections，自动创建默认的
            if len(collections) == 0:
                logger.info(
                    f"🔧 项目 {self.project_id} 没有Collections，自动创建默认Collections..."
                )
                await self.initialize_default_collections()
                # 重新获取
                all_collections = await RAGCollection.all().order_by("created_at")
                if self.project_id == "default":
                    collections = [
                        col for col in all_collections if "_" not in col.name
                    ]
                else:
                    project_prefix = f"{self.project_id}_"
                    collections = [
                        col
                        for col in all_collections
                        if col.name.startswith(project_prefix)
                    ]

            result = []
            for collection in collections:
                # 获取文档数量
                doc_count = await RAGDocument.filter(collection=collection).count()

                # 提取原始collection名称
                original_name = collection.name
                if self.project_id != "default" and "_" in collection.name:
                    original_name = collection.name.split("_", 1)[1]

                result.append(
                    {
                        "id": collection.id,
                        "name": original_name,  # 返回原始名称
                        "project_collection_name": collection.name,  # 完整的项目级别名称
                        "display_name": collection.display_name,
                        "description": collection.description,
                        "business_type": collection.business_type,
                        "dimension": collection.dimension,
                        "chunk_size": collection.chunk_size,
                        "chunk_overlap": collection.chunk_overlap,
                        "top_k": collection.top_k,
                        "similarity_threshold": collection.similarity_threshold,
                        "is_active": collection.is_active,
                        "document_count": doc_count,
                        "last_updated": collection.last_updated.isoformat(),
                        "created_at": collection.created_at.isoformat(),
                        "metadata": collection.metadata,
                        "project_id": self.project_id,
                    }
                )

            logger.info(
                f"📋 获取到 {len(result)} 个Collections | 项目: {self.project_id}"
            )
            return result

        except Exception as e:
            logger.error(
                f"❌ 获取Collections失败 | 项目: {self.project_id} | 错误: {e}"
            )
            return []

    async def get_collection_names(self) -> List[str]:
        """获取当前项目所有激活的Collection名称（返回原始名称）"""
        try:
            collections = await self.get_all_collections()
            # 只返回激活的collection的原始名称
            names = [col["name"] for col in collections if col["is_active"]]
            logger.info(
                f"📋 获取到 {len(names)} 个激活的Collection名称 | 项目: {self.project_id}"
            )
            return names
        except Exception as e:
            logger.error(
                f"❌ 获取Collection名称失败 | 项目: {self.project_id} | 错误: {e}"
            )
            return []

    async def get_collection_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取Collection（支持项目隔离）"""
        try:
            project_collection_name = self._get_project_collection_name(name)
            collection = await RAGCollection.get_or_none(name=project_collection_name)
            if not collection:
                logger.warning(f"Collection不存在: {name} -> {project_collection_name}")
                return None

            # 获取文档数量
            doc_count = await RAGDocument.filter(collection=collection).count()

            return {
                "id": collection.id,
                "name": name,  # 返回原始名称
                "project_collection_name": collection.name,  # 完整的项目级别名称
                "display_name": collection.display_name,
                "description": collection.description,
                "business_type": collection.business_type,
                "dimension": collection.dimension,
                "chunk_size": collection.chunk_size,
                "chunk_overlap": collection.chunk_overlap,
                "top_k": collection.top_k,
                "similarity_threshold": collection.similarity_threshold,
                "is_active": collection.is_active,
                "document_count": doc_count,
                "last_updated": collection.last_updated.isoformat(),
                "created_at": collection.created_at.isoformat(),
                "metadata": collection.metadata,
                "project_id": self.project_id,
            }

        except Exception as e:
            logger.error(
                f"❌ 获取Collection失败 | 名称: {name} | 项目: {self.project_id} | 错误: {e}"
            )
            return None

    async def create_collection(self, collection_data: Dict) -> Dict:
        """
        创建新的Collection（仅数据库记录，向量数据库由RAGService处理）
        支持项目隔离
        """
        try:
            original_name = collection_data["name"]
            project_collection_name = self._get_project_collection_name(original_name)

            # 检查项目级别的名称是否已存在
            existing = await RAGCollection.get_or_none(name=project_collection_name)
            if existing:
                return {
                    "success": False,
                    "message": f"Collection名称 '{original_name}' 在项目 {self.project_id} 中已存在",
                    "project_collection_name": project_collection_name,
                }

            logger.info(
                f"📝 创建Collection数据库记录: {original_name} -> {project_collection_name}"
            )

            # 准备数据库记录数据
            rag_config = get_rag_config()
            db_data = {
                "name": project_collection_name,
                "display_name": collection_data.get(
                    "display_name", f"{original_name} ({self.project_id})"
                ),
                "description": collection_data.get(
                    "description", f"项目 {self.project_id} 的 {original_name} 知识库"
                ),
                "business_type": collection_data.get("business_type", original_name),
                "dimension": collection_data.get(
                    "dimension", rag_config.milvus.dimension
                ),
                "chunk_size": collection_data.get("chunk_size", rag_config.chunk_size),
                "chunk_overlap": collection_data.get(
                    "chunk_overlap", rag_config.chunk_overlap
                ),
                "top_k": collection_data.get("top_k", rag_config.top_k),
                "similarity_threshold": collection_data.get(
                    "similarity_threshold", rag_config.similarity_threshold
                ),
                "is_active": collection_data.get("is_active", True),
                "metadata": {
                    "project_id": self.project_id,
                    "original_name": original_name,
                    "created_by": "collection_service",
                    **collection_data.get("metadata", {}),
                },
            }

            # 创建数据库记录
            collection = await RAGCollection.create(**db_data)
            logger.success(
                f"✅ Collection数据库记录创建成功: {project_collection_name}"
            )

            return {
                "success": True,
                "message": "Collection创建成功",
                "collection": {
                    "id": collection.id,
                    "name": original_name,
                    "project_collection_name": project_collection_name,
                    "display_name": collection.display_name,
                    "description": collection.description,
                    "business_type": collection.business_type,
                    "project_id": self.project_id,
                },
                "note": "向量数据库Collection将在首次使用时由RAGService自动创建",
            }

        except IntegrityError as e:
            logger.error(f"❌ Collection名称重复: {e}")
            return {"success": False, "message": "Collection名称已存在"}
        except Exception as e:
            logger.error(f"❌ 创建Collection失败: {e}")
            return {"success": False, "message": f"创建失败: {str(e)}"}

    async def update_collection(self, name: str, update_data: Dict) -> Dict:
        """更新Collection（仅数据库记录）"""
        try:
            project_collection_name = self._get_project_collection_name(name)
            collection = await RAGCollection.get_or_none(name=project_collection_name)
            if not collection:
                return {
                    "success": False,
                    "message": f"Collection '{name}' 在项目 {self.project_id} 中不存在",
                }

            logger.info(f"🔄 更新Collection: {name} -> {project_collection_name}")

            # 更新数据库记录
            for field, value in update_data.items():
                if hasattr(collection, field) and field not in [
                    "name",
                    "id",
                ]:  # 不允许修改name和id
                    setattr(collection, field, value)

            await collection.save()
            logger.success(
                f"✅ Collection数据库记录更新成功: {project_collection_name}"
            )

            return {
                "success": True,
                "message": "Collection更新成功",
                "collection_name": name,
                "project_collection_name": project_collection_name,
                "note": "向量数据库配置将在下次使用时自动同步",
            }

        except Exception as e:
            logger.error(
                f"❌ 更新Collection失败 | 名称: {name} | 项目: {self.project_id} | 错误: {e}"
            )
            return {"success": False, "message": f"更新失败: {str(e)}"}

    async def delete_collection(self, name: str) -> Dict:
        """删除Collection（仅数据库记录，向量数据库由RAGService处理）"""
        try:
            project_collection_name = self._get_project_collection_name(name)
            collection = await RAGCollection.get_or_none(name=project_collection_name)
            if not collection:
                return {
                    "success": False,
                    "message": f"Collection '{name}' 在项目 {self.project_id} 中不存在",
                }

            logger.warning(f"🗑️ 删除Collection: {name} -> {project_collection_name}")

            # 删除相关文档记录
            doc_count = await RAGDocument.filter(collection=collection).count()
            await RAGDocument.filter(collection=collection).delete()

            # 删除Collection记录
            await collection.delete()
            logger.success(
                f"✅ Collection删除成功: {project_collection_name}，同时删除了 {doc_count} 个文档记录"
            )

            return {
                "success": True,
                "message": f"Collection删除成功，同时删除了 {doc_count} 个相关文档记录",
                "collection_name": name,
                "project_collection_name": project_collection_name,
                "deleted_documents": doc_count,
                "note": "向量数据库中的数据需要通过RAGService清理",
            }

        except Exception as e:
            logger.error(
                f"❌ 删除Collection失败 | 名称: {name} | 项目: {self.project_id} | 错误: {e}"
            )
            return {"success": False, "message": f"删除失败: {str(e)}"}

    async def sync_from_milvus(self, rag_service) -> Dict[str, Any]:
        """
        从Milvus向量数据库同步collections到SQLite数据库

        Args:
            rag_service: RAGService实例，用于查询Milvus

        Returns:
            Dict[str, Any]: 同步结果
        """
        try:
            logger.info(f"🔄 开始从Milvus同步Collections | 项目: {self.project_id}")

            # 获取Milvus中的collections
            milvus_result = await rag_service.list_milvus_collections()
            if not milvus_result.get("success"):
                return {
                    "success": False,
                    "message": "获取Milvus Collections失败",
                    "error": milvus_result.get("error"),
                }

            milvus_collections = milvus_result.get("collections", [])

            # 获取数据库中已有的collections
            existing_collections = await self.get_all_collections()
            existing_names = {
                col["project_collection_name"] for col in existing_collections
            }

            # 同步结果统计
            created_count = 0
            updated_count = 0
            errors = []

            # 获取默认配置
            rag_config = get_rag_config()

            for milvus_col in milvus_collections:
                try:
                    project_collection_name = milvus_col["project_collection_name"]
                    original_name = milvus_col["name"]

                    if project_collection_name in existing_names:
                        # 已存在，可以选择更新（这里暂时跳过）
                        logger.info(
                            f"Collection已存在，跳过: {project_collection_name}"
                        )
                        continue

                    # 获取Milvus中的详细信息
                    milvus_info = await rag_service.get_milvus_collection_info(
                        original_name
                    )

                    # 创建数据库记录
                    collection_data = {
                        "name": project_collection_name,
                        "display_name": f"{original_name} ({self.project_id}) [从Milvus同步]",
                        "description": f"从Milvus同步的 {original_name} 知识库",
                        "business_type": original_name,
                        "dimension": rag_config.milvus.dimension,  # 使用默认配置
                        "chunk_size": rag_config.chunk_size,
                        "chunk_overlap": rag_config.chunk_overlap,
                        "top_k": rag_config.top_k,
                        "similarity_threshold": rag_config.similarity_threshold,
                        "metadata": {
                            "project_id": self.project_id,
                            "original_name": original_name,
                            "synced_from_milvus": True,
                            "milvus_entities": (
                                milvus_info.get("num_entities", 0)
                                if milvus_info.get("success")
                                else 0
                            ),
                        },
                    }

                    collection = await RAGCollection.create(**collection_data)
                    created_count += 1

                    logger.success(
                        f"✅ 从Milvus同步Collection: {project_collection_name}"
                    )

                except Exception as e:
                    error_msg = (
                        f"同步Collection失败 {project_collection_name}: {str(e)}"
                    )
                    errors.append(error_msg)
                    logger.error(f"❌ {error_msg}")

            logger.success(
                f"🎉 Milvus同步完成 | 项目: {self.project_id} | 新建: {created_count} | 错误: {len(errors)}"
            )

            return {
                "success": True,
                "project_id": self.project_id,
                "message": f"同步完成，新建 {created_count} 个Collection",
                "created_count": created_count,
                "updated_count": updated_count,
                "error_count": len(errors),
                "errors": errors,
                "milvus_collections_count": len(milvus_collections),
            }

        except Exception as e:
            logger.error(f"❌ 从Milvus同步失败 | 项目: {self.project_id} | 错误: {e}")
            return {
                "success": False,
                "project_id": self.project_id,
                "message": f"同步失败: {str(e)}",
                "error": str(e),
            }

    async def update_document_count(self, collection_name: str, count: int):
        """更新Collection的文档数量"""
        try:
            project_collection_name = self._get_project_collection_name(collection_name)
            collection = await RAGCollection.get_or_none(name=project_collection_name)
            if collection:
                collection.document_count = count
                await collection.save()
                logger.info(
                    f"📊 更新Collection文档数量: {project_collection_name} -> {count}"
                )
        except Exception as e:
            logger.error(
                f"❌ 更新文档数量失败 | Collection: {collection_name} | 项目: {self.project_id} | 错误: {e}"
            )


# ==================== 服务实例管理 ====================

# 项目级别的Collection服务实例缓存
_collection_services: Dict[str, RAGCollectionService] = {}


def get_collection_service(project_id: Optional[str] = None) -> RAGCollectionService:
    """
    获取Collection服务实例（支持项目隔离）

    Args:
        project_id: 项目ID，如果不提供则使用默认项目

    Returns:
        RAGCollectionService: Collection服务实例
    """
    global _collection_services

    project_id = project_id or "default"

    if project_id not in _collection_services:
        logger.info(f"🔧 创建新的Collection服务实例 | 项目: {project_id}")
        _collection_services[project_id] = RAGCollectionService(project_id=project_id)

    return _collection_services[project_id]


# 保持向后兼容性的全局实例
collection_service = get_collection_service("default")
