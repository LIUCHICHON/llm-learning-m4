# -*- coding: utf-8 -*-
"""
交互式对话台 · 自己一行行敲着玩

用法（复制这一行到终端）：
    ~/llm-lab/venv-m4/bin/python AI起步/对话台.py

进去之后：
    你> 中国的首都是哪里？
    AI > 北京

    /模型 qwen3-8b-v4flash:flash    换一个模型
    /温度 1.2                      调温度（0~2）
    /长度 500                      限制回答长度
    /历史                          看聊天记录
    /清空                          清空聊天记录
    /退出                          离开
"""

import json
import urllib.request

OLLAMA = "http://127.0.0.1:11434"

模型 = "qwen2.5:3b-instruct"
温度 = 0.7
最长 = 500
历史 = []


def 问(问题):
    """问一个问题，返回回答文本。"""
    历史.append({"role": "user", "content": 问题})
    payload = {
        "model": 模型,
        "messages": 历史,
        "stream": False,
        "think": False,
        "options": {"temperature": 温度, "num_predict": 最长},
    }
    req = urllib.request.Request(
        f"{OLLAMA}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.loads(r.read().decode("utf-8"))
    回答 = data["message"]["content"]
    历史.append({"role": "assistant", "content": 回答})
    return 回答


def 列出模型():
    try:
        data = json.loads(urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=5).read())
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def 多模型对比(问题, 指定=None):
    """同一个问题，同时问本机所有模型（或指定的几个），看差别。

    问题可以是任何你想问的 —— 不限于示例里的问题。
    指定 = 模型名列表，只对比这几个；不传就对比全部。
    """
    可用 = 列出模型()
    if not 可用:
        print(" 没找到模型")
        return
    if 指定:
        选中 = [m for m in 可用 if m in 指定] or 可用
    else:
        选中 = 可用
    print(f"\n问题：{问题}")
    print(f"参与对比的模型（{len(选中)} 个）：{', '.join(选中)}")
    print("-" * 60)
    for m in 选中:
        try:
            payload = {
                "model": m,
                "messages": [{"role": "user", "content": 问题}],
                "stream": False, "think": False,
                "options": {"temperature": 温度, "num_predict": 150},
            }
            req = urllib.request.Request(
                f"{OLLAMA}/api/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read().decode("utf-8"))
            回答 = data["message"]["content"].strip().replace("\n", " ")
            print(f"\n【{m}】")
            print(f"  {回答[:220]}")
        except Exception as e:
            print(f"\n【{m}】出错了：{str(e)[:80]}")
    print("-" * 60)
    print(" 👆 注意看：不同模型回答的详略和准确度不一样。")
    print("    名字里数字越大 = 参数越多 = 一般越聪明，但也越慢。")


def 帮助():
    print("""
  ────────────────────────────────────────────────
   命令（以 / 开头）
     /模型 <名字>     换一个模型
     /温度 <0~2>     调温度
     /长度 <数字>     限制回答最长多少 token
     /对比 <问题> [模型...]  让模型回答同一个问题，比一比
                       不带参数时用你最近问过的问题
                       带模型名时只对比那几个，例如：
                       /对比 什么是AI qwen2.5:3b-instruct qwen3-8b-v4flash:flash
     /历史            看聊天记录
     /清空            清空聊天记录（模型会忘掉之前说的）
     /退出            离开对话台
  ────────────────────────────────────────────────
  直接输入文字就是提问，回车发送。
  想换模型：/模型 qwen3-8b-v4flash:flash
  想调温度：/温度 1.5
""")


def 主循环():
    global 模型, 温度, 最长
    print("=" * 60)
    print(" 交互式对话台 · 自己敲着玩")
    print("=" * 60)
    可用 = 列出模型()
    if 可用:
        print(f" 本机可用模型：{', '.join(可用)}")
    print(f" 当前模型：{模型}   温度：{温度}")
    print(" 输入 /帮助 看命令，输入 /退出 离开")
    print()

    while True:
        try:
            输入 = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not 输入:
            continue

        if 输入.startswith("/"):
            命令 = 输入[1:].split()
            if not 命令:
                continue
            动作 = 命令[0]
            参数 = 命令[1:]

            if 动作 in ("退出", "quit", "q"):
                print("再见！")
                break
            elif 动作 == "帮助":
                帮助()
            elif 动作 == "模型":
                if 参数:
                    模型 = 参数[0]
                    print(f" 已切换到：{模型}")
                else:
                    print(f" 当前模型：{模型}")
                    print(f" 可选：{', '.join(列出模型())}")
            elif 动作 == "温度":
                if 参数:
                    try:
                        温度 = float(参数[0])
                        print(f" 温度已设为 {温度}")
                    except ValueError:
                        print(" 温度要填数字，比如 /温度 1.2")
                else:
                    print(f" 当前温度：{温度}")
            elif 动作 == "长度":
                if 参数:
                    try:
                        最长 = int(参数[0])
                        print(f" 回答长度上限：{最长}")
                    except ValueError:
                        print(" 长度要填数字，比如 /长度 300")
                else:
                    print(f" 当前长度上限：{最长}")
            elif 动作 == "对比":
                if 参数:
                    # 从末尾剥出模型名，其余整段是问题；问题里有空格也不会被切碎
                    词 = 参数[:]
                    可用 = 列出模型()
                    指定 = []
                    while 词 and 词[-1] in 可用:
                        指定.insert(0, 词.pop())
                    问题 = " ".join(词).strip()
                    if not 问题:
                        print(" 用法：/对比 你的问题 [模型名1 模型名2]")
                        continue
                    多模型对比(问题, 指定 or None)
                else:
                    # 不带参数：用最近问过的问题；没有就交互式问一句
                    最近 = None
                    for i in range(len(历史) - 2, -1, -2):
                        if 历史[i].get("role") == "user":
                            最近 = 历史[i]["content"]
                            break
                    if 最近:
                        print(f" 用你最近问过的问题：{最近}")
                        print(" （想换问题就直接输：/对比 你的问题）")
                        多模型对比(最近)
                    else:
                        try:
                            问题 = input(" 要对比什么问题？> ").strip()
                        except EOFError:
                            问题 = ""
                        if 问题:
                            多模型对比(问题)
                        else:
                            print(" 取消了。用法：/对比 你的问题 [模型名1 模型名2]")
            elif 动作 == "历史":
                if not 历史:
                    print(" （还没有聊天记录）")
                for i in range(0, len(历史), 2):
                    q = 历史[i]["content"][:60]
                    a = 历史[i + 1]["content"][:60] if i + 1 < len(历史) else ""
                    print(f"  {i//2+1}. 你: {q}")
                    print(f"     AI: {a}")
            elif 动作 == "清空":
                历史.clear()
                print(" 已清空聊天记录")
            else:
                print(f" 未知命令 /{动作}，输入 /帮助 看所有命令")
            continue

        # 普通提问
        print("AI> ", end="", flush=True)
        try:
            回答 = 问(输入)
            print(回答)
        except Exception as e:
            print(f"出错了：{e}")
        print()


if __name__ == "__main__":
    主循环()
