"""
RAG Collection管理服务
"""

from typing import Dict, List, Optional

from loguru import logger
from tortoise.exceptions import DoesNotExist, IntegrityError

from backend.models.rag import RAGCollection, RAGDocument


class RAGCollectionService:
    """RAG Collection管理服务"""

    async def initialize_default_collections(self):
        """初始化默认的Collections"""
        logger.info("🚀 初始化默认RAG Collections...")

        default_collections = [
            {
                "name": "general",
                "display_name": "通用知识库",
                "description": "通用知识和常见问题解答",
                "business_type": "general",
                "dimension": 768,
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "top_k": 5,
                "similarity_threshold": 0.7,
            },
            {
                "name": "testcase",
                "display_name": "测试用例知识库",
                "description": "测试用例生成和测试方法相关知识",
                "business_type": "testcase",
                "dimension": 768,
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "top_k": 5,
                "similarity_threshold": 0.7,
            },
            {
                "name": "ui_testing",
                "display_name": "UI测试知识库",
                "description": "UI自动化测试和脚本生成相关知识",
                "business_type": "ui_testing",
                "dimension": 768,
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "top_k": 5,
                "similarity_threshold": 0.7,
            },
            {
                "name": "ai_chat",
                "display_name": "AI对话知识库",
                "description": "AI对话和智能助手相关知识",
                "business_type": "ai_chat",
                "dimension": 768,
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "top_k": 5,
                "similarity_threshold": 0.7,
            },
        ]

        created_count = 0
        for collection_data in default_collections:
            try:
                # 检查是否已存在
                existing = await RAGCollection.get_or_none(name=collection_data["name"])
                if existing:
                    logger.info(f"Collection已存在: {collection_data['name']}")
                    continue

                # 创建新的Collection
                collection = await RAGCollection.create(**collection_data)
                logger.success(
                    f"✅ 创建Collection: {collection.name} - {collection.display_name}"
                )
                created_count += 1

            except Exception as e:
                logger.error(f"❌ 创建Collection失败 {collection_data['name']}: {e}")

        logger.success(f"🎉 默认Collections初始化完成，新创建 {created_count} 个")
        return created_count

    async def get_all_collections(self) -> List[Dict]:
        """获取所有Collections"""
        try:
            collections = await RAGCollection.all().order_by("created_at")
            result = []

            for collection in collections:
                # 获取文档数量
                doc_count = await RAGDocument.filter(collection=collection).count()

                result.append(
                    {
                        "id": collection.id,
                        "name": collection.name,
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
                    }
                )

            logger.info(f"📋 获取到 {len(result)} 个Collections")
            return result

        except Exception as e:
            logger.error(f"❌ 获取Collections失败: {e}")
            return []

    async def get_collection_names(self) -> List[str]:
        """获取所有激活的Collection名称"""
        try:
            collections = await RAGCollection.filter(is_active=True).all()
            names = [collection.name for collection in collections]
            logger.info(f"📋 获取到 {len(names)} 个激活的Collection名称: {names}")
            return names
        except Exception as e:
            logger.error(f"❌ 获取Collection名称失败: {e}")
            return []

    async def get_collection_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取Collection"""
        try:
            collection = await RAGCollection.get_or_none(name=name)
            if not collection:
                return None

            # 获取文档数量
            doc_count = await RAGDocument.filter(collection=collection).count()

            return {
                "id": collection.id,
                "name": collection.name,
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
            }

        except Exception as e:
            logger.error(f"❌ 获取Collection失败 {name}: {e}")
            return None

    async def create_collection(self, collection_data: Dict) -> Dict:
        """创建新的Collection"""
        try:
            # 检查名称是否已存在
            existing = await RAGCollection.get_or_none(name=collection_data["name"])
            if existing:
                return {
                    "success": False,
                    "message": f"Collection名称 '{collection_data['name']}' 已存在",
                }

            # 创建Collection
            collection = await RAGCollection.create(**collection_data)
            logger.success(f"✅ 创建Collection成功: {collection.name}")

            return {
                "success": True,
                "message": "Collection创建成功",
                "collection": {
                    "id": collection.id,
                    "name": collection.name,
                    "display_name": collection.display_name,
                    "description": collection.description,
                    "business_type": collection.business_type,
                },
            }

        except IntegrityError as e:
            logger.error(f"❌ Collection名称重复: {e}")
            return {"success": False, "message": "Collection名称已存在"}
        except Exception as e:
            logger.error(f"❌ 创建Collection失败: {e}")
            return {"success": False, "message": f"创建失败: {str(e)}"}

    async def update_collection(self, name: str, update_data: Dict) -> Dict:
        """更新Collection"""
        try:
            collection = await RAGCollection.get_or_none(name=name)
            if not collection:
                return {"success": False, "message": f"Collection '{name}' 不存在"}

            # 更新字段
            for field, value in update_data.items():
                if hasattr(collection, field) and field != "name":  # 不允许修改name
                    setattr(collection, field, value)

            await collection.save()
            logger.success(f"✅ 更新Collection成功: {collection.name}")

            return {"success": True, "message": "Collection更新成功"}

        except Exception as e:
            logger.error(f"❌ 更新Collection失败 {name}: {e}")
            return {"success": False, "message": f"更新失败: {str(e)}"}

    async def delete_collection(self, name: str) -> Dict:
        """删除Collection"""
        try:
            collection = await RAGCollection.get_or_none(name=name)
            if not collection:
                return {"success": False, "message": f"Collection '{name}' 不存在"}

            # 删除相关文档
            doc_count = await RAGDocument.filter(collection=collection).count()
            await RAGDocument.filter(collection=collection).delete()

            # 删除Collection
            await collection.delete()
            logger.success(
                f"✅ 删除Collection成功: {name}，同时删除了 {doc_count} 个文档"
            )

            return {
                "success": True,
                "message": f"Collection删除成功，同时删除了 {doc_count} 个相关文档",
            }

        except Exception as e:
            logger.error(f"❌ 删除Collection失败 {name}: {e}")
            return {"success": False, "message": f"删除失败: {str(e)}"}

    async def update_document_count(self, collection_name: str, count: int):
        """更新Collection的文档数量"""
        try:
            collection = await RAGCollection.get_or_none(name=collection_name)
            if collection:
                collection.document_count = count
                await collection.save()
                logger.info(f"📊 更新Collection文档数量: {collection_name} -> {count}")
        except Exception as e:
            logger.error(f"❌ 更新文档数量失败 {collection_name}: {e}")


# 创建全局实例
collection_service = RAGCollectionService()
