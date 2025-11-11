import json
import os

from dotenv import load_dotenv

load_dotenv()
import re

from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1"
)


def send_messages(messages):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
    )
    return response


def get_weather(city):
    if city == "北京":
        return "11"
    elif city == "西安":
        return "15"
    else:
        return "未找到该城市"


tools = [
    {
        "name": "get_weather",
        "description": "使用该工具获取指定城市的气温",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市",
                }
            },
            "required": ["city"],
        },
    },
]

REACT_PROMPT = """
You run in a loop of Thought, Action, Action Input, PAUSE, Observation.
At the end of the loop you output an Answer
use Thought to describe your thoughts about the question you have been asked.
use Action to run one of the actions available to you
use Action Input to indicate the input to the Action- then return PAUSE.
Observation will be the result of running those actions.

Your available actions are:

{tools}

Rules:
1- If the input is a greeting or a goodbye, respond directly in a friendly manner without using the Thought-Action loop.
2- Otherwise, follow the Thought-Action Input loop to find the best answer.
3- If you already have the answer to a part or the entire question, use your knowledge without relying on external actions.
4- If you need to execute more than one Action, do it on separate calls.
5- At the end, provide a final answer.

Some examples:

### 1
Question: 今天北京天气怎么样？
Thought: 我需要调用 get_weather 工具获取天气
Action: get_weather
Action Input: {"city": "北京"}

PAUSE

You will be called again with this:

Observation: 北京的气温是0度.

You then output:
Final Answer: 北京的气温是0度.

Begin!

New input: {input}"""

if __name__ == "__main__":
    query = "请比较北京和西安的气温谁高？"

    prompt = REACT_PROMPT.replace("{tools}", json.dumps(tools)).replace(
        "{input}", query
    )
    messages = [{"role": "user", "content": prompt}]

    while True:
        response = send_messages(messages)
        response_text = response.choices[0].message.content

        print("大模型的回复：")
        print(response_text)

        final_answer_match = re.search(r"Final Answer:\s*(.*)", response_text)
        if final_answer_match:
            final_answer = final_answer_match.group(1)
            print("最终答案:", final_answer)
            break

        messages.append({"role": "assistant", "content": response_text})

        action_match = re.search(r"Action:\s*(\w+)", response_text)
        action_input_match = re.search(
            r'Action Input:\s*({.*?}|".*?")', response_text, re.DOTALL
        )

        if action_match and action_input_match:
            tool_name = action_match.group(1)
            params = json.loads(action_input_match.group(1))

            observation = ""
            if tool_name == "get_weather":
                observation = get_weather(params["city"])
                print("人类的回复：Observation:", observation)

            messages.append({"role": "user", "content": f"Observation: {observation}"})
