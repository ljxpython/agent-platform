# MCP (Model Context Protocol) 配置说明

本项目已配置了多个MCP服务器，用于增强Claude Code的功能。

## 已配置的MCP服务器

### 1. Context7 MCP 服务器
- **类型**: HTTP传输
- **URL**: https://mcp.context7.com/mcp
- **功能**: 提供增强的上下文理解和管理能力

### 2. Serena MCP 服务器
- **类型**: 命令行启动
- **功能**: IDE助手，提供智能代码分析和建议
- **启动方式**: 通过uvx从GitHub仓库动态安装和启动

### 3. PromptX MCP 服务器
- **类型**: 命令行启动
- **功能**: 提示工程和优化工具
- **启动方式**: 通过dpml-prompt命令启动

### 4. AutoGen 文档 MCP 服务器
- **类型**: 远程服务
- **功能**: 提供Microsoft AutoGen框架的文档和示例
- **启动方式**: 通过mcp-remote连接GitHub资源

### 5. Memory MCP 服务器
- **包名**: @modelcontextprotocol/server-memory
- **版本**: ^2025.8.4
- **功能**: 提供持久化记忆管理功能

### 6. Sequential Thinking MCP 服务器
- **包名**: @modelcontextprotocol/server-sequential-thinking
- **版本**: ^2025.7.1
- **功能**: 支持序列化思维和推理过程

### 7. MagicUI MCP 服务器
- **类型**: HTTP传输
- **URL**: https://magicui.design/docs/mcp
- **功能**: 提供UI组件和设计模式支持

### 8. Puppeteer MCP 服务器
- **包名**: puppeteer
- **版本**: ^24.16.2
- **功能**: 提供浏览器自动化和网页测试能力

## 配置文件

### .clauderc.json
项目根目录下的`.clauderc.json`文件包含了所有MCP服务器的配置。

### package.json
包含了npm依赖的MCP服务器包和相关脚本。

## 使用方式

### npm脚本命令
```bash
# 启动memory服务器
npm run mcp:memory

# 启动sequential-thinking服务器
npm run mcp:sequential-thinking

# 启动autogen文档服务器
npm run mcp:autogen-docs

# 测试MCP配置
npm run mcp:test
```

### 手动启动命令
```bash
# Memory服务器
npx @modelcontextprotocol/server-memory

# Sequential Thinking服务器
npx @modelcontextprotocol/server-sequential-thinking

# AutoGen文档服务器
npx mcp-remote https://gitmcp.io/microsoft/autogen
```

## 依赖安装

确保所有依赖已正确安装：
```bash
npm install
```

## 注意事项

1. **网络要求**: Context7和MagicUI等HTTP服务器需要稳定的网络连接
2. **系统要求**: Serena服务器需要uvx工具支持
3. **版本兼容**: Puppeteer已更新到最新版本以避免安全警告
4. **本地优先**: 所有包都安装在项目本地，不影响全局环境

## 故障排除

如果某个MCP服务器无法启动：
1. 检查网络连接
2. 确认依赖包已正确安装
3. 查看Claude Code日志获取详细错误信息
4. 尝试手动启动对应的服务器进行调试

## 扩展配置

如需添加新的MCP服务器：
1. 更新`.clauderc.json`配置
2. 如果是npm包，添加到`package.json`依赖中
3. 运行`npm install`安装新依赖
4. 更新本文档说明

---

配置完成后，重启Claude Code以使配置生效。