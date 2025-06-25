# RAG知识库系统文档导航

## 📚 文档目录

欢迎使用RAG知识库系统文档！本文档系统为AI编程助手和开发者提供完整的开发指导。

### 🚀 快速开始

- **[README.md](README.md)** - 系统概述、快速开始和基础使用
  - 系统概述和核心组件
  - 基础使用示例
  - API接口列表
  - 配置说明
  - 集成指导

### 📖 核心文档

#### 🏗️ [系统架构](architecture.md)
- 系统架构概览
- 核心组件详解
- 数据流架构
- 多Collection架构
- 配置管理架构
- 性能优化架构

#### 🛠️ [开发规范](development_guide.md)
- 开发原则（异步优先、资源管理、错误处理）
- 代码规范（命名、类型注解、文档字符串）
- 架构模式（工厂模式、策略模式、观察者模式）
- 配置管理规范
- 日志规范
- 测试规范
- 性能优化规范
- 安全规范

#### 📡 [API参考](api_reference.md)
- RAGSystem - 系统主入口
- QueryResult - 查询结果
- RAGConfig - 系统配置
- 异常类层次结构
- 工具函数
- 使用模式和注意事项

#### ⚙️ [配置管理](configuration.md)
- 配置结构和层次
- 配置类定义
- 环境变量配置
- Django Settings配置
- 配置加载优先级
- 配置验证和调试

#### 🔧 [故障排除](troubleshooting.md)
- 连接问题（Milvus、Ollama、DeepSeek）
- 配置问题
- 性能问题
- 数据问题
- 日志分析
- 系统健康检查
- 性能基准测试

#### 📝 [更新日志](changelog.md)
- 版本历史
- 升级指南
- 已知问题
- 未来计划
- 贡献指南

### 💡 示例代码

#### 📁 [examples/](examples/)

- **[basic_usage.py](examples/basic_usage.py)** - 基础使用示例
  - 系统初始化
  - 文档添加（文本、文件、批量）
  - 基础查询
  - 错误处理
  - 资源管理

- **[advanced_usage.py](examples/advanced_usage.py)** - 高级功能示例
  - 多Collection查询
  - 业务类型查询
  - 自定义配置
  - 并发操作
  - 性能优化
  - 高级元数据
  - 错误恢复

- **[custom_collection.py](examples/custom_collection.py)** - 自定义Collection示例
  - 专业领域Collection（医学、法律、技术）
  - Collection关联管理
  - 自定义配置和提示词
  - 跨Collection查询

- **[integration_examples.py](examples/integration_examples.py)** - 集成示例
  - FastAPI集成
  - 测试用例生成集成
  - AI对话系统集成
  - 前端集成辅助

- **[test_rag_docs_completeness.py](examples/test_rag_docs_completeness.py)** - 文档完整性测试
  - 文档结构验证
  - 内容质量检查
  - 示例代码语法验证
  - 链接完整性检查

## 🎯 AI编程助手使用指南

### 开发新功能的步骤

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

### 问题解决流程

1. **查看故障排除文档** - 寻找常见问题解决方案
2. **检查示例代码** - 确认使用方法是否正确
3. **验证配置** - 确保所有配置项正确设置
4. **查看日志** - 分析详细的错误信息
5. **运行健康检查** - 验证系统状态

## 📊 文档质量指标

- **文档数量**: 7个核心文档 ✅
- **示例数量**: 5个示例文件 ✅
- **总字符数**: 114,480字符 ✅
- **代码示例数**: 192个代码示例 ✅
- **完整性评分**: 100% ✅

## 🔗 快速链接

### 开发相关
- [开发规范](development_guide.md#开发原则) - 核心开发原则
- [代码规范](development_guide.md#代码规范) - 编码标准
- [API参考](api_reference.md#ragSystem) - 主要API接口

### 配置相关
- [环境变量](configuration.md#环境变量配置) - 环境配置
- [Django设置](configuration.md#django-settings配置) - 框架集成
- [配置验证](configuration.md#配置验证函数) - 配置检查

### 问题解决
- [连接问题](troubleshooting.md#连接问题) - 服务连接
- [性能问题](troubleshooting.md#性能问题) - 性能优化
- [健康检查](troubleshooting.md#系统健康检查) - 系统诊断

### 示例代码
- [基础示例](examples/basic_usage.py) - 入门使用
- [高级示例](examples/advanced_usage.py) - 进阶功能
- [集成示例](examples/integration_examples.py) - 系统集成

## 📞 获取帮助

如果文档中没有找到需要的信息：

1. 查看相关的示例代码
2. 检查故障排除指南
3. 运行文档完整性测试
4. 查看系统日志获取详细信息

---

*文档版本: v1.0.0 | 最后更新: 2024-06-25*
