# test_case_service 持久化设计

## 目标

为 `runtime_service/services/test_case_service` 增加一条最小但稳定的正式落库链路：

```text
多模态输入
  -> 需求分析 / 策略 / 用例设计 / 评审 / 格式化
  -> persist_test_case_results
  -> interaction-data-service HTTP API
  -> test_case_documents / test_cases
```

本设计明确不复用 `usecase_workflow_agent` 的 workflow / snapshot / review 编排模型。

## 设计原则

1. 只保留一个模型可见持久化工具：`persist_test_case_results`
2. 只保留两类远端资源：`documents` 和 `test-cases`
3. 共享 HTTP client 只抽传输层，不抽业务 payload
4. `project_id` 等受信参数由 `runtime.config / runtime.state / runtime.context` 读取
5. 当前尚未完全透传项目上下文时，允许使用默认项目 ID 兜底

## runtime-service 侧结构

### 1. 服务私有工具

新增：

- `runtime_service/services/test_case_service/tools.py`

职责：

- 解析 `ToolRuntime`
- 读取 `project_id / thread_id / run_id / batch_id`
- 从 `multimodal_attachments` 构造文档持久化 payload
- 从最终测试用例构造测试用例持久化 payload
- 调用共享 HTTP client

实现注意：

- `persist_test_case_results` 的 `runtime` 参数必须使用标准 `ToolRuntime[...]` 注入形式
- 不要把 `runtime` 写成可选参数
- 不要再为这个工具显式绑定 `args_schema`
- 该工具应由函数签名自动推导 schema，否则 LangGraph 可能无法正确注入 `runtime`

### 2. 共享 HTTP client

新增：

- `runtime_service/integrations/interaction_data.py`

抽象边界：

- 负责 base_url / token / timeout / headers / HTTP JSON 请求
- 不理解任何具体业务字段
- 不替各服务组装 payload

这样其他服务后续也能复用同一个 client，但不会被 `test_case_service` 的数据结构绑死。

### 3. 默认项目 ID 策略

解析顺序：

1. `runtime.context.project_id`
2. `runtime.config.configurable.project_id`
3. `runtime.config.metadata.project_id`
4. `runtime.state.project_id`
5. `test_case_default_project_id`

当前默认值：

- `00000000-0000-0000-0000-000000000001`

这是过渡方案，后续接入真实项目上下文后应优先覆盖。

## interaction-data-service 侧结构

采用“每个服务一个专属接口前缀”的范式：

- `POST /api/test-case-service/documents`
- `GET /api/test-case-service/documents`
- `GET /api/test-case-service/documents/{document_id}`
- `POST /api/test-case-service/test-cases`
- `GET /api/test-case-service/test-cases`
- `GET /api/test-case-service/test-cases/{test_case_id}`
- `PATCH /api/test-case-service/test-cases/{test_case_id}`
- `DELETE /api/test-case-service/test-cases/{test_case_id}`

旧的 `/api/usecase-generation/*` 已退役，不再作为主路径。

## 数据落点

### 1. `test_case_documents`

存附件解析结果：

- `project_id`
- `batch_id`
- `filename`
- `content_type`
- `source_kind`
- `parse_status`
- `summary_for_model`
- `parsed_text`
- `structured_data`
- `provenance`
- `confidence`
- `error`

### 2. `test_cases`

存最终正式测试用例：

- `project_id`
- `batch_id`
- `case_id`
- `title`
- `description`
- `status`
- `module_name`
- `priority`
- `source_document_ids`
- `content_json`

其中完整业务结果和运行时元数据全部收敛到 `content_json.meta`。

## 调试与验证要求

禁止 mock 持久化链路。

验证必须同时满足：

1. 使用真实 PDF 或真实业务需求文本
2. 使用真实模型
3. 调用真实 `interaction-data-service`
4. 最终通过远端查询接口确认文档和测试用例已写入
5. 抓取并分析：
   - 流式输出内容
   - 工具调用记录
   - 远端返回结果
   - 最终异常或成功状态

## 已完成真实验证

已通过以下命令完成一轮真实落库验证：

```bash
cd apps/runtime-service
uv run python runtime_service/tests/services_test_case_service_persistence_live.py \
  --model-id deepseek_chat \
  --timeout 900
```

验证结果：

1. `persist_test_case_results` 已被真实调用
2. `interaction-data-service` 远端查询确认：
   - `documents_total = 1`
   - `test_cases_total = 4`
3. 退出码为 `0`

说明当前最小持久化架构已经可用。
