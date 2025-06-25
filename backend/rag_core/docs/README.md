# RAG知识库系统开发规范与使用说明

## 📚 文档目录

本目录包含RAG知识库系统的完整开发规范、使用说明和示例代码，帮助AI编程助手和开发者快速理解和使用RAG系统。

### 📋 文档结构

```
docs/
├── README.md                    # 本文件 - 总览和快速开始
├── architecture.md              # 系统架构设计文档
├── development_guide.md         # 开发规范和最佳实践
├── api_reference.md             # API接口参考文档
├── configuration.md             # 配置管理说明
├── examples/                    # 示例代码目录
│   ├── basic_usage.py          # 基础使用示例
│   ├── advanced_usage.py       # 高级使用示例
│   ├── custom_collection.py    # 自定义Collection示例
│   └── integration_examples.py # 集成示例
├── troubleshooting.md          # 故障排除指南
└── changelog.md                # 版本更新日志
```

## 🚀 快速开始

### 系统概述

RAG知识库系统是一个基于LlamaIndex、Milvus和DeepSeek的企业级检索增强生成系统，支持：

- **多Collection架构** - 为不同业务提供专业知识库
- **异步处理** - 高性能的异步操作
- **灵活配置** - 支持多种嵌入模型和LLM
- **业务分类** - 针对不同业务场景优化

### 核心组件

1. **RAGSystem** - 系统主入口，管理多个Collection
2. **QueryEngine** - 查询引擎，处理检索和生成
3. **CollectionManager** - Collection管理器
4. **EmbeddingGenerator** - 嵌入向量生成器
5. **LLMService** - 大语言模型服务
6. **VectorStore** - 向量数据库接口

### 基础使用示例

```python
from backend.rag_core.rag_system import RAGSystem

# 1. 创建RAG系统
async def basic_example():
    async with RAGSystem() as rag:
        # 2. 设置Collection
        await rag.setup_collection("general")

        # 3. 添加文档
        await rag.add_text("人工智能是计算机科学的一个分支。", "general")

        # 4. 查询
        result = await rag.query("什么是人工智能？", "general")
        print(f"回答: {result.answer}")
```

### 支持的业务类型

- **general** - 通用知识库
- **testcase** - 测试用例专业知识库
- **ui_testing** - UI测试专业知识库
- **ai_chat** - AI对话专业知识库

### 配置系统

在 `backend/conf/settings.yaml` 中配置RAG系统：

```yaml
# RAG 配置
milvus_host: "localhost"
milvus_port: 19530
ollama_base_url: "http://localhost:11434"
ollama_embedding_model: "nomic-embed-text"
deepseek_model: "deepseek-chat"
deepseek_api_key: "your-api-key"
deepseek_base_url: "https://api.deepseek.com/v1"
```

### 服务层使用

```python
from backend.services.rag.rag_service import RAGService

service = RAGService()
await service.initialize()

# 添加文本
result = await service.add_text(
    "测试用例设计需要考虑边界条件",
    "testcase"
)

# 查询
result = await service.query("如何设计测试用例？", "testcase")
print(result['answer'])
```

## 📡 API接口

### Collection管理

- `GET /api/v1/rag/collections` - 获取所有Collections信息
- `GET /api/v1/rag/collections/{collection_name}` - 获取指定Collection信息
- `POST /api/v1/rag/collections/setup` - 设置Collection
- `POST /api/v1/rag/collections/setup-all` - 设置所有Collections

### 文档管理

- `POST /api/v1/rag/documents/add-text` - 添加文本到知识库
- `POST /api/v1/rag/documents/add-file` - 添加文件到知识库

### 查询接口

- `POST /api/v1/rag/query` - RAG查询
- `POST /api/v1/rag/query/multiple` - 多Collection查询
- `POST /api/v1/rag/query/business` - 业务类型查询
- `POST /api/v1/rag/chat` - RAG聊天

### 系统管理

- `GET /api/v1/rag/stats` - 获取系统统计信息
- `GET /api/v1/rag/health` - 健康检查
- `DELETE /api/v1/rag/collections/{collection_name}/clear` - 清空Collection数据
- `DELETE /api/v1/rag/clear-all` - 清空所有数据

## 🔧 Collection配置

每个Collection可以独立配置：

```python
@dataclass
class CollectionConfig:
    name: str                    # Collection名称
    description: str             # 描述
    dimension: int = 768         # 向量维度
    business_type: str = "general"  # 业务类型
    top_k: int = 5              # 检索数量
    similarity_threshold: float = 0.7  # 相似度阈值
    chunk_size: int = 1000      # 分块大小
    chunk_overlap: int = 200    # 分块重叠
```

## 🧪 测试

运行集成测试：

```bash
cd backend/rag_core
python test_integration.py
```

测试内容：
- 配置验证
- 核心系统初始化
- 服务层功能
- 基本RAG功能（需要外部服务）

## 📁 目录结构

```
backend/rag_core/
├── __init__.py              # 模块初始化
├── collection_manager.py    # Collection管理器
├── data_loader.py          # 文档加载器
├── embedding_generator.py  # 嵌入生成器
├── llm_service.py          # LLM服务
├── query_engine.py         # 查询引擎
├── rag_system.py           # 主系统类
├── vector_store.py         # 向量数据库
├── test_integration.py     # 集成测试
└── docs/                   # 完整文档系统
    ├── README.md           # 本文件
    ├── architecture.md     # 系统架构
    ├── development_guide.md # 开发规范
    ├── api_reference.md    # API参考
    ├── configuration.md    # 配置管理
    ├── troubleshooting.md  # 故障排除
    ├── changelog.md        # 更新日志
    └── examples/           # 示例代码
        ├── basic_usage.py
        ├── advanced_usage.py
        ├── custom_collection.py
        ├── integration_examples.py
        └── test_rag_docs_completeness.py
```

## 📖 详细文档

### 🏗️ [系统架构](architecture.md)
了解RAG系统的整体架构设计、组件关系和数据流。

### 🛠️ [开发规范](development_guide.md)
开发RAG相关功能的规范、最佳实践和代码风格指南。

### 📡 [API参考](api_reference.md)
完整的API接口文档，包括所有类、方法和参数说明。

### ⚙️ [配置管理](configuration.md)
RAG系统的配置选项、环境变量和自定义配置方法。

### 💡 [示例代码](examples/)
丰富的示例代码，涵盖基础使用、高级功能和集成场景。

### 🔧 [故障排除](troubleshooting.md)
常见问题的解决方案和调试技巧。

## 🎯 AI编程助手指南

### 开发新功能时的步骤

1. **查看架构文档** - 了解系统设计和组件关系
2. **参考API文档** - 确认可用的接口和方法
3. **查看示例代码** - 学习最佳实践和使用模式
4. **遵循开发规范** - 确保代码质量和一致性
5. **测试和验证** - 使用提供的测试模板

### 常用开发模式

```python
# 模式1: 基础RAG查询
async with RAGSystem() as rag:
    result = await rag.query("问题", "collection_name")

# 模式2: 多Collection查询
async with RAGSystem() as rag:
    results = await rag.query_multiple_collections("问题", ["col1", "col2"])

# 模式3: 业务类型查询
async with RAGSystem() as rag:
    results = await rag.query_business_type("问题", "testcase")

# 模式4: 文档管理
async with RAGSystem() as rag:
    await rag.add_file("document.pdf", "general")
    await rag.add_text("文本内容", "general")
```

## 🔗 集成说明

### 与现有服务集成

RAG系统已集成到后端架构中：

1. **配置系统**: 使用统一的配置管理
2. **服务层**: 遵循现有的服务层模式
3. **API层**: 集成到FastAPI路由系统
4. **日志系统**: 使用loguru统一日志

### 为业务服务提供支持

不同业务可以使用对应的collection：

```python
# 测试用例服务使用testcase collection
result = await rag_service.query_business_type(
    "如何设计边界测试用例？",
    "testcase"
)

# UI测试服务使用ui_testing collection
result = await rag_service.query_business_type(
    "如何定位页面元素？",
    "ui_testing"
)
```

## 🚨 注意事项

1. **依赖服务**: 需要Milvus和Ollama服务运行
2. **API密钥**: 需要配置DeepSeek API密钥
3. **资源管理**: 使用异步上下文管理器确保资源清理
4. **错误处理**: 所有操作都有完整的错误处理和日志记录

## 🔮 未来扩展

1. **更多向量数据库**: 支持其他向量数据库
2. **更多LLM**: 支持其他大语言模型
3. **高级检索**: 支持混合检索、重排序等
4. **缓存机制**: 添加查询结果缓存
5. **监控指标**: 添加性能监控和指标收集

## 🔗 相关链接

- [LlamaIndex文档](https://docs.llamaindex.ai/)
- [Milvus文档](https://milvus.io/docs)
- [DeepSeek API文档](https://platform.deepseek.com/api-docs/)
- [Ollama文档](https://ollama.ai/docs)

## 📞 支持

如果在使用过程中遇到问题：

1. 查看 [故障排除文档](troubleshooting.md)
2. 检查 [示例代码](examples/)
3. 参考 [API文档](api_reference.md)
4. 查看系统日志获取详细错误信息

## 🔄 版本信息

当前版本: v1.0.0

查看 [更新日志](changelog.md) 了解版本变更详情。
