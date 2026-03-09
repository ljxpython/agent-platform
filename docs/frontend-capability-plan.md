# 前端能力对照与接入规划

本文档记录当前前端能力现状，以及后续接入更多 LangGraph 前端能力时的统一参考。相关能力未来会同时评估并逐步适配到 `platform-web` 与 `runtime-web`。

## 本地项目能力对照与接入规划

这一节用于记录当前 `agent-chat-ui` 在本仓库中的实际能力，以及未来参考
`langgraphjs/examples/ui-react` 接入更多 LangGraph 前端能力时的参考路径。

### 当前能力现状表（ASCII Matrix）

```text
+----------------------+----------+--------------------------------------+----------------------+
| 能力                 | 当前状态 | LangGraphJS example                  | 优先级               |
+----------------------+----------+--------------------------------------+----------------------+
| Tool Calls           | 已具备   | tool-calling-agent                   | 已有                 |
| Interrupt / HITL     | 已具备   | human-in-the-loop                    | 已有                 |
| Branch / Regenerate  | 已具备   | branching-chat                       | 已有                 |
| Artifact / UI 基础   | 已具备   | generative-ui related patterns       | 已有                 |
| Summary Messages     | 未实现   | summarization-agent                  | 第二优先级           |
| Reasoning Blocks     | 未实现   | reasoning-agent                      | 第二优先级           |
| Tool Progress        | 未实现   | tool-streaming                       | 第一优先级           |
| Reconnect Banner     | 未实现   | session-persistence                  | 第一优先级           |
| Custom Event Cards   | 未实现   | custom-streaming                     | 第四优先级           |
| Parallel Research    | 未实现   | parallel-research                    | 第四优先级           |
| Subagent Pipeline    | 未实现   | deepagent                            | 第三优先级           |
| Subagent + Tools     | 未实现   | deepagent-tools                      | 第三优先级           |
+----------------------+----------+--------------------------------------+----------------------+
```

### Example 参考表（ASCII Matrix）

```text
+----------------------+----------------------------------+----------------------+
| example              | 主要展示能力                     | 建议接入优先级       |
+----------------------+----------------------------------+----------------------+
| tool-calling-agent   | 基础 useStream + tool calls      | 已有                 |
| human-in-the-loop    | interrupt / approve / reject     | 已有                 |
| branching-chat       | branch / checkpoint / regenerate | 已有                 |
| session-persistence  | reconnectOnMount / thread 恢复   | 第一优先级           |
| tool-streaming       | tool progress                    | 第一优先级           |
| summarization-agent  | summary message                  | 第二优先级           |
| reasoning-agent      | reasoning blocks                 | 第二优先级           |
| deepagent            | subagent pipeline                | 第三优先级           |
| deepagent-tools      | subagent + tool calls            | 第三优先级           |
| parallel-research    | 多研究节点结果面板              | 第四优先级           |
| custom-streaming     | custom events cards              | 第四优先级           |
+----------------------+----------------------------------+----------------------+
```

### 当前项目已具备的能力

- **工具调用 Tool Calls**
  - 当前状态：已具备
  - 本地实现参考：`src/components/thread/messages/ai.tsx`
  - 说明：已支持渲染 tool calls 与 tool results。

- **人工审批 Interrupt / HITL**
  - 当前状态：已具备
  - 本地实现参考：`src/components/thread/agent-inbox/index.tsx`
  - 本地实现参考：`src/components/thread/agent-inbox/hooks/use-interrupted-actions.tsx`
  - 说明：已支持 interrupt 渲染、approve / edit / reject 提交。

- **分支切换 / Regenerate / 历史**
  - 当前状态：已具备
  - 本地实现参考：`src/components/thread/messages/ai.tsx`
  - 本地实现参考：`src/components/thread/messages/human.tsx`
  - 说明：已支持 branch 切换、编辑旧消息、regenerate。

- **Artifact / Generative UI 基础能力**
  - 当前状态：已具备
  - 本地实现参考：`src/components/thread/artifact.tsx`
  - 本地实现参考：`src/providers/Stream.tsx`
  - 说明：已支持 `uiMessageReducer` 路径和 artifact 面板渲染。

### 当前项目尚未具备的能力

- **摘要消息 Summary Messages**
  - 当前状态：未实现
  - 需要接入：摘要消息检测与专门 UI 卡片

- **推理区块 Reasoning Blocks**
  - 当前状态：未实现
  - 需要接入：reasoning content block 的识别与折叠展示

- **工具进度 Tool Progress**
  - 当前状态：未实现
  - 需要接入：工具执行中的流式进度卡片

- **自定义事件卡片 Custom Event Cards**
  - 当前状态：未实现
  - 需要接入：`progress` / `status` / `file-status` 自定义事件渲染

- **重连横幅 Reconnect Banner**
  - 当前状态：未实现
  - 需要接入：线程刷新后的恢复状态 UI

- **并行研究面板 Parallel Research Panel**
  - 当前状态：未实现
  - 需要接入：多研究节点的专门结果面板

- **子代理流水线 Subagent Pipeline**
  - 当前状态：未实现
  - 需要接入：deepagent / subagent 结果流式展示

- **带工具的子代理视图 Deep Agent with Tools**
  - 当前状态：未实现
  - 需要接入：subagent + tool call 联合展示

### LangGraphJS examples 能力矩阵

- **`tool-calling-agent`**
  - 展示能力：基础 `useStream` + tool calls
  - 前端参考：[tool-calling-agent/index.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/tool-calling-agent/index.tsx)
  - 后端参考：[tool-calling-agent/agent.ts](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/tool-calling-agent/agent.ts)

- **`human-in-the-loop`**
  - 展示能力：interrupt / approve / reject / edit / resume
  - 前端参考：[human-in-the-loop/index.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/human-in-the-loop/index.tsx)
  - 组件参考：[PendingApprovalCard.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/human-in-the-loop/components/PendingApprovalCard.tsx)
  - 后端参考：[human-in-the-loop/agent.ts](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/human-in-the-loop/agent.ts)

- **`summarization-agent`**
  - 展示能力：摘要中间件 / summary message
  - 前端参考：[summarization-agent/index.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/summarization-agent/index.tsx)
  - 后端参考：[summarization-agent/agent.ts](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/summarization-agent/agent.ts)

- **`reasoning-agent`**
  - 展示能力：推理内容单独流式展示
  - 前端参考：[reasoning-agent/index.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/reasoning-agent/index.tsx)
  - 后端参考：[reasoning-agent/agent.ts](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/reasoning-agent/agent.ts)

- **`tool-streaming`**
  - 展示能力：工具执行进度流
  - 前端参考：[tool-streaming/index.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/tool-streaming/index.tsx)
  - 组件参考：[ToolProgressCard.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/tool-streaming/components/ToolProgressCard.tsx)
  - 后端参考：[tool-streaming/agent.ts](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/tool-streaming/agent.ts)

- **`custom-streaming`**
  - 展示能力：`progress` / `status` / `file-status` 自定义事件
  - 前端参考：[custom-streaming/index.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/custom-streaming/index.tsx)
  - 组件参考：[ProgressCard.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/custom-streaming/components/ProgressCard.tsx)
  - 组件参考：[StatusBadge.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/custom-streaming/components/StatusBadge.tsx)
  - 组件参考：[FileOperationCard.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/custom-streaming/components/FileOperationCard.tsx)
  - 类型参考：[custom-streaming/types.ts](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/custom-streaming/types.ts)
  - 后端参考：[custom-streaming/agent.ts](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/custom-streaming/agent.ts)

- **`branching-chat`**
  - 展示能力：branch / checkpoint / regenerate / 编辑旧消息
  - 前端参考：[branching-chat/index.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/branching-chat/index.tsx)
  - 组件参考：[BranchSwitcher.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/branching-chat/components/BranchSwitcher.tsx)
  - 后端参考：[branching-chat/agent.ts](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/branching-chat/agent.ts)

- **`session-persistence`**
  - 展示能力：刷新后恢复流、thread 持久化、`reconnectOnMount`
  - 前端参考：[session-persistence/index.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/session-persistence/index.tsx)
  - 后端参考：[session-persistence/agent.ts](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/session-persistence/agent.ts)

- **`parallel-research`**
  - 展示能力：并行研究节点结果面板
  - 前端参考：[parallel-research/index.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/parallel-research/index.tsx)
  - 组件参考：[ResearchCard.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/parallel-research/components/ResearchCard.tsx)
  - 组件参考：[SelectedResearchDisplay.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/parallel-research/components/SelectedResearchDisplay.tsx)
  - 组件参考：[TopicBar.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/parallel-research/components/TopicBar.tsx)
  - 类型参考：[parallel-research/types.ts](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/parallel-research/types.ts)
  - 后端参考：[parallel-research/agent.ts](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/parallel-research/agent.ts)

- **`deepagent`**
  - 展示能力：subagent pipeline、`filterSubagentMessages`、`streamSubgraphs`
  - 前端参考：[deepagent/index.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/deepagent/index.tsx)
  - 组件参考：[SubagentPipeline.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/deepagent/components/SubagentPipeline.tsx)
  - 组件参考：[SubagentCard.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/deepagent/components/SubagentCard.tsx)
  - 后端参考：[deepagent/agent.ts](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/deepagent/agent.ts)
  - 工具参考：[deepagent/tools.ts](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/deepagent/tools.ts)

- **`deepagent-tools`**
  - 展示能力：subagent + tool calls 联合展示
  - 前端参考：[deepagent-tools/index.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/deepagent-tools/index.tsx)
  - 组件参考：[SubagentPipeline.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/deepagent-tools/components/SubagentPipeline.tsx)
  - 组件参考：[SubagentToolCallCard.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/deepagent-tools/components/SubagentToolCallCard.tsx)
  - 组件参考：[SubagentStreamCard.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/deepagent-tools/components/SubagentStreamCard.tsx)
  - 类型参考：[deepagent-tools/types.ts](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/deepagent-tools/types.ts)
  - 后端参考：[deepagent-tools/agent.ts](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/deepagent-tools/agent.ts)

### 建议接入优先级

- **第一优先级**
  - `session-persistence`
  - `tool-streaming`

- **第二优先级**
  - `summarization-agent`
  - `reasoning-agent`

- **第三优先级**
  - `deepagent`
  - `deepagent-tools`

- **第四优先级**
  - `parallel-research`
  - `custom-streaming`

### 共享入口与总参考

- 示例总入口：[examples/ui-react/src/components/Layout.tsx](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/components/Layout.tsx)
- 示例注册表：[examples/ui-react/src/examples/registry.ts](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/src/examples/registry.ts)
- graph 映射：[examples/ui-react/langgraph.json](https://github.com/langchain-ai/langgraphjs/tree/main/examples/ui-react/langgraph.json)

### 验收时的认知边界

- `graph_src_v2` 当前更适合验证：
  - Tool Calls
  - Interrupt / HITL
  - Branch / Regenerate
  - Thread / Reconnect 基础能力
  - Deepagent / Subagent 基础能力

- `graph_src_v2` 当前还不足以完整验证：
  - Summary Messages
  - Reasoning Blocks
  - Tool Progress
  - Custom Event Cards
  - Parallel Research Panel

- 如果后续要完整验证这些专项前端能力，建议在 `graph_src_v2` 里补充：
  - `summarization_demo`
  - `reasoning_demo`
  - `parallel_research_demo`
  - `custom_streaming_demo`
