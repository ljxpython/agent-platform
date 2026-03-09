# graph_src_v2 智能体脚手架模板（可直接复制）

本文提供三种最常用模板：

- 模板 A：`create_agent`（单智能体，推荐默认）
- 模板 B：`StateGraph`（多节点编排）
- 模板 C：`deepagent`（复杂任务分解）

## 0. 新增 agent 的最小目录

```text
graph_src_v2/agents/<your_agent>/
  __init__.py
  graph.py
  tools.py
  prompts.py
```

`__init__.py` 最小内容：

```python
from graph_src_v2.agents.<your_agent>.graph import graph
```

## 1) 模板 A：create_agent（推荐默认）

适合：单智能体、线性流程、快速上线。

```python
from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langgraph_sdk.runtime import ServerRuntime

from graph_src_v2.runtime.modeling import apply_model_runtime_params, resolve_model
from graph_src_v2.runtime.options import build_runtime_config, merge_trusted_auth_context
from graph_src_v2.tools.registry import build_tools


async def make_graph(config: RunnableConfig, runtime: ServerRuntime) -> Any:
    del runtime
    runtime_context = merge_trusted_auth_context(config, {})
    options = build_runtime_config(config, runtime_context)

    model = apply_model_runtime_params(resolve_model(options.model_spec), options)

    # 动态工具（平台）
    tools = await build_tools(options)
    # 本地必备工具（按需追加）
    # tools.extend([tool_a, tool_b])

    return create_agent(
        model=model,
        tools=tools,
        system_prompt=options.system_prompt,
        name="<your_agent_name>",
    )


graph = make_graph
```

## 2) 模板 B：StateGraph（多节点编排）

适合：路由、子图、显式状态机。

```python
from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from langgraph.config import get_config
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.runtime import Runtime

from graph_src_v2.runtime.context import RuntimeContext
from graph_src_v2.runtime.options import build_runtime_config, context_to_mapping, merge_trusted_auth_context


async def run_main(state: MessagesState, *, runtime: Runtime[RuntimeContext]) -> MessagesState:
    config: RunnableConfig = get_config()
    runtime_context = merge_trusted_auth_context(config, context_to_mapping(runtime.context))
    options = build_runtime_config(config, runtime_context)
    del options
    return {"messages": state.get("messages", [])}


_builder = StateGraph(MessagesState, context_schema=RuntimeContext)
_builder.add_node("run_main", run_main)
_builder.add_edge(START, "run_main")
_builder.add_edge("run_main", END)

graph = _builder.compile(name="<your_graph_id>")
```

## 3) 模板 C：deepagent（复杂多步任务）

适合：任务分解、多工具链、长流程探索。

```python
from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from langgraph.config import get_config
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.runtime import Runtime

from deepagents import create_deep_agent

from graph_src_v2.runtime.context import RuntimeContext
from graph_src_v2.runtime.modeling import apply_model_runtime_params, resolve_model
from graph_src_v2.runtime.options import build_runtime_config, context_to_mapping, merge_trusted_auth_context
from graph_src_v2.tools.registry import build_tools


async def run_deep(state: MessagesState, *, runtime: Runtime[RuntimeContext]) -> MessagesState:
    config: RunnableConfig = get_config()
    runtime_context = merge_trusted_auth_context(config, context_to_mapping(runtime.context))
    options = build_runtime_config(config, runtime_context)

    tools = await build_tools(options)
    model = apply_model_runtime_params(resolve_model(options.model_spec), options)

    agent = create_deep_agent(
        name="<your_deepagent_name>",
        model=model,
        tools=tools,
        system_prompt=options.system_prompt,
    )
    result = await agent.ainvoke({"messages": state.get("messages", [])})
    return {"messages": result.get("messages", [])}


_builder = StateGraph(MessagesState, context_schema=RuntimeContext)
_builder.add_node("run_deep", run_deep)
_builder.add_edge(START, "run_deep")
_builder.add_edge("run_deep", END)

graph = _builder.compile(name="<your_graph_id>")
```

## 4) 新 agent 落地清单

1. 在 `graph_src_v2/langgraph.json` 注册 graph id
2. 优先接入动态工具：`build_tools(options)`
3. 本地必备工具用 `tools.extend(...)` / `tools.append(...)`
4. 需要人工审核时，优先 `HumanInTheLoopMiddleware`
5. 验证：
   - `lsp_diagnostics` 无错误
   - `uv run python -m compileall <changed_files>`
   - 最小冒烟测试通过
