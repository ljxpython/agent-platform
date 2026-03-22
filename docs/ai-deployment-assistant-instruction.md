# For LLM Agents：本地部署执行手册

如果你是一个正在帮助用户处理这个仓库本地环境的 LLM 代理，请按下面的顺序执行。目标只有一个：基于当前仓库的真实结构，完成最小本地部署、联调、验证与结果汇总。

## Step 1：先读取仓库真相

开始动手前，先阅读以下文件，并以它们为准：

1. `README.md`
2. `docs/local-dev.md`
3. `docs/env-matrix.md`
4. `docs/deployment-guide.md`
5. `apps/platform-api/docs/local-dev.md`
6. `apps/runtime-service/README.md`

如果这些文档之间存在旧口径冲突，以根级文档描述的当前四应用结构和本手册为准。

## Step 2：确认当前仓库的固定事实

### 2.1 四个应用与端口

- `apps/runtime-service`：`8123`
- `apps/platform-api`：`2024`
- `apps/platform-web`：`3000`
- `apps/runtime-web`：`3001`

### 2.2 两条本地链路

- 平台链路：`platform-web -> platform-api -> runtime-service`
- 调试链路：`runtime-web -> runtime-service`

### 2.3 配置文件口径

当前只使用 app-local 配置文件，不使用根目录统一 `.env`。

本地部署时，应处理这些位置：

- `apps/platform-api/.env`
- `apps/platform-web/.env`
- `apps/runtime-web/.env`
- `apps/runtime-service/graph_src_v2/.env`
- `apps/runtime-service/graph_src_v2/conf/settings.yaml`
- 可选本地覆写：`apps/runtime-service/graph_src_v2/conf/settings.local.yaml`

### 2.4 不要沿用的旧假设

- 不要假设 `platform-api` 使用 repo-root `.env`
- 不要把 `apps/runtime-web/.env.example` 里的 `http://localhost:2024` 当作当前本地调试默认值
- 不要把 `/init-deep` 当作当前本地部署任务的前置步骤

## Step 3：先核对依赖，再开始配置

至少确认以下依赖可用：

- Python `>=3.13`
- `uv`
- Node `22.x`
- `pnpm 10.5.1`
- PostgreSQL，本地默认 `127.0.0.1:5432`

如果依赖缺失，优先直接补齐；如果用户尚未提供真实模型配置，也要继续完成能完成的部分。

## Step 4：按应用整理本地配置

### 4.1 `platform-api`

配置文件：`apps/platform-api/.env`

至少核对这些值：

- `LANGGRAPH_UPSTREAM_URL=http://127.0.0.1:8123`
- `DATABASE_URL`
- `PLATFORM_DB_ENABLED`
- `PLATFORM_DB_AUTO_CREATE`
- `JWT_ACCESS_SECRET`
- `JWT_REFRESH_SECRET`
- `BOOTSTRAP_ADMIN_USERNAME`
- `BOOTSTRAP_ADMIN_PASSWORD`

默认本地 bootstrap 账号通常是 `admin / admin123456`，只适用于临时本地环境。

### 4.2 `platform-web`

配置文件：`apps/platform-web/.env`

至少核对：

- `NEXT_PUBLIC_API_URL=http://localhost:2024`
- `NEXT_PUBLIC_ASSISTANT_ID=assistant`

### 4.3 `runtime-web`

配置文件：`apps/runtime-web/.env`

至少核对：

- `NEXT_PUBLIC_API_URL=http://localhost:8123`
- `NEXT_PUBLIC_ASSISTANT_ID=assistant`

这里必须明确：当前本地调试前端应直连 `runtime-service:8123`，不要沿用旧示例里的 `http://localhost:2024`。

### 4.4 `runtime-service`

配置文件：

- `apps/runtime-service/graph_src_v2/.env`
- `apps/runtime-service/graph_src_v2/conf/settings.yaml`
- 可选：`apps/runtime-service/graph_src_v2/conf/settings.local.yaml`

至少核对：

- `.env` 中的 `APP_ENV`
- `.env` 中的 `MODEL_ID`
- `settings.yaml` 中的 `default.default_model_id`
- `settings.yaml` 中的 `default.models.<model_id>`

## Step 5：严格处理模型配置

这是最容易出错的部分。

### 5.1 不允许编造的字段

以下值必须来自用户提供的真实材料，或来自用户明确授权复用的现有私有配置：

- `model_provider`
- `model`
- `base_url`
- `api_key`

不要伪造占位值并把它们描述为可运行配置。

### 5.2 最小一致性要求

当用户提供模型材料后，至少保证：

1. `MODEL_ID` 已写入 `apps/runtime-service/graph_src_v2/.env`
2. `settings.yaml` 中存在同名模型组
3. `default.default_model_id` 可落到这个模型组
4. 当前 `APP_ENV` 对应环境最终能解析到这个模型组
5. 模型组内四元组完整：`model_provider`、`model`、`base_url`、`api_key`

### 5.3 如果模型配置不完整

如果模型四元组不完整：

- 继续完成其他应用的本地配置和验证
- 明确列出缺失字段
- 在结果中说明 `runtime-service` 卡在真实模型配置，而不是笼统说“整套部署失败”

## Step 6：按顺序启动并验证

推荐顺序：

1. `runtime-service`
2. `platform-api`
3. `platform-web`
4. `runtime-web`

常用启动命令：

`runtime-service`

```bash
cd apps/runtime-service
uv run langgraph dev --config graph_src_v2/langgraph.json --port 8123 --no-browser
```

`platform-api`

```bash
cd apps/platform-api
uv run uvicorn main:app --host 0.0.0.0 --port 2024 --reload
```

`platform-web`

```bash
cd apps/platform-web
pnpm dev
```

`runtime-web`

```bash
cd apps/runtime-web
PORT=3001 pnpm dev
```

如果配置都已经准备好，也可以使用根目录脚本：

- `scripts/dev-up.sh`
- `scripts/check-health.sh`
- `scripts/dev-down.sh`

这些脚本是快捷启动方式，不是配置生成方式。脚本失败时，回到单服务逐个排查。

## Step 7：执行健康检查

### 7.1 `runtime-service`

```bash
curl http://127.0.0.1:8123/info
curl http://127.0.0.1:8123/internal/capabilities/models
curl http://127.0.0.1:8123/internal/capabilities/tools
```

### 7.2 `platform-api`

```bash
curl http://127.0.0.1:2024/_proxy/health
curl http://127.0.0.1:2024/api/langgraph/info
```

### 7.3 页面访问

- `platform-web`：`http://127.0.0.1:3000`
- `runtime-web`：`http://127.0.0.1:3001`

不要只贴命令输出，必须明确判定：

- `runtime-service` 是否能返回基础信息
- `platform-api` 是否能访问自身健康检查，并连到 runtime 上游
- `platform-web` 是否能打开
- `runtime-web` 是否能打开
- 哪些结果受真实模型配置缺失影响

## Step 8：最后汇报结果

完成后，给用户一份简洁、可执行的结果说明，至少包含：

1. 这次处理了哪些事项
2. 实际读取或写入了哪些配置文件
3. 哪些服务已成功启动
4. 哪些服务仍受什么问题阻塞
5. 本地访问地址
6. 如启用了本地默认 bootstrap 账号，明确给出账号密码并提醒仅限本地临时环境
7. 如果下次要重启，建议使用什么方式

推荐直接列出以下地址：

- `runtime-service: http://127.0.0.1:8123`
- `platform-api: http://127.0.0.1:2024`
- `platform-web: http://127.0.0.1:3000`
- `runtime-web: http://127.0.0.1:3001`

## Step 9：禁止事项

- 不要使用固定人设
- 不要把 `/init-deep` 写成必需步骤或推荐前置动作
- 不要假设存在根目录统一 `.env`
- 不要把 `runtime-web` 指到 `http://localhost:2024` 作为当前本地调试默认值
- 不要编造模型凭据、JWT 密钥、数据库密码或任何真实私密信息
- 不要只改文件不验证
- 不要在总结里省略失败原因和剩余阻塞项
