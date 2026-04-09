from __future__ import annotations

from typing import Any

from runtime_service.agents.personal_assistant_agent.prompts import SUPERVISOR_PROMPT
from runtime_service.agents.personal_assistant_agent.tools import (
    build_personal_assistant_agent,
)
from runtime_service.conf.settings import get_default_model_id
from runtime_service.middlewares.runtime_request import RuntimeRequestMiddleware
from runtime_service.runtime.modeling import resolve_model_by_id
from runtime_service.runtime.runtime_request_resolver import AgentDefaults
from runtime_service.tools.registry import abuild_runtime_tools, build_runtime_tools


PERSONAL_ASSISTANT_DEFAULTS = AgentDefaults(
    model_id=get_default_model_id(),
    system_prompt=SUPERVISOR_PROMPT,
    enable_tools=False,
)

BASELINE_MODEL = resolve_model_by_id(PERSONAL_ASSISTANT_DEFAULTS.model_id)


def _resolve_public_tools(settings: Any) -> list[Any]:
    return build_runtime_tools(
        enable_tools=settings.enable_tools,
        requested_tool_names=settings.requested_public_tool_names or None,
    )


async def _aresolve_public_tools(settings: Any) -> list[Any]:
    return await abuild_runtime_tools(
        enable_tools=settings.enable_tools,
        requested_tool_names=settings.requested_public_tool_names or None,
    )


graph = build_personal_assistant_agent(
    BASELINE_MODEL,
    middleware=[
        RuntimeRequestMiddleware(
            defaults=PERSONAL_ASSISTANT_DEFAULTS,
            required_tools=[],
            public_tools=[],
            public_tool_resolver=_resolve_public_tools,
            apublic_tool_resolver=_aresolve_public_tools,
        )
    ],
)
