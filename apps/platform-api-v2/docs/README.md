# Platform API V2 文档导航

当前 `apps/platform-api-v2` 以“先定规则，再写业务”为原则推进。

当前阶段状态：

- `Phase B: Control Plane Freeze` 已完成
- `Phase C: Data & Delivery Freeze` 已完成
- `Phase D: Final Standard Freeze` 已完成

优先阅读顺序：

1. `architecture-v2.md`
   - 目标服务边界、目录骨架、模块划分和长期形态
2. `engineering-standards.md`
   - 平台后端开发规范、权限/审计标准和 AI Harness 工作流
3. `permission-standard.md`
   - 平台级 / 项目级授权模型、策略判定和测试基线
4. `audit-standard.md`
   - 审计事件模型、命名、分页和脱敏规则
5. `operations-standard.md`
   - 长任务、operation/job、worker / queue 接入方式
6. `harness-playbook.md`
   - 人和 AI 代理在 `platform-api-v2` 中的统一工作流
7. `first-batch-module-map.md`
   - 第一批模块迁移顺序、旧接口映射和前后端协同顺序
8. `frontend-switch-strategy.md`
   - `platform-web-vue` 如何逐步切换到新的控制面
9. `phase-1-checklist.md`
   - 第一阶段可执行任务清单
10. `phase-2-checklist.md`
   - 第二阶段执行清单、优先级和进展维护规则
11. `phase-2-p1-runtime-workspace.md`
   - 运行工作台稳定化的共享基座、改造点和验证结果
12. `phase-2-governance-baseline.md`
   - operations、platform-config、PostgreSQL/Redis 边界和前端 service 收口
13. `phase-2-smoke-checklist.md`
   - 第二阶段演示与验收 smoke 清单
14. `phase-2-completion.md`
   - 第二阶段完成记录
15. `phase-2-release-draft.md`
   - 第二阶段 release / tag / changelog 草案
16. `phase-3-checklist.md`
   - 第三阶段执行清单
17. `phase-3-p0-operations-worker.md`
   - operations worker、queue 方案、手动启动和验收路径
18. `phase-3-p1-runtime-policies.md`
   - runtime policy overlay 的存储、接口和前端治理页收口
19. `phase-3-p2-operations-center.md`
   - operations 正式治理页、统一异步反馈流与 artifact 下载收口
20. `phase-3-p4-platform-config.md`
   - platform-config 治理入口、feature flags、权限与审计收口
21. `phase-3-completion.md`
   - 第三阶段完成说明、验证结果和 phase-4 入口
22. `phase-3-chat-acceptance-checklist.md`
   - chat 页面前端手动验收清单
23. `phase-4-checklist.md`
   - phase-3 之后的生产化、交付化与 Harness 收口规划
24. `phase-4-p1-artifact-lifecycle.md`
   - operation artifact 的 retention、cleanup、对象存储扩展边界
25. `phase-4-p1-redis-queue.md`
   - `db_polling + redis_list` 双后端、配置项和后续升级边界
26. `phase-4-p2-observability-and-security.md`
   - 可观测性、service account、安全边界与环境治理收口
27. `phase-4-p4-delivery-and-release.md`
   - CI、Docker、数据库脚本、发布模板与最小交付口径
28. `phase-4-p5-harness-and-templates.md`
   - Harness、开发者入口、模板和验收门槛
29. `runbook.md`
   - 当前故障排查和值班入口
30. `release-template.md`
   - release note / tag / rollback 模板
31. `postgres-baseline.md`
   - PostgreSQL 开发基线、Alembic 命令和数据库切换规则
32. `phase-4-frontend-acceptance.md`
   - phase-4 新治理页的前端手动验收清单
33. `langgraph-sdk-migration-plan.md`
   - `runtime_gateway + assistants adapter` 是否 SDK 化、endpoint 迁移矩阵和测试补齐清单
34. `legacy-solution-inheritance-checklist.md`
   - 旧 `platform-api` 方案里必须继承和明确不继承的点
35. `phase-5-legacy-sunset-and-final-standard-freeze.md`
   - 旧控制面下线、最终架构冻结、Harness 最终范式和正式执行顺序
36. `phase-6-control-plane-freeze.md`
   - Phase B 的模块边界、权限/审计、DTO 与错误码冻结清单
37. `phase-7-data-delivery-freeze.md`
   - Phase C 的数据库、队列、交付、备份恢复和环境分层冻结清单
38. `phase-8-final-standard-freeze.md`
   - Phase D 的正式宿主、正式文档入口、模板与 Harness 冻结清单
39. `change-delivery-checklist.md`
   - AI / 人协作统一交付清单
40. `module-delivery-template.md`
   - 新模块与新治理能力的标准交付模板

常用启动入口：

- 仓库根目录：`bash "./scripts/platform-web-vue-demo-up.sh"`
- 健康检查：`bash "./scripts/platform-web-vue-demo-health.sh"`
- 停止：`bash "./scripts/platform-web-vue-demo-down.sh"`
