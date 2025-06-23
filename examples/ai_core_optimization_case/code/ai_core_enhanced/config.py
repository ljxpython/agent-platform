"""
智能体配置管理系统
提供统一的配置管理、模板加载和环境配置功能
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger

# 注意：这是案例代码，实际使用时需要导入真实的模块
# from backend.ai_core.llm import ModelType


# 案例中的模拟导入
class ModelType:
    DEEPSEEK = "deepseek"
    QWEN_VL = "qwen_vl"
    UI_TARS = "ui_tars"


class AgentConfig:
    """智能体配置管理器"""

    def __init__(self, config_dir: str = "configs/agents"):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.templates: Dict[str, str] = {}

        logger.info(f"⚙️ [配置管理器] 初始化配置管理器")
        logger.info(f"   📁 配置目录: {self.config_dir}")

        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 加载配置
        self.load_configs()

    def load_configs(self) -> None:
        """加载所有智能体配置"""
        try:
            logger.info("📂 [配置管理器] 开始加载智能体配置")

            config_count = 0

            # 加载YAML配置文件
            for config_file in self.config_dir.glob("*.yaml"):
                try:
                    config_name = config_file.stem
                    config_data = self._load_yaml_file(config_file)

                    if config_data:
                        self.configs[config_name] = config_data
                        config_count += 1
                        logger.debug(f"   ✅ 加载配置: {config_name}")

                except Exception as e:
                    logger.error(f"   ❌ 加载配置失败: {config_file} | 错误: {e}")

            # 加载JSON配置文件
            for config_file in self.config_dir.glob("*.json"):
                try:
                    config_name = config_file.stem
                    config_data = self._load_json_file(config_file)

                    if config_data:
                        self.configs[config_name] = config_data
                        config_count += 1
                        logger.debug(f"   ✅ 加载配置: {config_name}")

                except Exception as e:
                    logger.error(f"   ❌ 加载配置失败: {config_file} | 错误: {e}")

            logger.success(
                f"✅ [配置管理器] 配置加载完成，共加载 {config_count} 个配置"
            )

            # 如果没有配置文件，创建默认配置
            if config_count == 0:
                self._create_default_configs()

        except Exception as e:
            logger.error(f"❌ [配置管理器] 配置加载异常: {e}")

    def _load_yaml_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """加载YAML文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"❌ [配置管理器] YAML文件加载失败: {file_path} | 错误: {e}")
            return None

    def _load_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """加载JSON文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ [配置管理器] JSON文件加载失败: {file_path} | 错误: {e}")
            return None

    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """
        获取智能体配置

        Args:
            agent_type: 智能体类型

        Returns:
            Dict[str, Any]: 智能体配置，如果不存在返回空字典
        """
        config = self.configs.get(agent_type, {})

        if config:
            logger.debug(f"📋 [配置管理器] 获取配置: {agent_type}")
        else:
            logger.warning(f"⚠️ [配置管理器] 配置不存在: {agent_type}")

        return config.copy()

    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有配置

        Returns:
            Dict[str, Dict[str, Any]]: 所有智能体配置
        """
        return self.configs.copy()

    def save_config(
        self, agent_type: str, config: Dict[str, Any], format: str = "yaml"
    ) -> bool:
        """
        保存智能体配置

        Args:
            agent_type: 智能体类型
            config: 配置数据
            format: 保存格式（yaml或json）

        Returns:
            bool: 保存是否成功
        """
        try:
            logger.info(f"💾 [配置管理器] 保存配置: {agent_type}")

            # 更新内存中的配置
            self.configs[agent_type] = config

            # 保存到文件
            if format.lower() == "yaml":
                file_path = self.config_dir / f"{agent_type}.yaml"
                with open(file_path, "w", encoding="utf-8") as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            else:
                file_path = self.config_dir / f"{agent_type}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)

            logger.success(f"✅ [配置管理器] 配置保存成功: {file_path}")
            return True

        except Exception as e:
            logger.error(f"❌ [配置管理器] 配置保存失败: {agent_type} | 错误: {e}")
            return False

    def _create_default_configs(self) -> None:
        """创建默认配置文件"""
        logger.info("🔧 [配置管理器] 创建默认配置文件")

        # 需求分析师配置
        requirement_config = {
            "name": "需求分析师",
            "model_type": "deepseek",
            "system_message": """你是一位资深的软件需求分析师，拥有超过10年的需求分析和软件测试经验。

你的任务是：
1. 深入理解用户提供的需求文档和描述
2. 识别关键功能点、业务流程和约束条件
3. 分析潜在的风险点和边界情况
4. 为后续的测试用例生成提供结构化的需求分析

请提供专业、详细的需求分析结果。""",
            "auto_memory": True,
            "auto_context": True,
            "description": "专业的需求分析智能体，负责分析用户需求并提供结构化的分析结果",
        }

        # 测试用例专家配置
        testcase_config = {
            "name": "测试用例专家",
            "model_type": "deepseek",
            "system_message": """你是一位资深的软件测试专家，拥有超过15年的测试用例设计和测试执行经验。

你的任务是：
1. 基于需求分析结果，设计全面的测试用例
2. 确保测试用例覆盖正常流程、异常流程和边界条件
3. 每个测试用例都要包含：测试目标、前置条件、测试步骤、预期结果
4. 测试用例要具体、可执行、可验证

请生成结构化、专业的测试用例，确保测试覆盖率和质量。""",
            "auto_memory": True,
            "auto_context": True,
            "description": "专业的测试用例设计智能体，负责生成高质量的测试用例",
        }

        # UI分析师配置
        ui_config = {
            "name": "UI分析师",
            "model_type": "qwen_vl",
            "system_message": """你是一位专业的UI/UX分析师，专门负责分析用户界面和交互设计。

你的任务是：
1. 分析界面截图和设计稿
2. 识别UI元素、布局结构和交互模式
3. 理解用户操作流程和界面逻辑
4. 为自动化测试提供详细的UI分析结果

请提供准确、详细的UI分析报告。""",
            "auto_memory": True,
            "auto_context": True,
            "description": "专业的UI分析智能体，负责分析用户界面和交互设计",
        }

        # 保存默认配置
        self.save_config("requirement_analysis", requirement_config)
        self.save_config("testcase_generation", testcase_config)
        self.save_config("ui_analysis", ui_config)


class ConfigValidator:
    """配置验证器"""

    @staticmethod
    def validate_agent_config(config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        验证智能体配置

        Args:
            config: 智能体配置

        Returns:
            tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []

        # 检查必需字段
        required_fields = ["name", "system_message"]
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")
            elif not config[field] or not str(config[field]).strip():
                errors.append(f"字段不能为空: {field}")

        # 检查模型类型
        if "model_type" in config:
            model_type = config["model_type"]
            if isinstance(model_type, str):
                valid_models = [e.value for e in ModelType]
                if model_type not in valid_models:
                    errors.append(
                        f"无效的模型类型: {model_type}，有效值: {valid_models}"
                    )

        return len(errors) == 0, errors


# 全局配置管理器实例
_agent_config: Optional[AgentConfig] = None


def get_agent_config_manager() -> AgentConfig:
    """获取全局配置管理器实例（单例模式）"""
    global _agent_config
    if _agent_config is None:
        _agent_config = AgentConfig()
    return _agent_config


# 便捷函数
def get_agent_config(agent_type: str) -> Dict[str, Any]:
    """
    获取智能体配置的便捷函数

    Args:
        agent_type: 智能体类型

    Returns:
        Dict[str, Any]: 智能体配置
    """
    return get_agent_config_manager().get_agent_config(agent_type)


def save_agent_config(agent_type: str, config: Dict[str, Any]) -> bool:
    """
    保存智能体配置的便捷函数

    Args:
        agent_type: 智能体类型
        config: 配置数据

    Returns:
        bool: 保存是否成功
    """
    return get_agent_config_manager().save_config(agent_type, config)


# 导出接口
__all__ = [
    "AgentConfig",
    "ConfigValidator",
    "get_agent_config_manager",
    "get_agent_config",
    "save_agent_config",
]
