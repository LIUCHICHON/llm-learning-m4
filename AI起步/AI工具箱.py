# -*- coding: utf-8 -*-
"""
AI 起步 · 公共工具模块

这个文件是所有课程共用的"工具箱"，你不需要读懂它，
直接用每一课提供的代码就行。

它帮你做三件事：
  1. 找到本机的 Ollama 服务（你的电脑上的 AI 引擎）
  2. 提供一个简单的"问一句"函数
  3. 把英文报错翻译成中文提示
"""

import json
import urllib.request
import urllib.error
import time

# ---------------------------------------------------------------------------
# Ollama 服务地址。ollama 是装在你电脑上的 AI 引擎，默认监听这个端口。
# ---------------------------------------------------------------------------
OLLAMA_HOST = "http://127.0.0.1:11434"

# 你本机已经下载好的中文模型。3B 表示大约 30 亿个参数（我们的大约 1.5GB）。
# 想用更强的模型，把下面这行换成 "qwen3-8b-v4flash:flash"
DEFAULT_MODEL = "qwen2.5:3b-instruct"


# ---------------------------------------------------------------------------
# 函数 1：检查 AI 引擎是否在运行
# ---------------------------------------------------------------------------
def 检查引擎():
    """检查 Ollama 是否在运行，返回 True/False。"""
    try:
        urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=3).read()
        return True
    except Exception:
        return False


def 列出模型():
    """返回本机已下载的模型名字列表。"""
    try:
        data = json.loads(urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=5).read())
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# 函数 2：问模型一句话
# ---------------------------------------------------------------------------
def 问模型(问题, 模型=DEFAULT_MODEL, 温度=0.7, 最长回答=500, 系统提示=None):
    """
    向本机模型提问，返回它的回答（字符串）。

    参数说明：
      问题     : 你想问的话，字符串
      模型     : 用哪个模型，默认 qwen2.5:3b-instruct
      温度     : 0~2。0 最保守，1 最有创意。写代码用 0.2，聊天用 0.7
      最长回答 : 最多生成多少字（token），默认 500
      系统提示: 给模型的身份设定，可以不填
    """
    messages = []
    if 系统提示:
        messages.append({"role": "system", "content": 系统提示})
    messages.append({"role": "user", "content": 问题})

    payload = {
        "model": 模型,
        "messages": messages,
        "stream": False,
        "think": False,   # 关闭思考过程，直接给答案（我们不需要看它想什么）
        "options": {
            "temperature": 温度,
            "num_predict": 最长回答,
        },
    }

    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    return data["message"]["content"]


# ---------------------------------------------------------------------------
# 函数 3：逐字显示（让等待过程看起来不那么空）
# ---------------------------------------------------------------------------
def 逐字显示(问题, 模型=DEFAULT_MODEL, 温度=0.7):
    """像 ChatGPT 那样，一个字一个字地把回答显示出来。"""
    payload = {
        "model": 模型,
        "messages": [{"role": "user", "content": 问题}],
        "stream": True,
        "think": False,
        "options": {"temperature": 温度, "num_predict": 800},
    }
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    print(f"💭 {问题}")
    print("─" * 60)
    with urllib.request.urlopen(req, timeout=300) as resp:
        for line in resp:
            line = line.decode("utf-8").strip()
            if not line:
                continue
            chunk = json.loads(line)
            piece = chunk.get("message", {}).get("content", "")
            if piece:
                print(piece, end="", flush=True)
    print("\n" + "─" * 60)


# ---------------------------------------------------------------------------
# 函数 4：把常见报错翻译成人话
# ---------------------------------------------------------------------------
def 友好报错(错误信息):
    """把英文报错翻译成你能看懂的中文提示。"""
    提示表 = [
        ("Connection refused", "AI 引擎没在运行。请打开'终端'，输入 ollama serve 然后回车。"),
        ("model not found", "模型不在本机。运行 ollama pull qwen2.5:3b-instruct 下载它。"),
        ("OutOfMemory", "内存不够。先关掉一些程序再试。"),
        ("Killed", "内存不够被系统强制关闭了。试试更小的模型 qwen2.5:0.5b。"),
        ("No such file", "文件路径不对。检查一下路径有没有打错。"),
        ("ModuleNotFoundError", "缺少依赖库。运行安装脚本 bash 安装环境.sh"),
        ("timed out", "等太久了。检查网络，或把问题改短一点。"),
    ]
    for 关键词, 建议 in 提示表:
        if 关键词.lower() in str(错误信息).lower():
            return 建议
    return f"未知错误：{错误信息}"


# ---------------------------------------------------------------------------
# 常用打印函数
# ---------------------------------------------------------------------------
def 标题(文字):
    print()
    print("=" * 66)
    print(f" {文字}")
    print("=" * 66)
    print()


def 小节(文字):
    print()
    print("-" * 66)
    print(f" {文字}")
    print("-" * 66)
    print()


def 说明(文字, flush=False):
    """打印一段解释性文字（缩进，便于和命令区分）。"""
    for 行 in 文字.split("\n"):
        print(f"   {行}", flush=flush)


def 等待(秒=1):
    time.sleep(秒)
