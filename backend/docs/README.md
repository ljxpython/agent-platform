# Backend开发文档

## 📚 文档导航

本目录包含后端系统的完整开发文档，按功能模块分类组织，为开发者和AI编程助手提供全面的技术指导。

### 📁 文档结构

```
docs/
├── README.md                    # 本文件 - 文档导航
├── api/                        # API开发相关
│   ├── api_development.md      # API开发规范
│   ├── response_handling.md    # 响应处理规范
│   └── sse_protocols.md        # SSE协议规范
├── development/                # 开发规范相关
│   ├── controller_patterns.md  # 控制器模式
│   ├── model_definitions.md    # 模型定义规范
│   ├── schema_validation.md    # 参数校验规范
│   └── best_practices.md       # 最佳实践指南
├── database/                   # 数据库相关
│   └── database_operations.md  # 数据库操作指南
├── core/                       # 核心架构
│   └── architecture.md         # 系统架构设计
└── examples/                   # 示例代码
    ├── crud_examples.py        # CRUD操作示例
    └── api_examples.py         # API开发示例
```

## 🚀 快速开始

### 新手入门路径

1. **了解系统架构** → [系统架构设计](core/architecture.md)
2. **学习开发规范** → [最佳实践指南](development/best_practices.md)
3. **掌握API开发** → [API开发规范](api/api_development.md)
4. **学习数据库操作** → [数据库操作指南](database/database_operations.md)
5. **参考示例代码** → [示例代码](examples/)

### AI编程助手使用指南

1. **架构理解** - 先阅读[架构文档](core/architecture.md)了解系统设计
2. **开发规范** - 遵循[开发规范](development/)中的标准
3. **API设计** - 参考[API文档](api/)进行接口开发
4. **代码实现** - 使用[示例代码](examples/)作为参考
5. **问题解决** - 查看[最佳实践](development/best_practices.md)

## 📡 API开发

### [API开发规范](api/api_development.md)
- RESTful API设计原则
- 参数校验和响应格式
- 权限控制和版本管理
- 错误处理和状态码规范

### [响应处理规范](api/response_handling.md)
- `backend.api_core.response`模块使用
- 统一响应格式标准
- 异常处理和错误响应
- RAG专用响应工具

### [SSE协议规范](api/sse_protocols.md)
- Server-Sent Events实现标准
- AI对话和RAG查询的SSE应用
- 消息队列集成和前端对接
- 性能优化和错误处理

## 🛠️ 开发规范

### [控制器模式](development/controller_patterns.md)
- CRUD基类使用方法
- 控制器代码复用模式
- 混入模式和继承策略
- 专用控制器设计范例

### [模型定义规范](development/model_definitions.md)
- 数据模型定义标准
- 基础模型继承和复用
- 关系映射和字段约束
- 性能优化和索引设计

### [参数校验规范](development/schema_validation.md)
- Pydantic Schema设计模式
- 复杂验证器和嵌套Schema
- 参数校验最佳实践
- 错误处理和性能优化

### [最佳实践指南](development/best_practices.md)
- 编码规范和命名约定
- 架构设计最佳实践
- 性能优化和安全考虑
- 测试和部署指南

## 🗄️ 数据库

### [数据库操作指南](database/database_operations.md)
- Tortoise ORM使用方法
- CRUD操作和复杂查询
- 事务处理和性能优化
- 原生SQL和批量操作

## 🏗️ 核心架构

### [系统架构设计](core/architecture.md)
- 分层架构详细说明
- 目录结构和组件职责
- 数据流和安全架构
- 部署和监控架构

## 💡 示例代码

### [CRUD操作示例](examples/crud_examples.py)
- 基础和高级CRUD控制器
- 批量操作和复杂查询
- 事务处理和性能优化
- 错误处理和最佳实践

### [API开发示例](examples/api_examples.py)
- 完整的RESTful API实现
- 权限控制和文件上传
- 搜索、统计和导出功能
- 异步任务和版本控制

## 🎯 核心技术栈

### 后端框架
- **Web框架**: FastAPI
- **ORM**: Tortoise ORM
- **数据库**: PostgreSQL (主)、Redis (缓存)
- **任务队列**: Celery + Redis

### AI核心
- **AI框架**: AutoGen 0.5.7
- **RAG系统**: LlamaIndex + Milvus + DeepSeek
- **向量数据库**: Milvus
- **嵌入模型**: Ollama (nomic-embed-text)

### 开发工具
- **日志**: Loguru
- **配置**: Pydantic Settings
- **测试**: Pytest
- **文档**: FastAPI自动生成

## 🔧 开发工具

### 核心模块
- **CRUD基类**: `backend.api_core.crud.CRUDBase`
- **响应处理**: `backend.api_core.response.response`
- **异常处理**: `backend.api_core.exceptions`
- **依赖注入**: `backend.api_core.deps`

### AI核心模块
- **AI智能体**: `backend.ai_core.agents`
- **消息队列**: `backend.ai_core.message_queue`
- **RAG系统**: `backend.rag_core.rag_system`

## 📞 获取帮助

### 文档使用指南

1. **按需查阅** - 根据开发任务查看相应模块文档
2. **示例优先** - 优先参考示例代码理解使用方法
3. **规范遵循** - 严格按照开发规范进行编码
4. **架构理解** - 深入理解系统架构设计原则

### 常见问题解决

1. **API开发问题** → 查看[API开发规范](api/api_development.md)
2. **数据库操作问题** → 查看[数据库操作指南](database/database_operations.md)
3. **代码规范问题** → 查看[最佳实践指南](development/best_practices.md)
4. **架构设计问题** → 查看[系统架构设计](core/architecture.md)

## 🔄 文档维护

### 更新原则
- **及时更新** - 代码变更时同步更新文档
- **示例完整** - 确保示例代码可执行
- **规范一致** - 保持文档间的一致性
- **版本同步** - 文档版本与代码版本保持同步

### 贡献指南
- 发现文档问题请及时反馈
- 新增功能需要同步更新文档
- 示例代码需要经过测试验证
- 遵循文档编写规范

---

*文档版本: v1.0.0 | 最后更新: 2024-06-25*
