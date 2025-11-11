# ReAct Demo 说明文档

## 什么是 ReAct

ReAct (Reasoning and Acting) 是一种让大语言模型能够进行**推理(Reasoning)**和**行动(Acting)**的框架。它通过交替进行思考、行动和观察的循环，使AI能够解决复杂问题。

## ReAct 的核心思想

ReAct 模拟人类的思考过程：
- **思考 (Thought)**: 分析当前情况，制定计划
- **行动 (Action)**: 执行具体操作（如调用工具）
- **观察 (Observation)**: 获取行动结果，调整策略

## 本目录文件说明

### `langgraph_ReAct.py`
使用 LangGraph 框架实现的 ReAct 代理，包含以下功能：
- 天气查询工具
- 时间获取工具
- 数学计算工具

### `react_demo.py` / `react_demo_final.py`
基础的 ReAct 实现示例，展示了 ReAct 的核心逻辑。

## ReAct 工作流程

```
用户输入 → 模型思考 → 决定行动 → 执行工具 → 观察结果 → 继续思考 → 最终回答
```

## 使用示例

运行 `langgraph_ReAct.py` 可以看到：
- 查询当前时间
- 计算数学表达式
- 比较城市天气

ReAct 代理会自动判断是否需要调用工具，并组合多个工具的结果来回答复杂问题。
