/**
 * Midscene 智能体系统 - 前端配置文件
 */

const CONFIG = {
    // API配置
    API: {
        BASE_URL: 'http://localhost:8001',
        ENDPOINTS: {
            UPLOAD_AND_ANALYZE: '/api/upload_and_analyze',
            UPLOAD_SINGLE: '/api/upload_single_and_analyze',
            STREAM_RESULTS: '/api/stream_results',
            ROOT: '/'
        },
        TIMEOUT: 300000, // 5分钟超时
    },

    // 文件上传配置
    UPLOAD: {
        MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
        ALLOWED_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
        MAX_FILES: 10
    },

    // UI配置
    UI: {
        NOTIFICATION_DURATION: 3000, // 通知显示时间
        SCROLL_BEHAVIOR: 'smooth',
        PROGRESS_ANIMATION_DURATION: 500
    },

    // 智能体配置
    AGENTS: {
        'UI分析智能体': {
            icon: '🔍',
            color: '#3498db',
            description: '分析界面UI元素'
        },
        '交互分析智能体': {
            icon: '🔄',
            color: '#e67e22',
            description: '分析用户交互流程'
        },
        'Midscene用例生成智能体': {
            icon: '🎯',
            color: '#27ae60',
            description: '生成Midscene测试脚本'
        }
    },

    // 消息类型配置
    MESSAGE_TYPES: {
        SYSTEM_START: 'system_start',
        AGENT_START: 'agent_start',
        STEP_INFO: 'step_info',
        STREAM_CHUNK: 'stream_chunk',
        AGENT_COMPLETE: 'agent_complete',
        AGENT_ERROR: 'agent_error',
        SYSTEM_COMPLETE: 'system_complete',
        SYSTEM_ERROR: 'system_error'
    },

    // 开发模式配置
    DEBUG: {
        ENABLED: false,
        LOG_LEVEL: 'info', // debug, info, warn, error
        MOCK_DELAY: 1000 // 模拟延迟
    }
};

// 根据环境调整配置
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    CONFIG.DEBUG.ENABLED = true;
    CONFIG.DEBUG.LOG_LEVEL = 'debug';
}

// 导出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
} else {
    window.CONFIG = CONFIG;
}
