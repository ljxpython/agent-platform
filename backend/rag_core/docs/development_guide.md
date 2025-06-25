# RAG知识库系统开发规范

## 🎯 开发原则

### 1. 异步优先
所有I/O操作必须使用异步模式，确保系统高性能。

```python
# ✅ 正确 - 异步操作
async def add_document(self, content: str):
    embeddings = await self.embedding_generator.embed_texts([content])
    await self.vector_db.add_nodes(nodes)

# ❌ 错误 - 同步操作
def add_document(self, content: str):
    embeddings = self.embedding_generator.embed_texts([content])  # 阻塞操作
```

### 2. 资源管理
使用上下文管理器确保资源正确释放。

```python
# ✅ 正确 - 使用上下文管理器
async with RAGSystem() as rag:
    result = await rag.query("问题")

# ✅ 正确 - 手动资源管理
rag = RAGSystem()
try:
    await rag.initialize()
    result = await rag.query("问题")
finally:
    await rag.cleanup()
```

### 3. 错误处理
使用分层异常处理，提供清晰的错误信息。

```python
# ✅ 正确 - 分层异常处理
try:
    result = await rag.query("问题", "collection")
except CollectionNotFoundError as e:
    logger.error(f"Collection不存在: {e}")
    raise
except EmbeddingError as e:
    logger.error(f"嵌入生成失败: {e}")
    raise
except Exception as e:
    logger.error(f"未知错误: {e}")
    raise RAGError(f"查询失败: {e}")
```

## 📝 代码规范

### 1. 命名规范

#### 类名 - PascalCase
```python
class RAGSystem:           # ✅ 正确
class QueryEngine:         # ✅ 正确
class ragSystem:           # ❌ 错误
```

#### 方法名 - snake_case
```python
async def add_text():      # ✅ 正确
async def query_multiple_collections():  # ✅ 正确
async def addText():       # ❌ 错误
```

#### 常量 - UPPER_SNAKE_CASE
```python
DEFAULT_CHUNK_SIZE = 1000  # ✅ 正确
MAX_RETRIES = 3           # ✅ 正确
defaultChunkSize = 1000   # ❌ 错误
```

### 2. 类型注解
所有公共方法必须包含完整的类型注解。

```python
# ✅ 正确 - 完整类型注解
async def query(
    self,
    question: str,
    collection_name: str = "general",
    top_k: Optional[int] = None
) -> QueryResult:
    pass

# ❌ 错误 - 缺少类型注解
async def query(self, question, collection_name="general"):
    pass
```

### 3. 文档字符串
使用Google风格的文档字符串。

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
        collection_name: 目标Collection名称，默认为"general"
        metadata: 可选的元数据信息

    Returns:
        int: 成功添加的节点数量

    Raises:
        CollectionNotFoundError: 当指定的Collection不存在时
        EmbeddingError: 当嵌入生成失败时

    Example:
        >>> async with RAGSystem() as rag:
        ...     count = await rag.add_text("人工智能是...", "general")
        ...     print(f"添加了 {count} 个节点")
    """
```

## 🏗️ 架构模式

### 1. 工厂模式
使用工厂函数创建复杂对象。

```python
# ✅ 推荐 - 工厂函数
async def create_rag_system(config: Optional[RAGConfig] = None) -> RAGSystem:
    """创建并初始化RAG系统"""
    rag = RAGSystem(config)
    await rag.initialize()
    return rag

# 使用
rag = await create_rag_system()
```

### 2. 策略模式
为不同业务类型提供不同的处理策略。

```python
class LLMService:
    def generate_rag_response(self, query: str, context: str) -> str:
        """通用RAG回答生成"""
        pass

    def generate_business_rag_response(
        self, query: str, context: str, business_type: str
    ) -> str:
        """业务专用RAG回答生成"""
        if business_type == "testcase":
            return self._generate_testcase_response(query, context)
        elif business_type == "ui_testing":
            return self._generate_ui_testing_response(query, context)
        else:
            return self.generate_rag_response(query, context)
```

### 3. 观察者模式
实现事件驱动的组件通信。

```python
class RAGSystem:
    def __init__(self):
        self._listeners = []

    def add_listener(self, listener):
        self._listeners.append(listener)

    async def _notify_document_added(self, collection_name: str, node_count: int):
        for listener in self._listeners:
            await listener.on_document_added(collection_name, node_count)
```

## 🔧 配置管理规范

### 1. 配置类设计
使用dataclass定义配置类。

```python
@dataclass
class CollectionConfig:
    """Collection配置类"""
    name: str
    description: str
    dimension: int = 768
    business_type: str = "general"

    # 验证方法
    def __post_init__(self):
        if self.dimension <= 0:
            raise ValueError("dimension必须大于0")
        if not self.name:
            raise ValueError("name不能为空")
```

### 2. 配置加载
支持多种配置来源。

```python
@classmethod
def from_settings(cls):
    """从settings加载配置"""
    return cls(
        host=getattr(settings, 'milvus_host', 'localhost'),
        port=getattr(settings, 'milvus_port', 19530),
    )

@classmethod
def from_env(cls):
    """从环境变量加载配置"""
    return cls(
        host=os.getenv('MILVUS_HOST', 'localhost'),
        port=int(os.getenv('MILVUS_PORT', '19530')),
    )
```

## 📊 日志规范

### 1. 日志级别使用

```python
# DEBUG - 详细调试信息
logger.debug(f"处理文档: {filename}, 大小: {file_size}")

# INFO - 关键操作记录
logger.info(f"📝 添加文本到 {collection_name} - 长度: {len(text)}")

# SUCCESS - 成功操作（loguru特有）
logger.success(f"✅ 文档添加完成 - Collection: {collection_name}, 节点数: {len(node_ids)}")

# WARNING - 异常情况警告
logger.warning(f"⚠️ Collection {collection_name} 已存在，跳过创建")

# ERROR - 错误信息
logger.error(f"❌ 文档添加失败 - Collection: {collection_name}: {e}")
```

### 2. 日志格式规范

```python
# ✅ 推荐格式 - 包含emoji、操作类型、关键信息
logger.info(f"🔍 执行RAG查询 - Collection: {collection_name}, 查询: {query_text}")
logger.success(f"✅ RAG查询完成 - Collection: {collection_name}, 耗时: {response_time:.3f}s")

# ❌ 避免格式 - 信息不足
logger.info("查询完成")
logger.info(f"查询: {query_text}")
```

## 🧪 测试规范

### 1. 单元测试
每个核心方法都应有对应的单元测试。

```python
import pytest
from backend.rag_core.rag_system import RAGSystem

class TestRAGSystem:
    @pytest.mark.asyncio
    async def test_add_text_success(self):
        """测试文本添加成功场景"""
        async with RAGSystem() as rag:
            await rag.setup_collection("test_collection")

            count = await rag.add_text("测试文本", "test_collection")

            assert count > 0
            assert isinstance(count, int)

    @pytest.mark.asyncio
    async def test_add_text_invalid_collection(self):
        """测试无效Collection场景"""
        async with RAGSystem() as rag:
            with pytest.raises(ValueError, match="Collection不存在"):
                await rag.add_text("测试文本", "invalid_collection")
```

### 2. 集成测试
测试组件间的协作。

```python
@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """端到端工作流测试"""
    async with RAGSystem() as rag:
        # 1. 设置Collection
        await rag.setup_collection("test")

        # 2. 添加文档
        count = await rag.add_text("人工智能是计算机科学的分支", "test")
        assert count > 0

        # 3. 查询
        result = await rag.query("什么是人工智能？", "test")
        assert result.answer
        assert len(result.retrieved_nodes) > 0
```

## 🚀 性能优化规范

### 1. 批处理优化
优先使用批处理操作。

```python
# ✅ 推荐 - 批量处理
texts = [node.text for node in nodes]
embeddings = await self.embedding_generator.embed_texts(texts)

# ❌ 避免 - 逐个处理
embeddings = []
for node in nodes:
    embedding = await self.embedding_generator.embed_text(node.text)
    embeddings.append(embedding)
```

### 2. 缓存策略
合理使用缓存减少重复计算。

```python
class EmbeddingGenerator:
    def __init__(self):
        self._cache = {}

    async def embed_text(self, text: str) -> List[float]:
        # 检查缓存
        if text in self._cache:
            return self._cache[text]

        # 生成嵌入
        embedding = await self._generate_embedding(text)

        # 缓存结果
        self._cache[text] = embedding
        return embedding
```

### 3. 资源池管理
使用连接池管理数据库连接。

```python
class MilvusVectorDB:
    def __init__(self, config: RAGConfig):
        self._connection_pool = ConnectionPool(
            host=config.milvus.host,
            port=config.milvus.port,
            max_connections=10
        )
```

## 🔒 安全规范

### 1. 输入验证
严格验证所有外部输入。

```python
def validate_collection_name(name: str) -> str:
    """验证Collection名称"""
    if not name or not isinstance(name, str):
        raise ValueError("Collection名称不能为空")

    if len(name) > 100:
        raise ValueError("Collection名称过长")

    if not re.match(r'^[a-zA-Z0-9_]+$', name):
        raise ValueError("Collection名称只能包含字母、数字和下划线")

    return name
```

### 2. 敏感信息处理
避免在日志中记录敏感信息。

```python
# ✅ 正确 - 脱敏处理
logger.info(f"使用API密钥: {api_key[:8]}***")

# ❌ 错误 - 泄露敏感信息
logger.info(f"使用API密钥: {api_key}")
```

## 📋 代码审查清单

### 提交前检查

- [ ] 所有方法都有类型注解
- [ ] 所有公共方法都有文档字符串
- [ ] 异步操作使用await
- [ ] 资源正确释放
- [ ] 异常处理完整
- [ ] 日志信息清晰
- [ ] 单元测试覆盖
- [ ] 性能考虑合理
- [ ] 安全检查通过

### 代码质量标准

- **可读性**: 代码清晰易懂，命名有意义
- **可维护性**: 模块化设计，低耦合高内聚
- **可测试性**: 易于编写和执行测试
- **性能**: 满足性能要求，资源使用合理
- **安全性**: 输入验证，敏感信息保护
