"""
UI测试Collection管理API接口
提供UI测试相关的Collection管理功能
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel

from backend.models.rag import RAGCollection
from backend.models.rag_file import RAGFileRecord

ui_collections_router = APIRouter()


class CollectionInfo(BaseModel):
    """Collection信息"""

    id: int
    name: str
    display_name: str
    description: str
    business_type: str
    document_count: int
    created_at: str


class CollectionStatsInfo(BaseModel):
    """Collection统计信息"""

    name: str
    display_name: str
    document_count: int
    total_size: int
    last_updated: Optional[str] = None


@ui_collections_router.get("/", summary="获取UI测试相关的Collection列表")
async def get_ui_testing_collections():
    """获取UI测试相关的Collection列表"""
    try:
        logger.info("📋 [UI测试Collection] 获取Collection列表")

        # 获取UI测试相关的collections
        collections = await RAGCollection.filter(
            business_type__in=["ui_testing", "general"]
        ).all()

        collection_list = []
        for collection in collections:
            # 统计文档数量
            doc_count = await RAGFileRecord.filter(
                collection_name=collection.name
            ).count()

            collection_list.append(
                {
                    "id": collection.id,
                    "name": collection.name,
                    "display_name": collection.display_name,
                    "description": collection.description,
                    "business_type": collection.business_type,
                    "document_count": doc_count,
                    "created_at": collection.created_at.isoformat(),
                }
            )

        logger.success(
            f"✅ [UI测试Collection] 获取成功，共{len(collection_list)}个Collection"
        )

        return {
            "code": 200,
            "msg": "获取Collection列表成功",
            "data": {"collections": collection_list},
        }

    except Exception as e:
        logger.error(f"❌ [UI测试Collection] 获取列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")


@ui_collections_router.get("/{collection_name}", summary="获取指定Collection的详细信息")
async def get_collection_detail(collection_name: str):
    """获取指定Collection的详细信息"""
    try:
        logger.info(
            f"📋 [UI测试Collection] 获取Collection详情 | 名称: {collection_name}"
        )

        # 获取Collection信息
        collection = await RAGCollection.get_or_none(name=collection_name)
        if not collection:
            raise HTTPException(
                status_code=404, detail=f"Collection '{collection_name}' 不存在"
            )

        # 统计文档信息
        documents = await RAGFileRecord.filter(collection_name=collection_name).all()
        doc_count = len(documents)
        total_size = sum(doc.file_size for doc in documents)

        # 获取最后更新时间
        last_updated = None
        if documents:
            latest_doc = max(documents, key=lambda x: x.created_at)
            last_updated = latest_doc.created_at.isoformat()

        collection_detail = {
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
            "document_count": doc_count,
            "total_size": total_size,
            "last_updated": last_updated,
            "created_at": collection.created_at.isoformat(),
        }

        logger.success(
            f"✅ [UI测试Collection] 获取详情成功 | Collection: {collection_name}"
        )

        return {"code": 200, "msg": "获取Collection详情成功", "data": collection_detail}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [UI测试Collection] 获取详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取详情失败: {str(e)}")


@ui_collections_router.get(
    "/{collection_name}/documents", summary="获取Collection中的文档列表"
)
async def get_collection_documents(
    collection_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取指定Collection中的文档列表"""
    try:
        logger.info(
            f"📄 [UI测试Collection] 获取文档列表 | Collection: {collection_name} | 页码: {page}"
        )

        # 检查Collection是否存在
        collection = await RAGCollection.get_or_none(name=collection_name)
        if not collection:
            raise HTTPException(
                status_code=404, detail=f"Collection '{collection_name}' 不存在"
            )

        # 分页查询文档
        offset = (page - 1) * page_size
        documents = (
            await RAGFileRecord.filter(collection_name=collection_name)
            .offset(offset)
            .limit(page_size)
            .order_by("-created_at")
            .all()
        )

        # 统计总数
        total = await RAGFileRecord.filter(collection_name=collection_name).count()

        document_list = []
        for doc in documents:
            document_list.append(
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_md5": doc.file_md5,
                    "file_size": doc.file_size,
                    "collection_name": doc.collection_name,
                    "user_id": doc.user_id,
                    "created_at": doc.created_at.isoformat(),
                }
            )

        logger.success(
            f"✅ [UI测试Collection] 获取文档列表成功 | Collection: {collection_name} | 文档数: {len(document_list)}"
        )

        return {
            "code": 200,
            "msg": "获取文档列表成功",
            "data": {
                "documents": document_list,
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size,
                },
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [UI测试Collection] 获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@ui_collections_router.get("/stats/summary", summary="获取UI测试Collection统计摘要")
async def get_collections_stats_summary():
    """获取UI测试相关Collection的统计摘要"""
    try:
        logger.info("📊 [UI测试Collection] 获取统计摘要")

        # 获取UI测试相关的collections
        collections = await RAGCollection.filter(
            business_type__in=["ui_testing", "general"]
        ).all()

        stats_list = []
        total_documents = 0
        total_size = 0

        for collection in collections:
            # 统计每个Collection的文档信息
            documents = await RAGFileRecord.filter(
                collection_name=collection.name
            ).all()
            doc_count = len(documents)
            collection_size = sum(doc.file_size for doc in documents)

            # 获取最后更新时间
            last_updated = None
            if documents:
                latest_doc = max(documents, key=lambda x: x.created_at)
                last_updated = latest_doc.created_at.isoformat()

            stats_list.append(
                {
                    "name": collection.name,
                    "display_name": collection.display_name,
                    "document_count": doc_count,
                    "total_size": collection_size,
                    "last_updated": last_updated,
                }
            )

            total_documents += doc_count
            total_size += collection_size

        summary = {
            "total_collections": len(collections),
            "total_documents": total_documents,
            "total_size": total_size,
            "collections": stats_list,
            "generated_at": logger.info.__globals__.get(
                "datetime", __import__("datetime")
            )
            .datetime.now()
            .isoformat(),
        }

        logger.success(
            f"✅ [UI测试Collection] 统计摘要获取成功 | Collection数: {len(collections)} | 总文档数: {total_documents}"
        )

        return {"code": 200, "msg": "获取统计摘要成功", "data": summary}

    except Exception as e:
        logger.error(f"❌ [UI测试Collection] 获取统计摘要失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计摘要失败: {str(e)}")


@ui_collections_router.get(
    "/{collection_name}/stats", summary="获取指定Collection的详细统计"
)
async def get_collection_detailed_stats(collection_name: str):
    """获取指定Collection的详细统计信息"""
    try:
        logger.info(
            f"📊 [UI测试Collection] 获取详细统计 | Collection: {collection_name}"
        )

        # 检查Collection是否存在
        collection = await RAGCollection.get_or_none(name=collection_name)
        if not collection:
            raise HTTPException(
                status_code=404, detail=f"Collection '{collection_name}' 不存在"
            )

        # 获取所有文档
        documents = await RAGFileRecord.filter(collection_name=collection_name).all()

        # 统计信息
        doc_count = len(documents)
        total_size = sum(doc.file_size for doc in documents)

        # 按用户统计
        user_stats = {}
        for doc in documents:
            user_id = doc.user_id or "anonymous"
            if user_id not in user_stats:
                user_stats[user_id] = {"count": 0, "size": 0}
            user_stats[user_id]["count"] += 1
            user_stats[user_id]["size"] += doc.file_size

        # 按时间统计（最近7天）
        from datetime import datetime, timedelta

        now = datetime.now()
        time_stats = {}
        for i in range(7):
            date = (now - timedelta(days=i)).date()
            time_stats[date.isoformat()] = 0

        for doc in documents:
            doc_date = doc.created_at.date()
            if doc_date.isoformat() in time_stats:
                time_stats[doc_date.isoformat()] += 1

        detailed_stats = {
            "collection_info": {
                "name": collection.name,
                "display_name": collection.display_name,
                "business_type": collection.business_type,
            },
            "document_stats": {
                "total_count": doc_count,
                "total_size": total_size,
                "average_size": total_size / doc_count if doc_count > 0 else 0,
            },
            "user_stats": user_stats,
            "time_stats": time_stats,
            "generated_at": datetime.now().isoformat(),
        }

        logger.success(
            f"✅ [UI测试Collection] 详细统计获取成功 | Collection: {collection_name}"
        )

        return {"code": 200, "msg": "获取详细统计成功", "data": detailed_stats}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [UI测试Collection] 获取详细统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取详细统计失败: {str(e)}")
