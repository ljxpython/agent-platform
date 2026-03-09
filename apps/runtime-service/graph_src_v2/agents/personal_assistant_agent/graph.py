from __future__ import annotations

from typing import Any

from graph_src_v2.agents.personal_assistant_agent.tools import (
    build_personal_assistant_agent,
)
from graph_src_v2.runtime.modeling import apply_model_runtime_params, resolve_model
from graph_src_v2.runtime.options import (
    build_runtime_config,
    merge_trusted_auth_context,
)
from graph_src_v2.tools.registry import build_tools
from langchain_core.runnables import RunnableConfig
from langgraph_sdk.runtime import ServerRuntime


async def make_graph(config: RunnableConfig, runtime: ServerRuntime) -> Any:
    del runtime
    runtime_context = merge_trusted_auth_context(config, {})
    options = build_runtime_config(config, runtime_context)
    model = apply_model_runtime_params(resolve_model(options.model_spec), options)
    base_tools = await build_tools(options)
    return build_personal_assistant_agent(model, base_tools)


graph = make_graph
