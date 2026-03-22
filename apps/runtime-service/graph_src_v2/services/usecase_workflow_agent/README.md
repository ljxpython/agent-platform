# usecase_workflow_agent 当前实现与重构目标

本文同时记录两件事：

- 当前代码已经真实实现了什么
- 下一轮准备按什么目标重构

这样做的原因很简单：当前仓库里的 `usecase_workflow_agent` 已经能跑，但新的目标架构和现在的实现并不完全一致。文档必须先把“现状”和“目标”分开，后续代码优化才不会跑偏。

## 1. 这个 agent 当前解决什么问题

当前样板负责一条后端业务链路：

1. 接收文本需求或附件（重点支持 PDF）
2. 理解需求内容
3. 产出候选用例并做评审
4. 接受人工修改意见
5. 在人工明确确认后执行最终持久化

它的价值不只是生成用例，更重要的是沉淀 `runtime-service` 里“业务工作流 agent 应该怎样组织”的做法。

## 2. 当前实现（代码真实状态）

当前目录结构：

```text
graph_src_v2/services/usecase_workflow_agent/
  __init__.py
  graph.py
  prompts.py
  tools.py
  schemas.py
  README.md
  refactor-plan.md
```

当前代码的真实职责分布：

- `graph.py`
  - 装配主 agent
  - 挂 `HumanInTheLoopMiddleware`
  - 挂 `WorkflowToolSelectionMiddleware`
  - 挂 `MultimodalMiddleware`
  - 做 greeting guard、阶段推断、工具过滤
- `prompts.py`
  - 定义主 agent 提示词
  - 定义需求分析子智能体提示词
  - 定义用例评审子智能体提示词
- `tools.py`
  - 定义两个子智能体调用工具
  - 定义工作流 snapshot 工具
  - 定义最终持久化工具
- `schemas.py`
  - 定义工作流状态与 snapshot 结构

### 2.1 当前 agent 结构

当前不是 deepagent，也不是显式 `StateGraph` 工作流。

当前实现基于 `create_agent(...)`，其中：

- 一个主 orchestrator 负责调度
- 两个业务子智能体实际存在：
  - `requirement_analysis_subagent`
  - `usecase_review_subagent`
- 三个工作流工具实际存在：
  - `record_requirement_analysis`
  - `record_usecase_review`
  - `persist_approved_usecases`

也就是说，当前代码真实状态还不是“四个 subagent”。

### 2.2 当前阶段模型

当前 `graph.py` 实际使用的主阶段是：

- `analysis`
- `review`
- `approval`
- `completed`

阶段推进逻辑大致如下：

```text
input + optional attachments
  -> MultimodalMiddleware
  -> run_requirement_analysis_subagent
  -> record_requirement_analysis
  -> review
  -> run_usecase_review_subagent
  -> record_usecase_review
  -> approval or stay in review
  -> HumanInTheLoopMiddleware
  -> persist_approved_usecases
  -> completed
```

### 2.3 当前持久化边界

当前代码里，真正对 `interaction-data-service` 发 HTTP 的路径只有最终持久化工具：

- `persist_approved_usecases`

但它当前会做两件事，而不只是写最终用例：

1. 把附件解析产物写入：
   - `/api/usecase-generation/workflows/documents`
2. 把最终批准用例写入：
   - `/api/usecase-generation/use-cases`

因此，“附件解析产物落库”当前不是概念上的计划，而是已经接在最终批准路径里的真实行为。

### 2.4 当前人工确认边界

当前唯一被 `HumanInTheLoopMiddleware` 拦截的动作是：

- `persist_approved_usecases`

当前支持的人工决策：

- `approve`
- `edit`
- `reject`

当前 `edit` 已经不是只改 `approval_note`，而是会携带 `revision_feedback` 回到 review 流程继续修订。

### 2.5 当前已知问题

这也是本轮重构的主要动因：

1. analysis / review 后的“对用户汇报”主要依赖 prompt，不是结构上强制保证。
2. `graph.py` 职责过重，同时承担：
   - agent 装配
   - greeting guard
   - 消息归一化
   - 阶段推断
   - 工具过滤
3. “用例生成”当前没有被拆成一个独立子智能体边界。
4. `interaction-data-service` 的工作流文档仍然假设中间 workflow/snapshot/review 过程会长期作为主路径持久化，这与当前准备收紧的目标不一致。

## 3. 目标架构（本轮文档确认后的计划目标）

下面这一节描述的是“准备重构成什么样”，不是“当前代码已经如此”。

### 3.1 目标 agent 结构

目标状态是：

- 一个主 orchestrator
- 四个业务 subagent

四个 subagent 分工如下：

1. `requirement_analysis_subagent`
   - 负责读取需求上下文与附件摘要
   - 输出结构化需求分析
2. `usecase_generation_subagent`
   - 负责基于需求分析结果生成候选用例
   - 支持吸收用户补充意见和上一轮修订意见
3. `usecase_review_subagent`
   - 负责审查候选用例
   - 输出缺失项、歧义项、规范问题、修订建议
4. `usecase_persist_subagent`
   - 负责最终持久化前的落库准备与执行
   - 只在用户明确确认后允许进入持久化路径

这里的重点不是把所有事情都丢给子智能体自由发挥，而是把“阶段责任”切清楚。

### 3.2 目标主 orchestrator 职责

主 orchestrator 只做四类事情：

1. 决定当前应该调用哪个 subagent
2. 读取上一步的结构化结果并推进状态
3. 在每个关键阶段后，给用户一段明确汇报
4. 在需要人工确认的地方停下来，等待用户决定

主 orchestrator 不再承担重型分析本身，也不应该把“是否给用户回话”留给 prompt 偶然决定。

### 3.3 目标阶段模型

目标阶段模型建议收敛为：

- `analysis`
- `generation`
- `review`
- `awaiting_user_confirmation`
- `persisting`
- `completed`
- `revision_requested`

推荐主链路：

```text
input + optional attachments
  -> analysis
  -> generation
  -> review
  -> user-visible summary + revision suggestions
  -> awaiting_user_confirmation
  -> persisting
  -> completed
```

如果用户提出修改意见：

```text
awaiting_user_confirmation
  -> revision_requested
  -> generation
  -> review
  -> awaiting_user_confirmation
```

### 3.4 目标用户可见输出规则

未来不允许再出现“工具跑完了，但前端几乎没收到可读回复”的情况。

目标规则是：

- analysis 完成后，主 orchestrator 必须汇报：
  - 识别出的核心需求
  - 关键风险或待澄清项
  - 下一步将进入用例生成
- generation 完成后，主 orchestrator 必须汇报：
  - 当前生成了什么范围的候选用例
  - 是否准备进入评审
- review 完成后，主 orchestrator 必须汇报：
  - 当前候选用例摘要
  - 评审结论
  - 修订建议
  - 现在是否建议用户确认
- persist 完成后，主 orchestrator 必须汇报：
  - 附件解析产物是否已入库
  - 最终用例是否已入库
  - 工作流是否完成

换句话说，结构化 snapshot 给系统消费，阶段总结给用户消费，两者都必须存在。

### 3.5 目标人工确认边界

目标状态下有两个明确的人类控制点：

1. review 完成后
   - 用户先看候选用例和评审建议
   - 决定“继续改”还是“可以进入落库准备”
2. persist 执行前
   - 继续保留 `HumanInTheLoopMiddleware` 作为最终硬门禁
   - 防止模型绕过最终确认直接写库

也就是说：

- review 后的确认是业务层确认
- persist 前的 HITL 是执行层确认

两层都保留，但分工不同。

## 4. 目标工具边界

重构后希望每个 subagent 都有自己的工具边界，而不是把所有工作流工具混在主 orchestrator 上。

### 4.1 requirement analysis

建议工具：

- `run_requirement_analysis_subagent`
- `record_requirement_analysis_snapshot`

### 4.2 usecase generation

建议工具：

- `run_usecase_generation_subagent`
- `record_candidate_usecases_snapshot`

### 4.3 usecase review

建议工具：

- `run_usecase_review_subagent`
- `record_usecase_review_snapshot`

### 4.4 usecase persistence

建议工具：

- `persist_requirement_documents`
- `persist_final_usecases`
- 或保留一个组合工具，但内部边界要清楚

这里的“persist subagent”依然应该是一个强约束、低自由度的执行边界，而不是无约束的开放式推理代理。

## 5. 目标 interaction-data-service 契约

这一轮目标不是彻底去掉 `interaction-data-service`，而是收紧它在这条业务流中的职责。

当前确认保留的结果域：

- 附件解析产物
- 最终批准用例

因此，当前目标契约优先保留：

- `/api/usecase-generation/workflows/documents`
- `/api/usecase-generation/use-cases`

而下面这些 workflow/snapshot/review/approve/persist 接口，在本轮目标里不再作为推荐主路径：

- `/api/usecase-generation/workflows`
- `/api/usecase-generation/workflows/{workflow_id}/snapshots`
- `/api/usecase-generation/workflows/{workflow_id}/review`
- `/api/usecase-generation/workflows/{workflow_id}/approve`
- `/api/usecase-generation/workflows/{workflow_id}/persist`

注意：这表示“目标优化方向”，不是“这些接口已经删除”。

## 6. 接下来怎么推进

这次不会直接按感觉改代码，而是按 `refactor-plan.md` 里的步骤推进。

建议阅读顺序：

1. 本文：确认当前实现与目标架构是否理解一致
2. `refactor-plan.md`：确认每一步准备怎么改、改到什么算完成
3. `apps/interaction-data-service/docs/usecase-workflow-design.md`：确认跨服务契约是否一致

只有文档确认后，才进入逐步代码优化。
