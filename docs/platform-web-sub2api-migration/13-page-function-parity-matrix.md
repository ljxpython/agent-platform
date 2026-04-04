# 13. 页面与功能对照矩阵

## 目标

这份文档只解决一件事：

- 把 `apps/platform-web` 现有页面，按当前 `apps/platform-web-vue` 的真实落地状态盘清楚

后续开发、验收、汇报都以这份矩阵为主，不再靠记忆讨论“哪个页到底做没做、做到什么程度”。

## 状态口径

- `已完成`：页面已进入主路由，核心链路可用，可作为现阶段验收通过项
- `部分完成`：页面已落地，但还没有达到与 `apps/platform-web` 对齐的验收标准
- `未开始`：当前 `platform-web-vue` 还没有对应正式页面或对应链路
- `暂缓`：当前阶段明确不做，不影响用户名密码登录演示主线

## 覆盖统计

- 源页面总数：`28`
- `已完成`：`17`
- `部分完成`：`3`
- `未开始`：`7`
- `暂缓`：`1`

## 已完成页面

| 来源路由 | `platform-web-vue` 对应路由 | 当前状态 | 说明 |
| --- | --- | --- | --- |
| `/auth/login` | `/auth/login` | 已完成 | 用户名密码登录主链路已接入 |
| `/workspace` | `/workspace` | 已完成 | 已有工作区默认跳转与上下文校验 |
| `/workspace/overview` | `/workspace/overview` | 已完成 | 作为总览首页和演示入口使用 |
| `/workspace/projects` | `/workspace/projects` | 已完成 | 列表页母版已接住真实接口 |
| `/workspace/users` | `/workspace/users` | 已完成 | 列表页母版已接住真实接口 |
| `/workspace/assistants` | `/workspace/assistants` | 已完成 | 助手列表已落到正式工作区 |
| `/workspace/graphs` | `/workspace/graphs` | 已完成 | Agent 图谱工作区可进入 |
| `/workspace/runtime` | `/workspace/runtime` | 已完成 | Runtime 概览页已落地 |
| `/workspace/runtime/models` | `/workspace/runtime/models` | 已完成 | Runtime Models 已落地 |
| `/workspace/runtime/tools` | `/workspace/runtime/tools` | 已完成 | Runtime Tools 已落地 |
| `/workspace/threads` | `/workspace/threads` | 已完成 | 已改成点选后加载详情，不再全量展开 |
| `/workspace/testcase` | `/workspace/testcase` | 已完成 | 已保持一级标题并承接三个二级页 |
| `/workspace/testcase/cases` | `/workspace/testcase/cases` | 已完成 | 用例管理页已落地 |
| `/workspace/testcase/documents` | `/workspace/testcase/documents` | 已完成 | 文档管理、预览、下载主链路已恢复 |
| `/workspace/me` | `/workspace/me` | 已完成 | 个人信息页已落地 |
| `/workspace/security` | `/workspace/security` | 已完成 | 安全设置页已落地 |
| `/workspace/audit` | `/workspace/audit` | 已完成 | 审计日志页已落地 |

## 部分完成页面

| 来源路由 | `platform-web-vue` 对应路由 | 当前状态 | 关键差距 | 执行顺序 |
| --- | --- | --- | --- | --- |
| `/workspace/sql-agent` | `/workspace/sql-agent` | 部分完成 | 已接入通用 chat 基座，并补齐运行中取消、Debug / Continue、`todos / files`、interrupt / HITL、tool call / artifact、markdown 输出、消息级复制 / 编辑 / 重试、retry branch 切换与 history 第一版；剩余缺口为 checkpoint history 可视化和移动端抽屉细节 | 1 |
| `/workspace/chat` | `/workspace/chat` | 部分完成 | 首次引导和真实对话已落地，并补齐运行中取消、Debug / Continue、`todos / files`、interrupt / HITL、tool call / artifact、markdown 输出、消息级复制 / 编辑 / 重试、retry branch 切换与 history 第一版；剩余缺口为 checkpoint history 可视化和移动端抽屉细节 | 1 |
| `/workspace/testcase/generate` | `/workspace/testcase/generate` | 部分完成 | 页面已存在，但生成链路和验收口径还没完全对齐 | 2 |

## 未开始页面

| 来源路由 | 目标建议路由 | 当前状态 | 主要依赖 | 执行顺序 |
| --- | --- | --- | --- | --- |
| `/workspace/assistants/[assistantId]` | `/workspace/assistants/:assistantId` | 未开始 | 助手详情数据装配、详情页母版 | 4 |
| `/workspace/assistants/new` | `/workspace/assistants/new` | 未开始 | 表单页母版、创建接口契约 | 5 |
| `/workspace/projects/[projectId]` | `/workspace/projects/:projectId` | 未开始 | 项目详情接口装配、详情页骨架 | 6 |
| `/workspace/users/[userId]` | `/workspace/users/:userId` | 未开始 | 用户详情接口装配、详情页骨架 | 7 |
| `/workspace/projects/new` | `/workspace/projects/new` | 未开始 | 创建表单、校验和提交反馈 | 8 |
| `/workspace/users/new` | `/workspace/users/new` | 未开始 | 创建表单、校验和提交反馈 | 9 |
| `/workspace/projects/[projectId]/members` | `/workspace/projects/:projectId/members` | 未开始 | 依赖项目详情页、成员管理接口和弹窗流 | 10 |

## 暂缓页面

| 来源路由 | 目标建议路由 | 当前状态 | 暂缓原因 |
| --- | --- | --- | --- |
| `/auth/callback` | `/auth/callback` | 暂缓 | 当前演示环境只走用户名密码登录，其他登录方式不在本轮范围 |

## 当前主线执行顺序

1. `testcase/generate`
2. `assistants/detail`
3. `assistants/new`
4. `projects/detail`
5. `users/detail`
6. `projects/new`
7. `users/new`
8. `projects/members`
9. `chat / sql-agent` 的 checkpoint history 可视化与移动端细节
10. 系统级一致性补完
11. 演示与验收硬化

## 系统级补完清单

- 公告数据接入或演示替身方案
- tooltip / 帮助提示体系
- 首次引导与入口提示体系
- dark mode 全链路一致性复查
- 大屏与小屏布局占满、溢出与滚动细节复查
- 演示账号、演示路径、烟测清单固化

## 使用方式

- 开工前，先看这份矩阵确认目标页是不是当前主线
- 开发中，新增或完成一个页面就更新对应状态
- 验收时，只按这份矩阵逐条过，不再临时口头补清单
