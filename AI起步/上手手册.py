# -*- coding: utf-8 -*-
'''
上手实验 · 三条亲手验证的路径

这个脚本会一步步带你走，每一步都真的执行、真的看到结果。
不是给你看代码，是让你亲手看到 AI 在工作。

用法: 在上课.sh 里输入「上手」，或直接运行本文件
'''

import json
import os
import subprocess
import urllib.request

OLLAMA = "http://127.0.0.1:11434"


def 标题(文字):
    print()
    print("=" * 62)
    print(f" {文字}")
    print("=" * 62)


def 小节(文字):
    print()
    print("-" * 62)
    print(f" {文字}")
    print("-" * 62)


def 说明(文字):
    for 行 in 文字.split("\n"):
        print(f"   {行}")


def 等待回车(提示="按回车继续，输入 q 跳过 > "):
    try:
        r = input(f"   {提示}").strip().lower()
    except EOFError:
        return False
    return r != "q"


def 问模型(问题, 模型="qwen2.5:3b-instruct", 温度=0.7, 最长=300):
    payload = {
        "model": 模型,
        "messages": [{"role": "user", "content": 问题}],
        "stream": False, "think": False,
        "options": {"temperature": 温度, "num_predict": 最长},
    }
    req = urllib.request.Request(
        f"{OLLAMA}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode("utf-8"))["message"]["content"]


def 列出模型():
    try:
        data = json.loads(urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=5).read())
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


# ===========================================================================
标题("上手实验 · 三条亲手验证的路径")

说明("""这一课不给你讲概念，而是让你亲手敲、亲眼看。

三条路径，从易到难：
  路径 A  对话台       —— 像聊天一样一行行敲，还能换模型调参数
  路径 B  终端 curl    —— 看清"请求-响应"的完整 JSON
  路径 C  Python 交互  —— 自己写代码，完全掌控

目标：跑完这一课，你能独立验证大模型书里的任何一个案例。""")


# ===========================================================================
# 路径 B（先做这个，因为它最透明）
# ===========================================================================
小节("路径 B · 终端 curl 命令（先看这个，它最透明）")

说明("""【什么是 curl】
  curl 是 Mac 自带的"发网络请求"工具。
  我们用它把一句话发给本机的 AI 引擎，再把回答显示出来。

【下面这条命令做了什么】
  curl -s http://127.0.0.1:11434/api/chat -d '{...}'
    -s              安静模式（不显示进度条）
    http://127.0.0.1:11434/api/chat   本机 AI 引擎的地址和接口
    -d '{...}'      要发过去的数据（JSON 格式）

【现在真的执行一条】
""")

if 等待回车():
    print()
    说明(">>> 执行中...")
    结果 = subprocess.run(
        ["curl", "-s", f"{OLLAMA}/api/chat", "-d", json.dumps({
            "model": "qwen2.5:3b-instruct",
            "messages": [{"role": "user", "content": "中国的首都是哪里？只回答城市名。"}],
            "stream": False, "think": False,
        })],
        capture_output=True, text=True, timeout=120)
    try:
        数据 = json.loads(结果.stdout)
        说明("   模型返回的原始 JSON（截断）：")
        原始 = json.dumps(数据, ensure_ascii=False)
        说明(f"      {原始[:180]}...")
        说明("")
        说明(f"   >>> 答案就在这个字段里：message.content = 「{数据['message']['content']}」")
    except Exception as e:
        说明(f"   ❌ 出错：{e}")

说明("")
说明("""【看懂这个 JSON —— 这是所有大模型 API 的通用套路】

  {
    "model": "qwen2.5:3b-instruct",     ← 用哪个模型
    "messages": [                          ← 对话内容（可以有多轮）
      {"role": "user", "content": "..."}     role: user=你, assistant=AI
    ],
    "stream": false,                       ← true=逐字返回, false=一次性返回
    "think": false,                        ← 关掉"思考过程"（有些模型会先想再答）
    "options": {                           ← 可选参数
      "temperature": 0.7,                  ← 发挥空间 0~2
      "num_predict": 300                   ← 最多生成多少 token
    }
  }

  不管哪家厂商（OpenAI / 通义 / 智谱 / 本地模型），核心都是这个。
  你看懂了这个 JSON，就掌握了调用大模型的基本功。""")


# ===========================================================================
# 路径 A
# ===========================================================================
小节("路径 A · 对话台（自己一行行敲着玩）")

说明(f"""【怎么打开】
  复制这一行到终端，回车：

  ~/llm-lab/venv-m4/bin/python AI起步/对话台.py

【进去之后会看到】
  本机可用模型：{', '.join(列出模型())}
  当前模型：qwen2.5:3b-instruct   温度：0.7

【你可以试试这些命令】
  中国的首都是哪里？              ← 直接打字提问
  /温度 1.5                       ← 调温度
  /模型 qwen3-8b-v4flash:flash    ← 换模型
  /对比 用一句话解释什么是通货膨胀  ← 所有模型回答同一问题，比一比
  /帮助                           ← 看全部命令
  /退出                           ← 离开

【最值得试的是 /对比】
  它会让本机 5 个模型分别回答同一个问题。
  你会亲眼看到：9B/8B 的回答准确详尽，
  0.5B 的可能自相矛盾（这正是"模型越大越强"的直观证据）。""")

if 等待回车("按回车直接在这里试一次 /对比 > "):
    print()
    说明(">>> 让 5 个模型分别回答同一个问题...")
    问题 = "用一句话解释什么是通货膨胀"
    print(f"\n   问题：{问题}\n")
    for m in 列出模型():
        try:
            回答 = 问模型(问题, 模型=m, 最长=150).strip().replace("\n", " ")
            print(f"   【{m}】")
            print(f"     {回答[:200]}")
            print()
        except Exception as e:
            print(f"   【{m}】出错：{str(e)[:60]}\n")
    说明("👆 仔细看每个回答的详略和准确度。")
    说明("   名字里数字越大 = 参数越多 = 一般越聪明，但也越慢。")


# ===========================================================================
# 路径 C
# ===========================================================================
小节("路径 C · Python 交互模式（自己写代码）")

说明("""【为什么值得试】
  路径 A 和 B 都是"发一段固定的东西"。路径 C 让你自己写，
  以后想批量处理 100 个问题、想把结果存文件，都靠它。

【第 1 步】在终端输入（回车后进入 >>> 模式）：
  ~/llm-lab/venv-m4/bin/python -i

【第 2 步】在 >>> 里定义函数（照着抄）：
  import json, urllib.request
  def 问(问题, 模型="qwen2.5:3b-instruct", 温度=0.7):
      d = {"model":模型,"messages":[{"role":"user","content":问题}],"stream":False,"think":False,
           "options":{"temperature":温度,"num_predict":300}}
      r = urllib.request.Request("http://127.0.0.1:11434/api/chat",
          data=json.dumps(d).encode(), headers={"Content-Type":"application/json"})
      return json.loads(urllib.request.urlopen(r,timeout=120).read())["message"]["content"]

【第 3 步】调用：
  问("中国的首都是哪里？只回答城市名。")

【第 4 步】做对照实验（这才是重点）：
  问("用一句话解释什么是通货膨胀", 温度=0.1)
  问("用一句话解释什么是通货膨胀", 温度=1.8)
  问("用一句话解释什么是通货膨胀", 模型="qwen3-8b-v4flash:flash")

【退出】输入 exit() 回车。""")

if 等待回车("按回车在这里直接看温度对照的效果 > "):
    print()
    说明(">>> 同一个问题，三种温度：")
    问题 = "给一个卖潮汕牛肉丸的店起个名字，要有故事感"
    for t in [0.1, 0.7, 1.5]:
        try:
            回答 = 问模型(问题, 温度=t, 最长=120).strip().replace("\n", " ")
            print(f"\n   温度 {t}:")
            print(f"     {回答[:180]}")
        except Exception as e:
            print(f"   ❌ {e}")
    print()
    说明("👆 温度 0.1 保守简短，温度 1.5 奔放发散。这就是'发挥空间'。")


# ===========================================================================
# 案例
# ===========================================================================
小节("三个案例，三条路径都能验证")

说明("""【案例 1】模型是"接话"的（第 1 课的内容）
  在对话台里问：中国的首都是
  注意模型是不是只答"北京"——它往往会接着往下写一整句。
  这证明它不是查答案库，是"接着往下写字"。

【案例 2】温度影响发挥空间（第 4 课的内容）
  用 /对比 或 Python 的 for 循环，固定问题只改温度。
  路径 C 最好用：
      for t in [0.1, 0.7, 1.5]:
          print(t, 问("给奶茶店起个名字", 温度=t))

【案例 3】模型越大越准（第 6 课的内容）
  用 /对比 问一个有深度的问题，
  仔细看 0.5B 的回答有没有逻辑错误（实测它会）。""")


# ===========================================================================
# 收尾
# ===========================================================================
标题("上手清单 · 做完这些你就真懂了")

说明("""  □ 用对话台问了 3 个问题
  □ 用 /温度 调过温度，对比过两次回答
  □ 用 /模型 换过模型
  □ 用 /对比 看过 5 个模型回答同一个问题
  □ 用 curl 敲过一次，看懂了返回的 JSON
  □ 在 Python 交互模式里定义过自己的 问() 函数
  □ 做过一次"只改温度，其它不变"的对照实验

【接下来】
  正式课程入口：
    bash AI起步/上课.sh

  完整的手册在：
    AI起步/《上手实验手册》.md

  电子书（含全部课程讲解）：
    AI起步/《AI起步》零基础教程.html""")
