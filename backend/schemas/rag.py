"""
RAG知识库相关的Schema
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ==================== Collection管理 ====================


class CollectionBase(BaseModel):
    """Collection基础Schema"""

    name: str = Field(..., description="Collection名称")
    display_name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    business_type: str = Field("general", description="业务类型")


class CollectionCreate(CollectionBase):
    """创建Collection Schema"""

    dimension: int = Field(768, description="向量维度")
    chunk_size: int = Field(1000, description="分块大小")
    chunk_overlap: int = Field(200, description="分块重叠")
    top_k: int = Field(5, description="检索数量")
    similarity_threshold: float = Field(0.7, description="相似度阈值")


class CollectionUpdate(BaseModel):
    """更新Collection Schema"""

    display_name: Optional[str] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    business_type: Optional[str] = Field(None, description="业务类型")
    chunk_size: Optional[int] = Field(None, description="分块大小")
    chunk_overlap: Optional[int] = Field(None, description="分块重叠")
    top_k: Optional[int] = Field(None, description="检索数量")
    similarity_threshold: Optional[float] = Field(None, description="相似度阈值")
    is_active: Optional[bool] = Field(None, description="是否激活")


class CollectionResponse(CollectionBase):
    """Collection响应Schema"""

    id: int
    dimension: int
    chunk_size: int
    chunk_overlap: int
    top_k: int
    similarity_threshold: float
    is_active: bool
    document_count: int
    last_updated: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any] = {}

    class Config:
        from_attributes = True


# ==================== 文档管理 ====================


class DocumentBase(BaseModel):
    """文档基础Schema"""

    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容")


class DocumentCreate(DocumentBase):
    """创建文档Schema"""

    collection_name: str = Field(..., description="Collection名称")
    file_type: str = Field("text/plain", description="文件类型")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class DocumentUpdate(BaseModel):
    """更新文档Schema"""

    title: Optional[str] = Field(None, description="文档标题")
    content: Optional[str] = Field(None, description="文档内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class DocumentResponse(DocumentBase):
    """文档响应Schema"""

    id: int
    collection_name: str
    file_path: Optional[str]
    file_type: str
    file_size: int
    node_count: int
    embedding_status: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any] = {}

    class Config:
        from_attributes = True


# ==================== 查询相关 ====================


class QueryRequest(BaseModel):
    """查询请求Schema"""

    question: str = Field(..., description="查询问题")
    collection_name: str = Field("general", description="Collection名称")
    top_k: Optional[int] = Field(None, description="检索数量")
    similarity_threshold: Optional[float] = Field(None, description="相似度阈值")


class MultiQueryRequest(BaseModel):
    """多Collection查询请求Schema"""

    question: str = Field(..., description="查询问题")
    collection_names: List[str] = Field(..., description="Collection名称列表")
    top_k: Optional[int] = Field(None, description="检索数量")


class BusinessQueryRequest(BaseModel):
    """业务类型查询请求Schema"""

    question: str = Field(..., description="查询问题")
    business_type: str = Field(..., description="业务类型")
    top_k: Optional[int] = Field(None, description="检索数量")


class QueryResponse(BaseModel):
    """查询响应Schema"""

    success: bool
    answer: str
    sources: List[Dict[str, Any]] = []
    collection_name: str
    query_time: float
    retrieved_count: int
    metadata: Dict[str, Any] = {}


# ==================== 文件上传 ====================


class FileUploadResponse(BaseModel):
    """文件上传响应Schema"""

    success: bool
    message: str
    filename: str
    document_id: Optional[int] = None
    file_size: int
    status: str


class BatchUploadResponse(BaseModel):
    """批量上传响应Schema"""

    success: bool
    message: str
    total_files: int
    successful_uploads: int
    failed_uploads: int
    results: List[FileUploadResponse]


# ==================== 系统统计 ====================


class SystemStats(BaseModel):
    """系统统计Schema"""

    total_collections: int
    total_documents: int
    total_vectors: int
    storage_used: str
    query_count_today: int
    avg_response_time: float
    system_health: str


class CollectionStats(BaseModel):
    """Collection统计Schema"""

    name: str
    display_name: str
    document_count: int
    vector_count: int
    storage_size: str
    last_query_time: Optional[str]
    avg_response_time: float


# ==================== 配置管理 ====================


class EmbeddingModelConfig(BaseModel):
    """嵌入模型配置Schema"""

    name: str = Field(..., description="模型名称")
    provider: str = Field(..., description="提供商")
    dimension: int = Field(..., description="向量维度")
    max_tokens: int = Field(..., description="最大Token数")
    api_key: Optional[str] = Field(None, description="API密钥")


class VectorDBConfig(BaseModel):
    """向量数据库配置Schema"""

    host: str = Field(..., description="主机地址")
    port: int = Field(..., description="端口号")
    timeout: int = Field(30, description="连接超时时间")
    max_connections: int = Field(100, description="最大连接数")


class SearchConfig(BaseModel):
    """搜索配置Schema"""

    default_top_k: int = Field(5, description="默认Top-K")
    similarity_threshold: float = Field(0.7, description="相似度阈值")
    enable_rerank: bool = Field(False, description="启用重排序")
    rerank_top_k: int = Field(10, description="重排序Top-K")


class SystemConfig(BaseModel):
    """系统配置Schema"""

    embedding: EmbeddingModelConfig
    vector_db: VectorDBConfig
    search: SearchConfig
    chunking: Dict[str, Any] = {}
    performance: Dict[str, Any] = {}


# ==================== API密钥管理 ====================


class APIKeyCreate(BaseModel):
    """创建API密钥Schema"""

    name: str = Field(..., description="密钥名称")
    provider: str = Field(..., description="服务提供商")
    key: str = Field(..., description="API密钥")


class APIKeyResponse(BaseModel):
    """API密钥响应Schema"""

    id: int
    name: str
    provider: str
    key: str  # 在实际返回时会被掩码处理
    status: str
    created_at: str
    last_used: Optional[str]

    class Config:
        from_attributes = True


# ==================== 监控相关 ====================


class QueryLogResponse(BaseModel):
    """查询日志响应Schema"""

    id: int
    query_text: str
    collection_name: str
    response_time: float
    retrieved_count: int
    status: str
    timestamp: str
    user_id: Optional[int]


class PerformanceMetrics(BaseModel):
    """性能指标Schema"""

    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: float
    query_rate: float
    avg_response_time: float
    error_rate: float
    uptime: str


class AlertResponse(BaseModel):
    """告警响应Schema"""

    id: int
    type: str
    title: str
    description: str
    timestamp: str
    resolved: bool


# ==================== 仪表板相关 ====================


class DashboardStats(BaseModel):
    """仪表板统计Schema"""

    total_collections: int
    total_documents: int
    total_vectors: int
    storage_used: str
    query_count_today: int
    avg_response_time: float
    system_health: str


class RecentActivity(BaseModel):
    """最近活动Schema"""

    id: str
    type: str
    description: str
    timestamp: str
    status: str
