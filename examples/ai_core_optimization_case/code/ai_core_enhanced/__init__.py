"""
AI核心组件增强版模块 - 优化案例

该模块包含AI核心框架的工程化优化组件：
- 智能体构建器（AgentBuilder）
- 配置管理系统（AgentConfig）
- 提示词模板管理（TemplateManager）

注意：这是一个参考案例，暂未集成到主系统中
"""

# 智能体构建器
from .builder import AgentBuilder, PresetAgentBuilder, agent_builder

# 配置管理
from .config import (
    AgentConfig,
    ConfigValidator,
    get_agent_config,
    get_agent_config_manager,
    save_agent_config,
)

# 模板管理
from .templates import (
    PromptTemplate,
    TemplateManager,
    get_template,
    get_template_manager,
    render_template,
)

__all__ = [
    # 智能体构建器
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

__version__ = "1.0.0"
__author__ = "AI Core Optimization Team"
__description__ = "AI核心框架工程化优化案例"
