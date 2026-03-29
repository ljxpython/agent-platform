from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from deepagents.middleware.subagents import SubAgent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.tools import ToolRuntime
from langchain_core.tools import tool


def list_research_agent_skills() -> list[str]:
    skills_root = Path(__file__).resolve().parent / "skills"
    return [str(skills_root)]


def list_research_subagents() -> list[SubAgent]:
    skill_sources = list_research_agent_skills()
    return [
        SubAgent(
            name="research-subagent",
            description=(
                "Focused web researcher for one subtopic. Collect concise evidence and "
                "save findings into local files with source links."
            ),
            system_prompt=(
                "You are a focused research subagent. Keep scope narrow, cite URLs, and "
                "return concise findings that can be merged by the parent agent."
            ),
            skills=skill_sources,
        )
    ]


def _read_runtime_state(runtime: ToolRuntime[Any, Any]) -> dict[str, Any]:
    state = runtime.state if hasattr(runtime, "state") else {}
    return state if isinstance(state, dict) else {}


def _trim_text(value: Any, *, max_chars: int) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "...[truncated]"


def _extract_key_points(structured_data: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(structured_data, Mapping):
        return []
    raw_points = structured_data.get("key_points")
    if not isinstance(raw_points, list):
        return []
    key_points: list[str] = []
    for item in raw_points[:8]:
        text = str(item).strip()
        if text:
            key_points.append(text)
    return key_points


def _extract_source_refs(structured_data: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(structured_data, Mapping):
        return []
    raw_refs = structured_data.get("source_refs")
    if not isinstance(raw_refs, list):
        return []
    refs: list[dict[str, Any]] = []
    for item in raw_refs[:8]:
        if isinstance(item, Mapping):
            refs.append(dict(item))
    return refs


@tool(
    "read_multimodal_attachments",
    description=(
        "Read parsed multimodal attachment artifacts from runtime state and return a "
        "compact JSON payload for research workflows."
    ),
)
def read_multimodal_attachments(runtime: ToolRuntime[None, Any]) -> str:
    state = _read_runtime_state(runtime)
    multimodal_summary = state.get("multimodal_summary")
    attachments_raw = state.get("multimodal_attachments")

    attachments: list[dict[str, Any]] = []
    if isinstance(attachments_raw, list):
        for item in attachments_raw:
            if not isinstance(item, Mapping):
                continue
            structured_data = (
                item.get("structured_data")
                if isinstance(item.get("structured_data"), Mapping)
                else None
            )
            attachments.append(
                {
                    "attachment_id": str(item.get("attachment_id") or ""),
                    "kind": str(item.get("kind") or ""),
                    "name": item.get("name"),
                    "status": str(item.get("status") or ""),
                    "summary_for_model": str(item.get("summary_for_model") or ""),
                    "parsed_text_preview": _trim_text(
                        item.get("parsed_text"), max_chars=1200
                    ),
                    "key_points": _extract_key_points(structured_data),
                    "source_refs": _extract_source_refs(structured_data),
                }
            )

    payload = {
        "multimodal_summary": (
            multimodal_summary.strip()
            if isinstance(multimodal_summary, str) and multimodal_summary.strip()
            else None
        ),
        "attachments": attachments,
    }
    return json.dumps(payload, ensure_ascii=False)


def build_research_runtime_tools() -> list[Any]:
    return [read_multimodal_attachments]


async def aget_research_private_tools(config: dict[str, Any]) -> list[Any]:
    """Build research-only private tools (currently optional Tavily MCP)."""

    tavily_api_key = str(
        config.get("research_tavily_api_key") or os.getenv("RESEARCH_TAVILY_API_KEY") or ""
    ).strip()
    if not tavily_api_key:
        return []

    client = MultiServerMCPClient(
        {
            "tavily_web": {
                "transport": "http",
                "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={tavily_api_key}",
            }
        }
    )
    return await client.get_tools()
