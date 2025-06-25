# 项目文档中心

## 📚 文档导航

欢迎来到AI驱动测试平台的文档中心！这里包含了项目的完整技术文档、开发指南和工作记录。

### 🎯 快速导航

#### 🏗️ 架构设计
- **[系统架构](architecture/SYSTEM_ARCHITECTURE.md)** - 整体系统架构设计
- **[后端架构](architecture/BACKEND_ARCHITECTURE.md)** - 后端服务架构
- **[前端架构](architecture/FRONTEND_ARCHITECTURE.md)** - 前端应用架构
- **[AI核心框架](architecture/AI_CORE_FRAMEWORK.md)** - AI智能体框架设计
- **[AI模块](architecture/AI_MODULES.md)** - AI智能体模块设计
- **[用户系统](architecture/USER_SYSTEM.md)** - 用户管理系统架构

#### 🛠️ 开发指南
- **[开发环境搭建](development/DEVELOPMENT_SETUP.md)** - 开发环境配置指南
- **[前后端集成](development/FRONTEND_BACKEND_INTEGRATION.md)** - 前后端集成开发
- **[日志系统](development/LOGGING_GUIDE.md)** - 日志系统使用指南
- **[AI核心框架指南](development/AI_CORE_FRAMEWORK_GUIDE.md)** - AI核心开发指南
- **[Midscene集成](development/MIDSCENE_INTEGRATION.md)** - Midscene UI测试集成
- **[Markdown渲染](development/MARKDOWN_RENDERER.md)** - Markdown组件开发

#### 🗄️ 数据库
- **[数据库设计](database/DATABASE_DESIGN.md)** - 数据库表结构设计
- **[数据初始化](database/DATA_INITIALIZATION.md)** - 初始数据配置
- **[迁移指南](database/MIGRATION_GUIDE.md)** - 数据库迁移操作

#### 🔒 安全系统
- **[JWT认证](security/JWT_AUTHENTICATION.md)** - JWT认证实现
- **[权限系统](security/PERMISSION_SYSTEM.md)** - RBAC权限控制

#### 🎨 UI设计
- **[UI设计指南](ui-design/UI_DESIGN_GUIDE.md)** - UI设计规范
- **[导航系统](ui-design/NAVIGATION_SYSTEM.md)** - 导航组件设计
- **[测试用例页面](ui-design/TESTCASE_PAGE_OPTIMIZATION.md)** - 测试用例页面优化
- **[UI优化记录](ui-design/UI_OPTIMIZATION_RECORD.md)** - UI优化历程

#### 🔧 故障排除
- **[AutoGen修复](troubleshooting/AUTOGEN_FIXES.md)** - AutoGen相关问题修复
- **[权限问题](troubleshooting/PERMISSION_TROUBLESHOOTING.md)** - 权限系统问题排查
- **[进程管理](troubleshooting/PROCESS_MANAGEMENT.md)** - 后端进程管理
- **[后端进程管理](troubleshooting/BACKEND_PROCESS_MANAGEMENT.md)** - 后端服务进程管理

#### ⚡ 性能优化
- **[代码简化](optimization/CODE_SIMPLIFICATION.md)** - 代码重构和简化
- **[文件上传集成](optimization/FILE_UPLOAD_INTEGRATION.md)** - 文件上传功能优化
- **[队列流式简化](optimization/QUEUE_STREAMING_SIMPLIFICATION.md)** - 消息队列优化
- **[测试用例API优化](optimization/TESTCASE_API_QUEUE_OPTIMIZATION.md)** - 测试用例服务优化

#### 🔧 环境配置
- **[Makefile指南](setup/MAKEFILE_GUIDE.md)** - 项目自动化脚本
- **[工厂模式](setup/FACTORY_PATTERN.md)** - 设计模式应用

#### 🎯 项目概览
- **[项目概述](overview/PROJECT_OVERVIEW.md)** - 项目整体介绍

#### 📋 工作记录
- **[工作总结](work/MYWORK.md)** - 项目开发工作记录
- **[AI对话开发](work/01-AIchat.md)** - AI对话功能开发记录
- **[智能体架构评审](work/02-智能体架构及用例评审v1版本.md)** - 架构设计评审
- **[用例生成优化](work/03-用例生成智能体及文件解析优化.md)** - 测试用例生成优化
- **[UI智能体搭建](work/04-UI智能体搭建.md)** - UI测试智能体开发
- **[架构优化](work/05-架构优化.md)** - 系统架构优化记录
- **[UI及RAG系统](work/06-UI及RAG系统初步搭建.md)** - UI和RAG系统开发

### 🚀 项目概览

本项目是一个基于AI的自动化测试平台，主要功能包括：

- **AI对话系统** - 基于AutoGen的多智能体对话
- **测试用例生成** - AI驱动的测试用例自动生成
- **UI脚本生成** - Midscene智能UI测试脚本生成
- **RAG知识库** - 企业级RAG检索增强生成系统
- **权限管理** - 企业级RBAC权限控制系统

### 🛠️ 技术栈

- **后端**: FastAPI + Tortoise ORM + PostgreSQL
- **前端**: React 18 + TypeScript + Ant Design Pro
- **AI框架**: AutoGen 0.5.7
- **RAG系统**: LlamaIndex + Milvus + DeepSeek
- **认证**: JWT + OAuth2
- **部署**: Docker + Docker Compose

### 📞 获取帮助

如果您在使用过程中遇到问题：

1. 查看相关的技术文档
2. 检查故障排除指南
3. 查看工作记录了解开发历程
4. 参考架构设计文档理解系统设计

---

*文档版本: v1.0.0 | 最后更新: 2024-06-25*
