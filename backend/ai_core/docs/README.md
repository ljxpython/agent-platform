# AI核心框架文档中心

[← 返回AI核心框架](../) | [📖 文档中心](../../../docs/) | [📋 导航索引](../../../docs/DOCS_INDEX.md)

## 🎯 文档概述

本文档中心提供了AI核心框架的完整开发指南，涵盖智能体开发、运行时管理、消息队列、内存管理、SSE流式输出、用户反馈等所有核心功能的详细使用说明。

## 📚 文档目录

### 🚀 核心指南

#### [AI核心框架开发指南](./AI_CORE_DEVELOPMENT_GUIDE.md)
- **内容**：框架概述、核心组件详解、基本使用方法
- **适用对象**：所有开发者
- **重点内容**：
  - LLM客户端管理器使用
  - 智能体工厂基本操作
  - 内存管理基础功能
  - 消息队列基本用法
  - 运行时管理入门

#### [测试用例生成服务详细实现案例](./TESTCASE_SERVICE_EXAMPLE.md)
- **内容**：完整的业务实现案例，展示框架的实际应用
- **适用对象**：业务开发者、架构师
- **重点内容**：
  - 智能体实现详解（需求分析、测试用例生成、优化、最终化）
  - 团队协作模式（RoundRobinGroupChat）
  - 运行时管理实现
  - 消息队列在业务中的应用
  - 内存管理的业务使用
  - API接口实现
  - 完整业务流程

### 🌊 技术深入

#### [SSE流式输出与用户反馈完整指南](./SSE_AND_FEEDBACK_GUIDE.md)
- **内容**：SSE技术详解和用户反馈机制实现
- **适用对象**：前后端开发者
- **重点内容**：
  - SSE技术原理和实现
  - 消息队列到SSE的转换
  - API接口层SSE实现
  - 前端SSE接收和解析
  - 用户反馈队列系统
  - 智能体中的用户交互
  - 完整交互流程
  - 高级特性和性能优化

#### [AutoGen运行时与业务封装指南](./AUTOGEN_RUNTIME_GUIDE.md)
- **内容**：AutoGen 0.5.7运行时系统和业务封装模式
- **适用对象**：高级开发者、架构师
- **重点内容**：
  - AutoGen运行时架构
  - 智能体注册与管理
  - 消息发布与订阅
  - 业务类封装模式
  - 生命周期管理
  - 状态管理
  - 高级特性和最佳实践

#### [框架集成与最佳实践指南](./FRAMEWORK_INTEGRATION_GUIDE.md)
- **内容**：框架与业务系统集成的最佳实践
- **适用对象**：架构师、技术负责人
- **重点内容**：
  - 框架集成架构
  - 通用组件与业务结合
  - 业务服务开发模式
  - API接口集成模式
  - 性能优化策略
  - 错误处理与监控
  - 最佳实践总结

## 🎯 快速导航

### 按角色导航

#### 🆕 新手开发者
1. 先阅读 [AI核心框架开发指南](./AI_CORE_DEVELOPMENT_GUIDE.md) 了解基础概念
2. 参考 [测试用例生成服务详细实现案例](./TESTCASE_SERVICE_EXAMPLE.md) 学习实际应用
3. 查看 [SSE流式输出与用户反馈完整指南](./SSE_AND_FEEDBACK_GUIDE.md) 了解前后端交互

#### 🔧 业务开发者
1. 重点阅读 [测试用例生成服务详细实现案例](./TESTCASE_SERVICE_EXAMPLE.md)
2. 参考 [框架集成与最佳实践指南](./FRAMEWORK_INTEGRATION_GUIDE.md) 的业务服务开发模式
3. 查看 [SSE流式输出与用户反馈完整指南](./SSE_AND_FEEDBACK_GUIDE.md) 实现用户交互

#### 🏗️ 架构师
1. 全面阅读 [框架集成与最佳实践指南](./FRAMEWORK_INTEGRATION_GUIDE.md)
2. 深入了解 [AutoGen运行时与业务封装指南](./AUTOGEN_RUNTIME_GUIDE.md)
3. 参考 [测试用例生成服务详细实现案例](./TESTCASE_SERVICE_EXAMPLE.md) 的架构设计

#### 🎨 前端开发者
1. 重点阅读 [SSE流式输出与用户反馈完整指南](./SSE_AND_FEEDBACK_GUIDE.md) 的前端部分
2. 参考 [测试用例生成服务详细实现案例](./TESTCASE_SERVICE_EXAMPLE.md) 的API接口
3. 查看 [框架集成与最佳实践指南](./FRAMEWORK_INTEGRATION_GUIDE.md) 的API集成模式

### 按功能导航

#### 🤖 智能体开发
- [智能体工厂使用](./AI_CORE_DEVELOPMENT_GUIDE.md#2-智能体工厂-factorypy)
- [智能体实现详解](./TESTCASE_SERVICE_EXAMPLE.md#🤖-智能体实现详解)
- [智能体注册与管理](./AUTOGEN_RUNTIME_GUIDE.md#🤖-智能体注册与管理)
- [智能体封装模式](./AUTOGEN_RUNTIME_GUIDE.md#3-智能体封装)

#### 📡 消息队列
- [消息队列基本使用](./AI_CORE_DEVELOPMENT_GUIDE.md#4-消息队列管理-message_queuepy)
- [消息队列详细应用](./TESTCASE_SERVICE_EXAMPLE.md#📡-消息队列使用详解)
- [业务消息类型定义](./FRAMEWORK_INTEGRATION_GUIDE.md#2-消息队列的业务集成)

#### 🌊 SSE流式输出
- [SSE技术原理](./SSE_AND_FEEDBACK_GUIDE.md#🌊-sse流式输出技术)
- [API接口SSE实现](./SSE_AND_FEEDBACK_GUIDE.md#3-api接口层sse实现)
- [前端SSE接收](./SSE_AND_FEEDBACK_GUIDE.md#4-前端sse接收实现)

#### 💬 用户反馈
- [反馈队列系统](./SSE_AND_FEEDBACK_GUIDE.md#💬-用户反馈机制)
- [智能体用户交互](./SSE_AND_FEEDBACK_GUIDE.md#2-智能体中的用户交互实现)
- [API反馈处理](./SSE_AND_FEEDBACK_GUIDE.md#3-api接口层反馈处理)

#### 🧠 内存管理
- [内存管理基础](./AI_CORE_DEVELOPMENT_GUIDE.md#3-内存管理器-memorypy)
- [内存业务应用](./TESTCASE_SERVICE_EXAMPLE.md#🧠-内存管理使用)
- [业务数据存储](./FRAMEWORK_INTEGRATION_GUIDE.md#3-内存管理的业务应用)

#### 🏗️ 运行时管理
- [运行时基础](./AI_CORE_DEVELOPMENT_GUIDE.md#5-运行时管理器-runtimepy)
- [运行时实现](./TESTCASE_SERVICE_EXAMPLE.md#🏗️-运行时管理实现)
- [AutoGen运行时详解](./AUTOGEN_RUNTIME_GUIDE.md#🏗️-autogen运行时架构)

## 🔗 相关资源

### 官方文档
- [AutoGen 0.5.7 官方文档](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/index.html)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Pydantic 官方文档](https://docs.pydantic.dev/)

### 项目文档
- [后端架构文档](../../../docs/architecture/BACKEND_ARCHITECTURE.md)
- [API文档](../../../docs/api/)
- [部署文档](../../../docs/deployment/)

### 示例代码
- [测试用例服务实现](../../services/testcase/)
- [API接口实现](../../api/v1/testcase.py)
- [优化案例参考](../../../examples/ai_core_optimization_case/)

## 🚀 快速开始

### 1. 环境准备
```bash
# 安装依赖
poetry install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置模型API密钥
```

### 2. 基础使用
```python
from backend.ai_core import (
    create_assistant_agent,
    put_message_to_queue,
    get_streaming_sse_messages_from_queue
)

# 创建智能体
agent = await create_assistant_agent(
    name="my_agent",
    system_message="你是一个助手",
    conversation_id="conv_123",
    auto_memory=True,
    auto_context=True
)

# 发送消息到队列
await put_message_to_queue("conv_123", "处理结果")

# 获取SSE流式输出
async for sse_message in get_streaming_sse_messages_from_queue("conv_123"):
    print(sse_message)
```

### 3. 完整示例
参考 [测试用例生成服务详细实现案例](./TESTCASE_SERVICE_EXAMPLE.md) 了解完整的业务实现。

## 📞 技术支持

### 问题排查
1. **查看日志**：框架使用loguru记录详细日志
2. **检查配置**：验证模型配置是否正确
3. **监控状态**：查看运行时和队列状态
4. **参考文档**：查阅相关功能文档

### 常见问题
- **模型配置问题**：参考 [LLM客户端管理](./AI_CORE_DEVELOPMENT_GUIDE.md#1-llm客户端管理器-llmpy)
- **SSE解析错误**：参考 [前端SSE接收](./SSE_AND_FEEDBACK_GUIDE.md#4-前端sse接收实现)
- **智能体注册失败**：参考 [智能体注册](./AUTOGEN_RUNTIME_GUIDE.md#🤖-智能体注册与管理)
- **内存管理问题**：参考 [内存管理](./AI_CORE_DEVELOPMENT_GUIDE.md#3-内存管理器-memorypy)

### 联系方式
- 查看项目文档：[文档中心](../../../docs/)
- 提交Issue：项目仓库Issues页面
- 技术讨论：项目讨论区

---

**最后更新时间**：2025-06-23
**文档版本**：v1.0
**框架版本**：基于AutoGen 0.5.7
