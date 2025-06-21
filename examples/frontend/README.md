# Midscene 智能体系统 - 前端界面

基于流式上传接口的现代化Web界面，用于Midscene.js自动化测试脚本生成。

## 🌟 特性

### 核心功能
- **流式实时分析**: 上传图片后立即获得实时分析进度
- **多文件上传**: 支持拖拽上传多张UI截图
- **三智能体协作**: 实时显示UI分析、交互分析、Midscene生成三个智能体的工作状态
- **响应式设计**: 适配桌面端和移动端设备

### 用户体验
- **实时进度**: 可视化进度条和状态指示器
- **流式输出**: AI生成内容实时显示，无需等待
- **错误处理**: 完善的错误提示和重试机制
- **结果管理**: 支持下载分析结果和复制生成的脚本

## 📁 文件结构

```
frontend/
├── index.html          # 主页面
├── styles.css          # 样式文件
├── app.js             # 应用逻辑
├── config.js          # 配置文件
└── README.md          # 说明文档
```

## 🚀 快速开始

### 1. 启动后端服务

```bash
cd backend/examples
python midscene_agents.py
```

后端服务将在 `http://localhost:8001` 启动。

### 2. 启动前端服务

#### 方法一：使用Python内置服务器
```bash
cd frontend
python -m http.server 8080
```

#### 方法二：使用Node.js服务器
```bash
cd frontend
npx serve -p 8080
```

#### 方法三：使用Live Server (VS Code扩展)
在VS Code中安装Live Server扩展，右键点击`index.html`选择"Open with Live Server"。

### 3. 访问应用

打开浏览器访问 `http://localhost:8080`

## 🎯 使用指南

### 基本流程

1. **输入用户ID**: 系统会自动生成唯一ID，也可手动修改
2. **上传图片**:
   - 点击上传区域选择文件
   - 或直接拖拽图片到上传区域
   - 支持多张图片同时上传
3. **描述需求**: 详细描述测试需求和期望的交互流程
4. **开始分析**: 点击"开始分析"按钮
5. **实时监控**: 观察三个智能体的实时工作进度
6. **获取结果**: 分析完成后可下载结果或复制脚本

### 界面说明

#### 上传区域
- **用户ID**: 用于标识分析任务的唯一标识符
- **文件上传**: 支持JPG、PNG、GIF、WebP格式，最大10MB
- **需求描述**: 详细描述测试场景和期望的用户交互流程

#### 分析区域
- **进度条**: 显示整体分析进度
- **系统日志**: 记录分析过程中的关键事件
- **智能体卡片**: 实时显示每个智能体的工作状态和输出内容

#### 结果区域
- **下载结果**: 下载包含所有分析结果的JSON文件
- **复制脚本**: 将生成的Midscene.js脚本复制到剪贴板
- **新建分析**: 重置界面开始新的分析任务

## 🔧 技术实现

### 核心技术
- **原生JavaScript**: 无框架依赖，轻量级实现
- **Fetch API**: 处理文件上传和流式响应
- **Server-Sent Events**: 实时接收后端推送的分析进度
- **CSS Grid/Flexbox**: 现代化响应式布局
- **Web APIs**: 文件处理、剪贴板操作等

### 流式处理
```javascript
// 处理流式响应
async handleStreamingResponse(response) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        // 处理SSE格式的数据
        this.processSSEChunk(chunk);
    }
}
```

### 消息处理
系统支持以下消息类型：
- `system_start`: 系统开始工作
- `agent_start`: 智能体开始工作
- `stream_chunk`: 流式内容块
- `agent_complete`: 智能体完成工作
- `system_complete`: 系统完成所有工作
- `*_error`: 各种错误消息

## 🎨 界面设计

### 设计理念
- **现代化**: 使用渐变背景和圆角设计
- **直观性**: 清晰的视觉层次和状态指示
- **响应式**: 适配各种屏幕尺寸
- **可访问性**: 良好的对比度和键盘导航支持

### 颜色方案
- **主色调**: 蓝紫渐变 (#667eea → #764ba2)
- **成功色**: 绿色 (#48bb78)
- **警告色**: 橙色 (#ed8936)
- **错误色**: 红色 (#f56565)
- **中性色**: 灰色系列

### 动画效果
- **进度条**: 平滑的宽度变化动画
- **状态指示器**: 工作状态的脉冲动画
- **按钮交互**: 悬停和点击的微交互
- **通知提示**: 滑入滑出动画

## 🔧 配置选项

### API配置
```javascript
const CONFIG = {
    API: {
        BASE_URL: 'http://localhost:8001',
        TIMEOUT: 300000 // 5分钟超时
    }
};
```

### 上传限制
```javascript
UPLOAD: {
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    ALLOWED_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    MAX_FILES: 10
}
```

## 🐛 故障排除

### 常见问题

1. **无法连接到后端服务**
   - 确认后端服务已启动在 `http://localhost:8001`
   - 检查防火墙设置
   - 查看浏览器控制台的网络错误

2. **文件上传失败**
   - 检查文件格式是否支持
   - 确认文件大小不超过10MB
   - 检查网络连接状态

3. **流式响应中断**
   - 检查网络稳定性
   - 确认后端服务正常运行
   - 查看浏览器控制台的错误信息

4. **界面显示异常**
   - 清除浏览器缓存
   - 检查浏览器兼容性
   - 确认CSS和JS文件加载正常

### 调试模式

在浏览器控制台中启用调试模式：
```javascript
CONFIG.DEBUG.ENABLED = true;
CONFIG.DEBUG.LOG_LEVEL = 'debug';
```

## 🌐 浏览器兼容性

- **Chrome**: 80+
- **Firefox**: 75+
- **Safari**: 13+
- **Edge**: 80+

## 📝 更新日志

### v1.0.0 (2025-06-17)
- 初始版本发布
- 支持流式上传和实时分析
- 三智能体协作界面
- 响应式设计
- 文件拖拽上传
- 结果下载和复制功能

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

MIT License - 详见 LICENSE 文件
