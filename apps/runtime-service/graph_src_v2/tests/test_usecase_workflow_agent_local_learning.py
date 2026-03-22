# pyright: reportMissingImports=false, reportMissingModuleSource=false
from __future__ import annotations

import asyncio
import importlib
import json
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.tools import ToolRuntime
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from graph_src_v2.middlewares.multimodal import MultimodalMiddleware  # noqa: E402
from graph_src_v2.services.usecase_workflow_agent import tools as workflow_tools  # noqa: E402
from graph_src_v2.services.usecase_workflow_agent.graph import (  # noqa: E402
    SYSTEM_PROMPT,
    UsecaseWorkflowState,
    WorkflowToolSelectionMiddleware,
)
from graph_src_v2.tests.test_usecase_workflow_langgraph_api_smoke import (  # noqa: E402
    _build_review_snapshot,
)


class ToolReadyFakeChatModel(FakeMessagesListChatModel):
    def bind_tools(self, tools: Any, *, tool_choice: Any = None, **kwargs: Any) -> Any:
        del tools, tool_choice, kwargs
        return self


def _seed_review_state(project_id: str, user_text: str) -> dict[str, Any]:
    snapshot = _build_review_snapshot(project_id)
    return {
        "current_stage": "awaiting_user_confirmation",
        "latest_snapshot": snapshot,
        "ready_for_persist": True,
        "messages": [
            ToolMessage(
                name="record_usecase_review",
                tool_call_id="seed_review_snapshot",
                content=json.dumps(snapshot, ensure_ascii=False),
            ),
            HumanMessage(content=user_text),
        ],
    }


def _build_local_agent(responses: list[AIMessage], monkeypatch: Any) -> Any:
    workflow_graph = importlib.import_module(
        "graph_src_v2.services.usecase_workflow_agent.graph"
    )
    fake_model = ToolReadyFakeChatModel(responses=cast(Any, responses))

    monkeypatch.setattr(workflow_graph, "merge_trusted_auth_context", lambda config, ctx: ctx)
    monkeypatch.setattr(
        workflow_graph,
        "build_runtime_config",
        lambda config, ctx: SimpleNamespace(model_spec="fake-model", system_prompt=""),
    )
    monkeypatch.setattr(workflow_graph, "resolve_model", lambda spec: fake_model)
    monkeypatch.setattr(workflow_graph, "apply_model_runtime_params", lambda model, options: model)

    return asyncio.run(workflow_graph.make_graph({"configurable": {}}, object()))


def _build_resume_agent(
    *, responses: list[AIMessage], expected_feedback: str, monkeypatch: Any
) -> Any:
    fake_model = ToolReadyFakeChatModel(responses=cast(Any, responses))
    observed_feedback: list[str] = []

    @tool(
        "run_usecase_generation_subagent",
        description="Run the usecase-generation specialist using the current thread state.",
    )
    def run_usecase_generation_subagent(
        runtime: ToolRuntime[None, UsecaseWorkflowState],
    ) -> str:
        messages = runtime.state.get("messages", [])
        latest_feedback = ""
        for message in reversed(messages):
            if getattr(message, "type", None) != "tool":
                continue
            if getattr(message, "name", None) != "persist_approved_usecases":
                continue
            content = getattr(message, "content", None)
            if not isinstance(content, str):
                continue
            payload = json.loads(content)
            latest_feedback = str(payload.get("payload", {}).get("human_revision_feedback") or "")
            break
        observed_feedback.append(latest_feedback)
        return json.dumps(
            {
                "summary": "Regenerated candidate use cases with the requested revisions.",
                "usecases": [{"title": "admin login separated from member login"}],
            }
        )

    @tool(
        "run_usecase_review_subagent",
        description="Run the usecase-review specialist using the current thread state.",
    )
    def run_usecase_review_subagent(
        runtime: ToolRuntime[None, UsecaseWorkflowState],
    ) -> str:
        del runtime
        return json.dumps(
            {
                "summary": "Updated use cases address the requested revisions.",
                "candidate_usecases": [{"title": "admin login separated from member login"}],
                "deficiencies": [],
                "strengths": ["revisions incorporated"],
                "revision_suggestions": [],
            }
        )

    monkeypatch.setattr(workflow_tools.requests, "post", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("edit resume must not persist")))

    agent = create_agent(
        model=fake_model,
        name="usecase_workflow_agent",
        tools=[
            run_usecase_generation_subagent,
            workflow_tools.record_generated_usecases,
            run_usecase_review_subagent,
            workflow_tools.record_usecase_review,
            workflow_tools.persist_approved_usecases,
        ],
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "persist_approved_usecases": {
                        "allowed_decisions": ["approve", "edit", "reject"],
                        "description": "Persisting reviewed use cases requires explicit human confirmation.",
                    }
                },
                description_prefix="Use case persistence pending confirmation",
            ),
            WorkflowToolSelectionMiddleware(),
            MultimodalMiddleware(),
        ],
        system_prompt=SYSTEM_PROMPT,
        state_schema=UsecaseWorkflowState,
        checkpointer=MemorySaver(),
    )
    return agent, observed_feedback, expected_feedback


def test_local_invoke_without_confirmation_asks_for_confirmation(monkeypatch: Any) -> None:
    agent = _build_local_agent(
        responses=[
            AIMessage(
                content="I have the reviewed use cases ready, but I need your explicit confirmation before persisting them."
            )
        ],
        monkeypatch=monkeypatch,
    )
    project_id = str(uuid.uuid4())

    result = asyncio.run(
        agent.ainvoke(
            _seed_review_state(
                project_id,
                "The review looks good. What happens if I have not explicitly confirmed persistence yet?",
            )
        )
    )

    assert "__interrupt__" not in result
    assert result["messages"][-1].type == "ai"
    assert not result["messages"][-1].tool_calls
    assert "confirm" in result["messages"][-1].content.lower()


def test_local_invoke_with_confirmation_exposes_persist_interrupt(monkeypatch: Any) -> None:
    agent = _build_local_agent(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "persist_approved_usecases",
                        "args": {"approval_note": "Explicitly confirmed by the reviewer."},
                        "id": "call_persist_approved_usecases",
                        "type": "tool_call",
                    }
                ],
            )
        ],
        monkeypatch=monkeypatch,
    )
    project_id = str(uuid.uuid4())

    result = asyncio.run(
        agent.ainvoke(
            _seed_review_state(
                project_id,
                "I explicitly confirm persistence. Please save the approved use cases now.",
            )
        )
    )

    assert result["messages"][-1].type == "ai"
    assert any(
        tool_call["name"] == "persist_approved_usecases"
        for tool_call in result["messages"][-1].tool_calls
    )
    assert "__interrupt__" in result
    assert any(
        action_request["name"] == "persist_approved_usecases"
        for interrupt in result["__interrupt__"]
        for action_request in getattr(interrupt, "value", {}).get("action_requests", [])
    )


def test_local_resume_with_edit_feedback_returns_to_review_loop(monkeypatch: Any) -> None:
    feedback = "Please split admin and member scenarios before saving."
    agent, observed_feedback, expected_feedback = _build_resume_agent(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "persist_approved_usecases",
                        "args": {"approval_note": "Explicitly confirmed by the reviewer."},
                        "id": "call_persist_approved_usecases",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "run_usecase_generation_subagent",
                        "args": {},
                        "id": "call_run_usecase_generation_subagent",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "record_generated_usecases",
                        "args": {},
                        "id": "call_record_generated_usecases",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "run_usecase_review_subagent",
                        "args": {},
                        "id": "call_run_usecase_review_subagent",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "record_usecase_review",
                        "args": {},
                        "id": "call_record_usecase_review",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="Updated review completed. Please confirm again before persistence."
            ),
        ],
        expected_feedback=feedback,
        monkeypatch=monkeypatch,
    )
    project_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    initial_result = asyncio.run(
        agent.ainvoke(
            _seed_review_state(
                project_id,
                "I explicitly confirm persistence. Please save the approved use cases now.",
            ),
            config=config,
        )
    )

    assert "__interrupt__" in initial_result

    resume_result = asyncio.run(
        agent.ainvoke(
            Command(
                resume={
                    "decisions": [
                        {
                            "type": "edit",
                            "edited_action": {
                                "name": "persist_approved_usecases",
                                "args": {"revision_feedback": feedback},
                            },
                        }
                    ]
                }
            ),
            config=config,
        )
    )

    assert "__interrupt__" not in resume_result
    assert observed_feedback == [expected_feedback]
    assert resume_result["messages"][-1].type == "ai"
    assert "confirm again" in resume_result["messages"][-1].content.lower()
    generated_messages = [
        message
        for message in resume_result["messages"]
        if getattr(message, "type", None) == "tool"
        and getattr(message, "name", None) == "record_generated_usecases"
    ]
    assert generated_messages
    persist_messages = [
        message
        for message in resume_result["messages"]
        if getattr(message, "type", None) == "tool"
        and getattr(message, "name", None) == "persist_approved_usecases"
    ]
    assert persist_messages
    persist_payload = json.loads(persist_messages[-1].content)
    assert persist_payload["stage"] == "reviewed_candidate_usecases"
    assert persist_payload["payload"]["human_revision_feedback"] == feedback
