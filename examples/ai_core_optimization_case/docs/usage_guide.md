# AI核心框架优化案例使用指南

## 📋 概述

本指南详细介绍如何使用AI核心框架优化案例中的各个组件，包括智能体构建器、配置管理系统和模板管理系统。

## 🚀 快速开始

### 1. 环境准备

确保你在项目根目录下，并且已经安装了所有依赖：

```bash
cd examples/ai_core_optimization_case
```

### 2. 运行演示

```bash
# 运行功能演示
python code/integration_examples/demo.py

# 运行优化服务示例
python code/integration_examples/optimized_service.py

# 运行测试
python tests/test_optimization.py
```

## 🏗️ 智能体构建器使用指南

### 基础用法

```python
from code.ai_core_enhanced import agent_builder, ModelType

# 创建构建器
builder = agent_builder()

# 链式调用设置参数
agent = await (builder
    .name("我的智能体")
    .prompt("你是一个AI助手")
    .model(ModelType.DEEPSEEK)
    .memory("conversation_123")
    .build())
```

### 预设构建器

```python
from code.ai_core_enhanced import PresetAgentBuilder

# 快速创建需求分析师
requirement_agent = await PresetAgentBuilder.requirement_analyst("conv_123").build()

# 快速创建测试用例专家
testcase_agent = await PresetAgentBuilder.testcase_expert("conv_123").build()

# 快速创建UI分析师
ui_agent = await PresetAgentBuilder.ui_analyst("conv_123").build()
```

### 批量配置

```python
# 使用字典批量设置
config = {
    "name": "批量配置智能体",
    "system_message": "你是通过批量配置创建的智能体",
    "model_type": ModelType.DEEPSEEK,
    "conversation_id": "batch_conv"
}

agent = await (agent_builder()
    .config_dict(config)
    .build())
```

### 构建器方法详解

| 方法 | 参数 | 说明 |
|------|------|------|
| `name(name)` | str | 设置智能体名称 |
| `prompt(prompt)` | str | 设置系统提示词 |
| `model(model_type)` | ModelType | 设置模型类型 |
| `memory(conversation_id)` | str | 设置对话内存 |
| `context(auto_context)` | bool | 设置自动上下文 |
| `config_dict(config)` | dict | 批量设置配置 |
| `kwargs(**kwargs)` | dict | 设置额外参数 |
| `build()` | - | 构建智能体 |
| `reset()` | - | 重置构建器 |
| `get_config()` | - | 获取当前配置 |

## ⚙️ 配置管理系统使用指南

### 获取配置

```python
from code.ai_core_enhanced import get_agent_config

# 获取智能体配置
config = get_agent_config("requirement_analysis")
print(f"智能体名称: {config.get('name')}")
print(f"模型类型: {config.get('model_type')}")
```

### 保存配置

```python
from code.ai_core_enhanced import save_agent_config

# 保存新的智能体配置
new_config = {
    "name": "自定义智能体",
    "model_type": "deepseek",
    "system_message": "你是一个自定义的AI助手",
    "auto_memory": True,
    "auto_context": True
}

success = save_agent_config("custom_agent", new_config)
if success:
    print("配置保存成功")
```

### 配置文件格式

智能体配置文件使用YAML格式，存放在`configs/agents/`目录下：

```yaml
# configs/agents/my_agent.yaml
name: "我的智能体"
model_type: "deepseek"
system_message: |
  你是一个专业的AI助手。

  你的任务是：
  1. 理解用户需求
  2. 提供准确回答
  3. 保持友好态度
auto_memory: true
auto_context: true
description: "这是一个自定义的智能体配置"
```

### 配置验证

```python
from code.ai_core_enhanced import ConfigValidator

# 验证配置
config = {
    "name": "测试智能体",
    "system_message": "测试提示词",
    "model_type": "deepseek"
}

is_valid, errors = ConfigValidator.validate_agent_config(config)
if is_valid:
    print("配置有效")
else:
    print(f"配置错误: {errors}")
```

## 📝 模板管理系统使用指南

### 使用模板

```python
from code.ai_core_enhanced import render_template

# 渲染模板
prompt = render_template(
    "requirement_analysis",
    project_background="电商平台",
    analysis_focus="用户体验优化"
)

print(prompt)
```

### 获取模板对象

```python
from code.ai_core_enhanced import get_template

# 获取模板
template = get_template("requirement_analysis")
if template:
    # 查看模板变量
    variables = template.get_variables()
    print(f"模板变量: {variables}")

    # 验证参数
    is_valid, missing = template.validate_variables(
        project_background="测试项目",
        analysis_focus="功能测试"
    )

    if is_valid:
        print("参数完整")
    else:
        print(f"缺失参数: {missing}")
```

### 模板文件格式

模板文件使用纯文本格式，支持`{variable}`格式的参数替换：

```text
# configs/templates/my_template.txt
你是一位专业的{role}，拥有{experience}年的工作经验。

项目背景：{project_background}
工作重点：{focus_area}

你的任务是：
1. 分析{analysis_target}
2. 提供{output_format}格式的结果
3. 确保{quality_requirements}

请基于以上要求开始工作。
```

### 创建自定义模板

```python
from code.ai_core_enhanced import PromptTemplate, get_template_manager

# 创建模板
template_content = """
你是一个{role}，专门负责{task}。

工作要求：
1. {requirement1}
2. {requirement2}
3. {requirement3}

请按照以上要求完成工作。
"""

template = PromptTemplate(template_content, "my_custom_template")

# 添加到管理器
manager = get_template_manager()
manager.add_template("my_custom_template", template)

# 保存到文件
manager.save_template("my_custom_template", template_content)
```

## 🔄 集成使用示例

### 完整的智能体创建流程

```python
from code.ai_core_enhanced import (
    agent_builder,
    get_agent_config,
    render_template,
    ModelType
)

async def create_custom_agent(conversation_id: str,
                            project_info: dict) -> Optional[Any]:
    """创建自定义智能体的完整流程"""

    # 1. 获取基础配置
    base_config = get_agent_config("requirement_analysis")

    # 2. 渲染个性化模板
    system_prompt = render_template(
        "requirement_analysis",
        project_background=project_info.get("background", "通用项目"),
        analysis_focus=project_info.get("focus", "功能分析")
    )

    # 3. 使用构建器创建智能体
    agent = await (agent_builder()
        .name(base_config.get("name", "智能体"))
        .prompt(system_prompt)
        .model(ModelType.DEEPSEEK)
        .memory(conversation_id)
        .build())

    return agent

# 使用示例
project_info = {
    "background": "移动端购物应用",
    "focus": "支付流程安全性"
}

agent = await create_custom_agent("conv_123", project_info)
```

### 批量创建智能体团队

```python
import asyncio

async def create_agent_team(conversation_id: str) -> dict:
    """批量创建智能体团队"""

    # 并行创建多个智能体
    tasks = [
        PresetAgentBuilder.requirement_analyst(conversation_id).build(),
        PresetAgentBuilder.testcase_expert(conversation_id).build(),
        PresetAgentBuilder.ui_analyst(conversation_id).build()
    ]

    # 等待所有智能体创建完成
    agents = await asyncio.gather(*tasks, return_exceptions=True)

    # 组装团队
    team = {}
    agent_names = ["requirement_analyst", "testcase_expert", "ui_analyst"]

    for i, agent in enumerate(agents):
        if not isinstance(agent, Exception) and agent:
            team[agent_names[i]] = agent

    return team

# 使用示例
team = await create_agent_team("conv_123")
print(f"创建了 {len(team)} 个智能体")
```

## 🔧 高级用法

### 自定义预设构建器

```python
class CustomPresetBuilder:
    """自定义预设构建器"""

    @staticmethod
    def data_analyst(conversation_id: str) -> AgentBuilder:
        """数据分析师预设"""
        return (agent_builder()
            .name("数据分析师")
            .prompt("""
你是一位专业的数据分析师，擅长数据挖掘和统计分析。

你的任务是：
1. 分析数据模式和趋势
2. 提供数据洞察和建议
3. 生成可视化报告
4. 确保分析结果的准确性

请提供专业的数据分析服务。
            """.strip())
            .model(ModelType.DEEPSEEK)
            .memory(conversation_id))

# 使用自定义预设
agent = await CustomPresetBuilder.data_analyst("conv_123").build()
```

### 动态配置加载

```python
def load_dynamic_config(agent_type: str, environment: str = "production"):
    """根据环境动态加载配置"""

    config_file = f"configs/agents/{environment}_{agent_type}.yaml"

    if Path(config_file).exists():
        return get_agent_config(f"{environment}_{agent_type}")
    else:
        # 回退到默认配置
        return get_agent_config(agent_type)

# 使用示例
config = load_dynamic_config("requirement_analysis", "development")
```

## 🐛 故障排除

### 常见问题

1. **智能体创建失败**
   - 检查必需参数是否提供（name, system_message）
   - 验证模型类型是否正确
   - 确认API密钥配置正确

2. **配置文件加载失败**
   - 检查配置文件格式是否正确
   - 确认文件路径是否存在
   - 验证YAML语法是否有误

3. **模板渲染失败**
   - 检查模板变量是否完整提供
   - 确认模板文件是否存在
   - 验证变量名是否匹配

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查构建器配置
builder = agent_builder().name("测试").prompt("测试")
print(f"当前配置: {builder.get_config()}")

# 验证模板变量
template = get_template("requirement_analysis")
if template:
    print(f"模板变量: {template.get_variables()}")
```

## 📞 获取帮助

如果遇到问题或需要帮助：

1. 查看错误日志获取详细信息
2. 检查配置文件格式和内容
3. 运行测试脚本验证功能
4. 参考示例代码了解正确用法

---

**最后更新**: 2025-06-23
**版本**: v1.0.0
