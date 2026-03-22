# pyright: reportMissingImports=false, reportMissingModuleSource=false
from __future__ import annotations

from collections.abc import Mapping
import json
import re
from typing import Any

from langchain.agents.middleware import ModelResponse

STAGE_ALLOWED_TOOLS: dict[str, list[str]] = {
    "analysis": [
        "run_requirement_analysis_subagent",
        "record_requirement_analysis",
    ],
    "generation": [
        "run_usecase_generation_subagent",
        "record_generated_usecases",
    ],
    "review": [
        "run_usecase_review_subagent",
        "record_usecase_review",
    ],
    "awaiting_user_confirmation": [
        "run_usecase_generation_subagent",
        "record_generated_usecases",
        "run_usecase_persist_subagent",
        "persist_approved_usecases",
    ],
    "completed": [],
}

GREETING_GUARD_SYSTEM_INSTRUCTION = (
    "Greeting-only check-in detected with no active workflow context. "
    "Reply briefly, then ask the user to provide requirement text or upload "
    "requirement materials before starting requirement analysis. "
    "Do not call workflow tools on this turn."
)

AWAITING_CONFIRMATION_SYSTEM_INSTRUCTION = (
    "The reviewed use cases are waiting for an explicit user decision. "
    "When the user clearly confirms persistence, prepare the final persistence plan with `run_usecase_persist_subagent` before calling `persist_approved_usecases`. "
    "If the user requests revisions, continue with generation tools instead of persisting. "
    "If the user has not decided yet, answer naturally and ask whether they want revisions or final persistence."
)

_TOOL_CALL_PLACEHOLDER_CONTENT = "[tool-call]"
_TOOL_PROGRESS_MESSAGES = {
    "run_requirement_analysis_subagent": "我正在分析需求内容，先提炼功能点、业务规则和边界条件。",
    "record_requirement_analysis": "我已经整理好需求分析结果，接下来开始生成候选用例。",
    "run_usecase_generation_subagent": "我正在根据需求分析生成候选用例。",
    "record_generated_usecases": "我已经整理好候选用例，接下来开始评审覆盖性和规范性。",
    "run_usecase_review_subagent": "我正在检查候选用例的覆盖性、规范性和缺失项。",
    "record_usecase_review": "我已经完成候选用例评审，正在整理结果给你确认。",
    "run_usecase_persist_subagent": "我正在整理最终落库计划，确认最终用例和附件持久化范围。",
    "persist_approved_usecases": "我正在根据你的确认执行最终落库。",
}

_GREETING_ONLY_RE = re.compile(
    r"^(?:"
    r"(?:你好(?:呀|啊|哈)?|您好|嗨|哈喽|hello|hi|hey|早上好|上午好|中午好|下午好|晚上好|在吗|在不在|有人吗|忙吗|在嘛|在么)"
    r"(?:[\s,!！?？,.，。~～]*(?:你好(?:呀|啊|哈)?|您好|嗨|哈喽|hello|hi|hey|早上好|上午好|中午好|下午好|晚上好|在吗|在不在|有人吗|忙吗|在嘛|在么))*"
    r")$",
    re.IGNORECASE,
)
_NEGATED_CONFIRMATION_RE = re.compile(
    r"(?:\b(?:not|don't|do not|without|haven't|have not|what happens if)\b|没有|未|不要|先不要|别)",
    re.IGNORECASE,
)
_EXPLICIT_PERSIST_CONFIRM_RE = re.compile(
    r"(?:"
    r"\b(?:confirm(?:ed|s|ing)?|approve(?:d|s|ing)?|go ahead|proceed)\b.*\b(?:persist|persistence|save)\b"
    r"|\b(?:persist|save)\b.*\b(?:approved use cases|current version|this version)\b"
    r"|确认(?:当前版本)?(?:可以)?(?:落库|保存|入库)"
    r"|(?:可以|确认)(?:落库|保存|入库)"
    r"|请(?:直接)?(?:落库|保存|入库)"
    r")",
    re.IGNORECASE,
)
_REVISION_REQUEST_RE = re.compile(
    r"(?:\b(?:revise|revision|modify|edit|update|change|regenerate|redo|split)\b|修改|修订|调整|重做|重新生成|拆分|补充)",
    re.IGNORECASE,
)


def get_message_content(message: Any) -> Any:
    if hasattr(message, "content"):
        return getattr(message, "content")
    if isinstance(message, Mapping):
        return message.get("content")
    return None


def get_message_type(message: Any) -> str | None:
    if hasattr(message, "type"):
        value = getattr(message, "type")
        return value if isinstance(value, str) else None
    if isinstance(message, Mapping):
        value = message.get("type")
        return value if isinstance(value, str) else None
    return None


def get_message_role(message: Any) -> str | None:
    if hasattr(message, "role"):
        value = getattr(message, "role")
        return value if isinstance(value, str) else None
    if isinstance(message, Mapping):
        value = message.get("role")
        return value if isinstance(value, str) else None
    return None


def get_message_name(message: Any) -> str | None:
    if hasattr(message, "name"):
        value = getattr(message, "name")
        return value if isinstance(value, str) else None
    if isinstance(message, Mapping):
        value = message.get("name")
        return value if isinstance(value, str) else None
    return None


def get_tool_calls(message: Any) -> list[Any]:
    if hasattr(message, "tool_calls"):
        value = getattr(message, "tool_calls")
        return value if isinstance(value, list) else []
    if isinstance(message, Mapping):
        value = message.get("tool_calls")
        return value if isinstance(value, list) else []
    return []


def get_tool_call_name(tool_call: Any) -> str | None:
    if isinstance(tool_call, Mapping):
        value = tool_call.get("name")
        return value if isinstance(value, str) else None
    value = getattr(tool_call, "name", None)
    return value if isinstance(value, str) else None


def with_message_content(message: Any, content: str) -> Any:
    if hasattr(message, "model_copy"):
        return message.model_copy(update={"content": content})
    if isinstance(message, Mapping):
        next_message = dict(message)
        next_message["content"] = content
        return next_message
    return message


def with_message_tool_calls(message: Any, tool_calls: list[Any]) -> Any:
    if hasattr(message, "model_copy"):
        return message.model_copy(update={"tool_calls": tool_calls})
    if isinstance(message, Mapping):
        next_message = dict(message)
        next_message["tool_calls"] = tool_calls
        return next_message
    return message


def has_explicit_message_content(content: Any) -> bool:
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, list):
        return bool(content)
    return False


def build_tool_progress_content(tool_calls: list[Any]) -> str:
    progress_parts: list[str] = []
    seen: set[str] = set()
    for tool_call in tool_calls:
        tool_name = get_tool_call_name(tool_call)
        if not tool_name:
            continue
        progress_text = _TOOL_PROGRESS_MESSAGES.get(tool_name)
        if not progress_text or progress_text in seen:
            continue
        progress_parts.append(progress_text)
        seen.add(progress_text)
    return "\n".join(progress_parts).strip()


def extract_text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if isinstance(item, str) and item.strip():
            parts.append(item.strip())
            continue
        if not isinstance(item, Mapping):
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
    return "\n".join(parts).strip()


def get_latest_user_text_from_messages(messages: Any) -> str:
    if not isinstance(messages, list):
        return ""
    for message in reversed(messages):
        message_type = get_message_type(message)
        message_role = get_message_role(message)
        if message_type not in {"human", "user"} and message_role != "user":
            continue
        return extract_text_from_content(get_message_content(message))
    return ""


def get_latest_user_text(request_messages: Any, state_messages: Any) -> str:
    latest_request_text = get_latest_user_text_from_messages(request_messages)
    if latest_request_text:
        return latest_request_text
    return get_latest_user_text_from_messages(state_messages)


def get_system_message_text(system_message: Any) -> str:
    content = get_message_content(system_message)
    if isinstance(content, str):
        return content.strip()
    return str(system_message or "").strip()


def normalize_tool_call_messages(messages: list[Any]) -> list[Any]:
    normalized: list[Any] = []
    for message in messages:
        role = get_message_role(message)
        message_type = get_message_type(message)
        tool_calls = get_tool_calls(message)
        content = get_message_content(message)
        if tool_calls and (message_type == "ai" or role == "assistant"):
            if not has_explicit_message_content(content):
                progress_content = build_tool_progress_content(tool_calls)
                normalized.append(
                    with_message_content(
                        message,
                        progress_content or _TOOL_CALL_PLACEHOLDER_CONTENT,
                    )
                )
                continue
        normalized.append(message)
    return normalized


def allowed_names_for_stage(stage: str) -> list[str]:
    return STAGE_ALLOWED_TOOLS.get(stage, STAGE_ALLOWED_TOOLS["analysis"])


def infer_stage_from_messages(messages: Any) -> str | None:
    if not isinstance(messages, list):
        return None
    for message in reversed(messages):
        if getattr(message, "type", None) != "tool":
            continue
        content = getattr(message, "content", None)
        if not isinstance(content, str):
            continue
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        stage = payload.get("stage")
        if stage == "requirement_analysis":
            return "generation"
        if stage == "generated_candidate_usecases":
            return "review"
        if stage == "reviewed_candidate_usecases":
            return "awaiting_user_confirmation" if bool(payload.get("persistable")) else "generation"
        if stage == "persisted":
            return "completed"
    return None


def infer_stage(state: Mapping[str, Any]) -> str:
    explicit = state.get("current_stage")
    explicit_stage = explicit if isinstance(explicit, str) and explicit else None
    message_stage = infer_stage_from_messages(state.get("messages"))
    if message_stage:
        return message_stage
    if explicit_stage:
        return explicit_stage
    return "analysis"


def has_multimodal_context(state: Mapping[str, Any]) -> bool:
    summary = state.get("multimodal_summary")
    if isinstance(summary, str) and summary.strip():
        return True
    attachments = state.get("multimodal_attachments")
    return isinstance(attachments, list) and bool(attachments)


def is_greeting_only_text(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized or len(normalized) > 24:
        return False
    return bool(_GREETING_ONLY_RE.fullmatch(normalized))


def is_explicit_persist_confirmation_text(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return False
    if _NEGATED_CONFIRMATION_RE.search(normalized):
        return False
    return bool(_EXPLICIT_PERSIST_CONFIRM_RE.search(normalized))


def is_revision_request_text(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return False
    if is_explicit_persist_confirmation_text(normalized):
        return False
    return bool(_REVISION_REQUEST_RE.search(normalized))


def should_guard_greeting_only_turn(state: Mapping[str, Any], request_messages: Any) -> bool:
    explicit_stage = state.get("current_stage")
    if isinstance(explicit_stage, str) and explicit_stage:
        return False
    if infer_stage_from_messages(state.get("messages")):
        return False
    if has_multimodal_context(state):
        return False
    latest_user_text = get_latest_user_text(request_messages, state.get("messages"))
    return is_greeting_only_text(latest_user_text)


def has_tool_message_since_latest_user_turn(messages: Any, tool_name: str) -> bool:
    if not isinstance(messages, list):
        return False

    latest_user_index: int | None = None
    for index in range(len(messages) - 1, -1, -1):
        message = messages[index]
        message_type = get_message_type(message)
        message_role = get_message_role(message)
        if message_type in {"human", "user"} or message_role == "user":
            latest_user_index = index
            break

    if latest_user_index is None:
        return False

    for message in messages[latest_user_index + 1 :]:
        if get_message_type(message) != "tool":
            continue
        if get_message_name(message) == tool_name:
            return True
    return False


def allowed_names_for_request(
    tool_names: list[str], stage: str | None, latest_user_text: str, state_messages: Any
) -> list[str]:
    if stage != "awaiting_user_confirmation":
        return tool_names
    if is_explicit_persist_confirmation_text(latest_user_text):
        if has_tool_message_since_latest_user_turn(
            state_messages, "run_usecase_persist_subagent"
        ):
            return [
                name for name in tool_names if name == "persist_approved_usecases"
            ]
        return [
            name
            for name in tool_names
            if name in {"run_usecase_persist_subagent", "persist_approved_usecases"}
        ]
    if is_revision_request_text(latest_user_text):
        return [
            name
            for name in tool_names
            if name in {"run_usecase_generation_subagent", "record_generated_usecases"}
        ]
    return []


def build_stage_system_message(system_text: str, stage: str, allowed_names: list[str]) -> str:
    stage_text = (
        f"Current workflow stage: {stage}. "
        f"Only use these tools now: {', '.join(allowed_names) if allowed_names else 'none'}"
    )
    system_sections = [section for section in [system_text, stage_text] if section]
    if stage == "awaiting_user_confirmation":
        system_sections.append(AWAITING_CONFIRMATION_SYSTEM_INSTRUCTION)
    return "\n\n".join(system_sections)


def sanitize_model_response(response: ModelResponse, allowed_names: list[str]) -> ModelResponse:
    result = getattr(response, "result", None)
    if not isinstance(result, list):
        return response

    allowed_name_set = set(allowed_names)
    next_result: list[Any] = []
    changed = False

    for message in result:
        tool_calls = get_tool_calls(message)
        if not tool_calls:
            next_result.append(message)
            continue

        next_message = message
        filtered_tool_calls = [
            tool_call
            for tool_call in tool_calls
            if (tool_name := get_tool_call_name(tool_call))
            and tool_name.strip()
            and tool_name in allowed_name_set
        ]

        if not has_explicit_message_content(get_message_content(next_message)):
            progress_content = build_tool_progress_content(filtered_tool_calls or tool_calls)
            if progress_content:
                next_message = with_message_content(next_message, progress_content)
                changed = True

        if len(filtered_tool_calls) != len(tool_calls):
            changed = True
            next_result.append(with_message_tool_calls(next_message, filtered_tool_calls))
            continue

        next_result.append(next_message)

    if not changed:
        return response

    return ModelResponse(
        result=next_result,
        structured_response=getattr(response, "structured_response", None),
    )


__all__ = [
    "AWAITING_CONFIRMATION_SYSTEM_INSTRUCTION",
    "GREETING_GUARD_SYSTEM_INSTRUCTION",
    "STAGE_ALLOWED_TOOLS",
    "allowed_names_for_request",
    "allowed_names_for_stage",
    "build_stage_system_message",
    "get_message_name",
    "get_latest_user_text",
    "get_system_message_text",
    "has_tool_message_since_latest_user_turn",
    "infer_stage",
    "normalize_tool_call_messages",
    "sanitize_model_response",
    "should_guard_greeting_only_turn",
]
