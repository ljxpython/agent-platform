# usecase_workflow_agent 重构实施计划

本文是下一轮代码优化的执行计划。

目标不是一次性推倒重写，而是按可验证的小步骤推进，让每一步都能：

- 保持代码可运行
- 保持行为可验证
- 让文档、测试、实现同步收敛

## 1. 已确认目标

本轮计划以以下目标为准：

1. 保留附件解析产物落库
2. 保留最终用例落库
3. 中间 analysis / generation / review 结果主要保存在线程状态和结构化 snapshot 中
4. 主 orchestrator 必须在每个阶段后对用户做可见汇报
5. 目标拓扑为：
   - 主 orchestrator
   - `requirement_analysis_subagent`
   - `usecase_generation_subagent`
   - `usecase_review_subagent`
   - `usecase_persist_subagent`
6. review 之后先由用户确认是否继续修订或进入持久化
7. persist 执行前继续保留最终 HITL 硬门禁

## 2. 非目标

这一轮先不做：

- 前端页面大改版
- 把整个工作流改成 deepagent
- 把所有历史 workflow API 一次性全部物理删除
- 新增与本流程无关的通用抽象层

## 3. 分步实施顺序

## Step 1. 收紧状态模型与文档命名

目标：先让“我们在说什么”一致。

计划动作：

- 把文档里的目标阶段统一成：
  - `analysis`
  - `generation`
  - `review`
  - `awaiting_user_confirmation`
  - `persisting`
  - `completed`
  - `revision_requested`
- 在 runtime 代码层整理当前 `approval` / `completed` / `review` 的语义映射
- 明确哪些是“当前实现字段”，哪些是“下一步目标字段”

完成标准：

- 文档和计划里不再混用旧阶段术语
- 后续代码改动能围绕同一套阶段语言推进

## Step 2. 拆出显式的 usecase generation 边界

目标：把“生成候选用例”从主 orchestrator 的隐式职责里拿出来。

计划动作：

- 新增 `usecase_generation_subagent`
- 为 generation 定义独立上下文构造与 snapshot 记录边界
- 明确 generation 输入来自：
  - requirement analysis 结果
  - 用户补充说明
  - 上一轮 revision feedback（如果有）

完成标准：

- 候选用例生成不再只是 review 工具顺带承担的隐式逻辑
- generation 成为一个独立可测的阶段

## Step 3. 强制主 orchestrator 输出阶段汇报

目标：彻底解决“前端看不到智能体在干什么”的问题。

计划动作：

- 定义 analysis / generation / review / persist 各阶段的标准汇报模板
- 把“给用户回复阶段总结”从 prompt 建议提升为 orchestration 约束
- 确保每轮关键工具执行后，都会有一条用户可读总结

完成标准：

- analysis 后一定有需求摘要
- generation 后一定有候选用例摘要
- review 后一定有评审结论和修改建议
- persist 后一定有持久化结果说明

## Step 4. 把 review 后确认做成显式业务关口

目标：review 完成后，不直接滑进持久化工具，而是先停给用户确认。

计划动作：

- 让主 orchestrator 在 review 完成后进入 `awaiting_user_confirmation`
- 明确用户可选动作：
  - 继续修改
  - 重新评审
  - 确认进入持久化
- 把 revision feedback 的入口和回流阶段说清楚

完成标准：

- review 结果先呈现给用户
- 业务层确认与执行层 HITL 不再混成一个阶段

## Step 5. 引入 usecase_persist_subagent 并收紧持久化工具边界

目标：把最终落库职责从“大工作流工具”收紧成清晰的 persist 阶段。

计划动作：

- 引入 `usecase_persist_subagent`
- 明确 persist 阶段内部只处理：
  - requirement document artifacts 持久化
  - final use cases 持久化
- 决定是保留一个组合工具，还是拆成两个内部工具

完成标准：

- 持久化边界清楚
- “附件解析产物落库”和“最终用例落库”都保留
- 只有用户确认后才进入 persist 阶段

## Step 6. 精简 graph.py

目标：把 `graph.py` 收回成装配层。

计划动作：

- 把阶段策略、阶段文案、状态推进规则抽到独立 helper / policy 模块
- 保留 `graph.py` 只做：
  - 模型装配
  - tool 装配
  - middleware 装配
  - HITL 注册

完成标准：

- `graph.py` 不再承担大量业务协议细节
- 阶段逻辑更容易单测

## Step 7. 收紧 interaction-data-service 的推荐主路径

目标：让跨服务契约只保留当前业务真正需要的结果域。

计划动作：

- 明确本流程继续保留：
  - `/api/usecase-generation/workflows/documents`
  - `/api/usecase-generation/use-cases`
- 把 workflow/snapshot/review/approve/persist 接口标记为清理候选
- 等 runtime 代码彻底不依赖这些接口后，再决定是否实际删除

完成标准：

- 文档中的推荐接口和运行时真实路径一致
- 清理工作有明确前置条件，不会误删仍在使用的接口

## Step 8. 测试与验收补强

目标：每一步改动都能验证，而不是靠肉眼猜。

计划动作：

- 补 analysis / generation / review / persist 的阶段性单测
- 补“阶段汇报必须出现”的测试
- 补 documents endpoint 真正被打到的 smoke / integration 验证
- 保留本地 REPL / manual QA 路径

完成标准：

- 用户可见汇报有测试覆盖
- 附件落库有真实验证路径
- revise loop 和最终 persist 都有回归保护

## 4. 推荐执行节奏

后续按下面节奏逐步做：

1. 先完成 Step 2 + Step 3
   - 先把 generation 拆开
   - 再把用户可见汇报做扎实
2. 再完成 Step 4 + Step 5
   - 先把 review 后确认关口做显式
   - 再收紧 persist subagent
3. 最后做 Step 6 + Step 7 + Step 8
   - 精简 `graph.py`
   - 收紧 IDS 契约
   - 补齐验证

这样做的原因是：

- 先解决用户最能感知的问题（没回复、职责不清）
- 再处理结构拆分
- 最后再做接口清理和架构收尾

## 5. 每一步的确认方式

后续真正开始改代码时，建议按这个节奏与用户确认：

1. 完成一个 Step
2. 跑对应测试 / 手工链路
3. 汇报改动点与验证结果
4. 再进入下一步

也就是说，后续优化不走“一次改完全部”，而走“文档确认后按计划逐步落地”。
