import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.minimaxi.com/v1",
    api_key="sk-cp-2yB2VsurvaUSShYQDUCljh4uYRssDae1gECT6_rzqtnyKIub_Y5v2LkvhVvAzbJpS1YR4kg-SIGGI9tUQIZGHK9NwmXiWKYD-DO21oW1p0--mOVrF0zV0UI",
)

SYSTEM_PROMPT = "你是一个智能助手，请根据用户的问题给出回答。"
EXIT_COMMANDS = {"exit", "quit", "q", "退出", "再见"}


def ask_minimax(messages: list) -> str:
    response = client.chat.completions.create(
        model="MiniMax-M2.7",
        messages=messages,
        stream=True,
    )

    reply_parts = []
    print("MiniMax: ", end="", flush=True)
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            print(content, end="", flush=True)
            reply_parts.append(content)
    print()
    return "".join(reply_parts)


def chat_with_minimax():
    print("--- 开始与 MiniMax 对话（输入 exit / quit / 退出 结束）---")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n--- 对话结束 ---")
            break

        if not user_input:
            continue

        if user_input.lower() in EXIT_COMMANDS:
            print("--- 对话结束 ---")
            break

        messages.append({"role": "user", "content": user_input})

        try:
            reply = ask_minimax(messages)
            messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            messages.pop()
            print(f"\n请求失败，错误信息: {e}")


if __name__ == "__main__":
    chat_with_minimax()
