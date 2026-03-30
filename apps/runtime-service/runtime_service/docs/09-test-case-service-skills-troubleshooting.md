# test_case_service skills 无法识别问题排查

## 问题现象

`test_case_service` 已经通过 `create_deep_agent(..., skills=["/skills/"])` 挂载了私有 skills，离线验证也能枚举出全部 `SKILL.md`，但在线对话时模型仍然直接开始输出测试分析或测试策略，没有先调用 `read_file` 读取 skill 文件。

典型表现：

- `_alist_skills` 能列出全部 skills
- `SkillsMiddleware.abefore_agent` 能把 skills 元数据注入进 state
- live 对话时模型回复里不提 skill，也没有 `read_file("/skills/.../SKILL.md")`
- 模型像“知道有 skills”，但实际没有按 skill 执行

## 影响范围

受影响服务：

- `runtime_service/services/test_case_service`

根因位于公共中间件：

- `runtime_service/middlewares/multimodal/prompting.py`

## 根因分析

这不是 `test_case_service` 的 skills 目录结构问题，也不是 `graph.py` 的 `backend` / `skills=["/skills/"]` 配置错误。

真实根因是 `SkillsMiddleware` 和 `MultimodalMiddleware` 在 `system_message` 表达形式上不兼容：

1. `SkillsMiddleware` 通过 `append_to_system_message(...)` 追加 skills prompt。
2. 追加后的 `SystemMessage` 使用的是 `content_blocks` 结构，而不是单纯的字符串 `content`。
3. `build_multimodal_system_message(...)` 旧实现只读取 `existing.content` 为字符串的情况。
4. 一旦请求链路经过 `MultimodalMiddleware`，前面注入的 skills prompt 会被丢失。
5. 模型最终拿到的 prompt 里看不到 skills 约束，于是直接凭模型先验知识作答。

最小复现思路：

```python
base = SystemMessage(content="BASE")
with_skills = append_to_system_message(base, "SKILLS")
result = build_multimodal_system_message(with_skills, None)
assert result is None  # 旧逻辑下这里会把 skills prompt 吃掉
```

## 修复方案

### 1. 修复公共中间件 prompt 合并逻辑

在 `runtime_service/middlewares/multimodal/prompting.py` 中新增 `_extract_system_message_text(...)`：

- 兼容 `SystemMessage.content` 为字符串
- 兼容 `SystemMessage.content_blocks` 中的文本块
- 在多模态 prompt 合并前先还原完整文本

这样 `MultimodalMiddleware` 不会再抹掉 `SkillsMiddleware` 注入的内容。

### 2. 收紧 test_case_service 的业务提示词

在 `runtime_service/services/test_case_service/prompts.py` 中补充强约束：

- 新任务或新阶段的第一件事必须是 `read_file`
- 在首个 `read_file` 完成前，不允许输出实质性分析内容
- 跨多个阶段的请求必须串行读取多个 skill
- 如果缺少当前阶段应有的 `read_file`，必须停止输出并补读

这一步不是修复根因，而是降低模型“偷懒跳过 skill”的概率，增强行为稳定性。

## 验证方式

### 离线验证

```bash
cd apps/runtime-service
.venv/bin/python runtime_service/tests/services_test_case_service_skills.py
```

预期结果：

- skills 枚举成功
- `SkillsMiddleware.abefore_agent` 注入成功
- `make_graph` 能正常构建

### 精确测试

```bash
cd apps/runtime-service
.venv/bin/pytest runtime_service/tests/test_multimodal_middleware.py -k "preserves_content_blocks_text or preserves_skills_system_prompt_without_attachments or removes_stale_section" -q
.venv/bin/pytest runtime_service/services/test_case_service/tests/test_smoke.py -q
```

### live 验证

```bash
cd apps/runtime-service
.venv/bin/python runtime_service/tests/services_test_case_service_skills.py --live --model deepseek_chat
```

修复后的关键判断标准：

- 第一阶段先 `read_file("/skills/requirement-analysis/SKILL.md")`
- 当用户要求“分析需求并制定测试策略”时，后续继续 `read_file("/skills/test-strategy/SKILL.md")`
- 工具调用记录中出现 `read_file`
- 回复内容能体现对应 skill 的阶段边界

## 排查 checklist

遇到“skills 不能识别”时，按这个顺序查：

1. 检查 `graph.py` 是否传入了 `backend` 和 `skills=["/skills/"]`
2. 检查 `FilesystemBackend.root_dir` 是否真的指向包含 `skills/` 目录的父目录
3. 运行 `_alist_skills` 或 `services_test_case_service_skills.py`，确认 skills 能被枚举
4. 检查 `SkillsMiddleware.abefore_agent` 是否把 `skills_metadata` 注入进 state
5. 检查请求链路中是否有后续 middleware 改写了 `system_message`
6. 重点核对后续 middleware 是否兼容 `SystemMessage.content_blocks`
7. 最后再看业务 prompt 是否足够强，是否明确要求先 `read_file`

## 结论

这次问题本质上是公共 middleware 的 prompt 合并 bug，导致 `test_case_service` 的 skills prompt 在模型调用前被覆盖掉。`test_case_service` 的架构本身没有根本性错误；修复公共中间件兼容性，再配合更强的业务 prompt 约束后，skills 已能被稳定识别并实际读取。
