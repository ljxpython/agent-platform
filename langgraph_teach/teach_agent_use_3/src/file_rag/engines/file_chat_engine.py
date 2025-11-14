# 文件对话引擎
"""
基于 LangGraph 的文件对话引擎，支持 PDF、图片和文本的智能对话
参考 agentic_rag_engine.py 的架构，整合 chat_file_graph.py 的功能
"""

import base64
import logging
import operator
from dataclasses import dataclass
from typing import Annotated, Any, Dict, List, Literal, Optional

from file_rag.agents.image_agent import agent as image_agent
from file_rag.agents.pdf_agent import agent as pdf_agent
from file_rag.core.config import settings
from file_rag.processors.pdf_processor import PDFProcessor
from langchain.agents import AgentState
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph

logger = logging.getLogger(__name__)

# ===== 数据模型 =====


@dataclass
class WorkflowState(MessagesState):
    """工作流状态，继承自 AgentState"""

    file_type: str = "text"  # 检测到的文件类型：pdf, image, text


# ===== 文件类型检测 =====


def detect_file_type(messages: List[Any]) -> str:
    """检测消息中的文件类型"""
    for message in messages:
        if hasattr(message, "content") and isinstance(message.content, list):
            for item in message.content:
                if isinstance(item, dict):
                    # 检测PDF文件
                    if (
                        item.get("type") == "file"
                        and item.get("mime_type") == "application/pdf"
                    ) or (
                        item.get("type") == "file"
                        and item.get("source_type") == "base64"
                        and item.get("mime_type") == "application/pdf"
                    ):
                        return "pdf"

                    # 检测图片文件 - 支持多种格式
                    elif (
                        (item.get("type") == "image_url")
                        or (
                            item.get("type") == "file"
                            and item.get("mime_type", "").startswith("image/")
                        )
                        or (item.get("type") == "image")
                        or ("image_url" in item and "url" in item.get("image_url", {}))
                    ):
                        return "image"
    return "text"


# ===== 通用清洗与转换 =====


def _sanitize_blocks(blocks: List[dict]) -> List[dict]:
    """仅保留模型支持的内容块类型：text、image_url、video_url。

    - text: {"type": "text", "text": str}
    - image_url: {"type": "image_url", "image_url": {"url": str}}
    - video_url: {"type": "video_url", "video_url": {"url": str}}
    其它类型全部丢弃。
    """
    sanitized: List[dict] = []
    for blk in blocks or []:
        if not isinstance(blk, dict):
            continue
        t = blk.get("type")
        if t == "text" and isinstance(blk.get("text"), str):
            sanitized.append({"type": "text", "text": blk.get("text")})
        elif t == "image_url" and isinstance(blk.get("image_url"), dict):
            url = blk["image_url"].get("url")
            if isinstance(url, str) and url:
                sanitized.append({"type": "image_url", "image_url": {"url": url}})
        elif t == "video_url" and isinstance(blk.get("video_url"), dict):
            url = blk["video_url"].get("url")
            if isinstance(url, str) and url:
                sanitized.append({"type": "video_url", "video_url": {"url": url}})
    return sanitized


def _convert_file_blocks_for_images(message: Any) -> Any:
    """将 HumanMessage 中的 file(base64 image) 转换为 image_url 数据 URI；
    非法/不支持的 file 块转换为说明性文本。仅处理 HumanMessage 且 content 为 list 的情况。
    返回新的消息对象（尽量保留原属性）。
    """
    try:
        is_human = (HumanMessage is None) or isinstance(message, HumanMessage)
        content = getattr(message, "content", None)
        if not is_human or not isinstance(content, list):
            return message

        new_blocks: List[dict] = []
        changed = False
        for part in content:
            if not isinstance(part, dict):
                continue
            t = part.get("type")
            if t != "file":
                # 保留其余块，稍后统一sanitize
                new_blocks.append(part)
                continue

            # 仅处理 file 类型
            mime = str(part.get("mime_type") or part.get("mimeType") or "").lower()
            raw_b64 = None
            data_val = part.get("data") if isinstance(part.get("data"), str) else None
            is_data_url = False
            if isinstance(data_val, str):
                if data_val.startswith("data:") and "," in data_val:
                    is_data_url = True
                    try:
                        raw_b64 = data_val.split(",", 1)[1]
                        mime_hdr = data_val.split(",", 1)[0]
                        if ":" in mime_hdr:
                            mime = mime_hdr.split(":", 1)[1].split(";", 1)[0]
                    except Exception:
                        raw_b64 = None
                else:
                    raw_b64 = data_val
            elif isinstance(part.get("base64"), str):
                raw_b64 = part.get("base64")

            # 将 image/* 的 file 转换为 image_url 数据URI
            if mime.startswith("image/") and (isinstance(raw_b64, str) or is_data_url):
                try:
                    data_uri = (
                        data_val if is_data_url else f"data:{mime};base64,{raw_b64}"
                    )
                    new_blocks.append(
                        {"type": "image_url", "image_url": {"url": data_uri}}
                    )
                    changed = True
                    continue
                except Exception:
                    pass

            # 其它文件（包括 application/pdf 等）在图片通道中不直接发送，降级为提示文本
            meta = part.get("metadata") or {}
            fname = meta.get("filename") or meta.get("name") or "未命名文件"
            new_blocks.append(
                {
                    "type": "text",
                    "text": f"收到文件: {fname} ({mime or '未知类型'})。模型不直接接收文件，已忽略原始文件内容。",
                }
            )
            changed = True

        # 清理到限定的块类型
        cleaned = _sanitize_blocks(new_blocks)

        if changed:
            # 复制 HumanMessage，替换 content
            try:
                return HumanMessage(
                    content=cleaned,
                    additional_kwargs=getattr(message, "additional_kwargs", {}),
                    response_metadata=getattr(message, "response_metadata", {}),
                    id=getattr(message, "id", None),
                )
            except Exception:
                # 失败则原样返回（尽管不太可能）
                return message
        else:
            # 即便未改动，也做一次清洗，避免非法字段
            try:
                return HumanMessage(
                    content=cleaned if cleaned else content,
                    additional_kwargs=getattr(message, "additional_kwargs", {}),
                    response_metadata=getattr(message, "response_metadata", {}),
                    id=getattr(message, "id", None),
                )
            except Exception:
                return message
    except Exception:
        return message


def _preprocess_images_messages(messages: List[Any]) -> List[Any]:
    """对消息列表做图片相关的预处理：
    - 将 HumanMessage 中的 file(base64 image) 转为 image_url 数据URI
    - 移除/替换不被模型支持的 file 类型
    仅处理 HumanMessage，其他消息保持不变。
    """
    processed: List[Any] = []
    for msg in messages or []:
        processed.append(_convert_file_blocks_for_images(msg))
    return processed


# ===== PDF 处理函数 =====


def process_pdf_messages(
    messages: List[Any], pdf_processor: PDFProcessor
) -> tuple[List[Any], str]:
    """处理包含PDF文件的消息，解析PDF内容并返回处理后的消息和系统提示"""
    processed_messages = []
    pdf_contents = []  # 收集所有PDF内容

    # 基础系统提示词
    system_content = "你是一个智能助手，可以分析和回答关于PDF文档内容的问题。"

    for message in messages:
        if hasattr(message, "content"):
            if isinstance(message.content, list):
                # 检查是否包含PDF文件
                contains_pdf = any(
                    isinstance(item, dict)
                    and item.get("type") == "file"
                    and item.get("mime_type") == "application/pdf"
                    for item in message.content
                )

                if contains_pdf:
                    # 处理包含PDF文件的多模态消息
                    text_parts = []

                    for item in message.content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                text_parts.append(item.get("text", ""))
                            elif (
                                item.get("type") == "file"
                                and item.get("mime_type") == "application/pdf"
                            ):
                                # 处理PDF文件
                                try:
                                    filename = item.get("metadata", {}).get(
                                        "filename", "unknown.pdf"
                                    )
                                    file_data = item.get("data", "") or item.get(
                                        "content", ""
                                    )

                                    if file_data:
                                        logger.info(f"处理PDF文件: {filename}")
                                        # 解码base64数据
                                        pdf_data = base64.b64decode(file_data)
                                        # 提取PDF文本
                                        pdf_text = pdf_processor.extract_text(
                                            pdf_data, filename
                                        )

                                        if pdf_text and len(pdf_text.strip()) > 0:
                                            pdf_content = f"📄 PDF文件 '{filename}' 的内容:\n\n{pdf_text}"
                                            pdf_contents.append(pdf_content)
                                            logger.info(
                                                f"PDF内容提取成功，长度: {len(pdf_text)} 字符"
                                            )
                                        else:
                                            pdf_contents.append(
                                                f"📄 PDF文件 '{filename}' 内容为空或无法提取"
                                            )
                                    else:
                                        pdf_contents.append(
                                            f"📄 PDF文件 '{filename}' 数据为空"
                                        )

                                except Exception as e:
                                    error_msg = (
                                        f"📄 PDF文件 '{filename}' 处理失败: {str(e)}"
                                    )
                                    pdf_contents.append(error_msg)
                                    logger.error(f"PDF处理错误: {e}")

                    # 只保留用户的文本部分
                    user_text = "\n".join(text_parts) if text_parts else ""

                    # 创建处理后的消息
                    if (
                        HumanMessage
                        and hasattr(message, "__class__")
                        and message.__class__.__name__ == "HumanMessage"
                    ):
                        if user_text.strip():
                            processed_message = HumanMessage(
                                content=[{"type": "text", "text": user_text}],
                                additional_kwargs=getattr(
                                    message, "additional_kwargs", {}
                                ),
                                response_metadata=getattr(
                                    message, "response_metadata", {}
                                ),
                                id=getattr(message, "id", None),
                            )
                        else:
                            processed_message = HumanMessage(
                                content=[
                                    {
                                        "type": "text",
                                        "text": "请分析上传的PDF文件内容。",
                                    }
                                ],
                                additional_kwargs=getattr(
                                    message, "additional_kwargs", {}
                                ),
                                response_metadata=getattr(
                                    message, "response_metadata", {}
                                ),
                                id=getattr(message, "id", None),
                            )
                        if hasattr(message, "metadata"):
                            processed_message.metadata = message.metadata
                        processed_messages.append(processed_message)
                    else:
                        processed_messages.append(message)
                else:
                    # 不包含PDF的消息，保持原样
                    processed_messages.append(message)
            else:
                # 纯文本消息，直接保留
                processed_messages.append(message)
        else:
            # 保持原消息
            processed_messages.append(message)

    # 构建系统消息
    if pdf_contents:
        pdf_context = "\n\n".join(pdf_contents)
        system_content = f"""你是一个智能助手，可以分析和回答关于PDF文档内容的问题。

以下是用户上传的PDF文件内容，请基于这些内容回答用户的问题：

{pdf_context}

请根据上述PDF内容回答用户的问题。如果问题与PDF内容相关，请引用具体的内容进行回答。"""

    return processed_messages, system_content


# ===== 文件对话引擎 =====


class FileChatEngine:
    """文件对话引擎 - 支持PDF、图片和文本的智能对话"""

    def __init__(self):
        self.pdf_processor = None
        self.graph = None
        self._initialized = False

    async def initialize(self):
        """初始化引擎"""
        if self._initialized:
            return

        try:
            # 初始化PDF处理器
            self.pdf_processor = PDFProcessor(enable_cache=True)
            # 构建图
            await self._build_graph()

            self._initialized = True
            logger.info("File chat engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize file chat engine: {str(e)}")
            raise

    async def _build_graph(self):
        """构建LangGraph工作流"""
        workflow = StateGraph(WorkflowState)

        # 添加节点
        workflow.add_node("detect_file_type", self._detect_file_type_node)
        workflow.add_node("pdf_processing", self._pdf_processing_node)
        workflow.add_node("image_processing", self._image_processing_node)
        workflow.add_node("text_processing", self._text_processing_node)

        # 添加边
        workflow.add_edge(START, "detect_file_type")

        # 添加条件边：根据文件类型路由
        workflow.add_conditional_edges(
            "detect_file_type",
            self._route_by_file_type_condition_edge,
            {
                "pdf_processing": "pdf_processing",
                "image_processing": "image_processing",
                "text_processing": "text_processing",
            },
        )

        # 所有处理节点都连接到END
        workflow.add_edge("pdf_processing", END)
        workflow.add_edge("image_processing", END)
        workflow.add_edge("text_processing", END)

        # 编译图
        self.graph = workflow.compile()
        logger.info("LangGraph workflow built successfully")

    def _detect_file_type_node(self, state: WorkflowState) -> WorkflowState:
        """检测消息中的文件类型"""
        messages = state.get("messages", [])
        file_type = detect_file_type(messages)

        logger.info(f"检测到文件类型: {file_type}")

        return {"file_type": file_type, "messages": messages}

    def _pdf_processing_node(self, state: WorkflowState) -> WorkflowState:
        """处理PDF文件的节点"""
        messages = state.get("messages", [])

        # 处理PDF消息
        processed_messages, system_content = process_pdf_messages(
            messages, self.pdf_processor
        )

        # 构建完整消息列表
        full_messages = [
            {"role": "system", "content": system_content}
        ] + processed_messages

        # 调用PDF智能体
        response = pdf_agent.invoke({"messages": full_messages})

        return {
            "messages": response["messages"],
            "file_type": state.get("file_type", "pdf"),
        }

    def _image_processing_node(self, state: WorkflowState) -> WorkflowState:
        """处理图片文件的节点"""
        logger.info("处理图片文件")
        # 在调用图片模型前，清洗并转换 file(base64 image) → image_url
        raw_messages = state.get("messages", [])
        safe_messages = _preprocess_images_messages(raw_messages)
        response = image_agent.invoke({"messages": safe_messages})

        return {
            "messages": response["messages"],
            "file_type": state.get("file_type", "image"),
        }

    def _text_processing_node(self, state: WorkflowState) -> WorkflowState:
        """处理纯文本的节点"""
        messages = state.get("messages", [])
        # 兜底：移除不被模型支持的 file 块
        cleaned: List[Any] = []
        for m in messages:
            try:
                if isinstance(m, HumanMessage) and isinstance(m.content, list):
                    cleaned_blocks = _sanitize_blocks(
                        [
                            blk
                            for blk in m.content
                            if isinstance(blk, dict) and blk.get("type") != "file"
                        ]
                    )
                    cleaned.append(
                        HumanMessage(
                            content=cleaned_blocks if cleaned_blocks else m.content,
                            additional_kwargs=getattr(m, "additional_kwargs", {}),
                            response_metadata=getattr(m, "response_metadata", {}),
                            id=getattr(m, "id", None),
                        )
                    )
                else:
                    cleaned.append(m)
            except Exception:
                cleaned.append(m)
        # 对于纯文本，使用PDF智能体作为默认处理器
        response = pdf_agent.invoke({"messages": cleaned})

        return {
            "messages": response["messages"],
            "file_type": state.get("file_type", "text"),
        }

    def _route_by_file_type_condition_edge(
        self, state: WorkflowState
    ) -> Literal["pdf_processing", "image_processing", "text_processing"]:
        """根据文件类型路由到相应的处理节点"""
        file_type = state.get("file_type", "text")

        if file_type == "pdf":
            return "pdf_processing"
        elif file_type == "image":
            return "image_processing"
        else:
            return "text_processing"


class FileChatEngineFactory:
    """文件对话引擎工厂类"""

    _instance = None

    @classmethod
    async def create_engine(cls) -> FileChatEngine:
        """创建或获取引擎实例（单例模式）"""
        if cls._instance is None:
            engine = FileChatEngine()
            await engine.initialize()
            cls._instance = engine
            logger.info("Created new file chat engine instance")

        return cls._instance

    @classmethod
    async def get_engine(cls) -> FileChatEngine:
        """获取引擎实例"""
        return await cls.create_engine()

    @classmethod
    def clear_instance(cls):
        """清理实例"""
        cls._instance = None
        logger.info("Cleared file chat engine instance")
