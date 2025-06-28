# RAG配置迁移文档

## 📋 迁移概述

本次迁移将 `backend/conf/rag_config.py` 中的硬编码常量迁移到 Dynaconf 配置管理系统中，实现了统一的配置管理。

## 🔄 迁移内容

### 迁移前的问题
- `rag_config.py` 中存在大量硬编码常量
- Collection配置分散在代码中
- 配置修改需要修改代码
- 缺乏统一的配置管理

### 迁移后的改进
- ✅ 所有常量迁移到 `backend/conf/settings.yaml`
- ✅ 结构化的配置管理
- ✅ 支持环境变量覆盖
- ✅ 统一的配置加载机制

## 📁 配置文件结构

### settings.yaml 新增配置结构

```yaml
rag:
  # Milvus 向量数据库配置
  milvus:
    host: "101.126.90.71"
    port: 19530
    default_collection: "general_knowledge"
    dimension: 1024

  # Ollama 嵌入服务配置
  ollama:
    base_url: "http://101.126.90.71:11434"
    embedding_model: "bge-m3"

  # DeepSeek 大语言模型配置
  deepseek:
    model: "deepseek-chat"
    api_key: "sk-xxx"
    base_url: "https://api.deepseek.com/v1"

  # Collection 默认配置
  collection_defaults:
    dimension: 768
    top_k: 5
    similarity_threshold: 0.7
    chunk_size: 1000
    chunk_overlap: 200

  # 预定义 Collections 配置
  collections:
    general:
      name: "general_knowledge"
      description: "通用知识库"
      business_type: "general"
      # 其他参数继承 collection_defaults

    testcase:
      name: "testcase_knowledge"
      description: "测试用例专业知识库"
      business_type: "testcase"
      chunk_size: 800      # 覆盖默认值
      chunk_overlap: 150   # 覆盖默认值
```

## 🔧 代码变更

### CollectionConfig 类
- 移除硬编码默认值
- 添加 `from_dict()` 类方法
- 支持从配置字典创建实例

### MilvusConfig 类
- 移除 `__post_init__` 方法中的硬编码collections
- 更新 `from_settings()` 方法读取新配置结构

### OllamaConfig 和 DeepSeekConfig 类
- 更新配置读取路径
- 使用嵌套配置结构

## 📊 迁移验证

所有配置迁移已通过以下测试验证：

1. ✅ 基础配置加载测试
2. ✅ Collections配置测试
3. ✅ Collection辅助函数测试
4. ✅ 配置默认值测试

## 🚀 使用方式

### 获取RAG配置
```python
from backend.conf.rag_config import get_rag_config

config = get_rag_config()
print(f"Milvus: {config.milvus.host}:{config.milvus.port}")
print(f"Collections: {list(config.milvus.collections.keys())}")
```

### 获取特定Collection配置
```python
from backend.conf.rag_config import get_collection_config

general_config = get_collection_config("general")
if general_config:
    print(f"Collection: {general_config.name}")
    print(f"Chunk size: {general_config.chunk_size}")
```

### 获取业务类型Collections
```python
config = get_rag_config()
testcase_collections = config.get_business_collections("testcase")
```

## 🔄 向后兼容性

- 所有现有API保持不变
- 配置加载逻辑完全兼容
- 不影响现有功能

## 🎯 优势

1. **统一管理**: 所有RAG配置集中在 settings.yaml
2. **灵活配置**: 支持环境变量和多环境配置
3. **易于维护**: 配置修改无需改动代码
4. **类型安全**: 保持强类型配置类
5. **扩展性**: 易于添加新的collection配置

## 📝 注意事项

- 修改配置后需要重启应用
- 环境变量可以覆盖配置文件设置
- 新增collection需要在 settings.yaml 中配置
- 配置验证在应用启动时进行

## 🔄 嵌入模型迁移 (2025-06-28)

### 迁移内容
- **嵌入模型**: nomic-embed-text → bge-m3
- **向量维度**: 768 → 1024
- **影响范围**: 所有 collections 和向量数据

### 迁移步骤
1. 更新配置文件中的 embedding_model 和 dimension
2. 运行迁移脚本: `python migrate_embedding_model.py`
3. 重新上传所有文档到知识库

### 注意事项
- ⚠️ 迁移会清除所有现有向量数据
- ⚠️ 需要确保 Ollama 已安装 bge-m3 模型
- ⚠️ 迁移后需要重新上传文档

## 🔗 相关文件

- `backend/conf/settings.yaml` - 主配置文件
- `backend/conf/rag_config.py` - RAG配置类
- `backend/conf/config.py` - Dynaconf配置加载器
- `migrate_embedding_model.py` - 嵌入模型迁移脚本
