/**
 * Midscene 智能体系统 - 前端应用
 * 基于流式上传接口的实时分析界面
 */

class MidsceneApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8001';
        this.currentUserId = null;
        this.isAnalyzing = false;
        this.agentProgress = 0;
        this.selectedFiles = [];
        this.analysisResults = {};

        this.init();
    }

    init() {
        this.bindEvents();
        this.setupFileUpload();
        this.generateUserId();
    }

    generateUserId() {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substr(2, 5);
        document.getElementById('userId').value = `user_${timestamp}_${random}`;
    }

    bindEvents() {
        // 表单提交
        document.getElementById('uploadForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFormSubmit();
        });

        // 结果操作按钮
        document.getElementById('downloadBtn')?.addEventListener('click', () => this.downloadResults());
        document.getElementById('copyBtn')?.addEventListener('click', () => this.copyScript());
        document.getElementById('downloadYamlBtn')?.addEventListener('click', () => this.downloadYamlScript());
        document.getElementById('downloadPlaywrightBtn')?.addEventListener('click', () => this.downloadPlaywrightScript());
        document.getElementById('newAnalysisBtn')?.addEventListener('click', () => this.resetAnalysis());
    }

    setupFileUpload() {
        const fileInput = document.getElementById('files');
        const uploadArea = document.getElementById('fileUploadArea');
        const fileList = document.getElementById('fileList');

        // 文件选择事件
        fileInput.addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files);
        });

        // 拖拽上传
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            this.handleFileSelect(e.dataTransfer.files);
        });
    }

    handleFileSelect(files) {
        this.selectedFiles = Array.from(files);
        this.updateFileList();

        // 更新文件输入框
        const fileInput = document.getElementById('files');
        const dt = new DataTransfer();
        this.selectedFiles.forEach(file => dt.items.add(file));
        fileInput.files = dt.files;
    }

    updateFileList() {
        const fileList = document.getElementById('fileList');

        if (this.selectedFiles.length === 0) {
            fileList.innerHTML = '';
            return;
        }

        fileList.innerHTML = this.selectedFiles.map((file, index) => `
            <div class="file-item">
                <div class="file-info">
                    <span class="file-icon">🖼️</span>
                    <span class="file-name">${file.name}</span>
                    <span class="file-size">(${this.formatFileSize(file.size)})</span>
                </div>
                <button type="button" class="remove-file" onclick="app.removeFile(${index})">×</button>
            </div>
        `).join('');
    }

    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.updateFileList();

        // 更新文件输入框
        const fileInput = document.getElementById('files');
        const dt = new DataTransfer();
        this.selectedFiles.forEach(file => dt.items.add(file));
        fileInput.files = dt.files;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async handleFormSubmit() {
        if (this.isAnalyzing) return;

        const formData = new FormData();
        const userId = document.getElementById('userId').value.trim();
        const requirement = document.getElementById('requirement').value.trim();
        const files = this.selectedFiles;

        // 验证输入
        if (!userId) {
            this.showNotification('请输入用户ID', 'error');
            return;
        }

        if (!requirement) {
            this.showNotification('请输入测试需求描述', 'error');
            return;
        }

        if (files.length === 0) {
            this.showNotification('请选择至少一张图片', 'error');
            return;
        }

        // 准备表单数据
        files.forEach(file => formData.append('files', file));
        formData.append('user_id', userId);
        formData.append('user_requirement', requirement);

        this.currentUserId = userId;
        this.startAnalysis();

        try {
            // 使用新的流式上传接口
            const response = await fetch(`${this.apiBaseUrl}/api/upload_and_analyze`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // 处理流式响应
            await this.handleStreamingResponse(response);

        } catch (error) {
            console.error('上传分析失败:', error);
            this.showNotification(`上传失败: ${error.message}`, 'error');
            this.resetForm();
        }
    }

    async handleStreamingResponse(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        try {
            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');

                // 保留最后一行（可能不完整）
                buffer = lines.pop() || '';

                // 处理完整的行
                for (const line of lines) {
                    if (line.trim().startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.trim().substring(6));
                            this.handleStreamMessage(data);
                        } catch (error) {
                            console.error('解析SSE消息失败:', error, line);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('读取流式响应失败:', error);
            this.showNotification('连接中断，请重试', 'error');
            this.resetForm();
        }
    }

    handleStreamMessage(data) {
        const { type, agent, content, message, step } = data;

        switch (type) {
            case 'system_start':
                this.addLogEntry(content || message, 'info');
                break;

            case 'agent_start':
                this.updateAgentStatus(agent, 'working', '工作中');
                this.updateAgentContent(agent, '');
                this.addLogEntry(`${agent} 开始工作: ${step}`, 'info');
                break;

            case 'step_info':
                this.addLogEntry(`${agent}: ${content}`, 'info');
                break;

            case 'stream_chunk':
                this.appendAgentContent(agent, content);
                break;

            case 'agent_complete':
                this.updateAgentStatus(agent, 'complete', '已完成');
                this.addLogEntry(`${agent} 完成工作`, 'success');

                // 根据智能体类型更新进度
                if (agent === 'UI分析智能体' || agent === '交互分析智能体') {
                    this.agentProgress += 25; // 四个智能体，每个25%
                } else if (agent === 'Midscene用例生成智能体') {
                    this.agentProgress += 25;
                } else if (agent === '脚本生成智能体') {
                    this.agentProgress += 25;
                }

                this.updateProgress(Math.min(this.agentProgress, 100));
                break;

            case 'agent_error':
                this.updateAgentStatus(agent, 'error', '错误');
                this.updateAgentContent(agent, `❌ 错误: ${content}`);
                this.addLogEntry(`${agent} 发生错误: ${content}`, 'error');
                break;

            case 'system_complete':
                this.addLogEntry('🎉 所有智能体协作分析完成！', 'success');
                this.updateProgress(100);
                this.completeAnalysis();
                break;

            case 'system_error':
                this.addLogEntry(`❌ 系统错误: ${content || message}`, 'error');
                this.showNotification('分析过程中发生错误', 'error');
                this.resetForm();
                break;

            default:
                console.log('未知消息类型:', data);
        }
    }

    startAnalysis() {
        this.isAnalyzing = true;
        this.agentProgress = 0;

        // 显示分析区域
        document.getElementById('analysisSection').style.display = 'block';
        document.getElementById('resultSection').style.display = 'none';

        // 禁用提交按钮
        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="btn-icon">⏳</span>分析中...';

        // 重置状态
        this.resetAgentStatus();
        this.clearSystemLog();
        this.updateProgress(0);

        // 滚动到分析区域
        document.getElementById('analysisSection').scrollIntoView({
            behavior: 'smooth'
        });
    }

    completeAnalysis() {
        this.isAnalyzing = false;
        document.getElementById('resultSection').style.display = 'block';
        this.resetForm();

        // 滚动到结果区域
        document.getElementById('resultSection').scrollIntoView({
            behavior: 'smooth'
        });
    }

    resetForm() {
        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span class="btn-icon">🚀</span>开始分析';
    }

    resetAnalysis() {
        this.isAnalyzing = false;
        this.agentProgress = 0;
        this.analysisResults = {};

        // 隐藏分析区域
        document.getElementById('analysisSection').style.display = 'none';
        document.getElementById('resultSection').style.display = 'none';

        // 重置表单
        this.resetForm();
        this.generateUserId();

        // 滚动到顶部
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    updateAgentStatus(agentName, status, text) {
        const statusMap = {
            'UI分析智能体': 'uiStatus',
            '交互分析智能体': 'interactionStatus',
            'Midscene用例生成智能体': 'midsceneStatus',
            '脚本生成智能体': 'scriptStatus'
        };

        const statusId = statusMap[agentName];
        if (statusId) {
            const statusElement = document.getElementById(statusId);
            statusElement.textContent = text;
            statusElement.className = `agent-status status-${status}`;
        }
    }

    updateAgentContent(agentName, content) {
        const contentMap = {
            'UI分析智能体': 'uiContent',
            '交互分析智能体': 'interactionContent',
            'Midscene用例生成智能体': 'midsceneContent',
            '脚本生成智能体': 'scriptContent'
        };

        const contentId = contentMap[agentName];
        if (contentId) {
            const element = document.getElementById(contentId);
            element.textContent = content;

            // 保存结果
            this.analysisResults[agentName] = content;
        }
    }

    appendAgentContent(agentName, content) {
        const contentMap = {
            'UI分析智能体': 'uiContent',
            '交互分析智能体': 'interactionContent',
            'Midscene用例生成智能体': 'midsceneContent',
            '脚本生成智能体': 'scriptContent'
        };

        const contentId = contentMap[agentName];
        if (contentId) {
            const element = document.getElementById(contentId);
            element.textContent += content;
            element.scrollTop = element.scrollHeight;

            // 更新保存的结果
            this.analysisResults[agentName] = element.textContent;
        }
    }

    addLogEntry(message, type) {
        const logDiv = document.getElementById('systemLog');
        const entry = document.createElement('div');
        entry.className = `log-entry log-${type}`;
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        logDiv.appendChild(entry);
        logDiv.scrollTop = logDiv.scrollHeight;
    }

    clearSystemLog() {
        document.getElementById('systemLog').innerHTML = '';
    }

    updateProgress(percentage) {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');

        progressFill.style.width = `${percentage}%`;
        progressText.textContent = `${Math.round(percentage)}%`;
    }

    resetAgentStatus() {
        // 重置所有智能体状态
        ['uiStatus', 'interactionStatus', 'midsceneStatus', 'scriptStatus'].forEach(id => {
            const element = document.getElementById(id);
            element.textContent = '等待中';
            element.className = 'agent-status status-waiting';
        });

        // 重置内容
        document.getElementById('uiContent').innerHTML = '<div class="waiting-message">等待开始分析...</div>';
        document.getElementById('interactionContent').innerHTML = '<div class="waiting-message">等待UI分析完成...</div>';
        document.getElementById('midsceneContent').innerHTML = '<div class="waiting-message">等待交互分析完成...</div>';
        document.getElementById('scriptContent').innerHTML = '<div class="waiting-message">等待Midscene生成完成...</div>';
    }

    async downloadResults() {
        const results = {
            userId: this.currentUserId,
            timestamp: new Date().toISOString(),
            analysisResults: this.analysisResults
        };

        const blob = new Blob([JSON.stringify(results, null, 2)], {
            type: 'application/json'
        });

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `midscene_analysis_${this.currentUserId}_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showNotification('分析结果已下载', 'success');
    }

    async copyScript() {
        const midsceneScript = this.analysisResults['Midscene用例生成智能体'] || '';

        if (!midsceneScript) {
            this.showNotification('没有可复制的脚本内容', 'error');
            return;
        }

        try {
            await navigator.clipboard.writeText(midsceneScript);
            this.showNotification('Midscene脚本已复制到剪贴板', 'success');
        } catch (error) {
            console.error('复制失败:', error);
            this.showNotification('复制失败，请手动复制', 'error');
        }
    }

    async downloadYamlScript() {
        const scriptResult = this.analysisResults['脚本生成智能体'] || '';

        if (!scriptResult) {
            this.showNotification('没有可下载的脚本内容', 'error');
            return;
        }

        try {
            // 解析脚本生成结果，提取YAML脚本
            const yamlScript = this.extractYamlScript(scriptResult);

            if (!yamlScript) {
                this.showNotification('未找到YAML脚本内容', 'error');
                return;
            }

            const blob = new Blob([yamlScript], { type: 'text/yaml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `midscene_test_${this.currentUserId}_${Date.now()}.yaml`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showNotification('YAML脚本已下载', 'success');
        } catch (error) {
            console.error('下载YAML脚本失败:', error);
            this.showNotification('下载失败，请重试', 'error');
        }
    }

    async downloadPlaywrightScript() {
        const scriptResult = this.analysisResults['脚本生成智能体'] || '';

        if (!scriptResult) {
            this.showNotification('没有可下载的脚本内容', 'error');
            return;
        }

        try {
            // 解析脚本生成结果，提取Playwright脚本
            const playwrightScript = this.extractPlaywrightScript(scriptResult);

            if (!playwrightScript) {
                this.showNotification('未找到Playwright脚本内容', 'error');
                return;
            }

            const blob = new Blob([playwrightScript], { type: 'text/typescript' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `midscene_test_${this.currentUserId}_${Date.now()}.spec.ts`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showNotification('Playwright脚本已下载', 'success');
        } catch (error) {
            console.error('下载Playwright脚本失败:', error);
            this.showNotification('下载失败，请重试', 'error');
        }
    }

    extractYamlScript(scriptResult) {
        try {
            // 方法1: 尝试提取JSON代码块中的yaml_script
            const jsonMatch = scriptResult.match(/```json\s*([\s\S]*?)\s*```/);
            if (jsonMatch) {
                try {
                    const jsonData = JSON.parse(jsonMatch[1]);
                    if (jsonData.yaml_script) {
                        return jsonData.yaml_script;
                    }
                } catch (e) {
                    console.warn('JSON代码块解析失败:', e);
                }
            }

            // 方法2: 尝试直接解析整个结果为JSON
            try {
                const jsonData = JSON.parse(scriptResult);
                if (jsonData.yaml_script) {
                    return jsonData.yaml_script;
                }
            } catch (e) {
                // JSON解析失败，继续尝试其他方法
            }

            // 方法3: 提取YAML代码块
            const yamlMatch = scriptResult.match(/```yaml\s*([\s\S]*?)\s*```/);
            if (yamlMatch) {
                return yamlMatch[1].trim();
            }

            // 方法4: 提取yml代码块
            const ymlMatch = scriptResult.match(/```yml\s*([\s\S]*?)\s*```/);
            if (ymlMatch) {
                return ymlMatch[1].trim();
            }

            // 方法5: 查找YAML关键字后的内容
            const yamlKeywordMatch = scriptResult.match(/(?:YAML脚本|yaml_script|YAML格式)[：:\s]*\n([\s\S]*?)(?=\n\n|Playwright|playwright_script|$)/i);
            if (yamlKeywordMatch) {
                return yamlKeywordMatch[1].trim();
            }

            // 如果都失败，返回空字符串
            console.warn('无法提取YAML脚本，尝试的方法都失败了');
            return '';
        } catch (error) {
            console.error('提取YAML脚本时发生错误:', error);
            return '';
        }
    }

    extractPlaywrightScript(scriptResult) {
        try {
            // 方法1: 尝试提取JSON代码块中的playwright_script
            const jsonMatch = scriptResult.match(/```json\s*([\s\S]*?)\s*```/);
            if (jsonMatch) {
                try {
                    const jsonData = JSON.parse(jsonMatch[1]);
                    if (jsonData.playwright_script) {
                        return jsonData.playwright_script;
                    }
                } catch (e) {
                    console.warn('JSON代码块解析失败:', e);
                }
            }

            // 方法2: 尝试直接解析整个结果为JSON
            try {
                const jsonData = JSON.parse(scriptResult);
                if (jsonData.playwright_script) {
                    return jsonData.playwright_script;
                }
            } catch (e) {
                // JSON解析失败，继续尝试其他方法
            }

            // 方法3: 提取TypeScript代码块
            const tsMatch = scriptResult.match(/```typescript\s*([\s\S]*?)\s*```/) ||
                           scriptResult.match(/```ts\s*([\s\S]*?)\s*```/);
            if (tsMatch) {
                return tsMatch[1].trim();
            }

            // 方法4: 提取JavaScript代码块（可能包含Playwright代码）
            const jsMatch = scriptResult.match(/```javascript\s*([\s\S]*?)\s*```/) ||
                           scriptResult.match(/```js\s*([\s\S]*?)\s*```/);
            if (jsMatch) {
                return jsMatch[1].trim();
            }

            // 方法5: 查找Playwright关键字后的内容
            const playwrightKeywordMatch = scriptResult.match(/(?:Playwright脚本|playwright_script|Playwright格式)[：:\s]*\n([\s\S]*?)(?=\n\n|YAML|yaml_script|$)/i);
            if (playwrightKeywordMatch) {
                return playwrightKeywordMatch[1].trim();
            }

            // 方法6: 查找import语句开始的代码块（通常是Playwright脚本的开始）
            const importMatch = scriptResult.match(/(import[\s\S]*?test\([\s\S]*?\}\);?)/);
            if (importMatch) {
                return importMatch[1].trim();
            }

            // 如果都失败，返回空字符串
            console.warn('无法提取Playwright脚本，尝试的方法都失败了');
            return '';
        } catch (error) {
            console.error('提取Playwright脚本时发生错误:', error);
            return '';
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.classList.add('show');

        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
}

// 初始化应用
const app = new MidsceneApp();

// 全局错误处理
window.addEventListener('error', (event) => {
    console.error('全局错误:', event.error);
    app.showNotification('发生未知错误，请刷新页面重试', 'error');
});

// 网络状态监听
window.addEventListener('online', () => {
    app.showNotification('网络连接已恢复', 'success');
});

window.addEventListener('offline', () => {
    app.showNotification('网络连接已断开', 'error');
});
