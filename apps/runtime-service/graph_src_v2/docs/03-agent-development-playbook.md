# graph_src_v2 智能体开发团队规范（Playbook）

本文是团队在 `graph_src_v2` 下开发智能体的统一实践，目标是：

- 代码简单可维护
- 运行时能力可配置
- 按业务场景选择合适模式

## 1. 总原则

- `config-first`：优先使用运行时配置驱动行为，不写死环境分支。
- `factory-by-exception`：只有确实需要工厂期上下文时才用复杂工厂逻辑。
- `dynamic + required tools`：平台工具动态加载，业务必备工具显式追加。
- 不强行统一一种框架：`create_agent` / `StateGraph` / `deepagent` 按场景选。

## 2. 模式选型规则

### 2.1 什么时候用 create_agent

适用：

- 单智能体为主
- 线性对话流程
- 无复杂路由/子图编排需求

推荐方式：

- 用工厂函数 `make_graph(...)` 返回 `create_agent(...)`
- 通过 `RunnableConfig` 解析模型与工具配置

### 2.2 什么时候用 StateGraph

适用：

- 多节点路由
- 子图组合
- 显式状态机与条件分支
- 需要更强可视化流程控制

### 2.3 什么时候用 deepagent

适用：

- 复杂多步任务
- 强任务分解/规划能力
- 工具链较长，执行路径不固定

## 3. 工厂函数规范

推荐签名：

```python
async def make_graph(config: RunnableConfig, runtime: ServerRuntime):
    ...
```

要求：

- 工厂函数负责装配，不做不必要重初始化。
- `RunnableConfig` 用于本次运行参数（模型、开关、工具等）。
- `ServerRuntime` 用于服务端上下文（user/store/access），按需使用。
- 若当前场景不需要 `user/store`，可暂不使用 runtime 里的用户逻辑。

## 4. 工具装配规范（重点）

统一采用“两段式装配”：

1) 动态平台工具（来自 `graph_src_v2/tools`）

```python
tools = await build_tools(options)
```

2) 本地必备工具（当前 agent 目录）

```python
tools.extend([...])
tools.append(...)
```

说明：

- 动态部分保证按配置启用/禁用能力。
- 本地必备部分保证关键业务能力稳定可用。
- 不再增加无意义中间封装层。

## 5. HITL（人机审核）规范

- 优先用官方 `HumanInTheLoopMiddleware`。
- 不重复封装自定义审批协议。
- 在 `langgraph dev`/托管持久化环境，不在图内手动注入本地 checkpointer。

## 6. assistant_entrypoint 样板说明

`graph_src_v2/agents/assistant_agent/graph_entrypoint.py` 作为当前推荐样板：

- 使用官方工厂函数签名
- 直接 `create_agent`（不额外包 `StateGraph`）
- 采用动态工具 + 本地必备工具装配
- 使用官方 HITL middleware

## 7. 开发流程（执行清单）

1. 明确业务场景，先做模式选型（create_agent / StateGraph / deepagent）
2. 落地工厂函数与运行时配置解析
3. 按“两段式装配”接入工具
4. 接入 HITL（若有高风险工具）
5. 验证：
   - 相关文件 `lsp_diagnostics` 无错误
   - `compileall` 通过
   - 最小冒烟测试通过

## 8. 禁止事项

- 为了“看起来统一”强行把所有 agent 套同一模式
- 为简单场景引入复杂图编排
- 在生产路径保留临时 demo 开关和无意义 wrapper
