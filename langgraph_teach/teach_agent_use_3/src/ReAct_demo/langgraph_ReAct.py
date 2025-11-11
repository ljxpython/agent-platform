from langchain.agents import create_agent
from langchain_core.tools import tool
from llms import get_default_model


# 示例工具函数
@tool
def get_weather(city: str) -> str:
    """获取天气信息"""
    if city == "北京":
        return "11°C，晴"
    elif city == "西安":
        return "15°C，多云"
    else:
        return f"未找到城市 '{city}' 的天气信息"


@tool
def get_time() -> str:
    """获取当前时间"""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
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


agent = create_agent(
    model=get_default_model(),
    tools=[get_weather, get_time, calculate],
)

if __name__ == "__main__":
    test_queries = [
        "现在几点了？",
        "几点了",
        "现在时间",
        "你好！",
        "计算 15 * 8 + 23",
        "北京和西安哪个城市更暖和？",
    ]
    for query in test_queries:
        response = agent.invoke({"messages": [{"role": "user", "content": query}]})
        print(f"[查询] {query}")
        print(f"[回复] {response['messages'][-1].content}")
        print("\n" + "=" * 50 + "\n")
