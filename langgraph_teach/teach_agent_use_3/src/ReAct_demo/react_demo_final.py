"""
ReAct框架最终修复版本 - 解决空参数判断问题
"""

import json
import os
import re
import traceback
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


@dataclass
class ToolResult:
    """工具执行结果"""

    success: bool
    data: Any = None
    error: str = None


class ToolRegistry:
    """动态工具注册器"""

    def __init__(self):
        self._tools: Dict[str, Dict] = {}
        self._functions: Dict[str, Callable] = {}

    def register(self, name: str, description: str, parameters: Dict, func: Callable):
        """注册工具"""
        tool_schema = {
            "name": name,
            "description": description,
            "parameters": parameters,
        }
        self._tools[name] = tool_schema
        self._functions[name] = func

    def get_tool_schema(self, name: str) -> Optional[Dict]:
        """获取工具schema"""
        return self._tools.get(name)

    def get_all_tools(self) -> List[Dict]:
        """获取所有工具schema"""
        return list(self._tools.values())

    def execute(self, name: str, params: Dict) -> ToolResult:
        """执行工具"""
        if name not in self._functions:
            return ToolResult(success=False, error=f"工具 '{name}' 未找到")

        try:
            result = self._functions[name](**params)
            return ToolResult(success=True, data=result)
        except Exception as e:
            error_msg = f"工具执行失败: {str(e)}"
            print(f"[错误] {error_msg}")
            print(f"[错误详情] {traceback.format_exc()}")
            return ToolResult(success=False, error=error_msg)


class LLMOutputParser:
    """LLM输出解析器 - 增强健壮性"""

    def __init__(self):
        # 多种可能的正则模式，用于匹配不同格式的输出
        self.patterns = {
            "thought": [
                r"思考[：:]\s*(.*?)(?=\n行动[：:]|\nFinal|\nAction|$)",
                r"Thought[：:]\s*(.*?)(?=\nAction[：:]|\nFinal|$)",
            ],
            "action": [
                r"行动[：:]\s*(\w+)",
                r"Action[：:]\s*(\w+)",
                r"行动\s*[:：]\s*(\w+)",  # 处理空格不一致的情况
                r"Action\s*[:：]\s*(\w+)",
            ],
            "action_input": [
                r"行动输入[：:]\s*({[\s\S]*?})",
                r"Action Input[：:]\s*({[\s\S]*?})",
                r"行动输入\s*[:：]\s*({[\s\S]*?})",  # 处理空格不一致
                r"Action Input\s*[:：]\s*({[\s\S]*?})",
            ],
            "final_answer": [
                r"最终答案[：:]\s*([\s\S]*)",
                r"Final Answer[：:]\s*([\s\S]*)",
            ],
            # 新增：直接回答的检测模式
            "direct_response": [
                r"^(?!.*(?:思考[：:]|行动[：:]|Action[：:]|Thought[：:])).*",  # 不包含思考/行动关键词
                r"^你好.*",  # 以你好开头
                r"^嗨.*",  # 以嗨开头
                r"^hello.*",  # 英文问候
                r"^hi.*",  # 英文问候
            ],
        }

    def _match_with_patterns(self, text: str, pattern_type: str) -> Optional[str]:
        """使用多种模式尝试匹配"""
        for pattern in self.patterns[pattern_type]:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return (
                    match.group(1).strip() if match.groups() else match.group(0).strip()
                )
        return None

    def parse_thought(self, text: str) -> Optional[str]:
        """解析思考过程"""
        return self._match_with_patterns(text, "thought")

    def parse_action(self, text: str) -> Optional[str]:
        """解析行动（工具名称）"""
        return self._match_with_patterns(text, "action")

    def parse_action_input(self, text: str) -> Optional[Dict]:
        """解析行动输入参数"""
        input_str = self._match_with_patterns(text, "action_input")
        if not input_str:
            return None

        try:
            # 清理JSON字符串（处理可能的格式问题）
            input_str = input_str.strip()
            # 处理中文引号
            input_str = input_str.replace('"', '"').replace('"', '"')
            # 处理多余的空格
            input_str = re.sub(r"\s+", " ", input_str)

            return json.loads(input_str)
        except json.JSONDecodeError as e:
            print(f"[解析错误] JSON解析失败: {e}")
            print(f"[解析错误] 原始字符串: {input_str}")
            return None

    def parse_final_answer(self, text: str) -> Optional[str]:
        """解析最终答案"""
        return self._match_with_patterns(text, "final_answer")

    def is_final_answer(self, text: str) -> bool:
        """判断是否包含最终答案"""
        return self.parse_final_answer(text) is not None

    def is_direct_response(self, text: str) -> bool:
        """判断是否为直接回答（无需工具）"""
        # 检查是否为问候语或直接回答
        for pattern in self.patterns["direct_response"]:
            if re.match(pattern, text.strip(), re.IGNORECASE):
                return True
        return False


class ReActAgent:
    """ReAct智能体"""

    def __init__(self, client: OpenAI, model: str = "deepseek-chat"):
        self.client = client
        self.model = model
        self.tool_registry = ToolRegistry()
        self.parser = LLMOutputParser()
        self.max_iterations = 10

        # 关键修复：改进提示模板，明确告诉模型何时应该结束
        self.prompt_template = """
你运行在一个循环中：思考、行动、行动输入、暂停、观察。
循环结束时输出最终答案。

使用"思考"来描述你对问题的分析过程。
使用"行动"来运行可用的工具。
使用"行动输入"来指定工具的输入参数 - 然后返回"暂停"。
"观察"将是运行工具的结果。

你的可用工具：

{tools}

规则：
1. 如果是问候或告别，直接友好回应，不使用思考-行动循环。
   - 问候包括：你好、嗨、hello、hi、早上好、下午好、晚上好等
   - 告别包括：再见、拜拜、goodbye、bye等
   - 对于这些情况，直接给出友好回应，不要输出"思考"、"行动"等关键词

2. 否则，遵循思考-行动输入循环来找到最佳答案。
3. 如果已有部分或全部答案，使用你的知识而不依赖外部工具。
4. 如需执行多个行动，分别调用。
5. 最后提供明确完整的最终答案。

**重要**：当你已经获得足够信息回答用户问题时，请直接输出"最终答案"，不要继续调用工具！

输出格式必须严格遵循：
思考：你的思考过程
行动：工具名称
行动输入：{{"参数名": "参数值"}}

PAUSE

现在开始！

新输入：{input}"""

    def register_tool(
        self, name: str, description: str, parameters: Dict, func: Callable
    ):
        """注册工具"""
        self.tool_registry.register(name, description, parameters, func)

    def _build_prompt(self, query: str) -> str:
        """构建提示"""
        tools_json = json.dumps(
            self.tool_registry.get_all_tools(), ensure_ascii=False, indent=2
        )
        return self.prompt_template.format(tools=tools_json, input=query)

    def _call_llm(self, messages: List[Dict]) -> str:
        """调用LLM"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,  # 降低随机性，提高一致性
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[LLM错误] 调用失败: {e}")
            return f"抱歉，LLM调用失败: {str(e)}"

    def _should_stop_iteration(
        self, query: str, iteration: int, response_text: str
    ) -> tuple[bool, str]:
        """
        判断是否应该停止迭代

        Returns:
            (是否应该停止, 停止原因)
        """
        # 1. 检查是否超过最大迭代次数
        if iteration >= self.max_iterations - 1:
            return True, "达到最大迭代次数"

        # 2. 检查是否已经获得最终答案
        if self.parser.is_final_answer(response_text):
            return True, "检测到最终答案"

        # 3. 特殊处理：时间查询类问题，避免无限循环
        time_keywords = ["几点了", "现在时间", "当前时间", "时间", "get_time"]
        if any(keyword in query for keyword in time_keywords) and iteration >= 1:
            # 如果已经调用过一次get_time，就应该给出答案
            if "get_time" in response_text and iteration >= 1:
                return True, "时间查询已获取足够信息"

        # 4. 特殊处理：简单计算问题
        calc_keywords = ["计算", "等于", "多少", "calculate"]
        if any(keyword in query for keyword in calc_keywords) and iteration >= 1:
            if "calculate" in response_text and iteration >= 1:
                return True, "计算问题已获取结果"

        # 5. 检查是否为直接回答
        if self.parser.is_direct_response(response_text):
            return True, "检测到直接回答"

        return False, "需要继续推理"

    def run(self, query: str) -> str:
        """运行ReAct循环"""
        print(f"[用户问题] {query}")

        messages = [{"role": "user", "content": self._build_prompt(query)}]

        for iteration in range(self.max_iterations):
            print(f"\n[第{iteration + 1}轮推理]")

            # 调用LLM
            response_text = self._call_llm(messages)
            print(f"[LLM回复] {response_text}")

            # 检查是否应该停止迭代
            should_stop, reason = self._should_stop_iteration(
                query, iteration, response_text
            )
            if should_stop:
                print(f"[停止推理] {reason}")

                # 提取最终答案或直接回复
                if self.parser.is_final_answer(response_text):
                    final_answer = self.parser.parse_final_answer(response_text)
                    print(f"\n[最终答案] {final_answer}")
                    return final_answer
                else:
                    # 如果不是最终答案格式，但应该停止，直接返回回复
                    print(f"\n[回复] {response_text}")
                    return response_text

            # 解析思考和行动
            thought = self.parser.parse_thought(response_text)
            action = self.parser.parse_action(response_text)
            action_input = self.parser.parse_action_input(response_text)

            print(f"[思考] {thought}")
            print(f"[行动] {action}")
            print(f"[输入] {action_input}")

            # 关键修复：正确处理空参数的情况
            # 原来的错误：if not action or action_input is None:
            # 修复后：只检查None，不检查空值
            if action is None or action_input is None:
                print("[警告] 未解析到行动或行动输入")

                # 如果回复看起来是合理的最终回答，直接返回
                if len(response_text.strip()) > 0:
                    # 检查是否包含明显的最终答案标志
                    if any(
                        keyword in response_text
                        for keyword in ["最终答案", "Final Answer", "答案是", "结果是"]
                    ):
                        print(f"\n[检测到最终答案] {response_text}")
                        return response_text

                    # 如果是知识性问题回答，也直接返回
                    if not any(
                        keyword in response_text
                        for keyword in ["思考", "行动", "Action", "Thought", "PAUSE"]
                    ):
                        print(f"\n[合理回复] {response_text}")
                        return response_text

                # 否则给出默认回复并继续
                messages.append(
                    {
                        "role": "user",
                        "content": "Observation: 抱歉，我无法理解您的请求格式",
                    }
                )
                continue

            # 执行工具
            tool_result = self.tool_registry.execute(action, action_input)

            if tool_result.success:
                observation = f"Observation: {tool_result.data}"
            else:
                observation = f"Observation: 工具执行失败 - {tool_result.error}"

            print(f"[观察] {observation}")
            messages.append({"role": "user", "content": observation})

        return "抱歉，推理轮次过多，无法得到答案"


# 示例工具函数
def get_weather(city: str) -> str:
    """获取天气信息"""
    if city == "北京":
        return "11°C，晴"
    elif city == "西安":
        return "15°C，多云"
    else:
        return f"未找到城市 '{city}' 的天气信息"


def get_time() -> str:
    """获取当前时间"""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate(expression: str) -> str:
    """计算数学表达式"""
    try:
        # 安全的表达式计算
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return "错误：表达式包含非法字符"

        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


if __name__ == "__main__":
    # 初始化客户端
    client = OpenAI(
        api_key=os.environ.get("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com/v1",
    )

    # 创建ReAct智能体
    agent = ReActAgent(client)

    # 动态注册工具
    agent.register_tool(
        name="get_weather",
        description="获取指定城市的天气信息",
        parameters={
            "type": "object",
            "properties": {"city": {"type": "string", "description": "城市名称"}},
            "required": ["city"],
        },
        func=get_weather,
    )

    agent.register_tool(
        name="get_time",
        description="获取当前时间",
        parameters={"type": "object", "properties": {}},
        func=get_time,
    )

    agent.register_tool(
        name="calculate",
        description="计算数学表达式",
        parameters={
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "数学表达式，如 '1+1'"}
            },
            "required": ["expression"],
        },
        func=calculate,
    )

    # 专门测试时间查询问题
    test_queries = [
        "现在几点了？",
        "几点了",
        "现在时间",
        "你好！",
        "计算 15 * 8 + 23",
        "北京和西安哪个城市更暖和？",
    ]

    for query in test_queries:
        print("\n" + "=" * 60)
        result = agent.run(query)
        print("=" * 60)
