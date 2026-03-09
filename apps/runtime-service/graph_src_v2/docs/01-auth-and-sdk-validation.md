# v2 鉴权与验证指南

## 1) 认证入口

统一文件：`graph_src_v2/auth/provider.py`

- `custom_auth`：本地 demo token 模式（默认）
- `oauth_auth`：Supabase OAuth 模式

## 2) Demo 模式（默认）

- `langgraph.json` 默认走 `./graph_src_v2/auth/provider.py:custom_auth`
- 可用 token：`owner-token`、`viewer-token`、`admin-token`

推荐检查：

1. `owner-token` 可以创建 thread
2. `viewer-token` 无法创建 thread（403）
3. `owner-token` 可在自己的 thread 上执行 run

## 3) OAuth 模式（Supabase）

把配置中的 `auth.path` 改成：

- `./graph_src_v2/auth/provider.py:oauth_auth`

并在 `.env` 中准备：

- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- 可选：`SUPABASE_TIMEOUT_SECONDS`

## 4) 启动命令

```bash
uv run langgraph dev --config graph_src_v2/langgraph.json --port 8123 --no-browser
```

## 5) 自动化验证

```bash
uv run pytest graph_src_v2/tests/test_auth_core.py graph_src_v2/tests/test_custom_routes.py graph_src_v2/tests/test_model_smoke.py -q
```
