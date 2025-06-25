# RAG知识库系统API参考

## 🎯 核心API概览

RAG知识库系统提供了完整的API接口，支持文档管理、知识检索和系统配置等功能。

## 📚 主要类和接口

### 1. RAGSystem - 系统主入口

RAG系统的主要接口，提供高级API用于管理多个知识库Collection。

#### 初始化

```python
class RAGSystem:
    def __init__(self, config: Optional[RAGConfig] = None):
        """
        初始化RAG系统

        Args:
            config: RAG系统配置，如果为None则使用默认配置
        """
```

#### 上下文管理器

```python
async def __aenter__(self) -> 'RAGSystem':
    """异步上下文管理器入口"""
    await self.initialize()
    return self

async def __aexit__(self, exc_type, exc_val, exc_tb):
    """异步上下文管理器出口"""
    await self.cleanup()
```

#### 系统管理

```python
async def initialize(self) -> None:
    """
    初始化RAG系统

    初始化所有组件，建立数据库连接，加载配置等。

    Raises:
        RAGError: 初始化失败时抛出
    """

async def cleanup(self) -> None:
    """
    清理系统资源

    关闭数据库连接，释放内存等。
    """

async def setup_collection(self, collection_name: str) -> None:
    """
    设置并初始化指定的Collection

    Args:
        collection_name: Collection名称

    Raises:
        ValueError: 当Collection名称无效时
        RAGError: 当Collection创建失败时
    """
```

#### 文档管理

```python
async def add_text(
    self,
    text: str,
    collection_name: str = "general",
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """
    添加文本到指定知识库

    Args:
        text: 要添加的文本内容
        collection_name: 目标Collection名称
        metadata: 可选的元数据信息

    Returns:
        int: 成功添加的节点数量

    Raises:
        ValueError: 当参数无效时
        CollectionNotFoundError: 当Collection不存在时
        EmbeddingError: 当嵌入生成失败时

    Example:
        >>> async with RAGSystem() as rag:
        ...     count = await rag.add_text("人工智能是...", "general")
        ...     print(f"添加了 {count} 个节点")
    """

async def add_file(
    self,
    file_path: str,
    collection_name: str = "general",
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """
    添加文件到指定知识库

    Args:
        file_path: 文件路径
        collection_name: 目标Collection名称
        metadata: 可选的元数据信息

    Returns:
        int: 成功添加的节点数量

    Raises:
        FileNotFoundError: 当文件不存在时
        ValueError: 当文件格式不支持时
        CollectionNotFoundError: 当Collection不存在时

    Example:
        >>> async with RAGSystem() as rag:
        ...     count = await rag.add_file("document.pdf", "general")
        ...     print(f"添加了 {count} 个节点")
    """

async def add_documents(
    self,
    documents: List[str],
    collection_name: str = "general",
    metadata_list: Optional[List[Dict[str, Any]]] = None
) -> int:
    """
    批量添加文档到指定知识库

    Args:
        documents: 文档内容列表
        collection_name: 目标Collection名称
        metadata_list: 可选的元数据列表

    Returns:
        int: 成功添加的节点总数

    Example:
        >>> docs = ["文档1内容", "文档2内容"]
        >>> async with RAGSystem() as rag:
        ...     count = await rag.add_documents(docs, "general")
    """
```

#### 知识检索

```python
async def query(
    self,
    question: str,
    collection_name: str = "general",
    top_k: Optional[int] = None
) -> QueryResult:
    """
    在指定知识库中查询问题

    Args:
        question: 用户问题
        collection_name: 目标Collection名称
        top_k: 检索的文档数量，如果为None则使用配置默认值

    Returns:
        QueryResult: 查询结果对象

    Raises:
        ValueError: 当问题为空时
        CollectionNotFoundError: 当Collection不存在时
        QueryError: 当查询失败时

    Example:
        >>> async with RAGSystem() as rag:
        ...     result = await rag.query("什么是人工智能？", "general")
        ...     print(f"回答: {result.answer}")
        ...     print(f"来源: {len(result.retrieved_nodes)} 个文档")
    """

async def query_multiple_collections(
    self,
    question: str,
    collection_names: List[str],
    top_k: Optional[int] = None
) -> List[QueryResult]:
    """
    在多个知识库中查询问题

    Args:
        question: 用户问题
        collection_names: 目标Collection名称列表
        top_k: 每个Collection检索的文档数量

    Returns:
        List[QueryResult]: 查询结果列表

    Example:
        >>> collections = ["general", "testcase"]
        >>> async with RAGSystem() as rag:
        ...     results = await rag.query_multiple_collections(
        ...         "如何编写测试用例？", collections
        ...     )
        ...     for result in results:
        ...         print(f"Collection: {result.collection_name}")
        ...         print(f"回答: {result.answer}")
    """

async def query_business_type(
    self,
    question: str,
    business_type: str,
    top_k: Optional[int] = None
) -> List[QueryResult]:
    """
    在指定业务类型的所有知识库中查询问题

    Args:
        question: 用户问题
        business_type: 业务类型 (general, testcase, ui_testing, ai_chat)
        top_k: 每个Collection检索的文档数量

    Returns:
        List[QueryResult]: 查询结果列表

    Example:
        >>> async with RAGSystem() as rag:
        ...     results = await rag.query_business_type(
        ...         "如何进行UI测试？", "ui_testing"
        ...     )
    """
```

#### 系统信息

```python
async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
    """
    获取Collection信息

    Args:
        collection_name: Collection名称

    Returns:
        Dict[str, Any]: Collection信息字典

    Example:
        >>> async with RAGSystem() as rag:
        ...     info = await rag.get_collection_info("general")
        ...     print(f"文档数量: {info['document_count']}")
    """

async def list_collections(self) -> List[str]:
    """
    列出所有可用的Collection

    Returns:
        List[str]: Collection名称列表
    """

async def get_system_stats(self) -> Dict[str, Any]:
    """
    获取系统统计信息

    Returns:
        Dict[str, Any]: 系统统计信息
    """
```

### 2. QueryResult - 查询结果

查询操作的返回结果对象。

```python
@dataclass
class QueryResult:
    """查询结果数据类"""

    answer: str                           # 生成的回答
    retrieved_nodes: List[NodeWithScore]  # 检索到的相关文档节点
    collection_name: str                  # 查询的Collection名称
    query_time: float                     # 查询耗时（秒）
    metadata: Dict[str, Any]              # 额外的元数据信息

    @property
    def source_count(self) -> int:
        """返回来源文档数量"""
        return len(self.retrieved_nodes)

    @property
    def confidence_score(self) -> float:
        """返回置信度分数（基于检索节点的平均分数）"""
        if not self.retrieved_nodes:
            return 0.0
        return sum(node.score for node in self.retrieved_nodes) / len(self.retrieved_nodes)
```

### 3. RAGConfig - 系统配置

RAG系统的配置管理类。

```python
@dataclass
class RAGConfig:
    """RAG系统总配置"""

    milvus: MilvusConfig      # Milvus数据库配置
    ollama: OllamaConfig      # Ollama嵌入模型配置
    deepseek: DeepSeekConfig  # DeepSeek语言模型配置

    @classmethod
    def from_settings(cls) -> 'RAGConfig':
        """从系统设置创建配置"""
        return cls(
            milvus=MilvusConfig.from_settings(),
            ollama=OllamaConfig.from_settings(),
            deepseek=DeepSeekConfig.from_settings(),
        )

    def get_collection_config(self, collection_name: str) -> Optional[CollectionConfig]:
        """获取指定Collection的配置"""
        return self.milvus.collections.get(collection_name)
```

### 4. 异常类

RAG系统定义的异常类层次结构。

```python
class RAGError(Exception):
    """RAG系统基础异常"""
    pass

class CollectionNotFoundError(RAGError):
    """Collection不存在异常"""
    pass

class EmbeddingError(RAGError):
    """嵌入生成异常"""
    pass

class QueryError(RAGError):
    """查询处理异常"""
    pass

class ConfigError(RAGError):
    """配置错误异常"""
    pass
```

## 🔧 工具函数

### 配置管理

```python
def get_rag_config() -> RAGConfig:
    """获取RAG系统配置"""
    return RAGConfig.from_settings()

def get_collection_config(collection_name: str) -> Optional[CollectionConfig]:
    """获取指定Collection的配置"""
    config = get_rag_config()
    return config.get_collection_config(collection_name)
```

### 系统工厂

```python
async def create_rag_system(config: Optional[RAGConfig] = None) -> RAGSystem:
    """
    创建并初始化RAG系统

    Args:
        config: 可选的配置对象

    Returns:
        RAGSystem: 已初始化的RAG系统实例
    """
    rag = RAGSystem(config)
    await rag.initialize()
    return rag
```

## 📋 使用模式

### 基础使用模式

```python
# 模式1: 上下文管理器（推荐）
async with RAGSystem() as rag:
    await rag.setup_collection("general")
    result = await rag.query("问题", "general")

# 模式2: 手动管理
rag = RAGSystem()
try:
    await rag.initialize()
    await rag.setup_collection("general")
    result = await rag.query("问题", "general")
finally:
    await rag.cleanup()
```

### 高级使用模式

```python
# 多Collection查询
async with RAGSystem() as rag:
    collections = ["general", "testcase", "ui_testing"]
    results = await rag.query_multiple_collections("问题", collections)

# 业务类型查询
async with RAGSystem() as rag:
    results = await rag.query_business_type("问题", "testcase")

# 批量文档添加
async with RAGSystem() as rag:
    documents = ["文档1", "文档2", "文档3"]
    count = await rag.add_documents(documents, "general")
```

## ⚠️ 注意事项

1. **异步操作**: 所有API都是异步的，必须使用`await`调用
2. **资源管理**: 推荐使用上下文管理器确保资源正确释放
3. **异常处理**: 注意捕获和处理相应的异常类型
4. **配置管理**: 确保正确配置Milvus、Ollama和DeepSeek服务
5. **性能考虑**: 批量操作比单个操作更高效
