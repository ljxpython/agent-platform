"""
Midscene 测试脚本生成智能体系统
包含四个智能体：页面元素分析智能体、交互分析智能体、Midscene用例生成智能体、脚本生成智能体
使用AutoGen 0.5.7框架实现
"""

import asyncio
import json
import os
import sys
import time
import traceback
from asyncio import Queue
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import ModelClientStreamingChunkEvent, TextMessage
from autogen_core import (
    CancellationToken,
    ClosureAgent,
    ClosureContext,
    DefaultTopicId,
    MessageContext,
    RoutedAgent,
    SingleThreadedAgentRuntime,
    TopicId,
    TypeSubscription,
    message_handler,
    type_subscription,
)
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from llms import deepseek_agent, doubao_multimodal_agent
from loguru import logger
from pydantic import BaseModel, Field

# ==================== 日志配置 ====================

# 移除默认的日志处理器
logger.remove()

# 添加控制台输出 - 彩色格式，便于开发调试
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>",
    level="DEBUG",
    colorize=True,
    backtrace=True,
    diagnose=True,
)

# 添加文件输出 - 详细日志，用于生产环境
logger.add(
    "logs/midscene_agents_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
    level="INFO",
    rotation="1 day",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
)

# 添加错误日志文件 - 只记录错误和警告
logger.add(
    "logs/midscene_agents_error_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
    level="WARNING",
    rotation="1 day",
    retention="60 days",
    compression="zip",
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
)

# 添加JSON格式日志 - 用于日志分析和监控
logger.add(
    "logs/midscene_agents_structured_{time:YYYY-MM-DD}.json",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
    level="INFO",
    rotation="1 day",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
    serialize=True,
)

# 创建日志目录
Path("logs").mkdir(exist_ok=True)

# 创建结果文件目录
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)


def get_result_file_path(user_id: str) -> str:
    """获取结果文件的完整路径"""
    filename = f"midscene_results_{user_id}.json"
    return str(RESULTS_DIR / filename)


logger.info("🚀 Midscene智能体系统启动 - 日志系统初始化完成")
logger.info(f"📁 日志文件存储路径: {Path('logs').absolute()}")
logger.info(f"🐍 Python版本: {sys.version}")
logger.info(f"⏰ 系统启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# ==================== 应用初始化 ====================

logger.info("🔧 初始化FastAPI应用...")
app = FastAPI(
    title="Midscene Test Generator API",
    version="1.0.0",
    description="基于图片生成Midscene测试脚本",
)

# 配置CORS中间件
logger.info("🌐 配置CORS中间件...")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",  # 前端开发服务器
        "http://127.0.0.1:8080",  # 前端开发服务器（备用）
        "http://localhost:3000",  # 可能的其他前端端口
        "http://127.0.0.1:3000",  # 可能的其他前端端口（备用）
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
logger.success("✅ CORS中间件配置完成")
logger.success("✅ FastAPI应用初始化完成")

# ==================== 队列管理 ====================

logger.info("📋 初始化消息队列管理系统...")
message_queues: Dict[str, Queue] = {}  # 按用户ID隔离队列
logger.info("📊 队列管理系统初始化完成")

# ==================== Topic定义 ====================

logger.info("🏷️ 定义智能体通信Topic...")
UI_ANALYSIS_TOPIC = "ui_analysis"
INTERACTION_ANALYSIS_TOPIC = "interaction_analysis"
MIDSCENE_GENERATION_TOPIC = "midscene_generation"
SCRIPT_GENERATION_TOPIC = "script_generation"
COLLABORATIVE_ANALYSIS_TOPIC = "collaborative_analysis"
TASK_RESULTS_TOPIC = "task_results"

logger.info(f"📌 UI分析Topic: {UI_ANALYSIS_TOPIC}")
logger.info(f"📌 交互分析Topic: {INTERACTION_ANALYSIS_TOPIC}")
logger.info(f"📌 Midscene生成Topic: {MIDSCENE_GENERATION_TOPIC}")
logger.info(f"📌 脚本生成Topic: {SCRIPT_GENERATION_TOPIC}")
logger.info(f"📌 协作分析Topic: {COLLABORATIVE_ANALYSIS_TOPIC}")
logger.info(f"📌 任务结果Topic: {TASK_RESULTS_TOPIC}")
logger.success("✅ Topic定义完成")

# ==================== 数据模型定义 ====================

logger.info("📋 定义数据模型...")


class UIAnalysisRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    image_path: str = Field(..., description="图片路径")
    user_requirement: str = Field(..., description="用户需求描述")

    def __post_init__(self):
        logger.debug(
            f"🔍 创建UI分析请求: user_id={self.user_id}, image_path={self.image_path}"
        )


class InteractionAnalysisRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    ui_elements: str = Field(..., description="UI元素分析结果")
    user_requirement: str = Field(..., description="用户需求描述")

    def __post_init__(self):
        logger.debug(f"🔄 创建交互分析请求: user_id={self.user_id}")


class MidsceneGenerationRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    ui_analysis: str = Field(..., description="UI分析结果")
    interaction_analysis: str = Field(..., description="交互分析结果")
    user_requirement: str = Field(..., description="用户需求描述")

    def __post_init__(self):
        logger.debug(f"🎯 创建Midscene生成请求: user_id={self.user_id}")


class ScriptGenerationRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    midscene_json: str = Field(..., description="Midscene JSON结果")
    user_requirement: str = Field(..., description="用户需求描述")

    def __post_init__(self):
        logger.debug(f"📜 创建脚本生成请求: user_id={self.user_id}")


class CollaborativeAnalysisRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    image_paths: List[str] = Field(..., description="图片路径列表")
    user_requirement: str = Field(..., description="用户需求描述")

    def __post_init__(self):
        logger.debug(
            f"🤝 创建协作分析请求: user_id={self.user_id}, 图片数量={len(self.image_paths)}"
        )


class TaskResult(BaseModel):
    user_id: str = Field(..., description="用户ID")
    agent_name: str = Field(..., description="智能体名称")
    content: str = Field(..., description="处理结果")
    step: str = Field(..., description="处理步骤")

    def __post_init__(self):
        logger.debug(
            f"📊 创建任务结果: user_id={self.user_id}, agent={self.agent_name}, step={self.step}"
        )


logger.success("✅ 数据模型定义完成")

# ==================== UI分析智能体 ====================

logger.info("🤖 定义UI分析智能体...")


@type_subscription(topic_type=UI_ANALYSIS_TOPIC)
class UIAnalysisAgent(RoutedAgent):

    def __init__(self, description: str):
        super().__init__(description=description)
        logger.info(f"🔍 UI分析智能体初始化: {description}")
        # 注意：self.id 在父类初始化后才可用，这里先不记录ID

        self.system_prompt = """你是UI元素识别专家，专门分析界面截图中的UI组件，为自动化测试提供精确的元素信息。

## 核心职责

### 1. 元素识别与分类
- **交互元素**: 按钮、链接、输入框、下拉菜单、复选框、单选按钮、开关
- **显示元素**: 文本、图片、图标、标签、提示信息
- **容器元素**: 表单、卡片、模态框、侧边栏、导航栏
- **列表元素**: 表格、列表项、菜单项、选项卡

### 2. 视觉特征描述标准
- **颜色**: 主色调、背景色、边框色（如"蓝色按钮"、"红色警告文字"）
- **尺寸**: 相对大小（大、中、小）和具体描述
- **形状**: 圆角、方形、圆形等
- **图标**: 具体图标类型（如"搜索图标"、"用户头像图标"）
- **文字**: 完整的文字内容和字体样式

### 3. 位置定位规范
- **绝对位置**: "页面左上角"、"右下角"、"中央区域"
- **相对位置**: "搜索框右侧"、"表单底部"、"导航栏下方"
- **层级关系**: "主容器内"、"弹窗中"、"侧边栏里"

### 4. 功能用途分析
- **操作类型**: 提交、取消、搜索、筛选、导航等
- **交互状态**: 可点击、禁用、选中、悬停等
- **业务功能**: 登录、注册、购买、编辑等

## 输出格式要求

请严格按照以下JSON格式输出，每个元素包含完整信息：

```json
[
  {
    "id": "element_001",
    "name": "登录按钮",
    "element_type": "button",
    "description": "页面右上角的蓝色圆角按钮，白色文字'登录'，位于搜索框右侧",
    "text_content": "登录",
    "position": {
      "area": "页面右上角",
      "relative_to": "搜索框右侧"
    },
    "visual_features": {
      "color": "蓝色背景，白色文字",
      "size": "中等尺寸",
      "shape": "圆角矩形"
    },
    "functionality": "用户登录入口",
    "interaction_state": "可点击",
    "confidence_score": 0.95
  }
]
```

## 质量标准

- **完整性**: 识别所有可见的交互元素（目标≥90%覆盖率）
- **准确性**: 元素类型和描述准确无误
- **详细性**: 每个元素包含足够的视觉特征用于自动化定位
- **结构化**: 严格遵循JSON格式，便于后续处理"""

    @message_handler
    async def analyze_ui(self, message: UIAnalysisRequest, ctx: MessageContext) -> None:
        start_time = time.time()
        logger.info(f"🔍 开始UI元素分析 - 用户ID: {message.user_id}")
        logger.info(f"📷 分析图片: {message.image_path}")
        logger.info(f"📝 用户需求: {message.user_requirement[:100]}...")
        logger.debug(f"🔧 消息上下文: {ctx}")

        try:
            # 验证图片文件是否存在
            image_path = Path(message.image_path)
            if not image_path.exists():
                logger.error(f"❌ 图片文件不存在: {message.image_path}")
                raise FileNotFoundError(f"图片文件不存在: {message.image_path}")

            logger.info(
                f"✅ 图片文件验证通过: {image_path.name} (大小: {image_path.stat().st_size} bytes)"
            )

            # 发送开始分析的消息
            if message.user_id in message_queues:
                logger.debug(f"📤 发送开始分析消息到队列: {message.user_id}")
                await message_queues[message.user_id].put(
                    {
                        "type": "agent_start",
                        "agent": "UI分析智能体",
                        "step": "开始分析UI元素",
                        "content": "正在分析界面截图中的UI元素...",
                    }
                )
                logger.debug("✅ 开始分析消息已发送")
            else:
                logger.warning(f"⚠️ 用户队列不存在: {message.user_id}")

            # 构建分析问题
            question = f"""请分析这张界面截图中的UI元素。用户需求：{message.user_requirement}

{self.system_prompt}

请严格按照上述要求分析图片中的所有UI元素，并以JSON格式输出结果。"""

            logger.debug(f"📝 构建分析问题完成，长度: {len(question)} 字符")

            # 创建多模态消息
            logger.info("🔧 创建多模态消息...")
            from llms import create_multimodal_message

            multimodal_message = create_multimodal_message(
                question, [message.image_path]
            )
            logger.success("✅ 多模态消息创建完成")

            # 使用流式输出进行分析
            logger.info("🚀 开始流式分析处理...")
            ui_analysis_result = ""
            chunk_count = 0
            total_content_length = 0

            async for item in doubao_multimodal_agent.run_stream(multimodal_message):
                if isinstance(item, ModelClientStreamingChunkEvent):
                    # 流式输出内容
                    chunk_content = item.content
                    ui_analysis_result += chunk_content
                    chunk_count += 1
                    total_content_length += len(chunk_content)

                    logger.debug(
                        f"📦 接收流式块 #{chunk_count}: {len(chunk_content)} 字符"
                    )

                    # 发送流式内容到队列
                    if message.user_id in message_queues:
                        await message_queues[message.user_id].put(
                            {
                                "type": "stream_chunk",
                                "agent": "UI分析智能体",
                                "content": chunk_content,
                            }
                        )
                        logger.trace(f"📤 流式块已发送到队列: {message.user_id}")
                    else:
                        logger.warning(
                            f"⚠️ 用户队列不存在，无法发送流式块: {message.user_id}"
                        )

                elif isinstance(item, TextMessage):
                    # 完整输出
                    ui_analysis_result = item.content
                    logger.info(f"📄 接收完整文本消息: {len(ui_analysis_result)} 字符")

                    # 发送完整结果
                    if message.user_id in message_queues:
                        await message_queues[message.user_id].put(
                            {
                                "type": "agent_complete",
                                "agent": "UI分析智能体",
                                "step": "UI元素分析完成",
                                "content": ui_analysis_result,
                            }
                        )
                        logger.debug("✅ 完整结果已发送到队列")

                elif isinstance(item, TaskResult):
                    # 任务结果
                    if item.messages:
                        ui_analysis_result = item.messages[-1].content
                        logger.info(f"📋 接收任务结果: {len(ui_analysis_result)} 字符")
                    else:
                        logger.warning("⚠️ 任务结果中没有消息内容")

            logger.success(
                f"✅ 流式分析完成 - 总块数: {chunk_count}, 总长度: {total_content_length} 字符"
            )

            # 发送结果到消息收集器
            logger.info("📤 发送分析结果到消息收集器...")
            task_result = TaskResult(
                user_id=message.user_id,
                agent_name="UI分析智能体",
                content=ui_analysis_result,
                step="UI元素分析完成",
            )

            await self.publish_message(
                message=task_result,
                topic_id=TopicId(type=TASK_RESULTS_TOPIC, source=self.id.key),
            )
            logger.debug(f"✅ 任务结果已发布到Topic: {TASK_RESULTS_TOPIC}")

            # 发送给交互分析智能体
            logger.info("🔄 发送结果给交互分析智能体...")
            interaction_request = InteractionAnalysisRequest(
                user_id=message.user_id,
                ui_elements=ui_analysis_result,
                user_requirement=message.user_requirement,
            )

            await self.publish_message(
                message=interaction_request,
                topic_id=TopicId(type=INTERACTION_ANALYSIS_TOPIC, source=self.id.key),
            )
            logger.debug(f"✅ 交互分析请求已发布到Topic: {INTERACTION_ANALYSIS_TOPIC}")

            # 计算处理时间
            processing_time = time.time() - start_time
            logger.success(
                f"🎉 UI分析完成 - 用户: {message.user_id}, 耗时: {processing_time:.2f}秒"
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                f"❌ UI分析失败 - 用户: {message.user_id}, 耗时: {processing_time:.2f}秒"
            )
            logger.error(f"🔥 错误详情: {str(e)}")
            logger.error(f"📍 错误堆栈: {traceback.format_exc()}")

            # 发送错误消息到队列
            if message.user_id in message_queues:
                logger.debug("📤 发送错误消息到用户队列...")
                await message_queues[message.user_id].put(
                    {
                        "type": "agent_error",
                        "agent": "UI分析智能体",
                        "step": "UI元素分析失败",
                        "content": f"分析失败: {str(e)}",
                    }
                )
                logger.debug("✅ 错误消息已发送到队列")

            # 发送错误结果到消息收集器
            logger.debug("📤 发送错误结果到消息收集器...")
            error_result = TaskResult(
                user_id=message.user_id,
                agent_name="UI分析智能体",
                content=f"分析失败: {str(e)}",
                step="UI元素分析失败",
            )

            await self.publish_message(
                message=error_result,
                topic_id=TopicId(type=TASK_RESULTS_TOPIC, source=self.id.key),
            )
            logger.debug("✅ 错误结果已发布到消息收集器")


# ==================== 交互分析智能体 ====================

logger.info("🔄 定义交互分析智能体...")


@type_subscription(topic_type=INTERACTION_ANALYSIS_TOPIC)
class InteractionAnalysisAgent(RoutedAgent):

    def __init__(self, description: str):
        super().__init__(description=description)
        logger.info(f"🔄 交互分析智能体初始化: {description}")
        # 注意：self.id 在父类初始化后才可用，这里先不记录ID

        self.system_prompt = """你是用户交互流程分析师，专门分析用户在界面上的操作流程，为自动化测试设计提供用户行为路径。

## 核心职责

### 1. 用户行为路径分析
- **主要流程**: 用户完成核心任务的标准路径
- **替代流程**: 用户可能采用的其他操作方式
- **异常流程**: 错误操作、网络异常等情况的处理
- **回退流程**: 用户撤销、返回等逆向操作

### 2. 交互节点识别
- **入口点**: 用户开始操作的位置
- **决策点**: 用户需要选择的关键节点
- **验证点**: 系统反馈和状态确认
- **出口点**: 流程完成或退出的位置

### 3. 操作序列设计
- **前置条件**: 执行操作前的必要状态
- **操作步骤**: 具体的用户动作序列
- **后置验证**: 操作完成后的状态检查
- **错误处理**: 异常情况的应对措施

### 4. 用户体验考量
- **操作便利性**: 符合用户习惯的操作方式
- **认知负荷**: 避免复杂的操作序列
- **反馈及时性**: 操作结果的即时反馈
- **容错性**: 允许用户纠错的机制

## 输出格式要求

请按照以下结构化格式输出交互流程：

```json
{
  "primary_flows": [
    {
      "flow_name": "用户登录流程",
      "description": "用户通过用户名密码登录系统",
      "steps": [
        {
          "step_id": 1,
          "action": "点击登录按钮",
          "target_element": "页面右上角蓝色登录按钮",
          "expected_result": "显示登录表单",
          "precondition": "用户未登录状态"
        }
      ],
      "success_criteria": "成功登录并跳转到主页",
      "error_scenarios": ["用户名密码错误", "网络连接失败"]
    }
  ],
  "alternative_flows": [],
  "interaction_patterns": {
    "navigation_style": "顶部导航栏",
    "input_validation": "实时验证",
    "feedback_mechanism": "弹窗提示",
    "error_handling": "内联错误信息"
  }
}
```"""

    @message_handler
    async def analyze_interaction(
        self, message: InteractionAnalysisRequest, ctx: MessageContext
    ) -> None:
        logger.info(f"开始交互流程分析，用户ID: {message.user_id}")

        try:
            # 发送开始分析的消息
            if message.user_id in message_queues:
                await message_queues[message.user_id].put(
                    {
                        "type": "agent_start",
                        "agent": "交互分析智能体",
                        "step": "开始分析用户交互流程",
                        "content": "正在基于UI元素设计用户交互流程...",
                    }
                )

            # 创建交互分析智能体
            interaction_agent = AssistantAgent(
                "interaction_analyst",
                model_client=doubao_multimodal_agent.agent.model_client,
                system_message=self.system_prompt,
                model_client_stream=True,  # 启用流式输出
            )

            question = f"""基于以下UI元素分析结果，请分析用户交互流程。

用户需求：{message.user_requirement}

UI元素分析结果：
{message.ui_elements}

请根据用户需求和UI元素，设计完整的用户交互流程，并严格按照JSON格式输出。"""

            # 使用流式输出
            interaction_analysis_result = ""
            async for item in interaction_agent.run_stream(task=question):
                if isinstance(item, ModelClientStreamingChunkEvent):
                    # 流式输出内容
                    chunk_content = item.content
                    interaction_analysis_result += chunk_content

                    # 发送流式内容到队列
                    if message.user_id in message_queues:
                        await message_queues[message.user_id].put(
                            {
                                "type": "stream_chunk",
                                "agent": "交互分析智能体",
                                "content": chunk_content,
                            }
                        )

                elif isinstance(item, TextMessage):
                    # 完整输出
                    interaction_analysis_result = item.content

                    # 发送完整结果
                    if message.user_id in message_queues:
                        await message_queues[message.user_id].put(
                            {
                                "type": "agent_complete",
                                "agent": "交互分析智能体",
                                "step": "交互流程分析完成",
                                "content": interaction_analysis_result,
                            }
                        )

                elif isinstance(item, TaskResult):
                    # 任务结果
                    if item.messages:
                        interaction_analysis_result = item.messages[-1].content

            # 发送结果到消息收集器
            await self.publish_message(
                message=TaskResult(
                    user_id=message.user_id,
                    agent_name="交互分析智能体",
                    content=interaction_analysis_result,
                    step="交互流程分析完成",
                ),
                topic_id=TopicId(type=TASK_RESULTS_TOPIC, source=self.id.key),
            )

            # 发送给Midscene生成智能体
            await self.publish_message(
                message=MidsceneGenerationRequest(
                    user_id=message.user_id,
                    ui_analysis=message.ui_elements,
                    interaction_analysis=interaction_analysis_result,
                    user_requirement=message.user_requirement,
                ),
                topic_id=TopicId(type=MIDSCENE_GENERATION_TOPIC, source=self.id.key),
            )

        except Exception as e:
            logger.error(f"交互分析失败: {e}")

            # 发送错误消息到队列
            if message.user_id in message_queues:
                await message_queues[message.user_id].put(
                    {
                        "type": "agent_error",
                        "agent": "交互分析智能体",
                        "step": "交互流程分析失败",
                        "content": f"分析失败: {str(e)}",
                    }
                )

            await self.publish_message(
                message=TaskResult(
                    user_id=message.user_id,
                    agent_name="交互分析智能体",
                    content=f"分析失败: {str(e)}",
                    step="交互流程分析失败",
                ),
                topic_id=TopicId(type=TASK_RESULTS_TOPIC, source=self.id.key),
            )


# Midscene用例生成智能体
@type_subscription(topic_type=MIDSCENE_GENERATION_TOPIC)
class MidsceneGenerationAgent(RoutedAgent):

    def __init__(self, description: str):
        super().__init__(description=description)
        self.system_prompt = """你是MidScene.js自动化测试专家，专门基于UI专家和交互分析师的分析结果，设计符合MidScene.js脚本风格的测试用例。

## MidScene.js 核心知识（基于官方文档）

### 支持的动作类型

#### 1. 复合操作
- **ai**: 自然语言描述的复合操作，如 "type 'computer' in search box, hit Enter"
- **aiAction**: ai的完整形式，功能相同

#### 2. 即时操作（精确控制时使用）
- **aiTap**: 点击操作，用于按钮、链接、菜单项
- **aiInput**: 文本输入，格式为 aiInput: "输入内容", locate: "元素描述"
- **aiHover**: 鼠标悬停，用于下拉菜单触发
- **aiScroll**: 滚动操作，支持方向和距离
- **aiKeyboardPress**: 键盘操作，如Enter、Tab等

#### 3. 数据提取操作
- **aiQuery**: 通用查询，支持复杂数据结构，使用多行格式
- **aiBoolean**: 布尔值查询
- **aiNumber**: 数值查询
- **aiString**: 字符串查询

#### 4. 验证和等待
- **aiAssert**: 断言验证
- **aiWaitFor**: 等待条件满足
- **sleep**: 固定等待（毫秒）

### MidScene.js 提示词最佳实践（基于官方指南）

#### 1. 提供详细描述和示例
- ✅ 优秀描述: "找到搜索框（搜索框的上方应该有区域切换按钮，如'国内'，'国际'），输入'耳机'，敲回车"
- ❌ 简单描述: "搜'耳机'"
- ✅ 详细断言: "界面上有个'外卖服务'的板块，并且标识着'正常'"
- ❌ 模糊断言: "外卖服务正在正常运行"

#### 2. 精确的视觉定位描述
- ✅ 详细位置: "页面右上角的'Add'按钮，它是一个带有'+'图标的按钮，位于'range'下拉菜单的右侧"
- ❌ 模糊位置: "Add按钮"
- 包含视觉特征: 颜色、形状、图标、相对位置
- 提供上下文参考: 周围元素作为定位锚点

#### 3. 单一职责原则（一个指令只做一件事）
- ✅ 分解操作:
  - "点击登录按钮"
  - "在表单中[邮箱]输入'test@test.com'"
  - "在表单中[密码]输入'test'"
  - "点击注册按钮"
- ❌ 复合操作: "点击登录按钮，然后点击注册按钮，在表单中输入邮箱和密码，然后点击注册按钮"

#### 4. API选择策略
- **确定交互类型时优先使用即时操作**: aiTap('登录按钮') > ai('点击登录按钮')
- **复杂流程使用ai**: 适合多步骤操作规划
- **数据提取使用aiQuery**: 避免使用aiAssert进行数据提取

#### 5. 基于视觉而非DOM属性
- ✅ 视觉描述: "标题是蓝色的"
- ❌ DOM属性: "标题有个`test-id-size`属性"
- ✅ 界面状态: "页面显示登录成功消息"
- ❌ 浏览器状态: "异步请求已经结束了"

#### 6. 提供选项而非精确数值
- ✅ 颜色选项: "文本的颜色，返回：蓝色/红色/黄色/绿色/白色/黑色/其他"
- ❌ 精确数值: "文本颜色的十六进制值"

#### 7. 交叉验证和断言策略
- 操作后检查结果: 每个关键操作后添加验证步骤
- 使用aiAssert验证状态: 确认操作是否成功
- 避免依赖不可见状态: 所有验证基于界面可见内容

## 重点任务

你将接收UI专家和交互分析师的分析结果，需要：

1. **整合分析结果**: 结合UI元素识别和交互流程分析
2. **设计测试场景**: 基于用户行为路径设计完整测试用例
3. **应用提示词最佳实践**:
   - 提供详细的视觉描述和上下文信息
   - 遵循单一职责原则，每个步骤只做一件事
   - 优先使用即时操作API（aiTap、aiInput等）
   - 基于视觉特征而非DOM属性进行描述
4. **详细视觉描述**: 利用UI专家提供的元素特征进行精确定位
5. **完整验证流程**: 包含操作前置条件、执行步骤和结果验证
6. **交叉验证策略**: 为每个关键操作添加验证步骤

## 输出格式要求

请输出结构化的测试场景，格式如下：

```json
{
  "test_scenarios": [
    {
      "scenario_name": "用户登录测试",
      "description": "验证用户通过用户名密码登录系统的完整流程",
      "priority": "high",
      "estimated_duration": "30秒",
      "preconditions": ["用户未登录", "页面已加载完成"],
      "test_steps": [
        {
          "step_id": 1,
          "action_type": "aiTap",
          "action_description": "页面右上角的蓝色'登录'按钮，它是一个圆角矩形按钮，白色文字，位于搜索框右侧约20像素处",
          "visual_target": "蓝色背景的登录按钮，具有圆角设计，按钮上显示白色'登录'文字，位于页面顶部导航区域的右侧",
          "expected_result": "显示登录表单弹窗或跳转到登录页面",
          "validation_step": "检查是否出现用户名和密码输入框"
        }
      ],
      "validation_points": [
        "登录按钮可点击",
        "表单正确显示",
        "输入验证正常",
        "登录成功跳转"
      ]
    }
  ]
}
```

## 设计原则

1. **基于真实分析**: 严格基于UI专家和交互分析师的输出设计测试
2. **MidScene.js风格**: 使用自然语言描述，符合MidScene.js的AI驱动特性
3. **视觉定位优先**: 充分利用UI专家提供的详细视觉特征
4. **流程完整性**: 确保测试场景覆盖完整的用户操作路径
5. **可执行性**: 每个步骤都能直接转换为MidScene.js YAML脚本
6. **提示词工程最佳实践**:
   - 详细描述胜过简单描述
   - 提供视觉上下文和参考点
   - 单一职责，每个步骤只做一件事
   - 基于界面可见内容而非技术实现
   - 为关键操作添加验证步骤
7. **稳定性优先**: 设计能够在多次运行中获得稳定响应的测试步骤
8. **错误处理**: 考虑异常情况和用户可能的错误操作
9. **多语言支持**: 支持中英文混合的界面描述"""

    @message_handler
    async def generate_midscene_test(
        self, message: MidsceneGenerationRequest, ctx: MessageContext
    ) -> None:
        logger.info(f"开始生成Midscene测试脚本，用户ID: {message.user_id}")

        try:
            # 发送开始分析的消息
            if message.user_id in message_queues:
                await message_queues[message.user_id].put(
                    {
                        "type": "agent_start",
                        "agent": "Midscene用例生成智能体",
                        "step": "开始生成Midscene测试脚本",
                        "content": "正在整合分析结果，生成Midscene.js测试脚本...",
                    }
                )

            # 创建Midscene生成智能体
            midscene_agent = AssistantAgent(
                "midscene_generator",
                model_client=doubao_multimodal_agent.agent.model_client,
                system_message=self.system_prompt,
                model_client_stream=True,  # 启用流式输出
            )

            question = f"""基于以下分析结果，生成符合MidScene.js规范的测试脚本。

用户需求：{message.user_requirement}

UI元素分析结果：
{message.ui_analysis}

交互流程分析结果：
{message.interaction_analysis}

请整合上述分析结果，设计完整的MidScene.js测试场景，严格按照JSON格式输出，确保：
1. 每个测试步骤都有详细的视觉描述
2. 遵循MidScene.js的最佳实践
3. 包含完整的验证流程
4. 可以直接转换为可执行的测试脚本"""

            # 使用流式输出
            midscene_test_result = ""
            async for item in midscene_agent.run_stream(task=question):
                if isinstance(item, ModelClientStreamingChunkEvent):
                    # 流式输出内容
                    chunk_content = item.content
                    midscene_test_result += chunk_content

                    # 发送流式内容到队列
                    if message.user_id in message_queues:
                        await message_queues[message.user_id].put(
                            {
                                "type": "stream_chunk",
                                "agent": "Midscene用例生成智能体",
                                "content": chunk_content,
                            }
                        )

                elif isinstance(item, TextMessage):
                    # 完整输出
                    midscene_test_result = item.content

                    # 发送完整结果
                    if message.user_id in message_queues:
                        await message_queues[message.user_id].put(
                            {
                                "type": "agent_complete",
                                "agent": "Midscene用例生成智能体",
                                "step": "Midscene测试脚本生成完成",
                                "content": midscene_test_result,
                            }
                        )

                elif isinstance(item, TaskResult):
                    # 任务结果
                    if item.messages:
                        midscene_test_result = item.messages[-1].content

            # 发送结果到消息收集器
            await self.publish_message(
                message=TaskResult(
                    user_id=message.user_id,
                    agent_name="Midscene用例生成智能体",
                    content=midscene_test_result,
                    step="Midscene测试脚本生成完成",
                ),
                topic_id=TopicId(type=TASK_RESULTS_TOPIC, source=self.id.key),
            )

            # 标记任务完成
            if message.user_id in message_queues:
                await message_queues[message.user_id].put(
                    {
                        "type": "system_complete",
                        "message": "所有智能体分析完成",
                        "content": "Midscene测试脚本已生成完成",
                    }
                )

        except Exception as e:
            logger.error(f"Midscene脚本生成失败: {e}")

            # 发送错误消息到队列
            if message.user_id in message_queues:
                await message_queues[message.user_id].put(
                    {
                        "type": "agent_error",
                        "agent": "Midscene用例生成智能体",
                        "step": "Midscene测试脚本生成失败",
                        "content": f"生成失败: {str(e)}",
                    }
                )

            await self.publish_message(
                message=TaskResult(
                    user_id=message.user_id,
                    agent_name="Midscene用例生成智能体",
                    content=f"生成失败: {str(e)}",
                    step="Midscene测试脚本生成失败",
                ),
                topic_id=TopicId(type=TASK_RESULTS_TOPIC, source=self.id.key),
            )


# ==================== 脚本生成智能体 ====================

logger.info("📜 定义脚本生成智能体...")


@type_subscription(topic_type=SCRIPT_GENERATION_TOPIC)
class ScriptGenerationAgent(RoutedAgent):

    def __init__(self, description: str):
        super().__init__(description=description)
        logger.info(f"📜 脚本生成智能体初始化: {description}")

        # 读取 Playwright 示例文件
        self.playwright_sample = self._load_playwright_sample()

        self.system_prompt = f"""你是专业的测试脚本生成专家，专门将Midscene JSON测试用例转换为可执行的YAML脚本和Playwright脚本。

## 核心职责

### 1. JSON解析和提取
- 解析Midscene JSON格式的测试用例
- 提取测试场景、步骤和验证点
- 识别操作类型和目标元素

### 2. YAML脚本生成
- 转换为标准的Midscene YAML格式
- 保持操作的语义和逻辑
- 确保脚本的可读性和可维护性

### 3. Playwright脚本生成
- 基于提供的示例模板生成Playwright测试脚本
- 使用Midscene的AI操作API
- 遵循TypeScript语法规范

## Playwright示例参考

以下是标准的Playwright + Midscene测试脚本示例：

```typescript
{self.playwright_sample}
```

## 输出格式要求

请严格按照以下JSON格式输出两种脚本：

```json
{{
  "yaml_script": "完整的YAML格式脚本内容",
  "playwright_script": "完整的TypeScript格式Playwright脚本内容",
  "script_info": {{
    "test_name": "测试名称",
    "description": "测试描述",
    "estimated_duration": "预估执行时间",
    "steps_count": 步骤数量
  }}
}}
```

## 生成规则

### YAML脚本规则
1. 使用标准的Midscene YAML语法
2. 每个操作独立成行
3. 保持缩进和格式规范
4. 包含必要的等待和验证步骤

### Playwright脚本规则
1. **固定头部导入**: 所有Playwright脚本必须以以下导入语句开头：
   import {{ expect }} from "@playwright/test";
   import {{ test }} from "./fixture";
2. 导入必要的fixture和类型定义
3. 使用beforeEach设置初始状态
4. 每个测试步骤使用对应的AI操作API
5. 包含适当的断言和验证
6. 遵循TypeScript语法规范
7. 使用提供的示例作为模板参考

## 质量标准
- **准确性**: 忠实转换原始JSON中的操作逻辑
- **可执行性**: 生成的脚本可以直接运行
- **可读性**: 代码结构清晰，注释适当
- **完整性**: 包含所有必要的步骤和验证"""

    def _load_playwright_sample(self) -> str:
        """加载Playwright示例文件"""
        try:
            # 读取search.spec.ts
            search_spec_path = Path("uitest/e2e/search.spec.ts")
            fixture_path = Path("uitest/e2e/fixture.ts")

            search_content = ""
            fixture_content = ""

            if search_spec_path.exists():
                with open(search_spec_path, "r", encoding="utf-8") as f:
                    search_content = f.read()

            if fixture_path.exists():
                with open(fixture_path, "r", encoding="utf-8") as f:
                    fixture_content = f.read()

            # 组合示例内容
            sample = f"""// fixture.ts 内容
{fixture_content}

// search.spec.ts 内容
{search_content}"""

            logger.info("✅ Playwright示例文件加载成功")
            return sample

        except Exception as e:
            logger.warning(f"⚠️ 无法加载Playwright示例文件: {e}")
            # 返回默认示例（确保包含固定的导入语句）
            return """import {{ expect }} from "@playwright/test";
import {{ test }} from "./fixture";

test.beforeEach(async ({{ page }}) => {{
  await page.goto("https://example.com");
  await page.waitForLoadState("networkidle");
}});

test("示例测试", async ({{ ai, aiQuery, aiAssert, aiInput, aiTap, aiScroll, aiWaitFor }}) => {{
  // 使用 aiInput 输入内容
  await aiInput('搜索内容', '搜索框');

  // 使用 aiTap 点击按钮
  await aiTap('搜索按钮');

  // 等待结果加载
  await aiWaitFor('搜索结果已加载', {{ timeoutMs: 30000 }});

  // 使用 aiAssert 验证结果
  await aiAssert("页面显示搜索结果");
}});"""

    @message_handler
    async def generate_scripts(
        self, message: ScriptGenerationRequest, ctx: MessageContext
    ) -> None:
        start_time = time.time()
        logger.info(f"📜 开始生成脚本 - 用户ID: {message.user_id}")
        logger.debug(f"📝 Midscene JSON长度: {len(message.midscene_json)} 字符")

        try:
            # 发送开始消息
            if message.user_id in message_queues:
                await message_queues[message.user_id].put(
                    {
                        "type": "agent_start",
                        "agent": "脚本生成智能体",
                        "step": "开始生成YAML和Playwright脚本",
                        "content": "正在解析Midscene JSON并生成可执行脚本...",
                    }
                )
                logger.debug("✅ 脚本生成开始消息已发送")

            # 构建生成问题
            question = f"""请将以下Midscene JSON测试用例转换为YAML脚本和Playwright脚本。

用户需求：{message.user_requirement}

Midscene JSON测试用例：
{message.midscene_json}

{self.system_prompt}

请严格按照JSON格式输出两种脚本，确保：
1. YAML脚本符合Midscene规范
2. Playwright脚本基于提供的示例模板
3. Playwright脚本必须以固定的导入语句开头：
   import {{ expect }} from "@playwright/test";
   import {{ test }} from "./fixture";
4. 两种脚本都能正确执行相同的测试逻辑
5. 包含适当的等待和验证步骤"""

            logger.debug(f"📝 构建生成问题完成，长度: {len(question)} 字符")

            # 使用DeepSeek智能体进行流式生成
            logger.info("🚀 开始流式脚本生成...")
            script_result = ""
            chunk_count = 0
            total_content_length = 0

            async for item in deepseek_agent.run_stream(task=question):
                if isinstance(item, ModelClientStreamingChunkEvent):
                    # 流式输出内容
                    chunk_content = item.content
                    script_result += chunk_content
                    chunk_count += 1
                    total_content_length += len(chunk_content)

                    logger.debug(
                        f"📦 接收流式块 #{chunk_count}: {len(chunk_content)} 字符"
                    )

                    # 发送流式内容到队列
                    if message.user_id in message_queues:
                        await message_queues[message.user_id].put(
                            {
                                "type": "stream_chunk",
                                "agent": "脚本生成智能体",
                                "content": chunk_content,
                            }
                        )
                        logger.trace(f"📤 流式块已发送到队列: {message.user_id}")
                    else:
                        logger.warning(
                            f"⚠️ 用户队列不存在，无法发送流式块: {message.user_id}"
                        )

                elif isinstance(item, TextMessage):
                    # 完整输出
                    script_result = item.content
                    logger.info(f"📄 接收完整文本消息: {len(script_result)} 字符")

                elif isinstance(item, TaskResult):
                    # 任务结果
                    if item.messages:
                        script_result = item.messages[-1].content
                        logger.info(f"📋 接收任务结果: {len(script_result)} 字符")
                    else:
                        logger.warning("⚠️ 任务结果中没有消息内容")

            logger.success(
                f"✅ 流式脚本生成完成 - 总块数: {chunk_count}, 总长度: {total_content_length} 字符"
            )

            # 发送完成消息
            if message.user_id in message_queues:
                await message_queues[message.user_id].put(
                    {
                        "type": "agent_complete",
                        "agent": "脚本生成智能体",
                        "step": "YAML和Playwright脚本生成完成",
                        "content": script_result,
                    }
                )
                logger.debug("✅ 脚本生成完成消息已发送")

            # 发送结果到消息收集器
            logger.info("📤 发送脚本生成结果到消息收集器...")
            task_result = TaskResult(
                user_id=message.user_id,
                agent_name="脚本生成智能体",
                content=script_result,
                step="YAML和Playwright脚本生成完成",
            )

            await self.publish_message(
                message=task_result,
                topic_id=TopicId(type=TASK_RESULTS_TOPIC, source=self.id.key),
            )
            logger.debug(f"✅ 任务结果已发布到Topic: {TASK_RESULTS_TOPIC}")

            # 计算处理时间
            processing_time = time.time() - start_time
            logger.success(
                f"🎉 脚本生成完成 - 用户: {message.user_id}, 耗时: {processing_time:.2f}秒"
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                f"❌ 脚本生成失败 - 用户: {message.user_id}, 耗时: {processing_time:.2f}秒"
            )
            logger.error(f"🔥 错误详情: {str(e)}")
            logger.error(f"📍 错误堆栈: {traceback.format_exc()}")

            # 发送错误消息到队列
            if message.user_id in message_queues:
                logger.debug("📤 发送错误消息到用户队列...")
                await message_queues[message.user_id].put(
                    {
                        "type": "agent_error",
                        "agent": "脚本生成智能体",
                        "step": "脚本生成失败",
                        "content": f"生成失败: {str(e)}",
                    }
                )
                logger.debug("✅ 错误消息已发送到队列")

            # 发送错误结果到消息收集器
            logger.debug("📤 发送错误结果到消息收集器...")
            error_result = TaskResult(
                user_id=message.user_id,
                agent_name="脚本生成智能体",
                content=f"生成失败: {str(e)}",
                step="脚本生成失败",
            )

            await self.publish_message(
                message=error_result,
                topic_id=TopicId(type=TASK_RESULTS_TOPIC, source=self.id.key),
            )
            logger.debug("✅ 错误结果已发布到消息收集器")


# 协作分析智能体 - 协调三个智能体的工作流程
@type_subscription(topic_type=COLLABORATIVE_ANALYSIS_TOPIC)
class CollaborativeAnalysisAgent(RoutedAgent):

    def __init__(self, description: str):
        super().__init__(description=description)

    @message_handler
    async def handle_collaborative_analysis(
        self, message: CollaborativeAnalysisRequest, ctx: MessageContext
    ) -> None:
        logger.info(
            f"开始协作分析，用户ID: {message.user_id}, 图片数量: {len(message.image_paths)}"
        )

        try:
            # 发送开始消息
            if message.user_id in message_queues:
                await message_queues[message.user_id].put(
                    {
                        "type": "system_start",
                        "message": "协作分析开始",
                        "content": f"开始三智能体协作分析流程，共 {len(message.image_paths)} 张图片",
                    }
                )

            # 第一步：UI分析智能体分析所有图片
            all_ui_analysis = []

            for i, image_path in enumerate(message.image_paths):
                if message.user_id in message_queues:
                    await message_queues[message.user_id].put(
                        {
                            "type": "step_start",
                            "message": f"UI分析第 {i+1}/{len(message.image_paths)} 张图片",
                            "content": f"正在分析图片: {Path(image_path).name}",
                        }
                    )

                # 发布UI分析请求
                await self.publish_message(
                    message=UIAnalysisRequest(
                        user_id=message.user_id,
                        image_path=image_path,
                        user_requirement=message.user_requirement,
                    ),
                    topic_id=TopicId(type=UI_ANALYSIS_TOPIC, source=self.id.key),
                )

                # 这里需要等待UI分析完成，实际实现中可以通过回调或状态管理来处理
                # 为了简化，我们先继续下一步的逻辑设计

            # 注意：实际的协作逻辑需要更复杂的状态管理
            # 这里先提供基本框架，具体实现需要状态跟踪

        except Exception as e:
            logger.error(f"协作分析失败: {e}")

            if message.user_id in message_queues:
                await message_queues[message.user_id].put(
                    {
                        "type": "system_error",
                        "message": "协作分析失败",
                        "content": f"错误: {str(e)}",
                    }
                )


# 消息收集智能体
CLOSURE_AGENT_TYPE = "collect_result_agent"


async def collect_results(
    _agent: ClosureContext, message: TaskResult, ctx: MessageContext
) -> None:
    """收集所有智能体的处理结果"""
    logger.info(f"收集结果: {message.agent_name} - {message.step}")

    # 将结果发送到用户队列
    if message.user_id in message_queues:
        await message_queues[message.user_id].put(
            {
                "agent": message.agent_name,
                "step": message.step,
                "content": message.content,
                "timestamp": asyncio.get_event_loop().time(),
            }
        )

    # 保存到文件
    result_file_path = get_result_file_path(message.user_id)
    async with aiofiles.open(result_file_path, mode="a+", encoding="utf-8") as f:
        result_data = {
            "user_id": message.user_id,
            "agent": message.agent_name,
            "step": message.step,
            "content": message.content,
            "timestamp": asyncio.get_event_loop().time(),
        }
        await f.write(json.dumps(result_data, ensure_ascii=False) + "\n")


# 系统管理类
class MidsceneAgentSystem:

    def __init__(self):
        self.user_runtimes: Dict[str, SingleThreadedAgentRuntime] = {}

    async def create_user_runtime(self, user_id: str) -> SingleThreadedAgentRuntime:
        """为用户创建运行时"""
        if user_id in self.user_runtimes:
            return self.user_runtimes[user_id]
        else:
            runtime = SingleThreadedAgentRuntime()
            self.user_runtimes[user_id] = runtime
            return runtime

    async def init_runtime(self, runtime: SingleThreadedAgentRuntime):
        """初始化运行时，注册所有智能体"""
        # 注册UI分析智能体
        await UIAnalysisAgent.register(
            runtime,
            UI_ANALYSIS_TOPIC,
            lambda: UIAnalysisAgent(description="页面元素分析智能体"),
        )

        # 注册交互分析智能体
        await InteractionAnalysisAgent.register(
            runtime,
            INTERACTION_ANALYSIS_TOPIC,
            lambda: InteractionAnalysisAgent(description="交互分析智能体"),
        )

        # 注册Midscene生成智能体
        await MidsceneGenerationAgent.register(
            runtime,
            MIDSCENE_GENERATION_TOPIC,
            lambda: MidsceneGenerationAgent(description="Midscene用例生成智能体"),
        )

        # 注册脚本生成智能体
        await ScriptGenerationAgent.register(
            runtime,
            SCRIPT_GENERATION_TOPIC,
            lambda: ScriptGenerationAgent(description="脚本生成智能体"),
        )

        # 注册消息收集智能体
        await ClosureAgent.register_closure(
            runtime,
            CLOSURE_AGENT_TYPE,
            collect_results,
            subscriptions=lambda: [
                TypeSubscription(
                    topic_type=TASK_RESULTS_TOPIC, agent_type=CLOSURE_AGENT_TYPE
                )
            ],
        )

    async def start_analysis(
        self, user_id: str, image_path: str, user_requirement: str
    ):
        """启动单图片分析流程（兼容方法）"""
        return await self.start_collaborative_analysis(
            user_id, [image_path], user_requirement
        )

    async def start_collaborative_analysis(
        self, user_id: str, image_paths: List[str], user_requirement: str
    ):
        """启动协作分析流程 - 多图片按顺序分析"""
        runtime = await self.create_user_runtime(user_id)
        runtime.start()

        # 初始化运行时
        await self.init_runtime(runtime)

        # 发布协作分析请求
        await runtime.publish_message(
            CollaborativeAnalysisRequest(
                user_id=user_id,
                image_paths=image_paths,
                user_requirement=user_requirement,
            ),
            topic_id=DefaultTopicId(type=COLLABORATIVE_ANALYSIS_TOPIC),
        )

        return runtime


# 创建系统实例
midscene_system = MidsceneAgentSystem()


def get_queue(user_id: str) -> Queue:
    """获取用户消息队列"""
    if user_id not in message_queues:
        message_queues[user_id] = Queue(maxsize=100)
    return message_queues[user_id]


async def message_generator(user_id: str):
    """消息生成器，用于SSE流式输出"""
    queue = get_queue(user_id)
    try:
        while True:
            message = await queue.get()

            # 处理不同类型的消息
            if isinstance(message, dict):
                message_type = message.get("type", "unknown")

                if message_type == "system_start":
                    # 系统开始工作
                    yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"

                elif message_type == "agent_start":
                    # 智能体开始工作
                    yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"

                elif message_type == "step_info":
                    # 步骤信息
                    yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"

                elif message_type == "stream_chunk":
                    # 流式内容块
                    yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"

                elif message_type == "agent_complete":
                    # 智能体完成工作
                    yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"

                elif message_type == "agent_error":
                    # 智能体错误
                    yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"

                elif message_type == "system_complete":
                    # 系统完成所有工作
                    yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"
                    break

                elif message_type == "system_error":
                    # 系统错误
                    yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"
                    break

                else:
                    # 其他类型的字典消息
                    yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"

            elif message == "COMPLETE":
                # 兼容旧的完成标记
                yield f"data: {json.dumps({'type': 'system_complete', 'message': '所有分析完成'}, ensure_ascii=False)}\n\n"
                break

            else:
                # 其他类型的消息
                yield f"data: {json.dumps({'type': 'message', 'content': str(message)}, ensure_ascii=False)}\n\n"

            queue.task_done()
    finally:
        # 不在这里清理队列，由协作分析函数负责清理
        logger.debug(f"📋 消息生成器结束 - 用户: {user_id}")
        pass


# 协作分析函数
async def run_collaborative_analysis(
    user_id: str, image_paths: List[str], user_requirement: str
):
    """运行协作分析流程 - 正确的协作顺序"""
    start_time = time.time()
    logger.info(f"🤝 开始协作分析流程 - 用户: {user_id}")
    logger.info(f"📷 图片数量: {len(image_paths)}")
    logger.info(f"📝 用户需求: {user_requirement[:100]}...")

    try:
        # 启动两个智能体并行工作
        logger.info("🚀 启动并行分析任务...")
        if user_id in message_queues:
            await message_queues[user_id].put(
                {
                    "type": "system_start",
                    "message": "开始协作分析",
                    "content": f"启动两个智能体并行工作：UI分析智能体处理 {len(image_paths)} 张图片，交互分析智能体处理用户需求",
                }
            )
            logger.debug("✅ 系统开始消息已发送到队列")
        else:
            logger.warning(f"⚠️ 用户队列不存在，无法发送系统开始消息: {user_id}")

        # 创建任务来并行执行UI分析和交互分析
        logger.info("📋 创建并行分析任务...")
        ui_task = asyncio.create_task(run_ui_analysis(user_id, image_paths))
        interaction_task = asyncio.create_task(
            run_interaction_analysis(user_id, user_requirement)
        )
        logger.debug("✅ 并行任务创建完成")

        # 等待两个智能体完成工作
        logger.info("⏳ 等待并行分析任务完成...")
        ui_result, interaction_result = await asyncio.gather(ui_task, interaction_task)

        parallel_time = time.time() - start_time
        logger.success(f"✅ 并行分析完成 - 耗时: {parallel_time:.2f}秒")
        logger.info(f"📊 UI分析结果长度: {len(ui_result)} 字符")
        logger.info(f"📊 交互分析结果长度: {len(interaction_result)} 字符")

        # 第三步：Midscene用例生成智能体整合两个结果
        logger.info("🎯 开始Midscene测试脚本生成...")
        if user_id in message_queues:
            await message_queues[user_id].put(
                {
                    "type": "agent_start",
                    "agent": "Midscene用例生成智能体",
                    "step": "开始生成Midscene测试脚本",
                    "content": "正在整合UI分析和交互分析结果，生成Midscene.js测试脚本...",
                }
            )
            logger.debug("✅ Midscene生成开始消息已发送")
        else:
            logger.warning(f"⚠️ 用户队列不存在，无法发送Midscene开始消息: {user_id}")

        # 获取Midscene生成智能体的系统提示词
        midscene_system_prompt = """你是MidScene.js自动化测试专家，专门基于UI专家和交互分析师的分析结果，设计符合MidScene.js脚本风格的测试用例。

## MidScene.js 核心知识（基于官方文档）

### 支持的动作类型

#### 1. 复合操作
- **ai**: 自然语言描述的复合操作，如 "type 'computer' in search box, hit Enter"
- **aiAction**: ai的完整形式，功能相同

#### 2. 即时操作（精确控制时使用）
- **aiTap**: 点击操作，用于按钮、链接、菜单项
- **aiInput**: 文本输入，格式为 aiInput: "输入内容", locate: "元素描述"
- **aiHover**: 鼠标悬停，用于下拉菜单触发
- **aiScroll**: 滚动操作，支持方向和距离
- **aiKeyboardPress**: 键盘操作，如Enter、Tab等

#### 3. 数据提取操作
- **aiQuery**: 通用查询，支持复杂数据结构，使用多行格式
- **aiBoolean**: 布尔值查询
- **aiNumber**: 数值查询
- **aiString**: 字符串查询

#### 4. 验证和等待
- **aiAssert**: 断言验证
- **aiWaitFor**: 等待条件满足
- **sleep**: 固定等待（毫秒）

请整合分析结果，设计完整的MidScene.js测试场景，严格按照JSON格式输出。"""

        midscene_question = f"""基于以下分析结果，生成符合MidScene.js规范的测试脚本。

用户需求：{user_requirement}

UI元素分析结果：
{ui_result}

交互流程分析结果：
{interaction_result}

请整合上述分析结果，设计完整的MidScene.js测试场景，严格按照JSON格式输出，确保：
1. 每个测试步骤都有详细的视觉描述
2. 遵循MidScene.js的最佳实践
3. 包含完整的验证流程
4. 可以直接转换为可执行的测试脚本"""

        # 创建Midscene生成智能体实例
        logger.info("🔧 创建Midscene生成智能体实例...")
        midscene_assistant = AssistantAgent(
            "midscene_generator",
            model_client=doubao_multimodal_agent.agent._model_client,
            system_message=midscene_system_prompt,
            model_client_stream=True,
        )
        logger.success("✅ Midscene生成智能体实例创建完成")

        logger.info("🚀 开始Midscene脚本生成流式处理...")
        midscene_result = ""
        chunk_count = 0

        async for item in midscene_assistant.run_stream(task=midscene_question):
            if isinstance(item, ModelClientStreamingChunkEvent):
                chunk_content = item.content
                midscene_result += chunk_content
                chunk_count += 1

                logger.debug(
                    f"📦 接收Midscene生成块 #{chunk_count}: {len(chunk_content)} 字符"
                )

                if user_id in message_queues:
                    await message_queues[user_id].put(
                        {
                            "type": "stream_chunk",
                            "agent": "Midscene用例生成智能体",
                            "content": chunk_content,
                        }
                    )
                    logger.trace(f"📤 Midscene生成块已发送到队列")
                else:
                    logger.warning(
                        f"⚠️ 用户队列不存在，无法发送Midscene流式块: {user_id}"
                    )

            elif isinstance(item, TextMessage):
                midscene_result = item.content
                logger.info(f"📄 接收Midscene完整文本: {len(midscene_result)} 字符")

            elif isinstance(item, TaskResult):
                if item.messages:
                    midscene_result = item.messages[-1].content
                    logger.info(f"📋 接收Midscene任务结果: {len(midscene_result)} 字符")

        logger.success(
            f"✅ Midscene脚本生成完成 - 总块数: {chunk_count}, 总长度: {len(midscene_result)} 字符"
        )

        logger.debug("📤 发送Midscene生成完成消息...")
        if user_id in message_queues:
            await message_queues[user_id].put(
                {
                    "type": "agent_complete",
                    "agent": "Midscene用例生成智能体",
                    "step": "Midscene测试脚本生成完成",
                    "content": midscene_result,
                }
            )
        else:
            logger.warning(f"⚠️ 用户队列不存在，无法发送Midscene完成消息: {user_id}")

        # 第四步：脚本生成智能体生成YAML和Playwright脚本
        logger.info("📜 开始脚本生成...")
        if user_id in message_queues:
            await message_queues[user_id].put(
                {
                    "type": "agent_start",
                    "agent": "脚本生成智能体",
                    "step": "开始生成YAML和Playwright脚本",
                    "content": "正在解析Midscene JSON并生成可执行脚本...",
                }
            )
            logger.debug("✅ 脚本生成开始消息已发送")
        else:
            logger.warning(f"⚠️ 用户队列不存在，无法发送脚本生成开始消息: {user_id}")

        # 构建脚本生成问题
        script_question = f"""请将以下Midscene JSON测试用例转换为YAML脚本和Midscene+Playwright脚本。

用户需求：{user_requirement}

Midscene JSON测试用例：
{midscene_result}

请严格根据JSON格式输出两种脚本，确保：
1. YAML脚本符合Midscene规范
2. Midscene+Playwright脚本参考下面的示例代码,尽量使用Midscene的用法
3. Midscene+Playwright脚本必须以固定的导入语句开头：
   import {{ expect }} from "@playwright/test";
   import {{ test }} from "./fixture";
4. 两种脚本都能正确执行相同的测试逻辑
5. 包含适当的等待和验证步骤
6. 脚本中每一个步骤都用中文做好详细的注释
### 示例代码
```typescript title="./e2e/ebay-search.spec.ts"
import {{ expect }} from '@playwright/test';
import {{ test }} from './fixture';

test.beforeEach(async ({{ page }}) => {{
  page.setViewportSize({{ width: 1200, height: 800 }});
  // 跳转到ebay首页
  await page.goto('https://www.ebay.com');
  // 等待页面加载完成
  await page.waitForLoadState('networkidle');
}});

test('search headphone on ebay', async ({{
  ai,
  aiQuery,
  aiAssert,
  aiInput,
  aiTap,
  aiScroll,
  aiWaitFor,
}}) => {{
  // 使用 aiInput 输入搜索关键词
  await aiInput('Headphones', '搜索框');

  // 使用 aiTap 点击搜索按钮
  await aiTap('搜索按钮');

  // 等待搜索结果加载
  await aiWaitFor('搜索结果列表已加载', {{ timeoutMs: 5000 }});

  // 使用 aiScroll 滚动到页面底部
  await aiScroll(
    {{
      direction: 'down',
      scrollType: 'untilBottom',
    }},
    '搜索结果列表',
  );

  // 使用 aiQuery 获取商品信息
  const items =
    await aiQuery<Array<{{ title: string; price: number }}>>(
      '获取搜索结果中的商品标题和价格',
    );

  console.log('headphones in stock', items);
  expect(items?.length).toBeGreaterThan(0);

  // 使用 aiAssert 验证筛选功能
  await aiAssert('界面左侧有类目筛选功能');
}});


"""

        logger.debug(f"📝 构建脚本生成问题完成，长度: {len(script_question)} 字符")

        # 使用DeepSeek智能体进行流式生成
        logger.info("🚀 开始流式脚本生成...")
        script_result = ""
        script_chunk_count = 0

        async for item in deepseek_agent.run_stream(task=script_question):
            if isinstance(item, ModelClientStreamingChunkEvent):
                chunk_content = item.content
                script_result += chunk_content
                script_chunk_count += 1

                logger.debug(
                    f"📦 接收脚本生成块 #{script_chunk_count}: {len(chunk_content)} 字符"
                )

                if user_id in message_queues:
                    await message_queues[user_id].put(
                        {
                            "type": "stream_chunk",
                            "agent": "脚本生成智能体",
                            "content": chunk_content,
                        }
                    )
                    logger.trace(f"📤 脚本生成块已发送到队列")
                else:
                    logger.warning(
                        f"⚠️ 用户队列不存在，无法发送脚本生成流式块: {user_id}"
                    )

            elif isinstance(item, TextMessage):
                script_result = item.content
                logger.info(f"📄 接收脚本生成完整文本: {len(script_result)} 字符")

            elif isinstance(item, TaskResult):
                if item.messages:
                    script_result = item.messages[-1].content
                    logger.info(f"📋 接收脚本生成任务结果: {len(script_result)} 字符")

        logger.success(
            f"✅ 脚本生成完成 - 总块数: {script_chunk_count}, 总长度: {len(script_result)} 字符"
        )

        # 发送脚本生成完成消息
        if user_id in message_queues:
            await message_queues[user_id].put(
                {
                    "type": "agent_complete",
                    "agent": "脚本生成智能体",
                    "step": "YAML和Playwright脚本生成完成",
                    "content": script_result,
                }
            )
            logger.debug("✅ 脚本生成完成消息已发送")
        else:
            logger.warning(f"⚠️ 用户队列不存在，无法发送脚本生成完成消息: {user_id}")

        # 完成所有分析
        logger.info("🎉 所有智能体协作完成")
        if user_id in message_queues:
            await message_queues[user_id].put(
                {
                    "type": "system_complete",
                    "message": "所有智能体协作完成",
                    "content": "Midscene测试脚本和可执行脚本已全部生成完成",
                }
            )
        else:
            logger.warning(f"⚠️ 用户队列不存在，无法发送系统完成消息: {user_id}")

        # 保存结果到文件
        result_file = get_result_file_path(user_id)
        logger.info(f"💾 保存分析结果到文件: {result_file}")

        async with aiofiles.open(result_file, mode="w", encoding="utf-8") as f:
            result_data = {
                "user_id": user_id,
                "image_paths": image_paths,
                "user_requirement": user_requirement,
                "ui_analysis": ui_result,
                "interaction_analysis": interaction_result,
                "midscene_script": midscene_result,
                "generated_scripts": script_result,
                "timestamp": asyncio.get_event_loop().time(),
            }
            await f.write(json.dumps(result_data, ensure_ascii=False, indent=2))

        total_time = time.time() - start_time
        logger.success(
            f"🎊 协作分析完全完成 - 用户: {user_id}, 总耗时: {total_time:.2f}秒"
        )
        logger.info(f"📁 结果文件: {Path(result_file).absolute()}")

        # 等待一小段时间确保所有消息都被处理
        await asyncio.sleep(1)

        # 主动清理用户队列
        if user_id in message_queues:
            logger.debug(f"🧹 主动清理用户队列: {user_id}")
            message_queues.pop(user_id, None)

    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"❌ 协作分析失败 - 用户: {user_id}, 耗时: {total_time:.2f}秒")
        logger.error(f"🔥 错误详情: {str(e)}")
        logger.error(f"📍 错误堆栈: {traceback.format_exc()}")

        if user_id in message_queues:
            await message_queues[user_id].put(
                {
                    "type": "system_error",
                    "message": "协作分析失败",
                    "content": f"错误: {str(e)}",
                }
            )

            # 等待一小段时间确保错误消息被处理
            await asyncio.sleep(1)

            # 清理用户队列
            logger.debug(f"🧹 错误情况下清理用户队列: {user_id}")
            message_queues.pop(user_id, None)
        else:
            logger.warning(f"⚠️ 用户队列不存在，无法发送错误消息: {user_id}")


async def run_ui_analysis(user_id: str, image_paths: List[str]) -> str:
    """UI分析智能体 - 分析多张图片"""
    start_time = time.time()
    logger.info(f"🔍 开始UI分析任务 - 用户: {user_id}, 图片数量: {len(image_paths)}")

    if user_id in message_queues:
        await message_queues[user_id].put(
            {
                "type": "agent_start",
                "agent": "UI分析智能体",
                "step": "开始分析UI元素",
                "content": f"正在分析 {len(image_paths)} 张界面截图中的UI元素...",
            }
        )
        logger.debug("✅ UI分析开始消息已发送")
    else:
        logger.warning(f"⚠️ 用户队列不存在，无法发送开始消息: {user_id}")

    all_ui_analysis = []

    for i, image_path in enumerate(image_paths):
        image_start_time = time.time()
        logger.info(f"📷 分析图片 {i+1}/{len(image_paths)}: {Path(image_path).name}")

        # 验证图片文件
        if not Path(image_path).exists():
            logger.error(f"❌ 图片文件不存在: {image_path}")
            continue

        file_size = Path(image_path).stat().st_size
        logger.debug(f"📊 图片信息: {Path(image_path).name}, 大小: {file_size} bytes")

        if user_id in message_queues:
            await message_queues[user_id].put(
                {
                    "type": "step_info",
                    "agent": "UI分析智能体",
                    "content": f"正在分析第 {i+1}/{len(image_paths)} 张图片: {Path(image_path).name}",
                }
            )
        else:
            logger.warning(f"⚠️ 用户队列不存在，无法发送步骤信息: {user_id}")

        # 获取UI分析智能体的系统提示词
        ui_system_prompt = """你是UI元素识别专家，专门分析界面截图中的UI组件，为自动化测试提供精确的元素信息。

## 核心职责

### 1. 元素识别与分类
- **交互元素**: 按钮、链接、输入框、下拉菜单、复选框、单选按钮、开关
- **显示元素**: 文本、图片、图标、标签、提示信息
- **容器元素**: 表单、卡片、模态框、侧边栏、导航栏
- **列表元素**: 表格、列表项、菜单项、选项卡

### 2. 视觉特征描述标准
- **颜色**: 主色调、背景色、边框色（如"蓝色按钮"、"红色警告文字"）
- **尺寸**: 相对大小（大、中、小）和具体描述
- **形状**: 圆角、方形、圆形等
- **图标**: 具体图标类型（如"搜索图标"、"用户头像图标"）
- **文字**: 完整的文字内容和字体样式

请严格按照JSON格式输出，每个元素包含完整信息。"""

        # 分析单张图片（不包含用户需求，专注于UI元素识别）
        question = f"""请分析这张界面截图中的UI元素。

{ui_system_prompt}

请严格按照上述要求分析图片中的所有UI元素，并以JSON格式输出结果。"""

        # 使用流式输出分析图片
        logger.info("🔧 创建多模态消息...")
        from llms import create_multimodal_message

        multimodal_message = create_multimodal_message(question, [image_path])
        logger.debug("✅ 多模态消息创建完成")

        logger.info("🚀 开始流式UI分析...")
        ui_result = ""
        chunk_count = 0

        async for item in doubao_multimodal_agent.run_stream(multimodal_message):
            if isinstance(item, ModelClientStreamingChunkEvent):
                chunk_content = item.content
                ui_result += chunk_content
                chunk_count += 1

                logger.debug(
                    f"📦 接收UI分析块 #{chunk_count}: {len(chunk_content)} 字符"
                )

                if user_id in message_queues:
                    await message_queues[user_id].put(
                        {
                            "type": "stream_chunk",
                            "agent": "UI分析智能体",
                            "content": chunk_content,
                        }
                    )
                else:
                    logger.warning(f"⚠️ 用户队列不存在，无法发送流式块: {user_id}")

            elif isinstance(item, TextMessage):
                ui_result = item.content
                logger.info(f"📄 接收UI分析完整文本: {len(ui_result)} 字符")

            elif isinstance(item, TaskResult):
                if item.messages:
                    ui_result = item.messages[-1].content
                    logger.info(f"📋 接收UI分析任务结果: {len(ui_result)} 字符")

        image_time = time.time() - image_start_time
        logger.success(
            f"✅ 图片 {i+1} 分析完成 - 耗时: {image_time:.2f}秒, 结果长度: {len(ui_result)} 字符"
        )

        all_ui_analysis.append(f"图片{i+1} ({Path(image_path).name}):\n{ui_result}")

    # 合并所有UI分析结果
    logger.info("📋 合并所有UI分析结果...")
    combined_ui_analysis = "\n\n" + "=" * 50 + "\n\n".join(all_ui_analysis)

    total_time = time.time() - start_time
    logger.success(f"🎉 UI分析任务完成 - 用户: {user_id}, 总耗时: {total_time:.2f}秒")
    logger.info(f"📊 合并结果长度: {len(combined_ui_analysis)} 字符")

    if user_id in message_queues:
        await message_queues[user_id].put(
            {
                "type": "agent_complete",
                "agent": "UI分析智能体",
                "step": "UI元素分析完成",
                "content": f"已完成 {len(image_paths)} 张图片的UI元素分析",
            }
        )
        logger.debug("✅ UI分析完成消息已发送")
    else:
        logger.warning(f"⚠️ 用户队列不存在，无法发送完成消息: {user_id}")

    return combined_ui_analysis


async def run_interaction_analysis(user_id: str, user_requirement: str) -> str:
    """交互分析智能体 - 基于用户需求设计交互流程"""
    start_time = time.time()
    logger.info(f"🔄 开始交互分析任务 - 用户: {user_id}")
    logger.info(f"📝 用户需求: {user_requirement[:100]}...")

    if user_id in message_queues:
        await message_queues[user_id].put(
            {
                "type": "agent_start",
                "agent": "交互分析智能体",
                "step": "开始分析用户交互流程",
                "content": "正在基于用户需求设计交互流程...",
            }
        )
        logger.debug("✅ 交互分析开始消息已发送")
    else:
        logger.warning(f"⚠️ 用户队列不存在，无法发送开始消息: {user_id}")

    # 获取交互分析智能体的系统提示词
    interaction_system_prompt = """你是用户交互流程分析师，专门分析用户在界面上的操作流程，为自动化测试设计提供用户行为路径。

## 核心职责

### 1. 用户行为路径分析
- **主要流程**: 用户完成核心任务的标准路径
- **替代流程**: 用户可能采用的其他操作方式
- **异常流程**: 错误操作、网络异常等情况的处理
- **回退流程**: 用户撤销、返回等逆向操作

### 2. 交互节点识别
- **入口点**: 用户开始操作的位置
- **决策点**: 用户需要选择的关键节点
- **验证点**: 系统反馈和状态确认
- **出口点**: 流程完成或退出的位置

请按照结构化格式输出交互流程，严格按照JSON格式。"""

    interaction_question = f"""基于用户需求，请设计完整的用户交互流程。

用户需求：{user_requirement}

{interaction_system_prompt}

请根据用户需求，设计完整的用户交互流程，并严格按照JSON格式输出。注意：此时还没有具体的UI元素信息，请基于需求设计通用的交互流程。"""

    # 创建交互分析智能体实例
    logger.info("🔧 创建交互分析智能体实例...")
    interaction_assistant = AssistantAgent(
        "interaction_analyst",
        model_client=doubao_multimodal_agent.agent._model_client,
        system_message=interaction_system_prompt,
        model_client_stream=True,
    )
    logger.success("✅ 交互分析智能体实例创建完成")

    logger.info("🚀 开始交互分析流式处理...")
    interaction_result = ""
    chunk_count = 0

    async for item in interaction_assistant.run_stream(task=interaction_question):
        if isinstance(item, ModelClientStreamingChunkEvent):
            chunk_content = item.content
            interaction_result += chunk_content
            chunk_count += 1

            logger.debug(f"📦 接收交互分析块 #{chunk_count}: {len(chunk_content)} 字符")

            if user_id in message_queues:
                await message_queues[user_id].put(
                    {
                        "type": "stream_chunk",
                        "agent": "交互分析智能体",
                        "content": chunk_content,
                    }
                )
            else:
                logger.warning(f"⚠️ 用户队列不存在，无法发送流式块: {user_id}")

        elif isinstance(item, TextMessage):
            interaction_result = item.content
            logger.info(f"📄 接收交互分析完整文本: {len(interaction_result)} 字符")

        elif isinstance(item, TaskResult):
            if item.messages:
                interaction_result = item.messages[-1].content
                logger.info(f"📋 接收交互分析任务结果: {len(interaction_result)} 字符")

    total_time = time.time() - start_time
    logger.success(f"✅ 交互分析完成 - 用户: {user_id}, 耗时: {total_time:.2f}秒")
    logger.info(f"📊 分析结果长度: {len(interaction_result)} 字符")

    if user_id in message_queues:
        await message_queues[user_id].put(
            {
                "type": "agent_complete",
                "agent": "交互分析智能体",
                "step": "交互流程分析完成",
                "content": "基于用户需求的交互流程设计已完成",
            }
        )
        logger.debug("✅ 交互分析完成消息已发送")
    else:
        logger.warning(f"⚠️ 用户队列不存在，无法发送完成消息: {user_id}")

    return interaction_result


# API接口
@app.post("/api/upload_and_analyze")
async def upload_and_analyze(
    files: List[UploadFile] = File(...),
    user_id: str = Form(...),
    user_requirement: str = Form(...),
):
    """上传多张图片并开始协作分析，返回流式响应"""
    start_time = time.time()
    logger.info(f"📤 接收上传请求 - 用户: {user_id}, 文件数量: {len(files)}")
    logger.info(f"📝 用户需求: {user_requirement[:100]}...")

    try:
        # 保存上传的图片
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        logger.debug(f"📁 上传目录: {upload_dir.absolute()}")

        uploaded_files = []

        for i, file in enumerate(files):
            file_start_time = time.time()
            file_path = upload_dir / f"{user_id}_{i}_{file.filename}"

            logger.info(f"💾 保存文件 {i+1}/{len(files)}: {file.filename}")

            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            file_size = len(content)
            file_time = time.time() - file_start_time
            logger.debug(
                f"✅ 文件保存完成: {file.filename}, 大小: {file_size} bytes, 耗时: {file_time:.2f}秒"
            )

            uploaded_files.append(str(file_path))

        # 创建用户消息队列
        logger.info(f"📋 创建用户消息队列: {user_id}")
        message_queues[user_id] = asyncio.Queue()
        logger.debug("✅ 用户消息队列创建完成")

        # 发送开始消息到队列
        logger.debug("📤 发送系统开始消息到队列...")
        await message_queues[user_id].put(
            {
                "type": "system_start",
                "message": "开始协作分析",
                "content": f"已上传 {len(uploaded_files)} 张图片，开始三智能体协作分析流程...",
                "files": uploaded_files,
                "requirement": user_requirement,
            }
        )

        # 启动协作分析任务（异步执行）
        logger.info("🚀 启动协作分析任务...")
        asyncio.create_task(
            run_collaborative_analysis(user_id, uploaded_files, user_requirement)
        )

        upload_time = time.time() - start_time
        logger.success(f"✅ 上传处理完成 - 用户: {user_id}, 耗时: {upload_time:.2f}秒")
        logger.info("📡 返回流式响应...")

        # 返回流式响应，参考 topic1.py 的 chat 接口
        return StreamingResponse(
            message_generator(user_id=user_id),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            },
        )

    except Exception as e:
        upload_time = time.time() - start_time
        logger.error(f"❌ 上传分析失败 - 用户: {user_id}, 耗时: {upload_time:.2f}秒")
        logger.error(f"🔥 错误详情: {str(e)}")
        logger.error(f"📍 错误堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"上传分析失败: {str(e)}")


@app.post("/upload_single_and_analyze")
async def upload_single_and_analyze(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    user_requirement: str = Form(...),
):
    """上传单张图片并开始分析，返回流式响应（兼容接口）"""
    start_time = time.time()
    logger.info(f"📤 接收单文件上传请求 - 用户: {user_id}, 文件: {file.filename}")
    logger.info(f"📝 用户需求: {user_requirement[:100]}...")

    try:
        # 保存上传的图片
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        logger.debug(f"📁 上传目录: {upload_dir.absolute()}")

        file_path = upload_dir / f"{user_id}_{file.filename}"
        logger.info(f"💾 保存文件: {file.filename}")

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        file_size = len(content)
        logger.debug(f"✅ 文件保存完成: {file.filename}, 大小: {file_size} bytes")

        # 创建用户消息队列
        logger.info(f"📋 创建用户消息队列: {user_id}")
        message_queues[user_id] = asyncio.Queue()

        await message_queues[user_id].put(
            {
                "type": "system_start",
                "message": "开始分析",
                "content": f"已上传图片 {file.filename}，开始智能体分析流程...",
                "file": str(file_path),
                "requirement": user_requirement,
            }
        )
        logger.debug("✅ 系统开始消息已发送")

        # 启动协作分析流程（单文件作为列表处理）
        logger.info("🚀 启动单文件协作分析流程...")
        asyncio.create_task(
            run_collaborative_analysis(user_id, [str(file_path)], user_requirement)
        )

        upload_time = time.time() - start_time
        logger.success(
            f"✅ 单文件上传处理完成 - 用户: {user_id}, 耗时: {upload_time:.2f}秒"
        )
        logger.info("📡 返回流式响应...")

        # 返回流式响应，参考 topic1.py 的 chat 接口
        return StreamingResponse(
            message_generator(user_id=user_id),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            },
        )

    except Exception as e:
        upload_time = time.time() - start_time
        logger.error(
            f"❌ 单文件上传分析失败 - 用户: {user_id}, 耗时: {upload_time:.2f}秒"
        )
        logger.error(f"🔥 错误详情: {str(e)}")
        logger.error(f"📍 错误堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"上传分析失败: {str(e)}")


@app.get("/stream_results")
async def stream_results(user_id: str):
    """获取分析结果的流式输出"""
    logger.info(f"📡 开始流式输出 - 用户: {user_id}")

    if user_id not in message_queues:
        logger.warning(f"⚠️ 用户队列不存在: {user_id}")
        raise HTTPException(status_code=404, detail=f"用户队列不存在: {user_id}")

    logger.debug(f"✅ 建立SSE连接 - 用户: {user_id}")

    return StreamingResponse(
        message_generator(user_id=user_id),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )


@app.get("/")
async def root():
    logger.debug("📍 根路径访问")
    return {"message": "Midscene Test Generator API", "version": "1.0.0"}


# ==================== 应用启动 ====================

if __name__ == "__main__":
    logger.info("🌟 启动Midscene智能体系统服务器...")
    logger.info("🔧 配置信息:")
    logger.info("   - 主机: 0.0.0.0")
    logger.info("   - 端口: 8001")
    logger.info("   - 日志级别: DEBUG")
    logger.info("   - 支持的功能: 多模态图片分析、三智能体协作、流式输出")

    import uvicorn

    try:
        uvicorn.run(app, host="0.0.0.0", port=8001)
    except KeyboardInterrupt:
        logger.info("🛑 接收到停止信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        logger.error(f"📍 错误堆栈: {traceback.format_exc()}")
    finally:
        logger.info("👋 Midscene智能体系统服务器已关闭")
