"""
提示词模板管理系统
提供模板加载、渲染和管理功能，支持动态参数替换
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


class PromptTemplate:
    """提示词模板类"""

    def __init__(self, template: str, name: str = ""):
        """
        初始化模板

        Args:
            template: 模板字符串
            name: 模板名称
        """
        self.template = template
        self.name = name
        self.variables = self._extract_variables()

        logger.debug(f"📝 [提示词模板] 创建模板: {name}")
        logger.debug(f"   🔧 变量: {self.variables}")

    def _extract_variables(self) -> List[str]:
        """提取模板中的变量"""
        # 匹配 {variable} 格式的变量
        pattern = r"\{([^}]+)\}"
        variables = re.findall(pattern, self.template)
        return list(set(variables))

    def render(self, **kwargs) -> str:
        """
        渲染模板

        Args:
            **kwargs: 模板变量

        Returns:
            str: 渲染后的字符串
        """
        try:
            logger.debug(f"🎨 [提示词模板] 渲染模板: {self.name}")
            logger.debug(f"   📋 参数: {list(kwargs.keys())}")

            # 检查缺失的变量
            missing_vars = [var for var in self.variables if var not in kwargs]
            if missing_vars:
                logger.warning(f"⚠️ [提示词模板] 缺失变量: {missing_vars}")

            # 渲染模板
            rendered = self.template.format(**kwargs)

            logger.debug(f"✅ [提示词模板] 模板渲染完成")
            return rendered

        except KeyError as e:
            logger.error(f"❌ [提示词模板] 模板变量缺失: {e}")
            return self.template
        except Exception as e:
            logger.error(f"❌ [提示词模板] 模板渲染失败: {e}")
            return self.template

    def get_variables(self) -> List[str]:
        """获取模板变量列表"""
        return self.variables.copy()

    def validate_variables(self, **kwargs) -> tuple[bool, List[str]]:
        """
        验证模板变量

        Args:
            **kwargs: 要验证的变量

        Returns:
            tuple[bool, List[str]]: (是否有效, 缺失的变量列表)
        """
        missing_vars = [var for var in self.variables if var not in kwargs]
        return len(missing_vars) == 0, missing_vars

    @classmethod
    def from_file(cls, template_path: str, name: str = "") -> "PromptTemplate":
        """
        从文件加载模板

        Args:
            template_path: 模板文件路径
            name: 模板名称

        Returns:
            PromptTemplate: 模板实例
        """
        try:
            path = Path(template_path)
            template_name = name or path.stem

            logger.debug(f"📂 [提示词模板] 从文件加载模板: {template_path}")

            with open(path, "r", encoding="utf-8") as f:
                template_content = f.read()

            logger.success(f"✅ [提示词模板] 模板加载成功: {template_name}")
            return cls(template_content, template_name)

        except FileNotFoundError:
            logger.error(f"❌ [提示词模板] 模板文件不存在: {template_path}")
            return cls("", name)
        except Exception as e:
            logger.error(f"❌ [提示词模板] 模板加载失败: {template_path} | 错误: {e}")
            return cls("", name)


class TemplateManager:
    """模板管理器"""

    def __init__(self, template_dir: str = "configs/templates"):
        """
        初始化模板管理器

        Args:
            template_dir: 模板目录
        """
        self.template_dir = Path(template_dir)
        self.templates: Dict[str, PromptTemplate] = {}

        logger.info(f"📚 [模板管理器] 初始化模板管理器")
        logger.info(f"   📁 模板目录: {self.template_dir}")

        # 确保模板目录存在
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # 加载模板
        self.load_templates()

    def load_templates(self) -> None:
        """加载所有模板"""
        try:
            logger.info("📂 [模板管理器] 开始加载模板")

            template_count = 0

            # 加载.txt模板文件
            for template_file in self.template_dir.glob("*.txt"):
                try:
                    template_name = template_file.stem
                    template = PromptTemplate.from_file(
                        str(template_file), template_name
                    )

                    if template.template:
                        self.templates[template_name] = template
                        template_count += 1
                        logger.debug(f"   ✅ 加载模板: {template_name}")

                except Exception as e:
                    logger.error(f"   ❌ 加载模板失败: {template_file} | 错误: {e}")

            logger.success(
                f"✅ [模板管理器] 模板加载完成，共加载 {template_count} 个模板"
            )

            # 如果没有模板文件，创建默认模板
            if template_count == 0:
                self._create_default_templates()

        except Exception as e:
            logger.error(f"❌ [模板管理器] 模板加载异常: {e}")

    def get_template(self, template_name: str) -> Optional[PromptTemplate]:
        """
        获取模板

        Args:
            template_name: 模板名称

        Returns:
            Optional[PromptTemplate]: 模板实例，如果不存在返回None
        """
        template = self.templates.get(template_name)

        if template:
            logger.debug(f"📝 [模板管理器] 获取模板: {template_name}")
        else:
            logger.warning(f"⚠️ [模板管理器] 模板不存在: {template_name}")

        return template

    def render_template(self, template_name: str, **kwargs) -> str:
        """
        渲染模板

        Args:
            template_name: 模板名称
            **kwargs: 模板变量

        Returns:
            str: 渲染后的字符串，如果模板不存在返回空字符串
        """
        template = self.get_template(template_name)
        if template:
            return template.render(**kwargs)
        return ""

    def add_template(self, name: str, template: PromptTemplate) -> None:
        """
        添加模板

        Args:
            name: 模板名称
            template: 模板实例
        """
        self.templates[name] = template
        logger.debug(f"➕ [模板管理器] 添加模板: {name}")

    def save_template(self, template_name: str, template_content: str) -> bool:
        """
        保存模板到文件

        Args:
            template_name: 模板名称
            template_content: 模板内容

        Returns:
            bool: 保存是否成功
        """
        try:
            logger.info(f"💾 [模板管理器] 保存模板: {template_name}")

            # 保存到文件
            file_path = self.template_dir / f"{template_name}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(template_content)

            # 更新内存中的模板
            self.templates[template_name] = PromptTemplate(
                template_content, template_name
            )

            logger.success(f"✅ [模板管理器] 模板保存成功: {file_path}")
            return True

        except Exception as e:
            logger.error(f"❌ [模板管理器] 模板保存失败: {template_name} | 错误: {e}")
            return False

    def get_all_templates(self) -> Dict[str, PromptTemplate]:
        """获取所有模板"""
        return self.templates.copy()

    def _create_default_templates(self) -> None:
        """创建默认模板"""
        logger.info("🔧 [模板管理器] 创建默认模板")

        # 需求分析模板
        requirement_template = """你是一位资深的软件需求分析师，拥有超过10年的需求分析和软件测试经验。

项目背景：{project_background}
分析重点：{analysis_focus}

你的任务是：
1. 深入理解用户提供的需求文档和描述
2. 识别关键功能点、业务流程和约束条件
3. 分析潜在的风险点和边界情况
4. 为后续的测试用例生成提供结构化的需求分析

请基于以上背景和重点，提供专业、详细的需求分析结果。"""

        # 测试用例生成模板
        testcase_template = """你是一位资深的软件测试专家，拥有超过15年的测试用例设计和测试执行经验。

测试目标：{test_objective}
测试范围：{test_scope}
质量要求：{quality_requirements}

你的任务是：
1. 基于需求分析结果，设计全面的测试用例
2. 确保测试用例覆盖正常流程、异常流程和边界条件
3. 每个测试用例都要包含：测试目标、前置条件、测试步骤、预期结果
4. 测试用例要具体、可执行、可验证

请基于以上目标和要求，生成结构化、专业的测试用例。"""

        # UI分析模板
        ui_template = """你是一位专业的UI/UX分析师，专门负责分析用户界面和交互设计。

分析目标：{analysis_target}
界面类型：{interface_type}
关注重点：{focus_areas}

你的任务是：
1. 分析界面截图和设计稿
2. 识别UI元素、布局结构和交互模式
3. 理解用户操作流程和界面逻辑
4. 为自动化测试提供详细的UI分析结果

请基于以上目标和重点，提供准确、详细的UI分析报告。"""

        # 保存默认模板
        self.save_template("requirement_analysis", requirement_template)
        self.save_template("testcase_generation", testcase_template)
        self.save_template("ui_analysis", ui_template)


# 全局模板管理器实例
_template_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """获取全局模板管理器实例（单例模式）"""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager


# 便捷函数
def get_template(template_name: str) -> Optional[PromptTemplate]:
    """
    获取模板的便捷函数

    Args:
        template_name: 模板名称

    Returns:
        Optional[PromptTemplate]: 模板实例
    """
    return get_template_manager().get_template(template_name)


def render_template(template_name: str, **kwargs) -> str:
    """
    渲染模板的便捷函数

    Args:
        template_name: 模板名称
        **kwargs: 模板变量

    Returns:
        str: 渲染后的字符串
    """
    return get_template_manager().render_template(template_name, **kwargs)


# 导出接口
__all__ = [
    "PromptTemplate",
    "TemplateManager",
    "get_template_manager",
    "get_template",
    "render_template",
]
