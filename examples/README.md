# 🤖 Midscene 智能体系统

基于Microsoft AutoGen和Midscene的多智能体UI自动化测试生成系统，支持从UI截图自动生成YAML和Playwright测试脚本。

## 🌟 系统特性

### 🎯 核心功能
- **四智能体协作**: UI分析 → 交互分析 → Midscene生成 → 脚本生成
- **多模态输入**: 支持图片上传和文本需求描述
- **双格式输出**: 自动生成YAML和Playwright测试脚本
- **实时流式**: SSE流式输出，实时显示生成进度
- **智能解析**: 自动提取和下载生成的脚本文件

### 🔧 技术架构
- **后端**: FastAPI + AutoGen + Doubao模型
- **前端**: 原生JavaScript + SSE客户端
- **智能体**: 基于AutoGen的多智能体协作框架
- **AI模型**: 豆包(Doubao)大语言模型支持

## 🚀 快速开始

### 📋 环境要求
- Python 3.8+
- Node.js 16+ (可选，用于前端开发)
- 豆包API密钥

### ⚡ 一键启动
```bash
# 克隆项目
git clone <repository-url>
cd autoui

# 启动所有服务
make start

# 访问前端界面
open http://localhost:8080
```

### 🔧 详细安装
```bash
# 1. 安装Python依赖
cd backend
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑.env文件，添加豆包API密钥

# 3. 启动后端服务
make start-backend

# 4. 启动前端服务
make start-frontend
```

## 📖 使用指南

### 🎮 基本使用流程

1. **上传UI截图**
   - 访问 http://localhost:8080
   - 点击"选择文件"上传UI截图
   - 支持PNG、JPG、JPEG格式

2. **输入测试需求**
   - 在文本框中描述测试需求
   - 例如："点击登录按钮，验证页面跳转"

3. **观察智能体协作**
   - 实时查看四个智能体的分析过程
   - UI分析智能体：分析界面元素
   - 交互分析智能体：分析交互逻辑
   - Midscene生成智能体：生成JSON测试用例
   - 脚本生成智能体：生成YAML和Playwright脚本

4. **下载测试脚本**
   - 点击"下载YAML脚本"获取Midscene格式脚本
   - 点击"下载Playwright脚本"获取TypeScript测试脚本

### 🛠️ Makefile命令

```bash
# 服务管理
make start              # 启动所有服务
make stop               # 停止所有服务
make restart            # 重启所有服务
make status             # 查看服务状态

# 单独服务管理
make start-backend      # 启动后端服务
make start-frontend     # 启动前端服务
make stop-backend       # 停止后端服务
make stop-frontend      # 停止前端服务

# 维护命令
make logs               # 查看后端日志
make clean              # 清理临时文件
make clean-ports        # 安全清理端口占用
make force-clean-ports  # 强制清理端口占用（危险）
```

## 🏗️ 系统架构

### 🤖 智能体架构
```
用户输入 → UI分析智能体 ↘
                        ↓
用户需求 → 交互分析智能体 → Midscene生成智能体 → 脚本生成智能体 → 输出脚本
```

### 📁 目录结构
```
autoui/
├── backend/                 # 后端服务
│   ├── examples/           # 智能体实现
│   │   ├── midscene_agents.py  # 主要智能体逻辑
│   │   └── results/        # 生成结果文件
│   └── conf/               # 配置文件
├── frontend/               # 前端界面
│   ├── index.html         # 主页面
│   ├── app.js             # 前端逻辑
│   └── styles.css         # 样式文件
├── docs/                   # 文档目录
│   ├── fixes/             # 修复文档
│   ├── features/          # 功能文档
│   ├── guides/            # 使用指南
│   └── frontend/          # 前端文档
├── uitest/                # UI测试示例
├── uploads/               # 上传文件存储
├── logs/                  # 日志文件
└── Makefile              # 构建脚本
```

## 🔧 配置说明

### 🌐 服务端口
- **后端API**: http://localhost:8001
- **前端界面**: http://localhost:8080

### 🔑 环境变量
```bash
# 豆包API配置
DOUBAO_API_KEY=your_api_key_here
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# 服务配置
BACKEND_HOST=localhost
BACKEND_PORT=8001
FRONTEND_PORT=8080
```

## 📚 文档索引

### 🔧 修复文档 (docs/fixes/)
- [花括号转义修复](docs/fixes/BRACKET_ESCAPE_FIX_SUMMARY.md)
- [CORS跨域修复](docs/fixes/CORS_FIX_SUMMARY.md)
- [导入语句修复](docs/fixes/FINAL_IMPORT_FIX_SUMMARY.md)
- [Makefile进程管理修复](docs/fixes/MAKEFILE_AND_RESULTS_FIX_SUMMARY.md)
- [Playwright导入修复](docs/fixes/PLAYWRIGHT_IMPORT_FIX_SUMMARY.md)
- [脚本解析修复](docs/fixes/SCRIPT_PARSING_FIX.md)

### 🌟 功能文档 (docs/features/)
- [脚本生成功能](docs/features/SCRIPT_GENERATION_SUMMARY.md)

### 📖 使用指南 (docs/guides/)
- [Makefile使用指南](docs/guides/MAKEFILE_USAGE.md)

### 🎨 前端文档 (docs/frontend/)
- [前端功能总结](docs/frontend/FRONTEND_SUMMARY.md)
- [前端开发指南](docs/frontend/FRONTEND_README.md)

## 🛡️ 安全特性

### 🔒 进程管理安全
- **智能进程识别**: 只杀掉确认是我们服务的进程
- **安全端口清理**: 不会误杀微信等其他应用程序
- **分级清理选项**: 提供安全和强制两种清理方式

### 🗂️ 文件管理
- **专门目录**: 结果文件统一保存在results目录
- **自动清理**: 支持一键清理临时文件和日志
- **路径管理**: 统一的文件路径管理函数

## 🐛 故障排除

### 常见问题

#### 1. 端口占用
```bash
# 查看端口占用
make status

# 安全清理端口
make clean-ports

# 强制清理端口（危险）
make force-clean-ports
```

#### 2. 服务启动失败
```bash
# 查看日志
make logs

# 重启服务
make restart
```

#### 3. 脚本下载失败
- 检查浏览器控制台错误信息
- 访问测试页面: http://localhost:8080/test_script_parsing.html
- 查看后端日志确认脚本生成状态

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Microsoft AutoGen](https://github.com/microsoft/autogen) - 多智能体框架
- [Midscene](https://github.com/web-infra-dev/midscene) - UI自动化测试框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python Web框架
- [豆包大模型](https://www.volcengine.com/product/doubao) - AI能力支持

---

🎉 **开始您的UI自动化测试之旅吧！** 如有问题，请查看文档或提交Issue。
