from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from runtime_service.runtime.runtime_request_resolver import (
    AgentDefaults,
    resolve_runtime_request,
)


class RuntimeRequestMiddleware(AgentMiddleware):
    def __init__(
        self,
        *,
        defaults: AgentDefaults,
        required_tools: Sequence[Any],
        public_tools: Sequence[Any],
    ) -> None:
        self.defaults = defaults
        self.required_tools = list(required_tools)
        self.public_tools = list(public_tools)

    def _apply_runtime_request(self, request: ModelRequest) -> ModelRequest:
        resolved = resolve_runtime_request(
            context=request.runtime.context if request.runtime is not None else None,
            defaults=self.defaults,
            required_tools=self.required_tools,
            public_tools=self.public_tools,
        )
        return request.override(
            model=resolved.model,
            tools=resolved.tools,
            system_message=SystemMessage(content=resolved.system_prompt),
        )

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        return handler(self._apply_runtime_request(request))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        return await handler(self._apply_runtime_request(request))
