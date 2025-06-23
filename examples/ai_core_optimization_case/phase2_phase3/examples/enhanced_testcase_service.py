#!/usr/bin/env python3
"""
增强版测试用例服务示例
展示如何在现有业务中集成Phase 2&3的新功能
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.ai_core import (  # 原有功能; 新增功能
    BaseMiddleware,
    MiddlewareContext,
    ModelType,
    TraceLevel,
    agent_operation,
    cache_result,
    create_assistant_agent,
    get_agent_debugger,
    get_agent_monitor,
    get_memory_manager,
    get_middleware_manager,
    retry_on_failure,
    smart_agent_operation,
)

# 导入内存相关函数
from backend.ai_core.memory import create_buffered_context


class TestCaseValidationMiddleware(BaseMiddleware):
    """测试用例验证中间件"""

    def __init__(self):
        super().__init__("testcase_validation", priority=10)

    async def before_operation(
        self, context: MiddlewareContext, *args, **kwargs
    ) -> bool:
        """操作前验证"""
        if context.operation in ["generate_testcase", "analyze_requirement"]:
            # 验证输入参数
            if not args or not args[0]:
                print(f"⚠️ [验证中间件] 输入参数为空: {context.operation}")
                return False

            # 验证对话ID
            if not context.conversation_id:
                print(f"⚠️ [验证中间件] 缺少对话ID: {context.operation}")
                return False

        return True

    async def after_operation(
        self, context: MiddlewareContext, result: Any, *args, **kwargs
    ) -> Any:
        """操作后处理"""
        if context.operation == "generate_testcase" and result:
            # 验证测试用例格式
            if isinstance(result, str) and "测试用例" in result:
                context.metadata["validation_passed"] = True
            else:
                context.metadata["validation_warning"] = "测试用例格式可能不完整"

        return result

    async def on_error(
        self, context: MiddlewareContext, error: Exception, *args, **kwargs
    ) -> bool:
        """错误处理"""
        print(f"❌ [验证中间件] 操作失败: {context.operation} | 错误: {error}")
        return False


class EnhancedTestCaseService:
    """增强版测试用例服务"""

    def __init__(self):
        """初始化服务"""
        self.agents: Dict[str, Any] = {}
        self.memory_manager = get_memory_manager()

        # 设置中间件
        self._setup_middleware()

        # 启用调试
        debugger = get_agent_debugger()
        debugger.enable_debug(TraceLevel.INFO)

        print("🧪 [增强测试用例服务] 初始化完成")

    def _setup_middleware(self):
        """设置中间件"""
        middleware_manager = get_middleware_manager()

        # 添加测试用例验证中间件
        validation_middleware = TestCaseValidationMiddleware()
        middleware_manager.add_middleware(validation_middleware)

        print("🔧 [增强测试用例服务] 中间件设置完成")

    @smart_agent_operation(
        "create_requirement_agent",
        enable_cache=True,
        cache_ttl=300,  # 5分钟缓存
        enable_retry=True,
        max_retries=2,
    )
    async def create_requirement_agent(
        self, conversation_id: str, project_background: str = "通用项目"
    ) -> Optional[Any]:
        """
        创建需求分析智能体（增强版）

        Args:
            conversation_id: 对话ID
            project_background: 项目背景

        Returns:
            智能体实例
        """
        # 获取或创建内存
        memory = await self.memory_manager.get_agent_memory(conversation_id)
        context = create_buffered_context(buffer_size=4000)

        # 创建智能体
        agent = await create_assistant_agent(
            name="需求分析师",
            system_message=f"""你是一位资深的软件需求分析师，拥有超过10年的需求分析和软件测试经验。

项目背景：{project_background}

你的任务是：
1. 深入理解用户提供的需求文档和描述
2. 识别关键功能点、业务流程和约束条件
3. 分析潜在的风险点和边界情况
4. 为后续的测试用例生成提供结构化的需求分析

请提供专业、详细的需求分析结果。""",
            model_type=ModelType.DEEPSEEK,
            conversation_id=conversation_id,
            auto_memory=True,
            auto_context=True,
        )

        if agent:
            self.agents[f"requirement_{conversation_id}"] = agent

        return agent

    @smart_agent_operation(
        "create_testcase_agent",
        enable_cache=True,
        cache_ttl=300,
        enable_retry=True,
        max_retries=2,
    )
    async def create_testcase_agent(
        self, conversation_id: str, test_scope: str = "核心功能"
    ) -> Optional[Any]:
        """
        创建测试用例生成智能体（增强版）

        Args:
            conversation_id: 对话ID
            test_scope: 测试范围

        Returns:
            智能体实例
        """
        # 获取或创建内存
        memory = await self.memory_manager.get_agent_memory(conversation_id)
        context = create_buffered_context(buffer_size=4000)

        # 创建智能体
        agent = await create_assistant_agent(
            name="测试用例专家",
            system_message=f"""你是一位资深的软件测试专家，拥有超过15年的测试用例设计和测试执行经验。

测试范围：{test_scope}

你的任务是：
1. 基于需求分析结果，设计全面的测试用例
2. 确保测试用例覆盖正常流程、异常流程和边界条件
3. 每个测试用例都要包含：测试目标、前置条件、测试步骤、预期结果
4. 测试用例要具体、可执行、可验证

请生成结构化、专业的测试用例，确保测试覆盖率和质量。""",
            model_type=ModelType.DEEPSEEK,
            conversation_id=conversation_id,
            auto_memory=True,
            auto_context=True,
        )

        if agent:
            self.agents[f"testcase_{conversation_id}"] = agent

        return agent

    @agent_operation(
        "analyze_requirement",
        enable_monitoring=True,
        enable_debug=True,
        enable_middleware=True,
        conversation_id=None,  # 将在运行时设置
    )
    async def analyze_requirement(
        self,
        conversation_id: str,
        requirement_text: str,
        project_background: str = "通用项目",
    ) -> str:
        """
        分析需求（增强版）

        Args:
            conversation_id: 对话ID
            requirement_text: 需求文本
            project_background: 项目背景

        Returns:
            需求分析结果
        """
        # 创建或获取需求分析智能体
        agent = await self.create_requirement_agent(conversation_id, project_background)

        if not agent:
            raise Exception("需求分析智能体创建失败")

        # 模拟智能体处理
        await asyncio.sleep(0.2)  # 模拟处理时间

        analysis_result = f"""
## 需求分析报告

### 项目背景
{project_background}

### 需求概述
{requirement_text[:200]}...

### 关键功能点
1. 用户管理功能
2. 数据处理功能
3. 接口交互功能

### 业务流程
1. 用户登录验证
2. 数据输入和验证
3. 业务逻辑处理
4. 结果输出和反馈

### 风险点分析
1. 数据安全风险
2. 性能瓶颈风险
3. 用户体验风险

### 测试建议
1. 功能测试覆盖所有关键路径
2. 性能测试验证系统负载能力
3. 安全测试确保数据保护
"""

        return analysis_result

    @agent_operation(
        "generate_testcase",
        enable_monitoring=True,
        enable_debug=True,
        enable_middleware=True,
        conversation_id=None,  # 将在运行时设置
    )
    async def generate_testcase(
        self,
        conversation_id: str,
        requirement_analysis: str,
        test_scope: str = "核心功能",
    ) -> str:
        """
        生成测试用例（增强版）

        Args:
            conversation_id: 对话ID
            requirement_analysis: 需求分析结果
            test_scope: 测试范围

        Returns:
            测试用例
        """
        # 创建或获取测试用例智能体
        agent = await self.create_testcase_agent(conversation_id, test_scope)

        if not agent:
            raise Exception("测试用例智能体创建失败")

        # 模拟智能体处理
        await asyncio.sleep(0.3)  # 模拟处理时间

        testcase_result = f"""
## 测试用例集

### 测试范围
{test_scope}

### 测试用例1：用户登录功能测试
**测试目标**：验证用户登录功能的正确性
**前置条件**：系统正常运行，用户账号已创建
**测试步骤**：
1. 打开登录页面
2. 输入正确的用户名和密码
3. 点击登录按钮
**预期结果**：成功登录，跳转到主页面

### 测试用例2：数据输入验证测试
**测试目标**：验证数据输入的有效性检查
**前置条件**：用户已登录系统
**测试步骤**：
1. 进入数据输入页面
2. 输入无效数据格式
3. 提交数据
**预期结果**：系统提示数据格式错误，不允许提交

### 测试用例3：系统性能测试
**测试目标**：验证系统在高负载下的性能表现
**前置条件**：系统部署完成
**测试步骤**：
1. 模拟100个并发用户
2. 执行核心业务操作
3. 监控系统响应时间
**预期结果**：响应时间小于2秒，系统稳定运行

### 测试用例4：异常处理测试
**测试目标**：验证系统异常情况的处理能力
**前置条件**：系统正常运行
**测试步骤**：
1. 模拟网络中断
2. 执行业务操作
3. 恢复网络连接
**预期结果**：系统能够优雅处理异常，提供友好提示
"""

        return testcase_result

    @cache_result(ttl=600)  # 10分钟缓存
    async def get_service_statistics(self) -> Dict[str, Any]:
        """获取服务统计信息（带缓存）"""
        monitor = get_agent_monitor()
        debugger = get_agent_debugger()

        # 获取监控统计
        monitor_summary = monitor.get_performance_summary()

        # 获取调试统计
        debug_summary = debugger.get_debug_summary()

        # 获取智能体统计
        agent_stats = {}
        for agent_key in self.agents.keys():
            stats = monitor.get_agent_stats("DemoAgent")  # 简化处理
            if stats:
                agent_stats[agent_key] = {
                    "total_calls": stats.total_calls,
                    "success_rate": 1 - stats.error_rate,
                    "avg_duration": stats.avg_duration,
                }

        return {
            "service_name": "增强测试用例服务",
            "active_agents": len(self.agents),
            "monitor_summary": monitor_summary,
            "debug_summary": debug_summary,
            "agent_statistics": agent_stats,
            "timestamp": asyncio.get_event_loop().time(),
        }


async def demo_enhanced_service():
    """演示增强版服务"""
    print("🚀 增强版测试用例服务演示")
    print("=" * 50)

    # 创建服务实例
    service = EnhancedTestCaseService()

    conversation_id = "enhanced_demo_conv_456"

    print("\n1. 需求分析（带监控、调试、中间件）:")
    requirement_text = """
    开发一个用户管理系统，包括用户注册、登录、个人信息管理等功能。
    系统需要支持角色权限管理，确保数据安全。
    要求系统响应速度快，用户体验良好。
    """

    analysis_result = await service.analyze_requirement(
        conversation_id, requirement_text, "企业级用户管理系统"
    )
    print(f"   需求分析完成，结果长度: {len(analysis_result)} 字符")

    print("\n2. 测试用例生成（带监控、调试、中间件）:")
    testcase_result = await service.generate_testcase(
        conversation_id, analysis_result, "用户管理核心功能"
    )
    print(f"   测试用例生成完成，结果长度: {len(testcase_result)} 字符")

    print("\n3. 服务统计信息（带缓存）:")
    stats1 = await service.get_service_statistics()
    print(f"   第一次获取统计: {stats1['service_name']}")
    print(f"   活跃智能体数: {stats1['active_agents']}")

    # 第二次调用应该从缓存获取
    stats2 = await service.get_service_statistics()
    print(f"   第二次获取统计（缓存）: {stats2['service_name']}")

    print("\n4. 监控数据分析:")
    monitor = get_agent_monitor()

    # 获取性能摘要
    perf_summary = monitor.get_performance_summary()
    print(f"   总操作次数: {perf_summary.get('total_calls', 0)}")
    print(f"   成功率: {perf_summary.get('success_rate', 0):.2%}")
    print(f"   平均耗时: {perf_summary.get('avg_duration', 0):.3f}s")

    # 获取最近的性能指标
    recent_metrics = monitor.get_recent_metrics(limit=5)
    print(f"   最近操作记录: {len(recent_metrics)} 条")

    print("\n5. 调试信息分析:")
    debugger = get_agent_debugger()

    # 获取调试摘要
    debug_summary = debugger.get_debug_summary()
    print(f"   调试模式: {'启用' if debug_summary['debug_enabled'] else '禁用'}")
    print(f"   跟踪事件数: {debug_summary['total_traces']}")
    print(f"   错误事件数: {debug_summary.get('recent_errors', 0)}")

    # 获取最近的跟踪事件
    recent_traces = debugger.get_traces(limit=3)
    print(f"   最近跟踪事件: {len(recent_traces)} 条")
    for trace in recent_traces:
        print(f"     - {trace.event_type}: {trace.message[:50]}...")


async def main():
    """主函数"""
    try:
        await demo_enhanced_service()

        print("\n" + "=" * 50)
        print("🎉 增强版测试用例服务演示完成！")

        print("\n📋 集成效果总结:")
        print("   ✅ 智能体创建带缓存和重试机制")
        print("   ✅ 业务操作集成监控、调试、中间件")
        print("   ✅ 自定义中间件实现业务验证")
        print("   ✅ 统计信息缓存提升查询性能")
        print("   ✅ 完整的可观测性和错误处理")

        print("\n🔮 业务价值:")
        print("   📊 实时监控智能体性能和健康状态")
        print("   🔍 详细的调试信息帮助问题定位")
        print("   🛡️ 中间件提供统一的验证和处理")
        print("   ⚡ 缓存机制提升系统响应速度")
        print("   🔧 灵活的扩展机制支持业务定制")

    except Exception as e:
        print(f"\n❌ 演示失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
