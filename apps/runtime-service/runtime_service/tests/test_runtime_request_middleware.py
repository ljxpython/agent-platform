from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from langchain.agents.middleware import ModelRequest, ModelResponse
from langchain.messages import AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.runtime import Runtime

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from runtime_service.middlewares.runtime_request import RuntimeRequestMiddleware  # noqa: E402
from runtime_service.runtime.context import RuntimeContext  # noqa: E402
from runtime_service.runtime.runtime_request_resolver import (  # noqa: E402
    AgentDefaults,
    resolve_runtime_request,
)


@tool("required_tool", description="Required tool for the graph.")
def required_tool() -> str:
    return "required"


@tool("optional_tool_a", description="Optional public tool A.")
def optional_tool_a() -> str:
    return "optional-a"


@tool("optional_tool_b", description="Optional public tool B.")
def optional_tool_b() -> str:
    return "optional-b"


class DummyModel:
    def __init__(self) -> None:
        self.bound_kwargs: dict[str, Any] = {}

    def bind(self, **kwargs: Any) -> DummyModel:
        self.bound_kwargs = dict(kwargs)
        return self


def test_resolve_runtime_request_prefers_context_values(monkeypatch: Any) -> None:
    dummy_model = DummyModel()

    monkeypatch.setattr(
        "runtime_service.runtime.runtime_request_resolver.resolve_model_by_id",
        lambda model_id: dummy_model if model_id == "demo-model" else None,
    )

    resolved = resolve_runtime_request(
        context=RuntimeContext(
            model_id="demo-model",
            system_prompt="context prompt",
            temperature=0.7,
            max_tokens=256,
            top_p=0.8,
            enable_tools=True,
            tools=["optional_tool_b"],
        ),
        defaults=AgentDefaults(
            model_id="default-model",
            system_prompt="default prompt",
            temperature=0.1,
            enable_tools=True,
            public_tool_names=("optional_tool_a",),
        ),
        required_tools=[required_tool],
        public_tools=[optional_tool_a, optional_tool_b],
    )

    assert resolved.system_prompt == "context prompt"
    assert resolved.tools == [required_tool, optional_tool_b]
    assert resolved.model is dummy_model
    assert dummy_model.bound_kwargs == {
        "temperature": 0.7,
        "max_tokens": 256,
        "top_p": 0.8,
    }


def test_resolve_runtime_request_rejects_unknown_public_tools(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "runtime_service.runtime.runtime_request_resolver.resolve_model_by_id",
        lambda _model_id: DummyModel(),
    )

    try:
        resolve_runtime_request(
            context=RuntimeContext(enable_tools=True, tools=["missing_tool"]),
            defaults=AgentDefaults(
                model_id="default-model",
                system_prompt="default prompt",
            ),
            required_tools=[required_tool],
            public_tools=[optional_tool_a],
        )
    except ValueError as exc:
        assert "Unsupported tools" in str(exc)
        assert "missing_tool" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown tool name.")


def test_runtime_request_middleware_wrap_model_call_updates_request(
    monkeypatch: Any,
) -> None:
    dummy_model = DummyModel()

    monkeypatch.setattr(
        "runtime_service.runtime.runtime_request_resolver.resolve_model_by_id",
        lambda _model_id: dummy_model,
    )

    middleware = RuntimeRequestMiddleware(
        defaults=AgentDefaults(
            model_id="default-model",
            system_prompt="default prompt",
            public_tool_names=("optional_tool_a",),
        ),
        required_tools=[required_tool],
        public_tools=[optional_tool_a, optional_tool_b],
    )
    request = ModelRequest(
        model=object(),
        messages=[],
        system_message=SystemMessage(content="base"),
        tools=[required_tool, optional_tool_a, optional_tool_b],
        runtime=Runtime(
            context=RuntimeContext(
                model_id="demo-model",
                system_prompt="context prompt",
                enable_tools=True,
                tools=["optional_tool_b"],
            )
        ),
    )

    def handler(updated_request: ModelRequest) -> ModelResponse:
        assert updated_request.model is dummy_model
        assert updated_request.system_prompt == "context prompt"
        assert updated_request.tools == [required_tool, optional_tool_b]
        return ModelResponse(result=[AIMessage(content="ok")])

    response = middleware.wrap_model_call(request, handler)

    assert response.result[0].text == "ok"


def test_runtime_request_middleware_awrap_model_call_updates_request(
    monkeypatch: Any,
) -> None:
    dummy_model = DummyModel()

    monkeypatch.setattr(
        "runtime_service.runtime.runtime_request_resolver.resolve_model_by_id",
        lambda _model_id: dummy_model,
    )

    middleware = RuntimeRequestMiddleware(
        defaults=AgentDefaults(
            model_id="default-model",
            system_prompt="default prompt",
            public_tool_names=("optional_tool_a",),
        ),
        required_tools=[required_tool],
        public_tools=[optional_tool_a, optional_tool_b],
    )
    request = ModelRequest(
        model=object(),
        messages=[],
        system_message=SystemMessage(content="base"),
        tools=[required_tool, optional_tool_a, optional_tool_b],
        runtime=Runtime(
            context=RuntimeContext(
                model_id="demo-model",
                enable_tools=False,
            )
        ),
    )

    async def handler(updated_request: ModelRequest) -> ModelResponse:
        assert updated_request.model is dummy_model
        assert updated_request.system_prompt == "default prompt"
        assert updated_request.tools == [required_tool]
        return ModelResponse(result=[AIMessage(content="ok")])

    response = asyncio.run(middleware.awrap_model_call(request, handler))

    assert response.result[0].text == "ok"
