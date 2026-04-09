from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from runtime_service.runtime.context import RuntimeContext, coerce_runtime_context
from runtime_service.runtime.modeling import resolve_model_by_id


@dataclass(frozen=True)
class AgentDefaults:
    model_id: str
    system_prompt: str
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    enable_tools: bool = True
    public_tool_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResolvedRuntimeRequest:
    context: RuntimeContext
    model: Any
    system_prompt: str
    tools: list[Any]


def normalize_tool_name(raw_name: Any) -> str:
    return str(raw_name or "").strip().lower()


def build_tool_catalog(tools: Sequence[Any]) -> dict[str, Any]:
    catalog: dict[str, Any] = {}
    for tool in tools:
        name = normalize_tool_name(getattr(tool, "name", ""))
        if not name:
            continue
        catalog[name] = tool
    return catalog


def _normalize_requested_tool_names(raw_names: Sequence[str] | None) -> list[str]:
    if raw_names is None:
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_name in raw_names:
        name = normalize_tool_name(raw_name)
        if not name or name in seen:
            continue
        seen.add(name)
        normalized.append(name)
    return normalized


def _bind_model_request_params(
    model: Any,
    *,
    temperature: float | None,
    max_tokens: int | None,
    top_p: float | None,
) -> Any:
    kwargs: dict[str, Any] = {}
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if top_p is not None:
        kwargs["top_p"] = top_p
    if not kwargs:
        return model
    return model.bind(**kwargs)


def _resolve_optional_tools(
    public_tool_catalog: Mapping[str, Any],
    requested_tool_names: Sequence[str],
) -> list[Any]:
    if not requested_tool_names:
        return []

    selected: list[Any] = []
    unknown: list[str] = []
    for name in requested_tool_names:
        tool = public_tool_catalog.get(name)
        if tool is None:
            unknown.append(name)
            continue
        selected.append(tool)

    if unknown:
        allowed = ", ".join(sorted(public_tool_catalog.keys()))
        raise ValueError(f"Unsupported tools: {unknown}. allowed: {allowed}")

    return selected


def _dedupe_tools_by_name(tools: Sequence[Any]) -> list[Any]:
    unique_tools: list[Any] = []
    seen: set[str] = set()
    for tool in tools:
        name = normalize_tool_name(getattr(tool, "name", ""))
        if not name or name in seen:
            continue
        seen.add(name)
        unique_tools.append(tool)
    return unique_tools


def resolve_runtime_request(
    *,
    context: RuntimeContext | Mapping[str, Any] | None,
    defaults: AgentDefaults,
    required_tools: Sequence[Any],
    public_tools: Sequence[Any],
) -> ResolvedRuntimeRequest:
    runtime_context = coerce_runtime_context(context)

    model_id = runtime_context.model_id or defaults.model_id
    system_prompt = runtime_context.system_prompt or defaults.system_prompt
    temperature = (
        runtime_context.temperature
        if runtime_context.temperature is not None
        else defaults.temperature
    )
    max_tokens = (
        runtime_context.max_tokens
        if runtime_context.max_tokens is not None
        else defaults.max_tokens
    )
    top_p = runtime_context.top_p if runtime_context.top_p is not None else defaults.top_p
    enable_tools = (
        runtime_context.enable_tools
        if runtime_context.enable_tools is not None
        else defaults.enable_tools
    )

    requested_public_tool_names = _normalize_requested_tool_names(
        runtime_context.tools
        if runtime_context.tools is not None
        else defaults.public_tool_names
    )
    public_tool_catalog = build_tool_catalog(public_tools)
    optional_tools = (
        _resolve_optional_tools(public_tool_catalog, requested_public_tool_names)
        if enable_tools
        else []
    )

    model = _bind_model_request_params(
        resolve_model_by_id(model_id),
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
    )
    tools = _dedupe_tools_by_name([*required_tools, *optional_tools])

    return ResolvedRuntimeRequest(
        context=runtime_context,
        model=model,
        system_prompt=system_prompt,
        tools=tools,
    )
