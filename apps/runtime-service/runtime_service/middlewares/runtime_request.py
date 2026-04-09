from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from runtime_service.runtime.runtime_request_resolver import (
    AgentDefaults,
    ResolvedRuntimeSettings,
    build_tool_catalog,
    dedupe_tools_by_name,
    resolve_optional_tools,
    resolve_runtime_settings,
)


class RuntimeRequestMiddleware(AgentMiddleware):
    def __init__(
        self,
        *,
        defaults: AgentDefaults,
        required_tools: Sequence[Any],
        public_tools: Sequence[Any],
        required_tool_resolver: (
            Callable[[ResolvedRuntimeSettings], Sequence[Any]] | None
        ) = None,
        arequired_tool_resolver: (
            Callable[[ResolvedRuntimeSettings], Awaitable[Sequence[Any]]] | None
        ) = None,
        public_tool_resolver: (
            Callable[[ResolvedRuntimeSettings], Sequence[Any]] | None
        ) = None,
        apublic_tool_resolver: (
            Callable[[ResolvedRuntimeSettings], Awaitable[Sequence[Any]]] | None
        ) = None,
        system_prompt_resolver: Callable[[ResolvedRuntimeSettings], str] | None = None,
    ) -> None:
        self.defaults = defaults
        self.required_tools = list(required_tools)
        self.public_tools = list(public_tools)
        self.required_tool_resolver = required_tool_resolver
        self.arequired_tool_resolver = arequired_tool_resolver
        self.public_tool_resolver = public_tool_resolver
        self.apublic_tool_resolver = apublic_tool_resolver
        self.system_prompt_resolver = system_prompt_resolver

    def _resolve_settings(self, request: ModelRequest) -> ResolvedRuntimeSettings:
        return resolve_runtime_settings(
            context=request.runtime.context if request.runtime is not None else None,
            defaults=self.defaults,
        )

    def _resolve_required_tools_sync(
        self,
        settings: ResolvedRuntimeSettings,
    ) -> list[Any]:
        if self.required_tool_resolver is not None:
            return list(self.required_tool_resolver(settings))
        if self.arequired_tool_resolver is not None:
            raise TypeError("arequired_tool_resolver is not available in sync model calls.")
        return list(self.required_tools)

    async def _resolve_required_tools_async(
        self,
        settings: ResolvedRuntimeSettings,
    ) -> list[Any]:
        if self.arequired_tool_resolver is not None:
            return list(await self.arequired_tool_resolver(settings))
        if self.required_tool_resolver is not None:
            return list(self.required_tool_resolver(settings))
        return list(self.required_tools)

    def _resolve_public_tools_sync(
        self,
        settings: ResolvedRuntimeSettings,
    ) -> list[Any]:
        if not settings.enable_tools:
            return []
        if self.public_tool_resolver is not None:
            return list(self.public_tool_resolver(settings))
        if self.apublic_tool_resolver is not None:
            raise TypeError("apublic_tool_resolver is not available in sync model calls.")
        return resolve_optional_tools(
            build_tool_catalog(self.public_tools),
            settings.requested_public_tool_names,
        )

    async def _resolve_public_tools_async(
        self,
        settings: ResolvedRuntimeSettings,
    ) -> list[Any]:
        if not settings.enable_tools:
            return []
        if self.apublic_tool_resolver is not None:
            return list(await self.apublic_tool_resolver(settings))
        if self.public_tool_resolver is not None:
            return list(self.public_tool_resolver(settings))
        return resolve_optional_tools(
            build_tool_catalog(self.public_tools),
            settings.requested_public_tool_names,
        )

    def _resolve_system_prompt(self, settings: ResolvedRuntimeSettings) -> str:
        if self.system_prompt_resolver is not None:
            return self.system_prompt_resolver(settings)
        return settings.system_prompt

    def _apply_runtime_request_sync(self, request: ModelRequest) -> ModelRequest:
        settings = self._resolve_settings(request)
        tools = dedupe_tools_by_name(
            [
                *self._resolve_required_tools_sync(settings),
                *self._resolve_public_tools_sync(settings),
            ]
        )
        return request.override(
            model=settings.model,
            tools=tools,
            system_message=SystemMessage(content=self._resolve_system_prompt(settings)),
        )

    async def _apply_runtime_request_async(self, request: ModelRequest) -> ModelRequest:
        settings = self._resolve_settings(request)
        tools = dedupe_tools_by_name(
            [
                *(await self._resolve_required_tools_async(settings)),
                *(await self._resolve_public_tools_async(settings)),
            ]
        )
        return request.override(
            model=settings.model,
            tools=tools,
            system_message=SystemMessage(content=self._resolve_system_prompt(settings)),
        )

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        return handler(self._apply_runtime_request_sync(request))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        return await handler(await self._apply_runtime_request_async(request))
