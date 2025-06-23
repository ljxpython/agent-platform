"""
AI核心组件增强版模块 - Phase 2&3 优化案例

该模块包含AI核心框架的完整工程化优化组件：

Phase 1 (已完成):
- 智能体构建器（AgentBuilder）
- 配置管理系统（AgentConfig）
- 提示词模板管理（TemplateManager）

Phase 2 - 监控观测系统:
- 智能体性能监控（AgentMonitor）
- 调试工具系统（AgentDebugger）
- 增强日志系统（StructuredLogger）

Phase 3 - 扩展性增强:
- 插件系统（PluginManager）
- 中间件系统（MiddlewareManager）
- 装饰器简化开发

注意：这是一个完整的参考案例，暂未集成到主系统中
"""

# Phase 1: 智能体构建器（从之前的案例导入）
try:
    from ..code.ai_core_enhanced.builder import (
        AgentBuilder,
        PresetAgentBuilder,
        agent_builder,
    )
    from ..code.ai_core_enhanced.config import (
        AgentConfig,
        ConfigValidator,
        get_agent_config,
        get_agent_config_manager,
        save_agent_config,
    )
    from ..code.ai_core_enhanced.templates import (
        PromptTemplate,
        TemplateManager,
        get_template,
        get_template_manager,
        render_template,
    )

    PHASE1_AVAILABLE = True
except ImportError:
    PHASE1_AVAILABLE = False
    print("⚠️ Phase 1 组件不可用，请确保已有构建器、配置和模板模块")

from .debug import (
    AgentDebugger,
    MessageTrace,
    TraceEvent,
    TraceLevel,
    debug_message,
    debug_trace,
    get_agent_debugger,
)
from .decorators import agent_operation, cache_result
from .decorators import debug_trace as debug_trace_decorator
from .decorators import monitor_performance, retry_on_failure, smart_agent_operation
from .logging_enhanced import (
    LogAnalyzer,
    PerformanceLogger,
    StructuredLogger,
    get_log_analyzer,
    get_performance_logger,
    get_structured_logger,
    log_agent_op,
    log_perf,
)
from .middleware import (
    BaseMiddleware,
    CacheMiddleware,
    LoggingMiddleware,
    MiddlewareContext,
    MiddlewareManager,
    PerformanceMiddleware,
    ValidationMiddleware,
    get_middleware_manager,
    with_middleware,
)

# Phase 2: 监控观测系统
from .monitoring import (
    AgentMonitor,
    AgentStats,
    PerformanceMetric,
    get_agent_monitor,
    monitor_agent_operation,
)

# Phase 3: 扩展性增强系统
from .plugins import (
    BasePlugin,
    PluginHook,
    PluginInfo,
    PluginManager,
    get_plugin_manager,
    plugin_hook,
)

# 构建完整的导出列表
__all__ = [
    # Phase 2: 监控观测系统
    "PerformanceMetric",
    "AgentStats",
    "AgentMonitor",
    "get_agent_monitor",
    "monitor_agent_operation",
    "TraceLevel",
    "TraceEvent",
    "MessageTrace",
    "AgentDebugger",
    "get_agent_debugger",
    "debug_trace",
    "debug_message",
    "StructuredLogger",
    "PerformanceLogger",
    "LogAnalyzer",
    "get_structured_logger",
    "get_performance_logger",
    "get_log_analyzer",
    "log_agent_op",
    "log_perf",
    # Phase 3: 扩展性增强系统
    "PluginInfo",
    "PluginHook",
    "BasePlugin",
    "PluginManager",
    "get_plugin_manager",
    "plugin_hook",
    "MiddlewareContext",
    "BaseMiddleware",
    "LoggingMiddleware",
    "PerformanceMiddleware",
    "ValidationMiddleware",
    "CacheMiddleware",
    "MiddlewareManager",
    "get_middleware_manager",
    "with_middleware",
    "agent_operation",
    "monitor_performance",
    "debug_trace_decorator",
    "cache_result",
    "retry_on_failure",
    "smart_agent_operation",
]

# 如果Phase 1可用，添加到导出列表
if PHASE1_AVAILABLE:
    __all__.extend(
        [
            # Phase 1: 智能体构建器
            "AgentBuilder",
            "agent_builder",
            "PresetAgentBuilder",
            # 配置管理
            "AgentConfig",
            "ConfigValidator",
            "get_agent_config_manager",
            "get_agent_config",
            "save_agent_config",
            # 模板管理
            "PromptTemplate",
            "TemplateManager",
            "get_template_manager",
            "get_template",
            "render_template",
        ]
    )

__version__ = "2.0.0"
__author__ = "AI Core Optimization Team"
__description__ = "AI核心框架完整工程化优化案例 - Phase 1, 2 & 3"

# 版本信息
PHASES = {
    "phase1": {
        "name": "智能体构建器系统",
        "status": "available" if PHASE1_AVAILABLE else "not_available",
        "components": ["AgentBuilder", "AgentConfig", "TemplateManager"],
    },
    "phase2": {
        "name": "监控观测系统",
        "status": "available",
        "components": ["AgentMonitor", "AgentDebugger", "StructuredLogger"],
    },
    "phase3": {
        "name": "扩展性增强系统",
        "status": "available",
        "components": ["PluginManager", "MiddlewareManager", "Decorators"],
    },
}


def get_version_info():
    """获取版本信息"""
    return {
        "version": __version__,
        "description": __description__,
        "phases": PHASES,
        "total_components": len(__all__),
    }
