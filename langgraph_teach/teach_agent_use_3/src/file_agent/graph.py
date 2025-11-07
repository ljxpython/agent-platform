import os
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

# Ensure src and project root are on sys.path for direct execution
_CURR_DIR = os.path.dirname(__file__)
_SRC_DIR = os.path.dirname(_CURR_DIR)
_ROOT_DIR = os.path.dirname(_SRC_DIR)
for _p in (_SRC_DIR, _ROOT_DIR):
    if _p and _p not in sys.path:
        sys.path.insert(0, _p)

# Reuse the robust PDF/image extraction used by the middleware
from file_agent.main import process_attachments_in_state
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.constants import END, START
from langgraph.graph import MessagesState, StateGraph

# Use existing model getters to ensure consistent configuration
from llms import get_default_model, get_doubao_model


# ---------------------------
# Routing / detection helpers
# ---------------------------
def _is_dry_run() -> bool:
    val = os.getenv("GRAPH_DRY_RUN", "").lower()
    return val in {"1", "true", "yes"}


def _get_last_human_message(messages: List[AnyMessage]) -> Optional[HumanMessage]:
    for m in reversed(messages or []):
        if isinstance(m, HumanMessage):
            return m
    return None


def _detect_content_type_from_blocks(blocks: Any) -> str:
    """Detect content type from a multimodal blocks list.

    Returns one of: 'pdf', 'image', 'text'
    """
    if not isinstance(blocks, list):
        return "text"

    def _is_pdf_mime(m: str) -> bool:
        m = (m or "").lower()
        return m.startswith("application/pdf")

    def _maybe_mime_from_data_url(data_url: str) -> Optional[str]:
        try:
            if (
                isinstance(data_url, str)
                and data_url.startswith("data:")
                and "," in data_url
            ):
                header = data_url.split(",", 1)[0]
                if ":" in header:
                    return header.split(":", 1)[1].split(";", 1)[0]
        except Exception:
            return None
        return None

    has_image = False

    for part in blocks:
        if not isinstance(part, dict):
            continue
        t = part.get("type")
        # Direct image parts
        if t == "image_url":
            return "image"

        if t == "file":
            mime = (
                part.get("mime_type")
                or part.get("mimeType")
                or _maybe_mime_from_data_url(part.get("data"))
                or ""
            )
            mime = str(mime).lower()
            if _is_pdf_mime(mime):
                return "pdf"
            if mime.startswith("image/"):
                has_image = True

    if has_image:
        return "image"
    return "text"


# ---------------------------
# Graph Node Implementations
# ---------------------------
def detect_node(state: MessagesState) -> Dict[str, Any]:
    """No-op node. Detection/branching happens via conditional edges."""
    # Nothing to write into state; just return empty delta.
    return {}


def image_chat_node(state: MessagesState) -> Dict[str, Any]:
    """Use Doubao model for image + text understanding."""
    if _is_dry_run():
        return {
            "messages": AIMessage(
                content="[DRY_RUN:image_chat] 已检测到图片消息，使用豆包进行图像理解。"
            )
        }
    model = get_doubao_model()
    result = model.invoke(state["messages"])  # type: ignore[index]
    return {"messages": result}


def pdf_chat_node(state: MessagesState) -> Dict[str, Any]:
    """Use DeepSeek for PDF understanding after pre-processing via extractor.

    We reuse `process_attachments_in_state` to transform the last human message:
    - Decode PDF base64 to file
    - Extract text (markdown) + images
    - Replace file blocks with clean text/image_url blocks
    Then we invoke the DeepSeek model with the cleaned multimodal content.
    """
    # Preprocess attachments in-place for this call (safe for the current step)
    try:
        process_attachments_in_state(state)  # may mutate last HumanMessage content
    except Exception:
        # If preprocessing fails, proceed and let model try its best
        pass

    # For DeepSeek (text-only), convert any image blocks into captions via Doubao,
    # then strip ALL image/file blocks in the entire history, leaving only text
    # for final DeepSeek invocation.
    msgs: List[AnyMessage] = list(state.get("messages", []))  # type: ignore[assignment]
    last_h = _get_last_human_message(msgs)
    if last_h is not None and isinstance(getattr(last_h, "content", None), list):
        blocks: List[Dict[str, Any]] = list(last_h.content)  # type: ignore[assignment]
        image_urls: List[str] = []
        text_blocks: List[Dict[str, Any]] = []
        for blk in blocks:
            if (
                isinstance(blk, dict)
                and blk.get("type") == "image_url"
                and isinstance(blk.get("image_url"), dict)
            ):
                url = blk["image_url"].get("url")
                if isinstance(url, str) and url:
                    image_urls.append(url)
            elif isinstance(blk, dict) and blk.get("type") == "text":
                text_blocks.append({"type": "text", "text": blk.get("text", "")})

        caption_text = ""
        if image_urls and not _is_dry_run():
            try:
                caption_text = _caption_images_with_doubao(image_urls)
            except Exception as _:
                caption_text = ""
        elif image_urls and _is_dry_run():
            caption_text = "[DRY_RUN] 已对PDF图片进行识别摘要。"

        if caption_text:
            text_blocks.append(
                {"type": "text", "text": f"以下为PDF内图片的识别摘要：\n{caption_text}"}
            )

        # Replace last human message content with text-only blocks
        try:
            new_last = HumanMessage(content=text_blocks)
            # rebuild messages keeping others, replacing last human occurrence
            for i in range(len(msgs) - 1, -1, -1):
                if isinstance(msgs[i], HumanMessage):
                    msgs[i] = new_last
                    break
        except Exception:
            pass

    # Regardless, ensure the ENTIRE message history is text-only for DeepSeek
    msgs = _to_text_only_for_deepseek(msgs)

    if _is_dry_run():
        return {
            "messages": AIMessage(
                content="[DRY_RUN:pdf_chat] 已检测到PDF，完成文本与图片提取（图片经豆包识别）后用DeepSeek总结。"
            )
        }

    model = get_default_model()  # DeepSeek
    result = model.invoke(msgs)  # type: ignore[arg-type]
    return {"messages": result}


def normal_chat_node(state: MessagesState) -> Dict[str, Any]:
    """Default DeepSeek chat when no files/images are present."""
    if _is_dry_run():
        return {
            "messages": AIMessage(
                content="[DRY_RUN:normal_chat] 普通对话，使用DeepSeek应答。"
            )
        }
    # Ensure entire history is text-only to satisfy DeepSeek API
    msgs: List[AnyMessage] = list(state.get("messages", []))  # type: ignore[assignment]
    msgs = _to_text_only_for_deepseek(msgs)
    model = get_default_model()
    result = model.invoke(msgs)  # type: ignore[arg-type]
    return {"messages": result}


# ---------------------------
# Conditional Edge
# ---------------------------
def route_edge(state: MessagesState) -> str:
    """Route to the appropriate node based on last human message."""
    msgs = state.get("messages", [])  # type: ignore[assignment]
    last_h = _get_last_human_message(msgs)
    if last_h is None:
        return "normal_chat"

    content = getattr(last_h, "content", None)
    ctype = _detect_content_type_from_blocks(content)
    if ctype == "pdf":
        return "pdf_chat"
    if ctype == "image":
        return "image_chat"
    return "normal_chat"


# ---------------------------
# Build & export graph
# ---------------------------
builder = StateGraph(MessagesState)

# Nodes
builder.add_node("detect", detect_node)
builder.add_node("image_chat", image_chat_node)
builder.add_node("pdf_chat", pdf_chat_node)
builder.add_node("normal_chat", normal_chat_node)

# Edges
builder.add_edge(START, "detect")
builder.add_conditional_edges("detect", route_edge)
builder.add_edge("image_chat", END)
builder.add_edge("pdf_chat", END)
builder.add_edge("normal_chat", END)

# Compiled graph
graph = builder.compile()


if __name__ == "__main__":
    # Optional: visualize to a file next to this module for quick inspection
    try:
        img = graph.get_graph().draw_mermaid_png()
        out_path = os.path.join(os.path.dirname(__file__), "file_agent_workflow.png")
        with open(out_path, "wb") as f:
            f.write(img)
        print(f"Workflow image saved to: {out_path}")
    except Exception as e:
        # In offline envs, this can fail due to remote rendering; it's safe to ignore
        print(f"Could not render workflow image: {e}")

    from file_agent.main import file_to_base64_block
    from langchain.messages import HumanMessage

    def _print_messages(tag: str, messages_state: Dict[str, Any]):
        print(f"\n===== {tag} =====")
        for m in messages_state.get("messages", []):
            try:
                m.pretty_print()
            except Exception:
                print(getattr(m, "content", m))

    # 1) Text-only → normal chat (exact example style)
    text_msg = HumanMessage(content="你好，介绍一下你自己。")
    routed = route_edge({"messages": [text_msg]})
    print(f"Expected route for text-only: {routed}")
    res = graph.invoke({"messages": [text_msg]})
    _print_messages("Normal Chat Response", res)

    # 2) Image chat → Doubao
    base_dir = os.path.dirname(__file__)
    # Try to pick an existing image in this folder
    image_exts = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
    image_path = None
    for fn in os.listdir(base_dir):
        if os.path.splitext(fn)[1].lower() in image_exts:
            image_path = os.path.join(base_dir, fn)
            break

    if image_path and os.path.isfile(image_path):
        image_block = file_to_base64_block(image_path)
        img_msg = HumanMessage(
            content=[
                {"type": "text", "text": "请描述图片中的关键信息。"},
                image_block,
            ]
        )
        routed = route_edge({"messages": [img_msg]})
        print(
            f"Expected route for image: {routed} | file={os.path.basename(image_path)}"
        )
        res = graph.invoke({"messages": [img_msg]})
        _print_messages("Image Chat Response", res)
    else:
        print("No test image found in src/file_agent.")

    # 3) PDF chat → DeepSeek (with preprocessing)
    pdf_path = None
    for fn in os.listdir(base_dir):
        if os.path.splitext(fn)[1].lower() == ".pdf":
            pdf_path = os.path.join(base_dir, fn)
            break

    if pdf_path and os.path.isfile(pdf_path):
        pdf_block = file_to_base64_block(pdf_path)
        pdf_msg = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": "请总结这份PDF的要点，并识别其中的图表或流程图。",
                },
                pdf_block,
            ]
        )
        routed = route_edge({"messages": [pdf_msg]})
        print(f"Expected route for pdf: {routed} | file={os.path.basename(pdf_path)}")
        res = graph.invoke({"messages": [pdf_msg]})
        _print_messages("PDF Chat Response", res)
    else:
        print("No test PDF found in src/file_agent.")


def _caption_images_with_doubao(image_urls: List[str]) -> str:
    """Use Doubao to caption images and return a combined Chinese summary."""
    from langchain.messages import HumanMessage

    model = get_doubao_model()
    content: List[Dict[str, Any]] = [
        {
            "type": "text",
            "text": "请逐一描述以下图片的内容（中文），涵盖文字、结构、图表与关键结论。",
        }
    ]
    for url in image_urls:
        content.append({"type": "image_url", "image_url": {"url": url}})
    resp = model.invoke([HumanMessage(content=content)])
    return resp.content if isinstance(resp.content, str) else str(resp.content)


def _to_text_only_for_deepseek(messages: List[AnyMessage]) -> List[AnyMessage]:
    """DeepSeek expects plain text messages. Convert any block-style content
    into a single text string and drop non-text parts.

    - text blocks -> appended as-is
    - image_url blocks -> replaced with a placeholder marker
    - file blocks -> replaced with a placeholder marker
    - other -> ignored
    """
    out: List[AnyMessage] = []
    for m in messages:
        content = getattr(m, "content", None)
        if isinstance(content, str):
            out.append(m)
            continue
        if isinstance(content, list):
            parts: List[str] = []
            for blk in content:
                if not isinstance(blk, dict):
                    continue
                t = blk.get("type")
                if t == "text":
                    txt = blk.get("text")
                    if isinstance(txt, str) and txt:
                        parts.append(txt)
                elif t == "image_url":
                    parts.append("[图片内容已识别并转为文字]")
                elif t == "file":
                    meta = blk.get("metadata") or {}
                    name = meta.get("filename") or meta.get("name") or "文件"
                    parts.append(f"[已接收文件：{name}]")
            new_text = "\n".join(parts).strip()
            try:
                out.append(m.__class__(content=new_text))  # preserve role/class
            except Exception:
                out.append(HumanMessage(content=new_text))
            continue
        # Fallback: stringify unknown content types
        try:
            out.append(m.__class__(content=str(content)))
        except Exception:
            out.append(HumanMessage(content=str(content)))
    return out
