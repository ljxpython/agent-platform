# Testcase 管理接口

这份文档描述 `apps/platform-api` 当前新增的 testcase 管理面接口。

## 1. 路由前缀

统一前缀：

- `/_management/projects/{project_id}/testcase`

## 2. 当前接口

### 2.1 聚合读取

- `GET /overview`
- `GET /batches`
- `GET /role`

用途：

- 给 `platform-web` 的 Testcase 工作区提供总览与批次筛选信息
- 给前端提供当前用户对当前项目的 testcase 写权限判断

### 2.2 用例管理

- `GET /cases`
- `GET /cases/export`
- `GET /cases/{case_id}`
- `POST /cases`
- `PATCH /cases/{case_id}`
- `DELETE /cases/{case_id}`

### 2.3 文档解析结果

- `GET /documents`
- `GET /documents/export`
- `GET /documents/{document_id}`
- `GET /documents/{document_id}/relations`
- `GET /documents/{document_id}/preview`
- `GET /documents/{document_id}/download`

## 3. 权限约束

当前实现：

- 读接口：`admin / editor / executor`
- 写接口：`admin / editor`

所有接口都先经过：

- `require_project_role(...)`

## 4. 当前请求链路

```text
platform-web
  -> /_management/projects/{project_id}/testcase/*
    -> platform-api testcase router
      -> InteractionDataService
        -> interaction-data-service /api/test-case-service/*
```

## 5. 当前实现分层

路由：

- `app/api/management/testcase.py`

请求 schema：

- `app/api/management/schemas.py`

本地 HTTP client：

- `app/services/local_json_http_client.py`

interaction-data-service 业务封装：

- `app/services/interaction_data_service.py`

## 6. 设计约束

- `platform-api` 不直接持有 testcase 业务数据
- `platform-api` 负责项目权限校验与协议整形
- `interaction-data-service` 负责 testcase 记录的真实存储与聚合查询
- 本地 JSON HTTP client 只负责通用的 base_url / timeout / header / JSON 处理，不理解 testcase 字段

## 7. Excel 导出实施方案

### 7.1 接口

- `GET /_management/projects/{project_id}/testcase/cases/export`

查询参数复用列表页筛选：

- `batch_id`
- `status`
- `query`
- `columns`（当前已支持，自定义导出列）

权限：

- `admin / editor / executor`

返回：

- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition: attachment; filename=...`

请求示例：

```http
GET /_management/projects/{project_id}/testcase/cases/export?batch_id=test-case-service:xxx&status=active&query=登录
Authorization: Bearer <token>
x-project-id: <project_id>
```

实现入口：

- 路由：`app/api/management/testcase.py`
- 业务：`app/services/interaction_data_service.py`
- Excel 生成：`app/services/testcase_case_export.py`

导出上限：

- 一期：单次最多 `2000` 条 testcase
- 二期：改为后端同步分页拉取，默认上限提高到 `10000`
- 超限返回 `400 testcase_export_limit_exceeded:{total}>{limit}`

### 7.2 导出内容

一期固定导出一个 workbook，包含两张 sheet：

1. `测试用例`
   - 导出当前筛选命中的正式 testcase
   - 一行一条 testcase
2. `导出信息`
   - `project_id`
   - 当前筛选条件
   - 导出时间
   - 导出总条数

`测试用例` sheet 默认列：

- `Case ID`
- `标题`
- `模块`
- `优先级`
- `状态`
- `描述`
- `前置条件`
- `步骤`
- `预期结果`
- `测试类型`
- `设计技术`
- `测试数据`
- `备注`
- `质量门禁`
- `质量分数`
- `批次 ID`
- `来源文档 IDs`
- `创建时间`
- `更新时间`

数组字段使用单元格多行文本，不额外拆子表：

- `preconditions`
- `steps`
- `expected_results`
- `source_document_ids`

对象字段处理：

- `test_data` 以 JSON 字符串写入单元格
- `quality_gate / quality_score` 从 `content_json.meta.quality_review` 提取
- 缺省值统一导出为空字符串，避免前端和 Excel 模板出现不一致空值口径

自定义列约束：

- 仅允许白名单字段
- 按前端传入顺序输出
- 去重后为空时回退到默认列

### 7.3 实现边界

1. 只导出 testcase，不混入 PDF 解析记录
2. 由 `platform-api` 生成 Excel，前端只负责发起下载
3. 导出接口会按筛选条件拉取 testcase 全量数据
4. 为了稳定性，二期改为服务端分页拉取后再统一组装 workbook；超限时返回明确错误，要求先缩小筛选范围
5. Excel 结构保持稳定，避免前端自己拼字段导致口径漂移

### 7.4 页面联动约束

- 导出筛选条件必须和 `/cases` 列表页完全一致
- 当前页看到什么筛选结果，导出就按同一条件出什么结果
- 不能新增“仅导出当前分页”语义，避免用户误判导出范围
- 文件名统一由后端生成，前端不自行命名

### 7.5 当前真实验证口径

本地已按真实服务链路验证：

1. 启动 `interaction-data-service`
2. 启动 `platform-api` 并指向本地 `interaction-data-service`
3. 使用真实 `admin` 登录获取 token
4. 调用真实导出接口下载 `.xlsx`
5. 使用 `openpyxl` 反读文件，校验：
   - 存在 `测试用例 / 导出信息` 两张 sheet
   - 真实 batch 导出条数正确
   - `batch_id / source_document_ids / steps` 等字段已落入工作簿
6. 调用真实 `documents/export / relations / preview / download`，校验：
   - `PDF解析记录 / 导出信息` 两张 sheet 可打开
   - `related_cases_count` 与真实关联一致
   - PDF 预览/下载响应头包含 `filename*=UTF-8''...`，中文文件名可用

## 8. 本地验证

```bash
uv run python -m py_compile \
  app/api/management/testcase.py \
  app/services/interaction_data_service.py \
  app/services/local_json_http_client.py \
  app/services/testcase_case_export.py \
  app/api/management/schemas.py

curl "http://127.0.0.1:2024/_proxy/health"
```

## 9. 二期接口方案与当前状态

说明：

- 本章最初用于冻结 testcase 管理接口二期范围
- 截至当前代码状态，下面列出的 `role / documents/export / relations / preview / download / cases export columns / 大结果集同步分页导出` 均已实现
- 后续 backlog 讨论不应再把这些接口当成待建设项

### 9.1 权限态接口

当前状态：

- 已实现

新增：

- `GET /_management/projects/{project_id}/testcase/role`

用途：

- 给 `platform-web` 返回当前用户在当前项目下的 testcase 写权限
- 避免前端靠按钮点击后再吃 `403`

返回建议：

```json
{
  "project_id": "uuid",
  "role": "admin",
  "can_write_testcase": true
}
```

约束：

- 仍然基于现有 `require_project_role(...)` 和当前登录用户
- 不单独引入新的权限体系

### 9.2 用例管理 CRUD 联动约束

当前状态：

- 已实现

前端写操作仍然使用：

- `POST /cases`
- `PATCH /cases/{case_id}`
- `DELETE /cases/{case_id}`

平台层约束：

1. `platform-api` 不自己生成 testcase 字段
2. 只负责：
   - 项目权限校验
   - 请求体校验
   - 错误码透传与协议整形
3. 结构化业务内容继续放在 `content_json`

推荐错误码：

- `400 invalid_payload`
- `403 forbidden`
- `404 testcase_not_found`
- `409 testcase_conflict`（如后续新增唯一约束）

### 9.3 PDF 管理二期接口

当前状态：

- 已实现

新增：

- `GET /_management/projects/{project_id}/testcase/documents/export`
- `GET /_management/projects/{project_id}/testcase/documents/{document_id}/relations`
- `GET /_management/projects/{project_id}/testcase/documents/{document_id}/preview`
- `GET /_management/projects/{project_id}/testcase/documents/{document_id}/download`

#### 9.3.1 documents/export

当前状态：

- 已实现

用途：

- 导出当前筛选命中的 PDF 解析记录

查询参数：

- `batch_id`
- `parse_status`
- `query`

返回：

- `.xlsx`

workbook 建议：

1. `PDF解析记录`
2. `导出信息`

字段建议：

- `Document ID`
- `文件名`
- `content_type`
- `source_kind`
- `parse_status`
- `batch_id`
- `summary_for_model`
- `parsed_text_excerpt`
- `parsed_text_length`
- `structured_data_json`
- `thread_id`
- `run_id`
- `storage_path`
- `created_at`
- `related_cases_count`

说明：

- `parsed_text` 不直接全量塞进 Excel
- 优先导出截断摘要和长度，避免 workbook 爆炸

#### 9.3.2 documents/{document_id}/relations

当前状态：

- 已实现

用途：

- 给前端 PDF 详情页展示“这份文档影响了哪些测试用例”

返回建议：

```json
{
  "document": { "...": "..." },
  "runtime_meta": {
    "thread_id": "xxx",
    "run_id": "xxx",
    "agent_key": "test_case_service"
  },
  "related_cases": [
    {
      "id": "uuid",
      "case_id": "TC-001",
      "title": "登录成功",
      "status": "active",
      "batch_id": "test-case-service:thread"
    }
  ],
  "related_cases_count": 1
}
```

#### 9.3.3 documents/{document_id}/preview 与 download

当前状态：

- 已实现

用途：

- `preview`：浏览器内联预览 PDF
- `download`：下载原始 PDF

边界：

- `platform-api` 仍不直接保存文件
- 只做鉴权、代理和响应头整形

### 9.4 Excel 导出二期

当前状态：

- 已实现

#### 9.4.1 自定义列

当前状态：

- 已实现

`GET /cases/export` 二期新增可选参数：

- `columns=case_id,title,module_name,...`

规则：

1. 后端维护固定列白名单
2. 不允许前端传任意 JSON path
3. 不传 `columns` 时继续走默认导出列，保持兼容

#### 9.4.2 大结果集同步分页导出

当前状态：

- 已实现

实现原则：

1. `platform-api` 内部分页拉取 `interaction-data-service`
2. 使用 `openpyxl` 的 `write_only` 模式生成 workbook
3. 当前不引入异步导出任务系统

推荐分页策略：

- 每页 `500`
- 同步导出最大 `10000`

超限行为：

- 返回 `400 testcase_export_limit_exceeded:{total}>{limit}`
- 前端提示用户缩小筛选范围

## 10. 二期真实验证口径

必须走真实服务链路：

1. 真实登录态
2. 真实项目角色
3. 真实 `platform-api`
4. 真实 `interaction-data-service`
5. 真实 PDF 记录和 testcase 数据

至少验证：

1. `role` 接口能正确区分 `admin / editor / executor`
2. CRUD 写操作在 `admin / editor` 下成功，在 `executor` 下返回 `403`
3. `documents/export` 可下载并被 `openpyxl` 正常读取
4. `relations` 返回的 testcase 数量与数据库实际关联一致
5. `preview / download` 在原始文件存在时可用，不存在时返回明确错误
6. `cases/export?columns=...` 能按列配置输出
7. 大结果集导出走后端分页后仍保持结果完整
