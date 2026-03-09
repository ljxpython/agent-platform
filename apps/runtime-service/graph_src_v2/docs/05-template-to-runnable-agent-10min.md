# 从模板到可运行 Agent（10 分钟实操）

目标：基于 `create_agent` 模板，10 分钟内新增一个可运行的 `hello_demo`。

## 1) 新建目录与文件

目录：

```text
graph_src_v2/agents/hello_demo_agent/
  __init__.py
  graph.py
  tools.py
```

`__init__.py`：

```python
from graph_src_v2.agents.hello_demo_agent.graph import graph
```

`tools.py`：

```python
from langchain_core.tools import tool


@tool("hello_tool", description="Return a short hello message.")
def hello_tool(name: str = "world") -> str:
    return f"hello, {name}"
```

`graph.py`：

```python
from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langgraph_sdk.runtime import ServerRuntime

from graph_src_v2.agents.hello_demo_agent.tools import hello_tool
from graph_src_v2.runtime.modeling import apply_model_runtime_params, resolve_model
from graph_src_v2.runtime.options import build_runtime_config, merge_trusted_auth_context
from graph_src_v2.tools.registry import build_tools


async def make_graph(config: RunnableConfig, runtime: ServerRuntime) -> Any:
    del runtime
    runtime_context = merge_trusted_auth_context(config, {})
    options = build_runtime_config(config, runtime_context)
    model = apply_model_runtime_params(resolve_model(options.model_spec), options)

    tools = await build_tools(options)
    tools.append(hello_tool)

    return create_agent(
        model=model,
        tools=tools,
        system_prompt=options.system_prompt,
        name="hello_demo",
    )


graph = make_graph
```

## 2) 注册到 langgraph.json

在 `graph_src_v2/langgraph.json` 的 `graphs` 中新增：

```json
"hello_demo": {
  "path": "./graph_src_v2/agents/hello_demo_agent/graph.py:graph",
  "description": "hello_demo 的用途说明，便于在 assistants/search 中直接查看"
}
```

## 3) 最小测试文件

新增 `graph_src_v2/tests/test_hello_demo_registration.py`：

```python
from __future__ import annotations

import json
from pathlib import Path


def test_hello_demo_registered() -> None:
    project_root = Path(__file__).resolve().parents[2]
    langgraph_file = project_root / "graph_src_v2" / "langgraph.json"
    data = json.loads(langgraph_file.read_text(encoding="utf-8"))
    assert "hello_demo" in data["graphs"]
```

## 4) 运行验证命令

在仓库根目录运行：

```bash
uv run python -m compileall graph_src_v2/agents/hello_demo_agent/graph.py
uv run pytest graph_src_v2/tests/test_hello_demo_registration.py -q
uv run langgraph dev --config graph_src_v2/langgraph.json --port 8123 --no-browser
```

## 5) 前端/接口快速验证

向 `hello_demo` 发送：

- `请调用 hello_tool，name=team`

期望：能触发工具调用并返回 `hello, team`。

## 6) 进阶（可选）

- 需要人工审批：在 `create_agent(...)` 增加 `HumanInTheLoopMiddleware`。
- 需要复杂编排：迁移到 `StateGraph` 模板。
- 需要强任务分解：迁移到 `deepagent` 模板。
