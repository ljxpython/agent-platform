# LangGraph v2 (Pure Graph-Native) Architecture

## Scope

- This version is an independent execution layer under `graph_src_v2`.
- Goal: keep one simple mental model — compiled graph entries + `RuntimeContext`.

## Core Contract

- Graph entrypoints export compiled graphs (`graph`) in each agent module.
- Runtime parameters flow through `context` and are typed by `RuntimeContext`.
- `config` is reserved for execution controls (for example `recursion_limit`).

## Directory Notes

- `graph_src_v2/langgraph.json`: graph registry for deployment.
- `graph_src_v2/runtime/context.py`: shared `RuntimeContext` schema.
- `graph_src_v2/agents/assistant_agent/graph.py`: compiled assistant graph.
- `graph_src_v2/agents/deepagent_agent/graph.py`: compiled deepagent graph.
- `graph_src_v2/runtime/options.py`: context/config to runtime options resolver.
- `graph_src_v2/runtime/modeling.py`: model provider resolution + runtime params binding.
- `graph_src_v2/tools/registry.py`: builtin tools + MCP tool assembly.

## Runtime Strategy

1. Node reads `runtime.context` (`Runtime[RuntimeContext]`).
2. `build_runtime_config(config, context)` resolves effective runtime options.
3. Node builds model/tools for this run and invokes inner agent/deepagent.

## Multi-Graph Rule

- `assistant` and `deepagent_demo` follow the same contract.
- Dynamic model routing and MCP/tool switches are runtime-driven per run.
- `deepagent_demo` keeps static `skills/subagents` lists for simpler maintenance.

## Runbook

```bash
APP_ENV=test langgraph dev --config graph_src_v2/langgraph.json
```
