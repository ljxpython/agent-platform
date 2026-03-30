---
name: test-case-design
description: 在测试策略之后激活。负责生成正式、结构化、可执行的测试用例，并尽量控制数量与冗余。
---

# 测试用例设计 Skill

## 激活场景
- `test-strategy` 已完成
- 用户要求生成正式测试用例

## 必做动作
1. 覆盖主流程、关键异常、必要边界
2. 选择最合适的设计技术：等价类、边界值、场景法、错误猜测等
3. 输出可直接落库的结构化测试用例

## 默认数量策略
- 用户未指定数量时：默认生成 3-5 条正式测试用例
- 用户要求“最小输出”时：优先保留最有价值的用例，不做铺量
- 用户明确要求更多条数时，再扩展

## 每条用例至少包含
- `case_id`
- `title`
- `module_name`
- `priority`
- `steps`
- `expected_results`

可选补充：`description`、`test_type`、`design_technique`、`preconditions`、`test_data`、`remarks`

## 约束
- 测试数据尽量具体，不要写“合法值”“有效数据”这类空话
- 预期结果必须可验证
- 不要为了凑数量制造低价值重复用例
- 结果必须适合后续 `persist_test_case_results` 直接使用
