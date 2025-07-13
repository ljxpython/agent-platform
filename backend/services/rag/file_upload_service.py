"""
RAG文件上传服务 - 重写版本
核心功能：MD5重复检测，避免重复上传到同一个collection
支持项目隔离的文件管理
"""

import hashlib
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from backend.models.rag_file import RAGFileRecord


class RAGFileUploadService:
    """
    RAG文件上传服务 - 重写版本

    设计原则：
    1. 专注于文件MD5重复检测
    2. 支持项目隔离
    3. 与RAGService配合使用
    4. 简化文件管理流程
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        初始化文件上传服务

        Args:
            project_id: 项目ID，用于文件隔离
        """
        self.project_id = project_id or "default"
        self.logger = logger.bind(
            service="RAGFileUploadService", project=self.project_id
        )

        self.logger.info(f"🔧 文件上传服务初始化 | 项目: {self.project_id}")

    def _get_project_collection_name(self, collection_name: str) -> str:
        """
        获取项目级别的 collection 名称
        格式: {project_id}_{collection_name}
        """
        if self.project_id == "default":
            return collection_name
        return f"{self.project_id}_{collection_name}"

    def calculate_file_md5(self, content: bytes) -> str:
        """计算文件内容的MD5哈希值"""
        try:
            return hashlib.md5(content).hexdigest()
        except Exception as e:
            self.logger.error(f"计算文件MD5失败: {e}")
            raise

    async def check_file_exists(
        self, file_md5: str, collection_name: str
    ) -> Optional[RAGFileRecord]:
        """
        检查文件是否已经在指定collection中存在（支持项目隔离）

        Args:
            file_md5: 文件MD5哈希值
            collection_name: 集合名称（原始名称）

        Returns:
            RAGFileRecord: 如果文件已存在，返回记录；否则返回None
        """
        try:
            project_collection_name = self._get_project_collection_name(collection_name)

            existing_record = await RAGFileRecord.get_existing_record(
                file_md5, project_collection_name
            )
            if existing_record:
                self.logger.info(
                    f"文件已存在 | MD5: {file_md5[:8]}... | Collection: {collection_name} -> {project_collection_name} | 原文件: {existing_record.filename}"
                )
            return existing_record
        except Exception as e:
            self.logger.error(
                f"检查文件是否存在失败 | Collection: {collection_name} | 项目: {self.project_id} | 错误: {e}"
            )
            return None

    async def record_uploaded_file(
        self,
        filename: str,
        file_md5: str,
        file_size: int,
        collection_name: str,
        user_id: Optional[str] = None,
    ) -> RAGFileRecord:
        """
        记录已上传的文件信息（支持项目隔离）

        Args:
            filename: 文件名
            file_md5: 文件MD5哈希值
            file_size: 文件大小
            collection_name: 集合名称（原始名称）
            user_id: 用户ID（可选）

        Returns:
            RAGFileRecord: 创建的文件记录
        """
        try:
            project_collection_name = self._get_project_collection_name(collection_name)

            record = await RAGFileRecord.create_record(
                filename=filename,
                file_md5=file_md5,
                file_size=file_size,
                collection_name=project_collection_name,
                user_id=user_id,
            )

            self.logger.success(
                f"记录文件上传 | 文件: {filename} | MD5: {file_md5[:8]}... | Collection: {collection_name} -> {project_collection_name}"
            )
            return record

        except Exception as e:
            self.logger.error(
                f"记录文件上传失败 | 文件: {filename} | 项目: {self.project_id} | 错误: {e}"
            )
            raise

    async def process_file_upload(
        self,
        filename: str,
        content: bytes,
        collection_name: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        处理文件上传的完整流程

        Args:
            filename: 文件名
            content: 文件内容
            collection_name: 集合名称
            user_id: 用户ID（可选）

        Returns:
            Dict: 处理结果
        """
        try:
            # 1. 计算文件MD5
            file_md5 = self.calculate_file_md5(content)
            file_size = len(content)

            self.logger.info(
                f"处理文件上传 | 文件: {filename} | 大小: {file_size} bytes | MD5: {file_md5[:8]}... | Collection: {collection_name}"
            )

            # 2. 检查文件是否已存在
            existing_record = await self.check_file_exists(file_md5, collection_name)

            if existing_record:
                # 文件已存在，返回重复信息
                return {
                    "success": False,
                    "status": "duplicate",
                    "message": f"文件已存在于 {collection_name} 知识库中",
                    "existing_file": existing_record.filename,
                    "existing_record": existing_record.to_dict(),
                    "skip_upload": True,
                }

            # 3. 文件不存在，可以上传
            return {
                "success": True,
                "status": "new_file",
                "message": "文件可以上传",
                "file_md5": file_md5,
                "file_size": file_size,
                "skip_upload": False,
            }

        except Exception as e:
            self.logger.error(f"处理文件上传失败: {filename} | 错误: {e}")
            return {
                "success": False,
                "status": "error",
                "message": f"处理失败: {str(e)}",
                "skip_upload": True,
            }

    async def complete_file_upload(
        self,
        filename: str,
        file_md5: str,
        file_size: int,
        collection_name: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        完成文件上传，记录到数据库

        Args:
            filename: 文件名
            file_md5: 文件MD5哈希值
            file_size: 文件大小
            collection_name: 集合名称
            user_id: 用户ID（可选）

        Returns:
            Dict: 完成结果
        """
        try:
            # 记录文件上传信息
            record = await self.record_uploaded_file(
                filename=filename,
                file_md5=file_md5,
                file_size=file_size,
                collection_name=collection_name,
                user_id=user_id,
            )

            return {
                "success": True,
                "message": "文件上传记录已保存",
                "record": record.to_dict(),
            }

        except Exception as e:
            self.logger.error(f"完成文件上传失败: {filename} | 错误: {e}")
            return {"success": False, "message": f"保存上传记录失败: {str(e)}"}

    async def get_collection_files(self, collection_name: str) -> Dict[str, Any]:
        """
        获取指定collection中的所有文件（支持项目隔离）

        Args:
            collection_name: 集合名称（原始名称）

        Returns:
            Dict: 文件列表和统计信息
        """
        try:
            project_collection_name = self._get_project_collection_name(collection_name)

            records = await RAGFileRecord.filter(
                collection_name=project_collection_name
            ).order_by("-created_at")

            files = [record.to_dict() for record in records]
            total_size = sum(record.file_size for record in records)

            self.logger.info(
                f"📋 获取Collection文件列表 | Collection: {collection_name} -> {project_collection_name} | 文件数: {len(files)}"
            )

            return {
                "success": True,
                "collection_name": collection_name,
                "project_collection_name": project_collection_name,
                "project_id": self.project_id,
                "file_count": len(files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "files": files,
            }

        except Exception as e:
            self.logger.error(
                f"获取collection文件列表失败 | Collection: {collection_name} | 项目: {self.project_id} | 错误: {e}"
            )
            return {"success": False, "message": f"获取文件列表失败: {str(e)}"}

    async def delete_document_record(
        self, record_id: int, user_id: str
    ) -> Dict[str, Any]:
        """
        删除文档记录（仅允许用户删除自己的文档或管理员删除）
        同时从向量数据库中删除相关向量数据

        Args:
            record_id: 记录ID
            user_id: 用户ID

        Returns:
            Dict: 删除结果详情
        """
        try:
            # 查找记录
            record = await RAGFileRecord.filter(id=record_id).first()
            if not record:
                self.logger.warning(f"文档记录不存在: ID={record_id}")
                return {
                    "success": False,
                    "message": "文档记录不存在",
                    "error_code": "RECORD_NOT_FOUND",
                }

            # 检查权限（用户只能删除自己的文档，或者是管理员）
            if record.user_id != user_id and user_id != "admin":
                self.logger.warning(
                    f"无权限删除文档: ID={record_id}, user_id={user_id}, owner={record.user_id}"
                )
                return {
                    "success": False,
                    "message": "无权限删除此文档",
                    "error_code": "PERMISSION_DENIED",
                }

            # 记录删除前的信息
            deleted_info = {
                "id": record.id,
                "filename": record.filename,
                "file_md5": record.file_md5,
                "collection_name": record.collection_name,
                "file_size": record.file_size,
                "user_id": record.user_id,
            }

            # 删除数据库记录
            await record.delete()
            self.logger.info(
                f"✅ 数据库记录删除成功: ID={record_id}, filename={record.filename}"
            )

            # TODO: 从向量数据库中删除相关向量数据
            # 注意：当前Milvus实现中，我们无法直接通过文件MD5删除特定文档的向量
            # 这是因为向量数据库中的节点ID与文件MD5没有直接关联
            # 未来可以考虑在向量数据库中添加metadata来支持按文件删除

            self.logger.success(f"✅ 文档删除完成: {deleted_info['filename']}")

            return {
                "success": True,
                "message": "文档删除成功",
                "deleted_document": deleted_info,
                "note": "向量数据库中的相关向量数据需要手动清理或重建collection",
            }

        except Exception as e:
            self.logger.error(f"❌ 删除文档记录失败: ID={record_id} | 错误: {e}")
            return {
                "success": False,
                "message": f"删除失败: {str(e)}",
                "error_code": "DELETE_ERROR",
            }

    async def get_document_statistics(
        self, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取文档统计信息（项目级别）

        Args:
            user_id: 用户ID（可选，如果提供则只统计该用户的文档）

        Returns:
            Dict: 统计信息
        """
        try:
            # 获取所有记录，然后在Python中过滤
            all_records_query = RAGFileRecord.all()
            if user_id:
                all_records_query = all_records_query.filter(user_id=user_id)

            all_records = await all_records_query.all()

            # 根据项目ID过滤records
            if self.project_id == "default":
                # 默认项目：查询不带项目前缀的collections
                records = [
                    record
                    for record in all_records
                    if "_" not in record.collection_name
                ]
            else:
                # 其他项目：查询带有项目前缀的collections
                project_prefix = f"{self.project_id}_"
                records = [
                    record
                    for record in all_records
                    if record.collection_name.startswith(project_prefix)
                ]

            # 计算统计信息
            total_count = len(records)
            completed_count = len([r for r in records if r.status == "completed"])

            # 按集合统计（项目级别）
            collection_stats = {}
            for record in records:
                # 提取原始collection名称
                original_name = record.collection_name
                if self.project_id != "default" and "_" in record.collection_name:
                    original_name = record.collection_name.split("_", 1)[1]

                collection_stats[original_name] = (
                    collection_stats.get(original_name, 0) + 1
                )

            # 计算总文件大小
            total_size = sum(record.file_size for record in records)

            stats = {
                "project_id": self.project_id,
                "total_documents": total_count,
                "completed_documents": completed_count,
                "collection_stats": collection_stats,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "success_rate": (
                    round(completed_count / total_count * 100, 2)
                    if total_count > 0
                    else 0
                ),
            }

            self.logger.info(
                f"文档统计 | 项目: {self.project_id} | 总数: {total_count}"
            )
            return stats

        except Exception as e:
            self.logger.error(f"获取文档统计失败 | 项目: {self.project_id} | 错误: {e}")
            return {"project_id": self.project_id, "error": str(e)}


# ==================== 服务实例管理 ====================

# 项目级别的文件上传服务实例缓存
_file_upload_services: Dict[str, RAGFileUploadService] = {}


def get_file_upload_service(project_id: Optional[str] = None) -> RAGFileUploadService:
    """
    获取文件上传服务实例（支持项目隔离）

    Args:
        project_id: 项目ID，如果不提供则使用默认项目

    Returns:
        RAGFileUploadService: 文件上传服务实例
    """
    global _file_upload_services

    project_id = project_id or "default"

    if project_id not in _file_upload_services:
        logger.info(f"🔧 创建新的文件上传服务实例 | 项目: {project_id}")
        _file_upload_services[project_id] = RAGFileUploadService(project_id=project_id)

    return _file_upload_services[project_id]


# 保持向后兼容性的全局实例
rag_file_upload_service = get_file_upload_service("default")
