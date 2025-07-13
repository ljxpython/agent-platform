# RAG 服务重写说明

## 🎯 重写目标

基于 `backend/rag_core` 的功能，重写 `backend/services/rag` 中的服务，避免重复造轮子，为 AI 测试系统提供项目隔离的 RAG 功能。

## 🏗️ 重写架构

### 设计原则

1. **避免重复造轮子** - 直接复用 `backend/rag_core` 已有功能
2. **薄封装设计** - services 层作为 rag_core 和 API 之间的薄封装
3. **项目隔离支持** - 为 AI 测试系统添加项目级别的知识库隔离
4. **保持 API 兼容性** - 确保现有 API 接口正常工作

### 架构层次

```
API Layer (backend/api/v1/rag/)
    ↓
Services Layer (backend/services/rag/) - 重写后
    ↓
Core Layer (backend/rag_core/) - 复用现有功能
    ↓
Vector DB (Milvus) + LLM (DeepSeek) + Embedding (BGE-M3)
```

## 📁 重写后的文件结构

### 1. RAGService (`rag_service.py`)

**功能定位：** RAGSystem 的薄封装，添加项目隔离支持

**主要变化：**
- 支持项目隔离：`{project_id}_{collection_name}`
- 直接使用 `RAGSystem` 作为核心引擎
- 添加项目级别的服务实例管理
- 保持与现有 API 的兼容性

**核心方法：**
```python
# Collection 管理
await rag_service.setup_collection(collection_name, overwrite=False)
await rag_service.get_collection_info(collection_name)
await rag_service.list_collections()

# 文档添加
await rag_service.add_text(text, collection_name, metadata)
await rag_service.add_file(file_path, collection_name)

# 查询功能
await rag_service.query(question, collection_name)
await rag_service.query_multiple_collections(question, collection_names)
await rag_service.chat(message, collection_name)

# 系统管理
await rag_service.get_system_stats()
await rag_service.clear_collection(collection_name)
```

**项目隔离示例：**
```python
# 默认项目
service_default = await get_rag_service("default")
await service_default.setup_collection("general")  # -> "general"

# 项目1
service_project1 = await get_rag_service("project1")
await service_project1.setup_collection("general")  # -> "project1_general"
```

### 2. RAGCollectionService (`collection_service.py`)

**功能定位：** 专注于数据库记录管理，向量数据库操作交给 rag_core

**主要变化：**
- 移除所有向量数据库操作相关代码
- 专注于 `RAGCollection` 数据库模型的 CRUD
- 支持项目隔离的 collection 管理
- 简化复杂的同步逻辑

**核心方法：**
```python
# Collection 数据库管理
await collection_service.initialize_default_collections()
await collection_service.get_all_collections()
await collection_service.get_collection_by_name(name)
await collection_service.create_collection(collection_data)
await collection_service.update_collection(name, update_data)
await collection_service.delete_collection(name)
```

### 3. RAGFileUploadService (`file_upload_service.py`)

**功能定位：** 文件管理和 MD5 重复检测，支持项目隔离

**主要变化：**
- 添加项目隔离支持
- 保持 MD5 重复检测核心功能
- 简化文件管理流程

**核心方法：**
```python
# 文件管理
await file_service.check_file_exists(file_md5, collection_name)
await file_service.record_uploaded_file(filename, file_md5, file_size, collection_name)
await file_service.get_collection_files(collection_name)
await file_service.get_document_statistics(user_id)
```

## 🔧 项目隔离机制

### Collection 命名规则

- **默认项目：** `collection_name` (如: `general`, `testcase`)
- **其他项目：** `{project_id}_{collection_name}` (如: `project1_general`, `project1_testcase`)

### 服务实例管理

每个项目都有独立的服务实例：

```python
# 获取项目级别的服务实例
rag_service = await get_rag_service("project1")
collection_service = get_collection_service("project1")
file_service = get_file_upload_service("project1")
```

### 数据隔离

1. **向量数据库：** 不同项目使用不同的 collection
2. **数据库记录：** 通过 collection 名称前缀隔离
3. **文件记录：** 通过 project_collection_name 隔离

## 🚀 使用示例

### 基本使用

```python
from backend.services.rag.rag_service import get_rag_service

# 获取项目的 RAG 服务
rag_service = await get_rag_service("my_project")

# 设置 collection
await rag_service.setup_collection("general")

# 添加文档
result = await rag_service.add_text(
    text="人工智能是计算机科学的一个分支",
    collection_name="general",
    metadata={"source": "test", "topic": "AI"}
)

# 查询
query_result = await rag_service.query(
    question="什么是人工智能？",
    collection_name="general"
)
```

### 项目隔离示例

```python
# 项目A
service_a = await get_rag_service("project_a")
await service_a.add_text("项目A的知识", "general")

# 项目B
service_b = await get_rag_service("project_b")
await service_b.add_text("项目B的知识", "general")

# 两个项目的数据完全隔离
result_a = await service_a.query("知识", "general")  # 只返回项目A的结果
result_b = await service_b.query("知识", "general")  # 只返回项目B的结果
```

## 📊 与原版本的对比

| 方面 | 原版本 | 重写版本 |
|------|--------|----------|
| **架构** | 重复实现 rag_core 功能 | 薄封装 rag_core |
| **项目隔离** | 不支持 | 完整支持 |
| **代码复杂度** | 高（重复造轮子） | 低（复用现有功能） |
| **维护成本** | 高 | 低 |
| **功能完整性** | 部分功能缺失 | 完整复用 rag_core |
| **API 兼容性** | - | 完全兼容 |

## 🎉 重写收益

1. **避免重复造轮子** - 直接复用 `backend/rag_core` 的成熟功能
2. **项目隔离支持** - 为 AI 测试系统提供多项目知识库管理
3. **代码简化** - 移除重复代码，降低维护成本
4. **功能完整** - 获得 rag_core 的所有功能
5. **向后兼容** - 现有 API 无需修改

## 🔄 迁移指南

现有代码无需修改，重写后的服务完全兼容现有 API 接口。如需使用项目隔离功能，只需在获取服务实例时指定 `project_id`：

```python
# 原来的用法（仍然有效）
from backend.services.rag.rag_service import get_rag_service
rag_service = await get_rag_service()

# 新的项目隔离用法
rag_service = await get_rag_service("my_project")
```
