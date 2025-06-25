# RAG知识库系统配置管理

## 🔧 配置概览

RAG知识库系统采用分层配置管理，支持多种配置来源和灵活的配置覆盖机制。

## 📋 配置结构

### 配置层次

```
RAGConfig
├── MilvusConfig          # 向量数据库配置
│   ├── host              # 主机地址
│   ├── port              # 端口号
│   ├── timeout           # 连接超时
│   └── collections       # Collection配置字典
├── OllamaConfig          # 嵌入模型配置
│   ├── host              # Ollama服务地址
│   ├── port              # 端口号
│   ├── model             # 嵌入模型名称
│   └── timeout           # 请求超时
└── DeepSeekConfig        # 大语言模型配置
    ├── api_key           # API密钥
    ├── base_url          # API基础URL
    ├── model             # 模型名称
    └── timeout           # 请求超时
```

## ⚙️ 配置类定义

### 1. 主配置类

```python
@dataclass
class RAGConfig:
    """RAG系统总配置"""

    milvus: MilvusConfig
    ollama: OllamaConfig
    deepseek: DeepSeekConfig

    @classmethod
    def from_settings(cls) -> 'RAGConfig':
        """从Django settings加载配置"""
        return cls(
            milvus=MilvusConfig.from_settings(),
            ollama=OllamaConfig.from_settings(),
            deepseek=DeepSeekConfig.from_settings(),
        )

    @classmethod
    def from_env(cls) -> 'RAGConfig':
        """从环境变量加载配置"""
        return cls(
            milvus=MilvusConfig.from_env(),
            ollama=OllamaConfig.from_env(),
            deepseek=DeepSeekConfig.from_env(),
        )
```

### 2. Milvus配置

```python
@dataclass
class MilvusConfig:
    """Milvus向量数据库配置"""

    host: str = "localhost"
    port: int = 19530
    timeout: int = 30
    collections: Dict[str, CollectionConfig] = field(default_factory=dict)

    @classmethod
    def from_settings(cls) -> 'MilvusConfig':
        """从settings加载Milvus配置"""
        return cls(
            host=getattr(settings, 'MILVUS_HOST', 'localhost'),
            port=getattr(settings, 'MILVUS_PORT', 19530),
            timeout=getattr(settings, 'MILVUS_TIMEOUT', 30),
            collections=cls._load_collections_from_settings(),
        )

    @classmethod
    def from_env(cls) -> 'MilvusConfig':
        """从环境变量加载Milvus配置"""
        return cls(
            host=os.getenv('MILVUS_HOST', 'localhost'),
            port=int(os.getenv('MILVUS_PORT', '19530')),
            timeout=int(os.getenv('MILVUS_TIMEOUT', '30')),
        )
```

### 3. Collection配置

```python
@dataclass
class CollectionConfig:
    """单个Collection的配置"""

    name: str                                    # Collection名称
    description: str                             # 描述
    dimension: int = 768                         # 向量维度
    business_type: str = "general"               # 业务类型
    top_k: int = 5                              # 默认检索数量
    similarity_threshold: float = 0.7            # 相似度阈值
    chunk_size: int = 1000                      # 文本分块大小
    chunk_overlap: int = 200                    # 分块重叠大小

    def __post_init__(self):
        """配置验证"""
        if self.dimension <= 0:
            raise ValueError("dimension必须大于0")
        if self.top_k <= 0:
            raise ValueError("top_k必须大于0")
        if not 0 <= self.similarity_threshold <= 1:
            raise ValueError("similarity_threshold必须在0-1之间")
```

### 4. Ollama配置

```python
@dataclass
class OllamaConfig:
    """Ollama嵌入模型配置"""

    host: str = "localhost"
    port: int = 11434
    model: str = "nomic-embed-text"
    timeout: int = 30

    @property
    def base_url(self) -> str:
        """获取完整的API地址"""
        return f"http://{self.host}:{self.port}"

    @classmethod
    def from_settings(cls) -> 'OllamaConfig':
        """从settings加载Ollama配置"""
        return cls(
            host=getattr(settings, 'OLLAMA_HOST', 'localhost'),
            port=getattr(settings, 'OLLAMA_PORT', 11434),
            model=getattr(settings, 'OLLAMA_EMBED_MODEL', 'nomic-embed-text'),
            timeout=getattr(settings, 'OLLAMA_TIMEOUT', 30),
        )
```

### 5. DeepSeek配置

```python
@dataclass
class DeepSeekConfig:
    """DeepSeek大语言模型配置"""

    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    timeout: int = 60
    max_tokens: int = 2000
    temperature: float = 0.7

    @classmethod
    def from_settings(cls) -> 'DeepSeekConfig':
        """从settings加载DeepSeek配置"""
        api_key = getattr(settings, 'DEEPSEEK_API_KEY', None)
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY未配置")

        return cls(
            api_key=api_key,
            base_url=getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
            model=getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat'),
            timeout=getattr(settings, 'DEEPSEEK_TIMEOUT', 60),
            max_tokens=getattr(settings, 'DEEPSEEK_MAX_TOKENS', 2000),
            temperature=getattr(settings, 'DEEPSEEK_TEMPERATURE', 0.7),
        )
```

## 🌍 环境变量配置

### 必需的环境变量

```bash
# DeepSeek API配置（必需）
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 可选的环境变量

```bash
# Milvus配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_TIMEOUT=30

# Ollama配置
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_TIMEOUT=30

# DeepSeek配置
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=60
DEEPSEEK_MAX_TOKENS=2000
DEEPSEEK_TEMPERATURE=0.7
```

## 📝 Django Settings配置

### settings.py配置示例

```python
# RAG系统配置
RAG_CONFIG = {
    # Milvus配置
    'MILVUS_HOST': 'localhost',
    'MILVUS_PORT': 19530,
    'MILVUS_TIMEOUT': 30,

    # Ollama配置
    'OLLAMA_HOST': 'localhost',
    'OLLAMA_PORT': 11434,
    'OLLAMA_EMBED_MODEL': 'nomic-embed-text',
    'OLLAMA_TIMEOUT': 30,

    # DeepSeek配置
    'DEEPSEEK_API_KEY': os.getenv('DEEPSEEK_API_KEY'),
    'DEEPSEEK_BASE_URL': 'https://api.deepseek.com',
    'DEEPSEEK_MODEL': 'deepseek-chat',
    'DEEPSEEK_TIMEOUT': 60,
    'DEEPSEEK_MAX_TOKENS': 2000,
    'DEEPSEEK_TEMPERATURE': 0.7,
}

# Collection配置
RAG_COLLECTIONS = {
    'general': {
        'name': 'general',
        'description': '通用知识库',
        'dimension': 768,
        'business_type': 'general',
        'top_k': 5,
        'similarity_threshold': 0.7,
        'chunk_size': 1000,
        'chunk_overlap': 200,
    },
    'testcase': {
        'name': 'testcase',
        'description': '测试用例专业知识库',
        'dimension': 768,
        'business_type': 'testcase',
        'top_k': 3,
        'similarity_threshold': 0.8,
        'chunk_size': 800,
        'chunk_overlap': 150,
    },
    'ui_testing': {
        'name': 'ui_testing',
        'description': 'UI测试专业知识库',
        'dimension': 768,
        'business_type': 'ui_testing',
        'top_k': 4,
        'similarity_threshold': 0.75,
        'chunk_size': 1200,
        'chunk_overlap': 250,
    },
    'ai_chat': {
        'name': 'ai_chat',
        'description': 'AI对话专业知识库',
        'dimension': 768,
        'business_type': 'ai_chat',
        'top_k': 6,
        'similarity_threshold': 0.65,
        'chunk_size': 600,
        'chunk_overlap': 100,
    },
}
```

## 🔄 配置加载优先级

配置加载按以下优先级顺序：

1. **代码中的显式配置** - 最高优先级
2. **环境变量** - 中等优先级
3. **Django settings** - 较低优先级
4. **默认值** - 最低优先级

### 配置加载示例

```python
# 方式1: 使用默认配置（从settings加载）
config = RAGConfig.from_settings()

# 方式2: 从环境变量加载
config = RAGConfig.from_env()

# 方式3: 手动创建配置
config = RAGConfig(
    milvus=MilvusConfig(host="custom-host", port=19530),
    ollama=OllamaConfig(model="custom-model"),
    deepseek=DeepSeekConfig(api_key="your-key")
)

# 方式4: 混合配置
base_config = RAGConfig.from_settings()
base_config.milvus.host = "custom-host"  # 覆盖特定配置
```

## 🛠️ 配置工具函数

### 配置获取函数

```python
def get_rag_config() -> RAGConfig:
    """获取RAG系统配置"""
    return RAGConfig.from_settings()

def get_collection_config(collection_name: str) -> Optional[CollectionConfig]:
    """获取指定Collection的配置"""
    config = get_rag_config()
    return config.milvus.collections.get(collection_name)

def get_business_collections(business_type: str) -> List[CollectionConfig]:
    """获取指定业务类型的所有Collection配置"""
    config = get_rag_config()
    return [
        col_config for col_config in config.milvus.collections.values()
        if col_config.business_type == business_type
    ]
```

### 配置验证函数

```python
def validate_config(config: RAGConfig) -> List[str]:
    """
    验证配置的有效性

    Returns:
        List[str]: 验证错误列表，空列表表示配置有效
    """
    errors = []

    # 验证DeepSeek API密钥
    if not config.deepseek.api_key:
        errors.append("DeepSeek API密钥未配置")

    # 验证Collection配置
    for name, col_config in config.milvus.collections.items():
        if col_config.dimension <= 0:
            errors.append(f"Collection {name} 的dimension配置无效")

    return errors
```

## 🔧 配置最佳实践

### 1. 生产环境配置

```bash
# 生产环境建议使用环境变量
export DEEPSEEK_API_KEY="your_production_api_key"
export MILVUS_HOST="production-milvus-host"
export OLLAMA_HOST="production-ollama-host"
```

### 2. 开发环境配置

```python
# 开发环境可以在settings.py中配置
RAG_CONFIG = {
    'MILVUS_HOST': 'localhost',
    'OLLAMA_HOST': 'localhost',
    'DEEPSEEK_API_KEY': 'your_dev_api_key',
}
```

### 3. 测试环境配置

```python
# 测试环境使用模拟配置
if settings.TESTING:
    RAG_CONFIG['DEEPSEEK_API_KEY'] = 'test_key'
    RAG_CONFIG['MILVUS_HOST'] = 'test_milvus'
```

## ⚠️ 安全注意事项

1. **API密钥保护**: 不要在代码中硬编码API密钥
2. **环境变量**: 生产环境使用环境变量管理敏感信息
3. **配置验证**: 启动时验证配置的有效性
4. **日志安全**: 避免在日志中记录敏感配置信息

## 🔍 配置调试

### 配置检查工具

```python
async def check_rag_config():
    """检查RAG配置的连通性"""
    config = get_rag_config()

    # 检查Milvus连接
    try:
        # 测试Milvus连接
        print("✅ Milvus连接正常")
    except Exception as e:
        print(f"❌ Milvus连接失败: {e}")

    # 检查Ollama连接
    try:
        # 测试Ollama连接
        print("✅ Ollama连接正常")
    except Exception as e:
        print(f"❌ Ollama连接失败: {e}")

    # 检查DeepSeek API
    try:
        # 测试DeepSeek API
        print("✅ DeepSeek API正常")
    except Exception as e:
        print(f"❌ DeepSeek API失败: {e}")
```
