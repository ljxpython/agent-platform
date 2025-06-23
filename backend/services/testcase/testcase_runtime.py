"""
测试用例生成运行时
基于AI核心框架的测试用例生成专用运行时实现
"""

from typing import Any, Dict

from autogen_core import DefaultTopicId, SingleThreadedAgentRuntime
from loguru import logger

from backend.ai_core.runtime import BaseRuntime
from backend.services.testcase.agents import (
    FinalizationMessage,
    OptimizationMessage,
    RequirementAnalysisAgent,
    RequirementAnalysisMessage,
    TestCaseFinalizationAgent,
    TestCaseGenerationAgent,
    TestCaseGenerationMessage,
    TestCaseOptimizationAgent,
)


class TestCaseRuntime(BaseRuntime):
    """测试用例生成专用运行时"""

    def __init__(self):
        super().__init__()
        self.topic_types = {
            "requirement_analysis": "requirement_analysis",
            "testcase_generation": "testcase_generation",
            "testcase_optimization": "testcase_optimization",
            "testcase_finalization": "testcase_finalization",
        }

        logger.info("🧪 [测试用例运行时] 初始化完成")

    async def register_agents(
        self, runtime: SingleThreadedAgentRuntime, conversation_id: str
    ) -> None:
        """
        注册测试用例生成相关的智能体

        Args:
            runtime: 运行时实例
            conversation_id: 对话ID
        """
        logger.info(f"🤖 [测试用例运行时] 注册智能体 | 对话ID: {conversation_id}")

        try:
            # 注册需求分析智能体
            await RequirementAnalysisAgent.register(
                runtime,
                self.topic_types["requirement_analysis"],
                lambda: RequirementAnalysisAgent(),
            )

            # 注册测试用例生成智能体
            await TestCaseGenerationAgent.register(
                runtime,
                self.topic_types["testcase_generation"],
                lambda: TestCaseGenerationAgent(),
            )

            # 注册测试用例优化智能体
            await TestCaseOptimizationAgent.register(
                runtime,
                self.topic_types["testcase_optimization"],
                lambda: TestCaseOptimizationAgent(),
            )

            # 注册测试用例最终化智能体
            await TestCaseFinalizationAgent.register(
                runtime,
                self.topic_types["testcase_finalization"],
                lambda: TestCaseFinalizationAgent(),
            )

            # 注册消息收集器（暂时注释掉）
            # await MessageCollector.register(
            #     runtime,
            #     "collect_result",
            #     lambda: MessageCollector()
            # )

            logger.success(
                f"✅ [测试用例运行时] 智能体注册完成 | 对话ID: {conversation_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ [测试用例运行时] 智能体注册失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            raise

    async def start_requirement_analysis(
        self, conversation_id: str, requirement_data: Dict[str, Any]
    ) -> None:
        """
        启动需求分析流程

        Args:
            conversation_id: 对话ID
            requirement_data: 需求数据
        """
        logger.info(f"📋 [测试用例运行时] 启动需求分析 | 对话ID: {conversation_id}")

        try:
            # 更新状态
            await self.update_state(
                conversation_id, "requirement_analysis", "processing"
            )

            # 保存用户输入到内存
            await self.save_to_memory(
                conversation_id,
                {
                    "type": "user_input",
                    "content": requirement_data,
                    "stage": "requirement_analysis",
                },
            )

            # 发布消息到需求分析智能体
            runtime = self.get_runtime(conversation_id)
            if runtime:
                # 创建需求分析消息
                req_msg = RequirementAnalysisMessage(
                    conversation_id=conversation_id,
                    text_content=requirement_data.get("text_content", ""),
                    files=requirement_data.get("files", []),
                    round_number=requirement_data.get("round_number", 1),
                )

                await runtime.publish_message(
                    req_msg,
                    topic_id=DefaultTopicId(
                        type=self.topic_types["requirement_analysis"]
                    ),
                )

                logger.success(
                    f"✅ [测试用例运行时] 需求分析消息已发布 | 对话ID: {conversation_id}"
                )
            else:
                raise RuntimeError(f"运行时不存在: {conversation_id}")

        except Exception as e:
            logger.error(
                f"❌ [测试用例运行时] 需求分析启动失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            raise


# 全局测试用例运行时实例
_testcase_runtime: TestCaseRuntime = None


def get_testcase_runtime() -> TestCaseRuntime:
    """获取全局测试用例运行时实例（单例模式）"""
    global _testcase_runtime
    if _testcase_runtime is None:
        _testcase_runtime = TestCaseRuntime()
    return _testcase_runtime


# 导出接口
__all__ = ["TestCaseRuntime", "get_testcase_runtime"]
