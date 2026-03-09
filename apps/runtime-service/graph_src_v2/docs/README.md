# graph_src_v2 新手开发与使用指南

`graph_src_v2` 是纯执行层：负责 LangGraph 图运行、运行时参数解析、工具/MCP 装配与鉴权。

## 1) 先理解这套最小心智模型

- 图入口：`assistant`、`assistant_entrypoint`、`deepagent_demo`、`graph_patterns_memory_demo`、`personal_assistant_demo`、`customer_support_handoffs_demo`、`skills_sql_assistant_demo`
- 运行时配置：`runtime/options.py`（模型、工具、MCP 开关与参数）
- 模型装配：`runtime/modeling.py`
- 工具装配：`tools/registry.py`
- MCP 清单：`mcp/servers.py`
- 自定义路由：`custom_routes/app.py` + `custom_routes/tools.py` + `custom_routes/models.py`
- 鉴权：`auth/provider.py`（`custom_auth` + `oauth_auth`）

## 2) 本地启动（推荐）

在项目根目录执行：

```bash
uv run langgraph dev --config graph_src_v2/langgraph.json --port 8123 --no-browser
```

默认行为：

- `langgraph.json` 本地模式不启用 auth
- 默认不启用公共工具池（`enable_tools=false`）
- 开启后可通过 `tools` 选择一个、多个或全部工具（本地工具 + MCP server 能力）

### 2.0 查看 graph 详细说明（来自 `langgraph.json` 的 `graphs[*].description`）

服务启动后可直接查询：

```bash
curl -sS -X POST http://127.0.0.1:8123/assistants/search -H "Content-Type: application/json" -d '{}'
```

返回中每个 assistant 都包含 `description` 字段；该字段来源于 `langgraph.json` 中对应 graph 的 `description`。

补充阅读：

- `02-runnableconfig-vs-serverruntime.md`：`RunnableConfig` 与 `ServerRuntime` 的详细对比、选型与实践建议。
- `03-agent-development-playbook.md`：团队智能体开发规范（模式选型、工具装配、工厂函数、HITL、验证流程）。
- `04-agent-scaffold-templates.md`：可复制脚手架模板（create_agent / StateGraph / deepagent）。
- `05-template-to-runnable-agent-10min.md`：从模板到可运行 agent 的 10 分钟实操示例（含注册与最小测试）。
- `06-multimodal-middleware-design.md`：多模态中间件设计草案（为什么放中间层、为什么增强不覆盖、image/pdf/doc 的分流原则、state/context/message/metadata 的职责边界）。

### 2.1 personal_assistant_demo 是什么

- 迁移自 LangChain 官方 `subagents-personal-assistant` 示例
- 三层结构：低层日历/邮件工具 → calendar/email 子 agent → supervisor agent
- 设计原则：最小可运行、薄封装、无额外注册层

### 2.2 customer_support_handoffs_demo 是什么

- 迁移自 LangChain 官方 `handoffs-customer-support` 示例
- 核心机制：单 agent + 状态机 step 切换（`warranty_collector` → `issue_classifier` → `resolution_specialist`）
- 通过 tool 返回 `Command(update=...)` 更新工作流状态，不做过度封装

### 2.3 skills_sql_assistant_demo 是什么

- 迁移自 LangChain 官方 `skills-sql-assistant` 示例
- 工厂期按 `configurable.model_id` 选择模型；运行期按 `configurable.enable_tools/tools` 通过 `build_tools(options)` 装配平台工具池
- 核心机制：通过 middleware 暴露 skills 摘要，按需用 `load_skill` 加载详细 schema/业务规则
- 目标：减少上下文冗余（progressive disclosure），保持单 agent 对话体验

### 2.4 deepagent_demo（已并入数据分析能力）

- 统一保留 `deepagent_demo`，移除单独的 `deepagents_data_analysis_demo` 教学变体
- 既支持通用 deep task 分解，也支持本地 CSV 分析、脚本化处理、可视化产物输出
- 默认不使用 Slack 或任何聊天投递集成，仅回报本地产物路径

### 2.5 assistant（LangChain 概念教学模式）

- 在原有 assistant 基础上默认开启 LangChain 概念教学能力（无需额外开关）
- 覆盖三类核心知识点：`tools 调用`、`人机交互（interrupt 审批）`、`多智能体（tool-wrapped subagents）`
- 开启后会注入 `ask_knowledge_specialist` / `ask_ops_specialist` / `ask_email_specialist` / `request_human_approval` 四类演示工具

### 2.6 assistant 前端验证场景（默认可用）

以下场景直接在前端对 `assistant` 发送消息即可，不需要额外配置：

说明：`assistant` 现在按官方 `human-in-the-loop` 文档接入 `HumanInTheLoopMiddleware`，
会在命中 `request_human_approval` / `send_demo_email` 时产生标准 interrupt（approve/edit/reject），
不再使用工具内“自动审批”逻辑。

1. 多智能体（subagents）
   - 示例输入：`请调用 ask_knowledge_specialist 和 ask_ops_specialist，给我“上线 feature flag 审批流”的实现建议和发布计划。`
   - 预期：会触发 `ask_knowledge_specialist` 与 `ask_ops_specialist` 两类工具调用。

2. 人机交互（HITL 审批）
   - 示例输入：`我要直接全量发布到生产。你必须先调用 request_human_approval，未批准前不要继续执行。`
   - 预期：运行进入 interrupt，前端可进行 approve/edit/reject 决策。

3. 全链路（tools + 多智能体 + HITL）
   - 示例输入：`先让知识专家给方案，再让运维专家给发布计划，然后发变更通知邮件；发邮件前必须走 request_human_approval。`
   - 预期：依次触发专家工具、审批中断，审批后继续并生成邮件结果。

4. 拒绝分支（HITL 负路径）
   - 示例输入：`准备向全员发送“今晚停机”的邮件，先申请人工审批。`
   - 预期：若前端选择 reject，最终回复会明确动作被拒绝，并停止后续高风险操作。

### 2.7 graph_patterns_memory_demo（综合 Graph 开发样例）

- 目标：一个 demo 同时覆盖 `tools`、`人机审批 HITL`、`多智能体`、`子图`、`长期记忆`
- 子图：父图中通过 `add_node("run_specialists_subgraph", specialist_subgraph)` 挂载已编译子图
- 长期记忆：使用平台托管 store（LangGraph API persistence），在运行节点中通过 `runtime.store.asearch/aput` 读写用户记忆
- 多智能体：supervisor 通过 `ask_knowledge_specialist` / `ask_ops_specialist` 工具代理子 agent
- HITL：按官方 `langgraph/interrupts` 模式在父图节点直接调用 `interrupt(...)`，前端可直接收到评审中断（approve/edit/reject）

### 2.8 graph_patterns_memory_demo 前端触发语句（可直接复制）

以下语句可直接在前端对 `graph_patterns_memory_demo` 发送：

1. 多智能体 + tools
   - `请调用 ask_knowledge_specialist 和 ask_ops_specialist，给我“用户通知系统上线”的实现建议和发布计划。`

2. HITL 审批中断
   - `请先调用 request_human_approval 再执行任何上线动作，动作是“生产环境灰度发布10%”。`

3. HITL + 发邮件（双审批点）
   - `请先走 request_human_approval，然后调用 send_demo_email 给 ops@example.com 发送上线通知。`

4. 子图路径（专家协作）
   - `请走专家协作流程：先让知识专家分析风险，再让运维专家给出回滚方案。`

5. 长期记忆写入
   - `记住: 我偏好先灰度5%，观察10分钟再继续放量。`

6. 长期记忆读取（下一轮再发）
   - `结合你记住的我的发布偏好，给我一个今晚的上线执行方案。`

前端审批（interrupt）恢复时可提交：

- approve: `{ "decisions": [{"type":"approve"}] }`
- edit: `{ "decisions": [{"type":"edit","edited_action":{"name":"send_demo_email","args":{"to":["ops@example.com"],"subject":"变更通知-灰度5%","body":"先灰度5%，10分钟观察后再放量"}}}] }`
- reject: `{ "decisions": [{"type":"reject","message":"今晚冻结发布，请改为明早执行"}] }`

### 2.9 HITL 选型说明（create_agent vs StateGraph）

- `create_agent`（LangChain agent 直跑场景）推荐 `HumanInTheLoopMiddleware`：
  - 由 middleware 自动拦截工具调用并产出标准 HITL interrupt。
  - 适合单 agent 或“外层不是自定义 StateGraph 节点编排”的场景。
- `StateGraph`（父图编排 + 子图组合场景）推荐在父图节点直接 `interrupt(...)`：
  - 中断在主图层产生，前端更容易稳定接收与恢复。
  - 适合你现在 `graph_patterns_memory_demo` 这种“父图 + 子图 + 记忆 + 路由”组合流程。
  - 为兼容当前前端渲染，`action_requests` 同时提供 `args`（前端读取）与 `arguments`（官方文档命名）。
- 中断恢复依赖平台持久化 + 同一 `thread_id`（LangGraph API 会自动提供 checkpointer）。

## 3) 最快可用验证路径

### 3.1 直接跑测试

```bash
uv run pytest graph_src_v2/tests/test_auth_core.py graph_src_v2/tests/test_custom_routes.py graph_src_v2/tests/test_model_smoke.py -q
```

### 3.2 HTTP 手工验证（不依赖外部目录）

```bash
curl -sS http://127.0.0.1:8123/internal/capabilities/tools
curl -sS http://127.0.0.1:8123/internal/capabilities/models
```

## 4) 运行时参数怎么传（最常用）

你通常通过 `context` / `configurable` 传：

- `model_id`
- `enable_tools`
- `tools`（例如 `word_count,to_upper,mcp:local_text`）
- 可选模型参数：`temperature`、`max_tokens`、`top_p`

说明：`model_provider/model/base_url/api_key` 不需要用户传，统一由 `conf/settings.yaml` 的模型组映射。

## 5) 自定义路由（给其他服务查询能力）

已暴露在同一服务下：

- `GET /internal/capabilities/tools`
- `GET /internal/capabilities/models`

用途：让外部服务查询当前“可用能力”清单与“可选模型目录（前端展示名）”。

## 6) deepagent 的约定（已简化）

`deepagent_demo` 现在走官方风格薄封装：

- 直接 `create_deep_agent(...)`
- `skills` 来自 `list_deepagent_skills()`
- `subagents` 来自 `list_subagents()`
- 不再使用复杂的 runtime 动态 subagent 解析链

## 7) 推荐开发流程（团队统一）

1. 改代码前先确认目录职责，不跨层引用
2. 改完先跑：
   - `uv run pytest graph_src_v2/tests/test_auth_core.py graph_src_v2/tests/test_custom_routes.py graph_src_v2/tests/test_model_smoke.py -q`
   - `uv run python -m compileall graph_src_v2`
3. 若改了运行时行为，更新本 README 与 `01-auth-and-sdk-validation.md`

## 8) 常见问题

- 为什么工具没生效？
  - 默认关闭，需显式设置 `enable_tools=true`。
- 为什么 MCP 工具没生效？
  - 需要在 `tools` 中包含对应 MCP server（例如 `mcp:local_text`），或在 `enable_tools=true` 且不传 `tools` 时使用全量工具池。
- 为什么只传了 `model_id` 就能跑？
  - 因为模型四元组由 `settings.yaml` 统一映射。
- 为什么 `request_human_approval` 看起来自动通过，或没有中断？
  - 根因：工具内自处理审批逻辑不稳定，容易在不同运行路径下表现为“自动审批/无 interrupt”。
  - 已修复：`assistant` 改为官方 `HumanInTheLoopMiddleware` 模式，审批中断由 middleware 统一触发。
  - 当前策略：命中 `request_human_approval` / `send_demo_email` 时触发标准 HITL interrupt，支持 `approve/edit/reject`。
  - 使用要点：前端在同一线程上下文中恢复执行（保持同一个会话线程），按中断返回结构提交 decision。

- 为什么 `graph_patterns_memory_demo` 启动时报 custom store/checkpointer 错误？
  - 根因：LangGraph API 环境由平台托管 persistence，不允许图内显式注入自定义 `store` 或 `checkpointer`。
  - 处理：移除图内 `compile(..., store=...)` / `compile(..., checkpointer=...)`，使用平台默认持久化。

- 为什么命中审批后前端有时“没下文”？
  - 根因：`interrupt(...)` 在节点中断点暂停，恢复前不一定产生新的 AI 文本；如果前端未正确渲染 `__interrupt__` 卡片，就会像“没回复”。
  - 处理：
    - 后端 payload 兼容前端：`action_requests` 同时包含 `args` 与 `arguments`；
    - 前端优先按 `__interrupt__` 渲染审批卡片，而非依赖中断前 assistant 文本。

- 为什么 `记住: 我偏好先灰度5%...` 之前会卡住？
  - 根因：句子包含“灰度/上线”等词，被误判为审批请求。
  - 处理：记忆写入句式优先级更高，命中 `记住:` / `remember:` 时直接写长期记忆并返回确认，不走审批。

- 为什么 `再次发一封邮件` 之前容易没有后续？
  - 根因：这是“邮件意图但信息可能不足”的典型输入。
  - 处理：
    - 能从历史工具结果提取收件人则复用并进入审批；
    - 不能提取则明确追问补充收件人，避免静默。

- 为什么看起来“没有点审批也发了邮件”？
  - 根因：早期逻辑是 fail-open（无效/缺失决策可能被当成默认通过），且子图曾暴露 `send_demo_email`。
  - 处理：
    - 决策解析改为 fail-closed：仅 `approve/edit/reject` 有效；
    - `edit` 必须包含合法 `edited_action`；
    - 子图不再暴露 `send_demo_email`，邮件发送只能经过父图审批门。
