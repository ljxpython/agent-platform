"""
智能体构建器
提供链式API简化智能体创建，提升开发体验
"""

from typing import Any, Dict, List, Optional

from autogen_agentchat.agents import AssistantAgent
from loguru import logger

# 注意：这是案例代码，实际使用时需要导入真实的模块
# from backend.ai_core.factory import create_assistant_agent
# from backend.ai_core.llm import ModelType


# 案例中的模拟导入
class ModelType:
    DEEPSEEK = "deepseek"
    QWEN_VL = "qwen_vl"
    UI_TARS = "ui_tars"


async def create_assistant_agent(**kwargs):
    """模拟的智能体创建函数"""

    class MockAgent:
        def __init__(self, name):
            self.name = name

    return MockAgent(kwargs.get("name", "MockAgent"))


class AgentBuilder:
    """
    智能体构建器 - 链式API

    提供流畅的链式API来创建智能体，简化开发体验
    """

    def __init__(self):
        """初始化构建器"""
        self.config = {}
        logger.debug("🏗️ [智能体构建器] 初始化构建器")

    def name(self, name: str) -> "AgentBuilder":
        """
        设置智能体名称

        Args:
            name: 智能体名称

        Returns:
            AgentBuilder: 构建器实例（支持链式调用）
        """
        if not name or not name.strip():
            logger.warning("⚠️ [智能体构建器] 智能体名称为空")
            return self

        self.config["name"] = name.strip()
        logger.debug(f"🏷️ [智能体构建器] 设置名称: {name}")
        return self

    def prompt(self, prompt: str) -> "AgentBuilder":
        """
        设置系统提示词

        Args:
            prompt: 系统提示词

        Returns:
            AgentBuilder: 构建器实例（支持链式调用）
        """
        if not prompt or not prompt.strip():
            logger.warning("⚠️ [智能体构建器] 系统提示词为空")
            return self

        self.config["system_message"] = prompt.strip()
        logger.debug(f"📝 [智能体构建器] 设置提示词: {prompt[:100]}...")
        return self

    def model(self, model_type: ModelType) -> "AgentBuilder":
        """
        设置模型类型

        Args:
            model_type: 模型类型

        Returns:
            AgentBuilder: 构建器实例（支持链式调用）
        """
        self.config["model_type"] = model_type
        logger.debug(f"🤖 [智能体构建器] 设置模型: {model_type.value}")
        return self

    def memory(self, conversation_id: str) -> "AgentBuilder":
        """
        设置对话内存

        Args:
            conversation_id: 对话ID

        Returns:
            AgentBuilder: 构建器实例（支持链式调用）
        """
        if not conversation_id or not conversation_id.strip():
            logger.warning("⚠️ [智能体构建器] 对话ID为空")
            return self

        self.config["conversation_id"] = conversation_id.strip()
        self.config["auto_memory"] = True
        logger.debug(f"🧠 [智能体构建器] 设置内存: {conversation_id}")
        return self

    def context(self, auto_context: bool = True) -> "AgentBuilder":
        """
        设置自动上下文

        Args:
            auto_context: 是否自动创建上下文

        Returns:
            AgentBuilder: 构建器实例（支持链式调用）
        """
        self.config["auto_context"] = auto_context
        logger.debug(f"🔄 [智能体构建器] 设置自动上下文: {auto_context}")
        return self

    def config_dict(self, config: Dict[str, Any]) -> "AgentBuilder":
        """
        批量设置配置

        Args:
            config: 配置字典

        Returns:
            AgentBuilder: 构建器实例（支持链式调用）
        """
        if config:
            self.config.update(config)
            logger.debug(f"⚙️ [智能体构建器] 批量设置配置: {list(config.keys())}")
        return self

    def kwargs(self, **kwargs) -> "AgentBuilder":
        """
        设置额外参数

        Args:
            **kwargs: 额外参数

        Returns:
            AgentBuilder: 构建器实例（支持链式调用）
        """
        if kwargs:
            self.config.update(kwargs)
            logger.debug(f"🔧 [智能体构建器] 设置额外参数: {list(kwargs.keys())}")
        return self

    async def build(self) -> Optional[AssistantAgent]:
        """
        构建智能体

        Returns:
            Optional[AssistantAgent]: 创建的智能体实例，失败时返回None
        """
        try:
            logger.info("🏗️ [智能体构建器] 开始构建智能体")
            logger.debug(f"   📋 配置参数: {list(self.config.keys())}")

            # 验证必需参数
            if "name" not in self.config:
                logger.error("❌ [智能体构建器] 缺少必需参数: name")
                return None

            if "system_message" not in self.config:
                logger.error("❌ [智能体构建器] 缺少必需参数: system_message")
                return None

            # 设置默认值
            if "model_type" not in self.config:
                self.config["model_type"] = ModelType.DEEPSEEK
                logger.debug("🔧 [智能体构建器] 使用默认模型: DEEPSEEK")

            # 创建智能体
            agent = await create_assistant_agent(**self.config)

            if agent:
                logger.success(
                    f"✅ [智能体构建器] 智能体构建成功: {self.config['name']}"
                )
            else:
                logger.error(f"❌ [智能体构建器] 智能体构建失败: {self.config['name']}")

            return agent

        except Exception as e:
            logger.error(f"❌ [智能体构建器] 构建过程异常: {e}")
            logger.error(f"   🐛 错误类型: {type(e).__name__}")
            logger.error(f"   📋 配置参数: {self.config}")
            return None

    def reset(self) -> "AgentBuilder":
        """
        重置构建器

        Returns:
            AgentBuilder: 构建器实例（支持链式调用）
        """
        self.config.clear()
        logger.debug("🔄 [智能体构建器] 构建器已重置")
        return self

    def get_config(self) -> Dict[str, Any]:
        """
        获取当前配置

        Returns:
            Dict[str, Any]: 当前配置字典
        """
        return self.config.copy()


# 便捷函数
def agent_builder() -> AgentBuilder:
    """
    创建智能体构建器的便捷函数

    Returns:
        AgentBuilder: 新的构建器实例
    """
    return AgentBuilder()


# 预设构建器
class PresetAgentBuilder:
    """预设智能体构建器"""

    @staticmethod
    def requirement_analyst(conversation_id: str) -> AgentBuilder:
        """
        需求分析师预设

        Args:
            conversation_id: 对话ID

        Returns:
            AgentBuilder: 配置好的构建器
        """
        return (
            agent_builder()
            .name("需求分析师")
            .prompt(
                """
你是一位资深的软件需求分析师，拥有超过10年的需求分析和软件测试经验。

你的任务是：
1. 深入理解用户提供的需求文档和描述
2. 识别关键功能点、业务流程和约束条件
3. 分析潜在的风险点和边界情况
4. 为后续的测试用例生成提供结构化的需求分析

请提供专业、详细的需求分析结果。
            """.strip()
            )
            .model(ModelType.DEEPSEEK)
            .memory(conversation_id)
        )

    @staticmethod
    def testcase_expert(conversation_id: str) -> AgentBuilder:
        """
        测试用例专家预设

        Args:
            conversation_id: 对话ID

        Returns:
            AgentBuilder: 配置好的构建器
        """
        return (
            agent_builder()
            .name("测试用例专家")
            .prompt(
                """
你是一位资深的软件测试专家，拥有超过15年的测试用例设计和测试执行经验。

你的任务是：
1. 基于需求分析结果，设计全面的测试用例
2. 确保测试用例覆盖正常流程、异常流程和边界条件
3. 每个测试用例都要包含：测试目标、前置条件、测试步骤、预期结果
4. 测试用例要具体、可执行、可验证

请生成结构化、专业的测试用例，确保测试覆盖率和质量。
            """.strip()
            )
            .model(ModelType.DEEPSEEK)
            .memory(conversation_id)
        )

    @staticmethod
    def ui_analyst(conversation_id: str) -> AgentBuilder:
        """
        UI分析师预设

        Args:
            conversation_id: 对话ID

        Returns:
            AgentBuilder: 配置好的构建器
        """
        return (
            agent_builder()
            .name("UI分析师")
            .prompt(
                """
你是一位专业的UI/UX分析师，专门负责分析用户界面和交互设计。

你的任务是：
1. 分析界面截图和设计稿
2. 识别UI元素、布局结构和交互模式
3. 理解用户操作流程和界面逻辑
4. 为自动化测试提供详细的UI分析结果

请提供准确、详细的UI分析报告。
            """.strip()
            )
            .model(ModelType.QWEN_VL)
            .memory(conversation_id)
        )


# 导出接口
__all__ = ["AgentBuilder", "agent_builder", "PresetAgentBuilder"]
