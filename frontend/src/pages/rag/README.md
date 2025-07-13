# RAG 前端功能增强

## 🎯 功能概述

基于 `backend/rag_core` 的功能，为前端创建了对应的展示和功能调用页面，支持项目隔离和 Milvus 向量数据库集成。

## 📁 新增页面

### 1. CollectionManagementEnhanced.tsx

**功能特点：**
- **双数据源展示**：同时显示 SQLite 数据库和 Milvus 向量数据库中的 Collections
- **项目隔离**：支持多项目的 Collection 管理
- **Milvus 集成**：直接查询 Milvus 中实际存在的 Collections
- **同步功能**：一键从 Milvus 同步 Collections 到 SQLite

**主要功能：**
```typescript
// 查询 SQLite 中的 Collections
GET /api/v1/rag/collections/?project_id=${projectId}

// 查询 Milvus 中的 Collections
GET /api/v1/rag/collections/milvus?project_id=${projectId}

// 从 Milvus 同步到 SQLite
POST /api/v1/rag/collections/sync-from-milvus?project_id=${projectId}

// 获取 Milvus Collection 详细信息
GET /api/v1/rag/collections/${collection_name}/milvus-info?project_id=${projectId}
```

**界面特色：**
- 标签页切换：SQLite 数据库 vs Milvus 向量数据库
- 项目选择器：支持多项目切换
- 同步按钮：将 Milvus 中的 Collections 同步到 SQLite
- 详细信息模态框：显示 Collection 的 Schema、索引等信息

### 2. RAGCoreFeatures.tsx

**功能特点：**
- **完整 RAG 工作流**：展示 `backend/rag_core` 的所有核心功能
- **实时交互**：支持查询、文档添加、聊天等操作
- **项目隔离**：所有操作都支持项目级别隔离
- **系统监控**：实时显示系统统计信息

**主要功能模块：**

#### RAG 查询
```typescript
// 执行 RAG 查询
POST /api/v1/rag/query?project_id=${projectId}
{
  "question": "用户问题",
  "collection_name": "目标Collection"
}
```

#### 文档添加
```typescript
// 添加文本到知识库
POST /api/v1/rag/documents/add-text?project_id=${projectId}
{
  "text": "文本内容",
  "collection_name": "目标Collection",
  "metadata": {"source": "manual"}
}
```

#### RAG 聊天
```typescript
// RAG 聊天接口
POST /api/v1/rag/chat?project_id=${projectId}
{
  "message": "聊天消息",
  "collection_name": "目标Collection"
}
```

#### 系统统计
```typescript
// 获取系统统计信息
GET /api/v1/rag/system/stats?project_id=${projectId}
```

### 3. DocumentManagementEnhanced.tsx

**功能特点：**
- **文件管理**：支持文件上传和文本添加
- **MD5 重复检测**：避免重复上传相同文件
- **项目隔离**：文件按项目隔离管理
- **统计信息**：显示各 Collection 的文档统计

**主要功能：**

#### 文件上传
```typescript
// 文件上传
POST /api/v1/rag/documents/upload?project_id=${projectId}&collection_name=${collection}
```

#### 文件列表
```typescript
// 获取 Collection 中的文件
GET /api/v1/rag/documents/files/${collection}?project_id=${projectId}
```

#### 文档统计
```typescript
// 获取文档统计信息
GET /api/v1/rag/documents/stats?project_id=${projectId}
```

## 🔧 项目隔离机制

### 前端实现

所有页面都支持项目选择器：
```typescript
const [projectId, setProjectId] = useState<string>('default');

// 项目选择器组件
<Select value={projectId} onChange={setProjectId}>
  <Option value="default">默认项目</Option>
  <Option value="project1">项目1</Option>
  <Option value="project2">项目2</Option>
</Select>
```

### API 调用

所有 API 调用都包含 `project_id` 参数：
```typescript
const response = await fetch(`/api/endpoint?project_id=${projectId}`);
```

## 🌟 核心特性

### 1. Milvus 集成

**实时查询 Milvus：**
- 直接查询 Milvus 向量数据库中实际存在的 Collections
- 显示 Collection 的详细信息（Schema、索引、实体数量等）
- 支持从 Milvus 同步 Collections 到 SQLite

**同步机制：**
- 一键同步：将 Milvus 中的 Collections 同步到 SQLite 数据库
- 智能过滤：根据项目 ID 过滤相关的 Collections
- 状态提示：显示同步进度和结果

### 2. 项目隔离

**多项目支持：**
- 每个项目有独立的知识库空间
- Collection 命名规则：`{project_id}_{collection_name}`
- 文件和文档按项目隔离存储

**用户体验：**
- 项目选择器：方便切换不同项目
- 数据隔离：不同项目的数据完全分离
- 统计信息：按项目显示统计数据

### 3. 完整 RAG 工作流

**端到端功能：**
- 文档上传 → 向量化 → 存储 → 查询 → 生成答案
- 支持文件上传和文本直接添加
- 实时查询和聊天功能
- 系统监控和统计信息

## 📊 界面设计

### 设计风格
- **Ant Design Pro 风格**：统一的设计语言
- **Gemini 风格 UI**：简洁现代的界面
- **浅色主题**：清爽的视觉体验

### 交互特性
- **标签页切换**：不同功能模块的清晰分离
- **实时反馈**：操作结果的即时提示
- **响应式设计**：适配不同屏幕尺寸
- **加载状态**：清晰的加载和进度提示

## 🚀 使用指南

### 1. Collection 管理

1. 选择项目
2. 切换到 "Milvus向量数据库" 标签页
3. 查看 Milvus 中实际存在的 Collections
4. 点击 "同步到SQLite" 按钮同步数据
5. 切换到 "SQLite数据库" 标签页查看同步结果

### 2. RAG 功能测试

1. 进入 "RAG核心功能" 页面
2. 选择项目和 Collection
3. 在 "RAG查询" 标签页输入问题进行查询
4. 在 "文档添加" 标签页添加新的文本内容
5. 在 "RAG聊天" 标签页进行对话测试

### 3. 文档管理

1. 进入 "文档管理" 页面
2. 选择项目和 Collection
3. 上传文件或添加文本
4. 查看文件列表和统计信息
5. 管理文档的生命周期

## 🔄 API 集成

### 新增 API 端点

```typescript
// Milvus Collections 查询
GET /api/v1/rag/collections/milvus

// Milvus 同步
POST /api/v1/rag/collections/sync-from-milvus

// Milvus Collection 详情
GET /api/v1/rag/collections/{name}/milvus-info

// RAG 查询
POST /api/v1/rag/query

// RAG 聊天
POST /api/v1/rag/chat

// 系统统计
GET /api/v1/rag/system/stats

// 文档统计
GET /api/v1/rag/documents/stats
```

### 项目隔离参数

所有 API 都支持 `project_id` 查询参数：
```
?project_id=default  // 默认项目
?project_id=project1 // 项目1
```

## 🎉 功能亮点

1. **真实数据展示**：直接查询 Milvus 向量数据库，显示真实存在的 Collections
2. **一键同步**：将 Milvus 中的 Collections 同步到 SQLite，保持数据一致性
3. **项目隔离**：完整的多项目支持，数据完全隔离
4. **完整工作流**：从文档上传到查询生成的完整 RAG 流程
5. **实时交互**：支持实时查询、聊天和文档管理
6. **系统监控**：详细的统计信息和系统状态监控

这些增强功能为 AI 测试系统提供了完整的 RAG 知识库管理能力，支持多项目隔离和 Milvus 向量数据库的深度集成。
