import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from io import BytesIO
from typing import List, Union

import PIL
import requests
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import MultiModalMessage
from autogen_core import Image
from autogen_core.models import ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient

from examples.conf.config import settings

# 单例设计模式
openai_model_client = OpenAIChatCompletionClient(
    model=settings.aimodel.model,
    base_url=settings.aimodel.base_url,
    api_key=settings.aimodel.api_key,
    model_info={
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "family": ModelFamily.UNKNOWN,
        "structured_output": True,
        "multiple_system_messages": True,
    },
    temperature=0.2,
    top_p=0.7,
)


# 豆包
doubao_model_client = OpenAIChatCompletionClient(
    model=settings.ui_tars_model.model,
    base_url=settings.ui_tars_model.base_url,
    api_key=settings.ui_tars_model.api_key,
    model_info={
        "vision": True,
        "function_calling": True,
        "json_output": True,
        "family": ModelFamily.UNKNOWN,
        "structured_output": True,
        "multiple_system_messages": True,
    },
)


# 图片处理工具函数
def load_image_from_url(url: str) -> Image:
    """从URL加载图片"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        pil_image = PIL.Image.open(BytesIO(response.content))
        return Image(pil_image)
    except Exception as e:
        raise ValueError(f"无法从URL加载图片: {e}")


def load_image_from_file(file_path: Union[str, Path]) -> Image:
    """从本地文件加载图片"""
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {file_path}")

        pil_image = PIL.Image.open(file_path)
        return Image(pil_image)
    except Exception as e:
        raise ValueError(f"无法从文件加载图片: {e}")


def create_multimodal_message(
    text: str, images: List[Union[str, Path, Image]], source: str = "user"
) -> MultiModalMessage:
    """创建多模态消息"""
    content = [text]

    for img in images:
        if isinstance(img, Image):
            content.append(img)
        elif isinstance(img, str):
            if img.startswith(("http://", "https://")):
                content.append(load_image_from_url(img))
            else:
                content.append(load_image_from_file(img))
        else:
            content.append(load_image_from_file(img))

    return MultiModalMessage(content=content, source=source)


class DoubaoMultiModalAgent:
    """豆包多模态智能体封装类"""

    def __init__(
        self,
        name: str = "doubao_multimodal_agent",
        system_message: str = "你是一个多模态AI助手，能够分析图片并回答相关问题。",
    ):
        self.agent = AssistantAgent(
            name=name,
            model_client=doubao_model_client,
            system_message=system_message,
            model_client_stream=True,  # 支持流式输出
        )

    async def analyze_image_from_url(
        self, image_url: str, question: str = "请描述这张图片的内容"
    ):
        """分析来自URL的图片"""
        try:
            image = load_image_from_url(image_url)
            multimodal_message = MultiModalMessage(
                content=[question, image], source="user"
            )
            result = await self.agent.run(task=multimodal_message)
            return result
        except Exception as e:
            raise ValueError(f"图片分析失败: {e}")

    async def analyze_image_from_file(
        self, file_path: Union[str, Path], question: str = "请描述这张图片的内容"
    ):
        """分析本地图片文件"""
        try:
            image = load_image_from_file(file_path)
            multimodal_message = MultiModalMessage(
                content=[question, image], source="user"
            )
            result = await self.agent.run(task=multimodal_message)
            return result
        except Exception as e:
            raise ValueError(f"图片分析失败: {e}")

    async def analyze_multiple_images(
        self, images: List[Union[str, Path]], question: str = "请分析这些图片的内容"
    ):
        """分析多张图片"""
        try:
            multimodal_message = create_multimodal_message(question, images)
            result = await self.agent.run(task=multimodal_message)
            return result
        except Exception as e:
            raise ValueError(f"多图片分析失败: {e}")

    def run_stream(self, task):
        """流式运行"""
        return self.agent.run_stream(task=task)

    async def run(self, task):
        """普通运行"""
        return await self.agent.run(task=task)


class DeepSeekAgent:
    """DeepSeek智能体封装类"""

    def __init__(
        self,
        name: str = "deepseek_agent",
        system_message: str = "你是一个专业的代码生成助手，能够根据需求生成高质量的测试脚本。",
    ):
        self.agent = AssistantAgent(
            name=name,
            model_client=openai_model_client,  # 使用DeepSeek模型客户端
            system_message=system_message,
            model_client_stream=True,  # 支持流式输出
        )

    async def generate_script(self, prompt: str):
        """生成脚本"""
        try:
            result = await self.agent.run(task=prompt)
            return result
        except Exception as e:
            raise ValueError(f"脚本生成失败: {e}")

    def run_stream(self, task):
        """流式运行"""
        return self.agent.run_stream(task=task)

    async def run(self, task):
        """普通运行"""
        return await self.agent.run(task=task)


# 创建智能体实例
doubao_multimodal_agent = DoubaoMultiModalAgent()
deepseek_agent = DeepSeekAgent()
