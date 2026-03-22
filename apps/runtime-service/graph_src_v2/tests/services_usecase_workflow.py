# pyright: reportMissingImports=false, reportMissingModuleSource=false
import asyncio
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from graph_src_v2.devtools.multimodal_frontend_compat import build_human_message_from_paths
from graph_src_v2.middlewares.multimodal import MultimodalMiddleware
from graph_src_v2.runtime.modeling import apply_model_runtime_params, resolve_model
from graph_src_v2.runtime.options import build_runtime_config, merge_trusted_auth_context
from graph_src_v2.services.usecase_workflow_agent.graph import (
    SYSTEM_PROMPT,
    UsecaseWorkflowState,
    WorkflowToolSelectionMiddleware,
    _bind_non_streaming_model,
)
from graph_src_v2.services.usecase_workflow_agent.tools import (
    build_usecase_workflow_service_config,
    build_usecase_workflow_tools,
)


def _load_first_pdf_message() -> Any:
    test_data_dir = Path(__file__).resolve().parents[1] / "test_data"

    try:
        pdf_path = next(test_data_dir.glob("*.pdf"))
    except StopIteration as exc:
        raise FileNotFoundError(f"No PDF found in {test_data_dir}") from exc

    return build_human_message_from_paths(
        "请分析这个 PDF 的需求内容，先告诉我你看到了什么，不要持久化。",
        [pdf_path],
    )


async def _build_local_agent(config: RunnableConfig) -> Any:
    runtime_context = merge_trusted_auth_context(config, {})
    options = build_runtime_config(config, runtime_context)
    build_usecase_workflow_service_config(config)
    model = apply_model_runtime_params(resolve_model(options.model_spec), options)
    model = _bind_non_streaming_model(model)
    tools = build_usecase_workflow_tools(model)
    system_prompt = options.system_prompt or SYSTEM_PROMPT

    # This debug REPL builds the agent locally with MemorySaver so Command(resume=...)
    # can continue the same thread after a local interrupt.
    return create_agent(
        model=model,
        name="usecase_workflow_agent",
        tools=tools,
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
        system_prompt=system_prompt,
        state_schema=UsecaseWorkflowState,
        checkpointer=MemorySaver(),
    )


def _chunk_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
                continue
            if not isinstance(item, dict):
                continue
            if item.get("type") == "text" and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    return ""


def _extract_interrupt(update: Any) -> Any | None:
    if isinstance(update, dict) and "__interrupt__" in update:
        return update["__interrupt__"]
    return None


async def _stream_turn(agent: Any, payload: Any, config: RunnableConfig) -> bool:
    saw_stream_text = False

    async for mode, event in agent.astream(
        payload,
        config=config,
        stream_mode=["messages", "updates"],
    ):
        if mode == "messages":
            message, _metadata = event
            text = _chunk_text(getattr(message, "content", ""))
            if text:
                if not saw_stream_text:
                    print("stream", end=" ", flush=True)
                    saw_stream_text = True
                print(text, end="", flush=True)
            continue

        if saw_stream_text:
            print()
            saw_stream_text = False

        print("update", event)
        if _extract_interrupt(event) is not None:
            print("interrupt", _extract_interrupt(event))
            return True

    if saw_stream_text:
        print()

    return False


def _build_interrupt_resume_payload(decision: str, feedback: str = "") -> dict[str, Any]:
    if decision == "edit":
        feedback_text = feedback.strip()
        if not feedback_text:
            raise ValueError("edit feedback is required")
        return {
            "decisions": [
                {
                    "type": "edit",
                    "edited_action": {
                        "name": "persist_approved_usecases",
                        "args": {"revision_feedback": feedback_text},
                    },
                }
            ]
        }
    return {"decisions": [{"type": decision}]}


def _prompt_interrupt_decision() -> tuple[str, str]:
    while True:
        decision = input("you ").strip().lower()
        if decision in {"approve", "reject", "quit"}:
            return decision, ""
        if decision == "edit":
            feedback = input("edit feedback ").strip()
            if feedback:
                return decision, feedback
            print("edit feedback required")
            continue
        print("interrupt approve | edit | reject | quit")


async def _run_repl() -> None:
    thread_id = str(uuid4())
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    agent = await _build_local_agent(config)

    first_message = _load_first_pdf_message()
    interrupted = await _stream_turn(agent, {"messages": [first_message]}, config)

    while True:
        if interrupted:
            decision, feedback = _prompt_interrupt_decision()
            if decision == "quit":
                return
            interrupted = await _stream_turn(
                agent,
                Command(resume=_build_interrupt_resume_payload(decision, feedback)),
                config,
            )
            continue

        user_text = input("you ").strip()
        if not user_text:
            continue
        if user_text.lower() == "quit":
            return

        interrupted = await _stream_turn(agent, {"messages": [user_text]}, config)


def graph_local() -> None:
    asyncio.run(_run_repl())


if __name__ == "__main__":
    graph_local()
