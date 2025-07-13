"""
RAG Collection管理API
提供Collection的CRUD操作
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel

from backend.models.rag import RAGCollection
from backend.services.rag.collection_service import get_collection_service
from backend.services.rag.rag_service import get_rag_service

rag_collections_router = APIRouter()


class CollectionCreateRequest(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = ""
    business_type: str = "general"
    chunk_size: Optional[int] = None  # 使用默认配置
    chunk_overlap: Optional[int] = None  # 使用默认配置
    dimension: Optional[int] = None  # 使用当前模型对应的dimension
    top_k: Optional[int] = None  # 使用默认配置
    similarity_threshold: Optional[float] = None  # 使用默认配置


class CollectionUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    business_type: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    dimension: Optional[int] = None
    top_k: Optional[int] = None
    similarity_threshold: Optional[float] = None


@rag_collections_router.get("/", summary="获取Collection列表")
async def get_collections(
    project_id: Optional[str] = Query(None, description="项目ID")
):
    """获取所有Collections列表（支持项目隔离）"""
    try:
        project_id = project_id or "default"
        logger.info(f"📋 获取Collection列表 | 项目: {project_id}")

        # 使用Collection服务获取列表
        from backend.services.rag.collection_service import get_collection_service

        collection_service = get_collection_service(project_id)
        collection_list = await collection_service.get_all_collections()

        return {
            "code": 200,
            "msg": "获取Collection列表成功",
            "data": {
                "collections": collection_list,
                "project_id": project_id,
            },
            "total": len(collection_list),
        }

    except Exception as e:
        logger.error(f"❌ 获取Collection列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取Collection列表失败: {str(e)}")


@rag_collections_router.get("/milvus", summary="获取Milvus中的Collection列表")
async def get_milvus_collections(
    project_id: Optional[str] = Query(None, description="项目ID")
):
    """获取Milvus向量数据库中实际存在的Collections列表"""
    try:
        project_id = project_id or "default"
        logger.info(f"🔍 获取Milvus Collection列表 | 项目: {project_id}")

        # 获取RAG服务
        from backend.services.rag.rag_service import get_rag_service

        rag_service = await get_rag_service(project_id)
        result = await rag_service.list_milvus_collections()

        if result.get("success"):
            return {
                "code": 200,
                "msg": "获取Milvus Collection列表成功",
                "data": result,
            }
        else:
            return {
                "code": 500,
                "msg": result.get("message", "获取失败"),
                "data": result,
            }

    except Exception as e:
        logger.error(f"❌ 获取Milvus Collection列表失败: {e}")
        raise HTTPException(
            status_code=500, detail=f"获取Milvus Collection列表失败: {str(e)}"
        )


@rag_collections_router.post("/sync-from-milvus", summary="从Milvus同步Collections")
async def sync_collections_from_milvus(
    project_id: Optional[str] = Query(None, description="项目ID")
):
    """从Milvus向量数据库同步Collections到SQLite数据库"""
    try:
        project_id = project_id or "default"
        logger.info(f"🔄 从Milvus同步Collections | 项目: {project_id}")

        # 获取服务实例
        from backend.services.rag.collection_service import get_collection_service
        from backend.services.rag.rag_service import get_rag_service

        rag_service = await get_rag_service(project_id)
        collection_service = get_collection_service(project_id)

        # 执行同步
        result = await collection_service.sync_from_milvus(rag_service)

        if result.get("success"):
            return {
                "code": 200,
                "msg": result.get("message", "同步成功"),
                "data": result,
            }
        else:
            return {
                "code": 500,
                "msg": result.get("message", "同步失败"),
                "data": result,
            }

    except Exception as e:
        logger.error(f"❌ 从Milvus同步Collections失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@rag_collections_router.get(
    "/{collection_name}/milvus-info", summary="获取Milvus中Collection详细信息"
)
async def get_milvus_collection_info(
    collection_name: str, project_id: Optional[str] = Query(None, description="项目ID")
):
    """获取Milvus中Collection的详细信息"""
    try:
        project_id = project_id or "default"
        logger.info(
            f"🔍 获取Milvus Collection信息 | Collection: {collection_name} | 项目: {project_id}"
        )

        # 获取RAG服务
        from backend.services.rag.rag_service import get_rag_service

        rag_service = await get_rag_service(project_id)
        result = await rag_service.get_milvus_collection_info(collection_name)

        if result.get("success"):
            return {
                "code": 200,
                "msg": "获取Collection信息成功",
                "data": result,
            }
        else:
            return {
                "code": 404 if "不存在" in result.get("message", "") else 500,
                "msg": result.get("message", "获取失败"),
                "data": result,
            }

    except Exception as e:
        logger.error(f"❌ 获取Milvus Collection信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取信息失败: {str(e)}")


@rag_collections_router.post("/init-defaults", summary="初始化默认Collections")
async def init_default_collections(
    project_id: Optional[str] = Query(None, description="项目ID")
):
    """初始化默认Collections"""
    try:
        project_id = project_id or "default"
        logger.info(f"🔧 初始化默认Collections | 项目: {project_id}")

        # 获取Collection服务
        from backend.services.rag.collection_service import get_collection_service

        collection_service = get_collection_service(project_id)

        # 初始化默认Collections
        created_count = await collection_service.initialize_default_collections()

        return {
            "code": 200,
            "msg": f"默认Collections初始化成功，创建了 {created_count} 个Collection",
            "data": {
                "project_id": project_id,
                "created_count": created_count,
            },
        }

    except Exception as e:
        logger.error(f"❌ 初始化默认Collections失败: {e}")
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")


@rag_collections_router.post("/", summary="创建Collection")
async def create_collection(request: CollectionCreateRequest):
    """创建新的Collection，包括数据库记录和向量数据库collection"""
    try:
        logger.info(f"📝 创建Collection: {request.name}")

        # 获取默认配置
        from backend.conf.rag_config import get_rag_config

        rag_config = get_rag_config()
        defaults = rag_config.milvus.collections.get("general", None)

        # 如果没有默认配置，使用配置文件中的默认值
        if not defaults:
            config_defaults = {
                "dimension": rag_config.milvus.dimension,
                "top_k": 5,
                "similarity_threshold": 0.7,
                "chunk_size": 1000,
                "chunk_overlap": 200,
            }
        else:
            config_defaults = {
                "dimension": defaults.dimension,
                "top_k": defaults.top_k,
                "similarity_threshold": defaults.similarity_threshold,
                "chunk_size": defaults.chunk_size,
                "chunk_overlap": defaults.chunk_overlap,
            }

        # 准备collection数据，使用默认值填充未指定的参数
        collection_data = {
            "name": request.name,
            "display_name": request.display_name,
            "description": request.description,
            "business_type": request.business_type,
            "chunk_size": (
                request.chunk_size
                if request.chunk_size is not None
                else config_defaults["chunk_size"]
            ),
            "chunk_overlap": (
                request.chunk_overlap
                if request.chunk_overlap is not None
                else config_defaults["chunk_overlap"]
            ),
            "dimension": (
                request.dimension
                if request.dimension is not None
                else config_defaults["dimension"]
            ),
            "top_k": (
                request.top_k if request.top_k is not None else config_defaults["top_k"]
            ),
            "similarity_threshold": (
                request.similarity_threshold
                if request.similarity_threshold is not None
                else config_defaults["similarity_threshold"]
            ),
        }

        logger.info(
            f"📋 使用配置: dimension={collection_data['dimension']}, top_k={collection_data['top_k']}, chunk_size={collection_data['chunk_size']}"
        )

        # 调用服务层创建Collection（包括向量数据库）
        result = await collection_service.create_collection(collection_data)

        if not result["success"]:
            logger.warning(f"⚠️ Collection创建失败: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])

        logger.success(f"✅ Collection创建成功: {request.name}")

        return {
            "code": 200,
            "msg": "Collection创建成功",
            "data": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 创建Collection失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建Collection失败: {str(e)}")


@rag_collections_router.get("/{collection_id}", summary="获取Collection详情")
async def get_collection(collection_id: int):
    """获取指定Collection的详情"""
    try:
        logger.info(f"🔍 获取Collection详情: ID={collection_id}")

        collection = await RAGCollection.filter(id=collection_id).first()
        if not collection:
            logger.warning(f"⚠️ Collection不存在: ID={collection_id}")
            raise HTTPException(status_code=404, detail="Collection不存在")

        # 统计文档数量
        from backend.models.rag_file import RAGFileRecord

        doc_count = await RAGFileRecord.filter(collection_name=collection.name).count()

        collection_data = {
            "id": collection.id,
            "name": collection.name,
            "display_name": collection.display_name,
            "description": collection.description,
            "business_type": collection.business_type,
            "chunk_size": collection.chunk_size,
            "chunk_overlap": collection.chunk_overlap,
            "dimension": collection.dimension,
            "top_k": collection.top_k,
            "similarity_threshold": collection.similarity_threshold,
            "is_active": collection.is_active,
            "document_count": doc_count,
            "created_at": (
                collection.created_at.isoformat() if collection.created_at else None
            ),
            "updated_at": (
                collection.updated_at.isoformat() if collection.updated_at else None
            ),
        }

        logger.success(f"✅ 获取Collection详情成功: {collection.name}")

        return {
            "code": 200,
            "msg": "获取Collection详情成功",
            "data": {"collection": collection_data},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取Collection详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取Collection详情失败: {str(e)}")


@rag_collections_router.put("/{collection_id}", summary="更新Collection")
async def update_collection(collection_id: int, request: CollectionUpdateRequest):
    """更新Collection信息，包括数据库记录和向量数据库配置"""
    try:
        logger.info(f"✏️ 更新Collection: ID={collection_id}")

        collection = await RAGCollection.filter(id=collection_id).first()
        if not collection:
            logger.warning(f"⚠️ Collection不存在: ID={collection_id}")
            raise HTTPException(status_code=404, detail="Collection不存在")

        # 准备更新数据
        update_data = {}
        if request.display_name is not None:
            update_data["display_name"] = request.display_name
        if request.description is not None:
            update_data["description"] = request.description
        if request.business_type is not None:
            update_data["business_type"] = request.business_type
        if request.chunk_size is not None:
            update_data["chunk_size"] = request.chunk_size
        if request.chunk_overlap is not None:
            update_data["chunk_overlap"] = request.chunk_overlap
        if request.dimension is not None:
            update_data["dimension"] = request.dimension
        if request.top_k is not None:
            update_data["top_k"] = request.top_k
        if request.similarity_threshold is not None:
            update_data["similarity_threshold"] = request.similarity_threshold

        if update_data:
            # 调用服务层更新Collection
            result = await collection_service.update_collection(
                collection.name, update_data
            )

            if not result["success"]:
                logger.warning(f"⚠️ Collection更新失败: {result['message']}")
                raise HTTPException(status_code=400, detail=result["message"])

            # 重新获取更新后的数据
            collection = await RAGCollection.filter(id=collection_id).first()

        logger.success(f"✅ Collection更新成功: {collection.name}")

        return {
            "code": 200,
            "msg": "Collection更新成功",
            "data": {
                "collection": {
                    "id": collection.id,
                    "name": collection.name,
                    "display_name": collection.display_name,
                    "description": collection.description,
                    "business_type": collection.business_type,
                    "chunk_size": collection.chunk_size,
                    "chunk_overlap": collection.chunk_overlap,
                    "dimension": collection.dimension,
                    "top_k": collection.top_k,
                    "similarity_threshold": collection.similarity_threshold,
                    "updated_at": (
                        collection.updated_at.isoformat()
                        if collection.updated_at
                        else None
                    ),
                }
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 更新Collection失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新Collection失败: {str(e)}")


@rag_collections_router.delete("/{collection_id}", summary="删除Collection")
async def delete_collection(collection_id: int):
    """删除Collection，包括数据库记录和向量数据库collection"""
    try:
        logger.info(f"🗑️ 删除Collection: ID={collection_id}")

        collection = await RAGCollection.filter(id=collection_id).first()
        if not collection:
            logger.warning(f"⚠️ Collection不存在: ID={collection_id}")
            raise HTTPException(status_code=404, detail="Collection不存在")

        # 检查是否有关联文档
        from backend.models.rag_file import RAGFileRecord

        doc_count = await RAGFileRecord.filter(collection_name=collection.name).count()

        if doc_count > 0:
            logger.warning(
                f"⚠️ Collection包含文档，无法删除: {collection.name} ({doc_count} 个文档)"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Collection '{collection.name}' 包含 {doc_count} 个文档，请先删除所有文档后再删除Collection",
            )

        # 调用服务层删除Collection（包括向量数据库）
        collection_name = collection.name
        result = await collection_service.delete_collection(collection_name)

        if not result["success"]:
            logger.warning(f"⚠️ Collection删除失败: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])

        logger.success(f"✅ Collection删除成功: {collection_name}")

        return {
            "code": 200,
            "msg": "Collection删除成功",
            "data": {"deleted_collection": collection_name},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除Collection失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除Collection失败: {str(e)}")


@rag_collections_router.get("/{collection_id}/stats", summary="获取Collection统计信息")
async def get_collection_stats(collection_id: int):
    """获取Collection的统计信息"""
    try:
        logger.info(f"📊 获取Collection统计: ID={collection_id}")

        collection = await RAGCollection.filter(id=collection_id).first()
        if not collection:
            logger.warning(f"⚠️ Collection不存在: ID={collection_id}")
            raise HTTPException(status_code=404, detail="Collection不存在")

        # 统计信息
        from backend.models.rag_file import RAGFileRecord

        total_docs = await RAGFileRecord.filter(collection_name=collection.name).count()
        completed_docs = await RAGFileRecord.filter(
            collection_name=collection.name, status="completed"
        ).count()

        # 计算总文件大小
        records = await RAGFileRecord.filter(collection_name=collection.name).all()
        total_size = sum(record.file_size for record in records)

        stats = {
            "collection_name": collection.name,
            "display_name": collection.display_name,
            "total_documents": total_docs,
            "completed_documents": completed_docs,
            "processing_documents": total_docs - completed_docs,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "success_rate": (
                round(completed_docs / total_docs * 100, 2) if total_docs > 0 else 0
            ),
            "business_type": collection.business_type,
            "chunk_size": collection.chunk_size,
            "chunk_overlap": collection.chunk_overlap,
            "dimension": collection.dimension,
            "top_k": collection.top_k,
            "similarity_threshold": collection.similarity_threshold,
        }

        logger.success(f"✅ Collection统计获取成功: {collection.name}")

        return {"code": 200, "msg": "获取Collection统计成功", "data": {"stats": stats}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取Collection统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取Collection统计失败: {str(e)}")


@rag_collections_router.post("/{name}/sync", summary="同步Collection信息")
async def sync_collection(name: str):
    """
    从向量数据库同步Collection信息到数据库
    读取向量数据库中的collection详细信息，与数据库记录进行校对和更新
    """
    try:
        logger.info(f"🔄 同步Collection信息: {name}")

        result = await collection_service.sync_collection_from_vector_db(name)

        if result["success"]:
            return {
                "code": 200,
                "msg": result["message"],
                "data": {
                    "collection_name": name,
                    "differences": result.get("differences", []),
                    "updates_applied": result.get("updates_applied", 0),
                    "updated_fields": result.get("updated_fields", []),
                },
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"同步Collection信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@rag_collections_router.post("/sync-all", summary="同步所有Collection信息")
async def sync_all_collections():
    """
    同步所有Collections的信息
    批量从向量数据库读取信息并更新数据库记录
    """
    try:
        logger.info("🔄 批量同步所有Collections信息")

        result = await collection_service.sync_all_collections()

        if result["success"]:
            return {
                "code": 200,
                "msg": result["message"],
                "data": {
                    "total_collections": result["total_collections"],
                    "total_updates": result["total_updates"],
                    "details": result["details"],
                },
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量同步Collections失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量同步失败: {str(e)}")
