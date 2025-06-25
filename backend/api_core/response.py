"""
统一响应处理工具
"""

from typing import Any, Dict, List, Optional

from fastapi.responses import JSONResponse

from backend.schemas.base import Fail, Success, SuccessExtra


class ResponseUtil:
    """统一响应工具类"""

    @staticmethod
    def success(
        data: Optional[Any] = None, msg: str = "操作成功", code: int = 200, **kwargs
    ) -> Success:
        """成功响应"""
        return Success(code=code, msg=msg, data=data, **kwargs)

    @staticmethod
    def fail(
        msg: str = "操作失败", code: int = 400, data: Optional[Any] = None, **kwargs
    ) -> Fail:
        """失败响应"""
        return Fail(code=code, msg=msg, data=data, **kwargs)

    @staticmethod
    def success_with_pagination(
        data: Optional[Any] = None,
        total: int = 0,
        page: int = 1,
        page_size: int = 20,
        msg: str = "操作成功",
        code: int = 200,
        **kwargs,
    ) -> SuccessExtra:
        """带分页的成功响应"""
        return SuccessExtra(
            code=code,
            msg=msg,
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            **kwargs,
        )

    @staticmethod
    def not_found(msg: str = "资源不存在") -> Fail:
        """404响应"""
        return ResponseUtil.fail(msg=msg, code=404)

    @staticmethod
    def unauthorized(msg: str = "未授权访问") -> Fail:
        """401响应"""
        return ResponseUtil.fail(msg=msg, code=401)

    @staticmethod
    def forbidden(msg: str = "禁止访问") -> Fail:
        """403响应"""
        return ResponseUtil.fail(msg=msg, code=403)

    @staticmethod
    def validation_error(
        msg: str = "参数验证失败", errors: Optional[List] = None
    ) -> Fail:
        """422响应"""
        data = {"errors": errors} if errors else None
        return ResponseUtil.fail(msg=msg, code=422, data=data)

    @staticmethod
    def server_error(msg: str = "服务器内部错误") -> Fail:
        """500响应"""
        return ResponseUtil.fail(msg=msg, code=500)


class RAGResponseUtil:
    """RAG专用响应工具类"""

    @staticmethod
    def collection_success(collections: List[Dict], total: int = None) -> Success:
        """Collection列表成功响应"""
        if total is None:
            total = len(collections)
        return ResponseUtil.success(
            data={"collections": collections, "total": total}, msg="获取Collections成功"
        )

    @staticmethod
    def collection_created(collection_data: Dict) -> Success:
        """Collection创建成功响应"""
        return ResponseUtil.success(
            data=collection_data, msg="Collection创建成功", code=201
        )

    @staticmethod
    def collection_updated() -> Success:
        """Collection更新成功响应"""
        return ResponseUtil.success(msg="Collection更新成功")

    @staticmethod
    def collection_deleted(count: int = 0) -> Success:
        """Collection删除成功响应"""
        msg = f"Collection删除成功"
        if count > 0:
            msg += f"，同时删除了 {count} 个相关文档"
        return ResponseUtil.success(msg=msg)

    @staticmethod
    def collection_not_found(name: str) -> Fail:
        """Collection不存在响应"""
        return ResponseUtil.not_found(f"Collection '{name}' 不存在")

    @staticmethod
    def collection_exists(name: str) -> Fail:
        """Collection已存在响应"""
        return ResponseUtil.fail(f"Collection名称 '{name}' 已存在", code=409)

    @staticmethod
    def documents_success(
        documents: List[Dict], total: int, page: int = 1, page_size: int = 20
    ) -> SuccessExtra:
        """文档列表成功响应"""
        return ResponseUtil.success_with_pagination(
            data={"documents": documents},
            total=total,
            page=page,
            page_size=page_size,
            msg="获取文档列表成功",
        )

    @staticmethod
    def document_created(document_id: int) -> Success:
        """文档创建成功响应"""
        return ResponseUtil.success(
            data={"document_id": document_id}, msg="文档创建成功", code=201
        )

    @staticmethod
    def document_deleted() -> Success:
        """文档删除成功响应"""
        return ResponseUtil.success(msg="文档删除成功")

    @staticmethod
    def document_not_found() -> Fail:
        """文档不存在响应"""
        return ResponseUtil.not_found("文档不存在")

    @staticmethod
    def query_success(result: Dict) -> Success:
        """查询成功响应"""
        return ResponseUtil.success(data=result, msg="查询执行成功")

    @staticmethod
    def stats_success(stats: Dict) -> Success:
        """统计信息成功响应"""
        return ResponseUtil.success(data=stats, msg="获取统计信息成功")

    @staticmethod
    def upload_success(results: List[Dict], total: int) -> Success:
        """文件上传成功响应"""
        successful = len([r for r in results if r.get("status") == "uploaded"])
        failed = total - successful

        msg = f"处理了 {total} 个文件"
        if failed > 0:
            msg += f"，成功 {successful} 个，失败 {failed} 个"

        return ResponseUtil.success(
            data={
                "results": results,
                "total": total,
                "successful": successful,
                "failed": failed,
            },
            msg=msg,
        )


# 创建全局实例
response = ResponseUtil()
rag_response = RAGResponseUtil()
