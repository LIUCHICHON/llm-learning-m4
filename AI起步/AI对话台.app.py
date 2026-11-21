# -*- coding: utf-8 -*-
"""
AI 对话台 · 桌面版（图形界面，双击即用）

不需要终端、不需要敲命令、不需要懂代码。
双击这个文件就会弹出一个窗口。

使用哪个 Python：
  系统自带那个（/usr/bin/python3）就能跑，因为只用标准库 tkinter + urllib。
"""

import json
import os
import sys
import threading
import queue
import urllib.request
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox

# ---- 图形引擎自举 ----
# 系统自带的 Python 用 Tk 8.5，在 macOS 上会画出「窗口在、内容空」的毛病。
# 如果发现图形引擎太老，自动换用新版本 Python 重新启动自己（只重启一次）。
if tk.TkVersion < 8.6 and not os.environ.get("AI_DIRECTOR_REEXEC"):
    _候选 = [
        os.path.expanduser("~/.workbuddy/binaries/python/versions/3.13.12/bin/python3"),
        os.path.expanduser("~/llm-lab/venv-m4/bin/python"),
    ]
    for _py in _候选:
        if os.path.exists(_py) and _py != sys.executable:
            _环境 = dict(os.environ)
            _环境["AI_DIRECTOR_REEXEC"] = "1"
            os.execve(_py, [_py, os.path.abspath(__file__)] + sys.argv[1:], _环境)

OLLAMA = "http://127.0.0.1:11434"

# ---------------------------------------------------------------- 配色
底色 = "#f5f2ea"
纸白 = "#fffdf8"
文字 = "#2f2b26"
强调 = "#8a5a2b"
浅强调 = "#f0e2cf"
输入底 = "#ffffff"
边框 = "#ddd6c6"
占位色 = "#a9a29a"


def 装占位提示(控件, 提示文字):
    """
    给输入框装一个「灰色提示字」。
    - 一开始显示灰字，但它不是真正的内容；
    - 用户一点、一打字、一粘贴，灰字立刻消失；
    - 用户把内容删空，灰字又回来。
    这样从别处复制文字粘贴进来时，不会和旧文字混在一起。
    """
    控件.是占位 = True
    控件.configure(fg=占位色)
    控件.insert("1.0", 提示文字)

    def 清占位(事件=None):
        if getattr(控件, "是占位", False):
            控件.delete("1.0", "end")
            控件.是占位 = False
            控件.configure(fg=文字)

    def 恢复占位(事件=None):
        if not getattr(控件, "是占位", False) and not 控件.get("1.0", "end").strip():
            控件.是占位 = True
            控件.configure(fg=占位色)
            控件.insert("1.0", 提示文字)

    def 取内容():
        if getattr(控件, "是占位", False):
            return ""
        return 控件.get("1.0", "end").strip()

    # 注意：不要绑 FocusIn，否则一聚焦灰字就没了，用户看不到提示
    控件.bind("<ButtonPress>", 清占位, add="+")
    控件.bind("<KeyPress>", 清占位, add="+")
    控件.bind("<FocusOut>", 恢复占位, add="+")
    控件.清占位 = 清占位
    控件.恢复占位 = 恢复占位
    控件.取内容 = 取内容
    return 控件


def 取模型列表():
    """问本机 AI 引擎要一下有哪些模型。"""
    try:
        数据 = json.loads(urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=3).read())
        return [m["name"] for m in 数据.get("models", [])]
    except Exception:
        return []


def 问模型(问题, 模型, 温度, 最长, 历史, 回调):
    """在后台线程里问模型，结果通过回调送回界面。"""
    payload = {
        "model": 模型,
        "messages": 历史 + [{"role": "user", "content": 问题}],
        "stream": False,
        "think": False,
        "options": {"temperature": 温度, "num_predict": 最长},
    }
    try:
        req = urllib.request.Request(
            f"{OLLAMA}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=300) as r:
            数据 = json.loads(r.read().decode("utf-8"))
        回调(数据["message"]["content"], None)
    except Exception as e:
        回调(None, str(e))


class 对话台(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI 对话台")
        self.geometry("980x760")
        self.minsize(760, 560)
        self.configure(bg=底色)
        self.resizable(True, True)

        self.历史 = []
        self.最近问题 = ""
        self.消息队列 = queue.Queue()
        # 右键菜单弹出前，先把用户已经选中的文字记下来。
        # 否则菜单弹出/焦点变化时选区可能被清掉，复制就只能拿到全文。
        self._菜单选区 = {}

        self._建界面()
        self.after(100, self._处理队列)

        # 检查引擎
        self._检测引擎()

    def _检测引擎(self):
        """检查 AI 引擎是否在跑，并据此更新界面。"""
        模 = 取模型列表()
        if 模:
            self.模型框["values"] = 模
            if not self.模型框.get():
                self.模型框.current(0)
            self.发送按钮.configure(state="normal", text="发送  (回车)")
            self.重新按钮.configure(state="disabled", text="✓ 引擎正常")
            self._追加系统("👋 欢迎！下面输入框里打字提问，也可以直接 ⌘V 粘贴。\n"
                          "   灰色的字只是提示，一点就没，不会混进你的问题。\n"
                          "   想让 AI 解释你复制的那段文字？点「解释剪贴板」。\n"
                          "   回车发送；右上角换模型、拖滑块调「发挥空间」。\n"
                          "   输入 /帮助 看本地命令（命令直接在本机执行）。\n"
                          "   想知道模型谁更强？点「五模型对比」。\n")
        else:
            self.发送按钮.configure(state="disabled", text="发送  (回车)")
            self.重新按钮.configure(state="normal", text="重新检测引擎")
            self._追加系统("❌ 找不到本机的 AI 引擎（Ollama）。\n\n"
                          "   【怎么开】\n"
                          "   1. 打开「应用程序」→ 「实用工具」→ 「终端」\n"
                          "   2. 输入 ollama serve 然后按回车\n"
                          "   3. 那个黑窗口保持不关，回来点「重新检测引擎」\n\n"
                          "   （完全不想碰终端？直接在这个 WorkBuddy 对话框里问我也可以。）")

    # ------------------------------------------------------------ 建界面
    def _建界面(self):
        # ---- 顶部标题栏 ----
        顶 = tk.Frame(self, bg=强调, height=64)
        顶.pack(fill="x")
        顶.pack_propagate(False)
        tk.Label(顶, text="AI 对话台", bg=强调, fg="#ffffff",
                 font=("PingFang SC", 20, "bold")).pack(side="left", padx=18, pady=14)
        tk.Label(顶, text="本机运行 · 不联网 · 不花钱", bg=强调, fg="#f0d9c0",
                 font=("PingFang SC", 11)).pack(side="left")

        # ---- 设置区 ----
        设置 = tk.Frame(self, bg=底色)
        设置.pack(fill="x", padx=16, pady=(12, 6))

        tk.Label(设置, text="用哪个模型", bg=底色, fg=文字,
                 font=("PingFang SC", 11)).pack(side="left")
        self.模型框 = ttk.Combobox(设置, state="readonly", width=30,
                                  font=("PingFang SC", 11))
        模 = 取模型列表()
        if 模:
            self.模型框["values"] = 模
            self.模型框.current(0)
        self.模型框.pack(side="left", padx=(6, 18))

        tk.Label(设置, text="发挥空间", bg=底色, fg=文字,
                 font=("PingFang SC", 11)).pack(side="left")
        self.温度值 = tk.DoubleVar(value=0.7)
        self.温度条 = ttk.Scale(设置, from_=0.0, to=1.6, orient="horizontal",
                              variable=self.温度值, length=160,
                              command=self._温度变了)
        self.温度条.pack(side="left", padx=6)
        self.温度标签 = tk.Label(设置, text="0.7", bg=底色, fg=强调,
                                 font=("PingFang SC", 11, "bold"), width=5)
        self.温度标签.pack(side="left")
        tk.Label(设置, text="← 保守      奔放 →", bg=底色, fg="#8a8175",
                 font=("PingFang SC", 9)).pack(side="left", padx=(2, 0))

        self.最长 = tk.IntVar(value=600)

        # ---- 对话区 ----
        对话框 = tk.Frame(self, bg=底色)
        对话框.pack(fill="both", expand=True, padx=16, pady=6)
        self.对话 = scrolledtext.ScrolledText(
            对话框, wrap="word", bg=纸白, fg=文字,
            font=("PingFang SC", 13), relief="flat", bd=0,
            height=16,
            padx=16, pady=14, state="disabled", insertwidth=0)
        self.对话.pack(fill="both", expand=True)
        self._装右键菜单(self.对话, 可粘贴=False)   # 对话记录可以选中复制

        # 对话区平时只读防止误改，但按住鼠标时临时放开，让用户能拖选文字；
        # 选区由 _装右键菜单 里统一的松开记录逻辑保存，这里只管恢复只读。
        def _临时可选(事件):
            if str(self.对话.cget("state")) == "disabled":
                self.对话.configure(state="normal")

        def _恢复只读(事件):
            self.对话.configure(state="disabled")

        self.对话.bind("<ButtonPress-1>", _临时可选, add="+")
        self.对话.bind("<ButtonRelease-1>", _恢复只读, add="+")

        # ---- 输入区 ----
        输入区 = tk.Frame(self, bg=底色)
        输入区.pack(fill="x", padx=16, pady=(6, 14))

        self.输入框 = tk.Text(输入区, height=3, bg=输入底, fg=文字,
                             font=("PingFang SC", 13), relief="solid", bd=1,
                             insertbackground=强调, wrap="word", padx=10, pady=8)
        self.输入框.pack(fill="x")
        装占位提示(self.输入框, "在这里输入问题（可以直接 ⌘V 粘贴）…")
        self.输入框.focus_set()
        self.输入框.bind("<Return>", self._回车发送)
        self.输入框.bind("<Shift-Return>", lambda e: None)
        self._装右键菜单(self.输入框, 可粘贴=True)

        # 复制粘贴专用小按钮行（解决"从别处复制进来"的门槛）
        粘贴行 = tk.Frame(输入区, bg=底色)
        粘贴行.pack(fill="x", pady=(6, 0))
        tk.Button(粘贴行, text="📋 粘贴文字", command=self._粘贴到输入框,
                  bg=纸白, fg=强调, font=("PingFang SC", 10),
                  padx=10, pady=3, relief="solid", bd=1,
                  cursor="hand2").pack(side="left")
        tk.Button(粘贴行, text="🔍 解释剪贴板内容", command=self._解释剪贴板,
                  bg=浅强调, fg=强调, font=("PingFang SC", 10),
                  padx=10, pady=3, relief="solid", bd=1,
                  cursor="hand2").pack(side="left", padx=6)
        tk.Button(粘贴行, text="📄 复制全部对话", command=self._复制对话,
                  bg=纸白, fg=强调, font=("PingFang SC", 10),
                  padx=10, pady=3, relief="solid", bd=1,
                  cursor="hand2").pack(side="left")
        tk.Label(粘贴行, text="复制来的文字先点「粘贴文字」，再按发送",
                 bg=底色, fg="#8a8175", font=("PingFang SC", 9)).pack(side="left", padx=10)

        按钮行 = tk.Frame(输入区, bg=底色)
        按钮行.pack(fill="x", pady=(8, 0))

        self.发送按钮 = tk.Button(按钮行, text="发送  (回车)", command=self._发送,
                                bg=强调, fg="#ffffff", font=("PingFang SC", 12, "bold"),
                                padx=22, pady=6, relief="flat", cursor="hand2")
        self.发送按钮.pack(side="left")

        self.重新按钮 = tk.Button(按钮行, text="重新检测引擎", command=self._检测引擎,
                                bg="#c9c2b4", fg=文字, font=("PingFang SC", 11),
                                padx=14, pady=5, relief="flat", cursor="hand2",
                                state="disabled")
        self.重新按钮.pack(side="left", padx=(0, 8))

        tk.Button(按钮行, text="清空对话", command=self._清空,
                 bg=浅强调, fg=强调, font=("PingFang SC", 11),
                 padx=14, pady=5, relief="flat", cursor="hand2").pack(side="left", padx=8)

        tk.Button(按钮行, text="五模型对比", command=self._对比,
                 bg="#8a8175", fg="#ffffff", font=("PingFang SC", 11),
                 padx=14, pady=5, relief="flat", cursor="hand2").pack(side="left")

        tk.Button(按钮行, text="退出", command=self.destroy,
                 bg="#c9c2b4", fg=文字, font=("PingFang SC", 11),
                 padx=14, pady=5, relief="flat", cursor="hand2").pack(side="right")

        tk.Label(按钮行, text="提示：Enter 发送，Shift+Enter 换行",
                 bg=底色, fg="#8a8175", font=("PingFang SC", 9)).pack(side="right", padx=10)

    # ------------------------------------------------------------ 辅助
    def _温度变了(self, 值):
        self.温度标签.configure(text=f"{float(值):.1f}")

    def _追加(self, 文本, 颜色=None):
        self.对话.configure(state="normal")
        if 颜色:
            self.对话.tag_configure("标", foreground=颜色)
            self.对话.insert("end", 文本, "标")
        else:
            self.对话.insert("end", 文本)
        self.对话.insert("end", "\n\n")
        self.对话.see("end")
        self.对话.configure(state="disabled")

    def _追加系统(self, 文本):
        self._追加(文本, "#8a8175")

    def _追加你(self, 文本):
        self._追加("你：" + 文本, 强调)

    def _追加AI(self, 文本):
        self._追加("AI：" + 文本, "#1f6b4f")

    # ------------------------------------------------------------ 复制粘贴
    def _装右键菜单(self, 控件, 可粘贴=False):
        """macOS 里右键也能粘贴 / 复制 / 全选，不必死记快捷键。"""
        菜单 = tk.Menu(控件, tearoff=0)
        if 可粘贴:
            菜单.add_command(label="粘贴 (⌘V)", command=lambda: self._粘贴到(控件))
        菜单.add_command(label="复制 (⌘C)", command=lambda: self._复制控件内容(控件))
        菜单.add_command(label="全选 (⌘A)", command=lambda: 控件.tag_add("sel", "1.0", "end"))
        if 可粘贴:
            菜单.add_separator()
            菜单.add_command(label="清空输入", command=lambda: self._清空控件(控件))

        def 记选区(事件):
            # 每次左键松开都记下当前拖选的文字；没选中就清掉旧快照
            try:
                sel = 控件.get("sel.first", "sel.last")
            except tk.TclError:
                sel = ""
            if sel.strip():
                self._菜单选区[控件] = sel
            else:
                self._菜单选区.pop(控件, None)

        def 弹出(事件):
            # 右键本身可能清掉选区；只有读到非空选区才更新快照，
            # 否则保留左键松开时记下的那份，避免复制退回全文。
            try:
                sel = 控件.get("sel.first", "sel.last")
                if sel.strip():
                    self._菜单选区[控件] = sel
            except tk.TclError:
                pass
            try:
                菜单.post(事件.x_root, 事件.y_root)
            except Exception:
                pass

        控件.bind("<ButtonRelease-1>", 记选区, add="+")
        控件.bind("<Button-2>", 弹出, add="+")   # macOS 右键
        控件.bind("<Button-3>", 弹出, add="+")   # 部分系统右键

    def _读剪贴板(self):
        try:
            return self.clipboard_get().strip()
        except Exception:
            return ""

    def _写到剪贴板(self, 文本):
        self.clipboard_clear()
        self.clipboard_append(文本)
        self.update_idletasks()

    def _清空控件(self, 控件):
        控件.delete("1.0", "end")
        if hasattr(控件, "恢复占位"):
            控件.恢复占位()

    def _粘贴到(self, 控件):
        内容 = self._读剪贴板()
        if not 内容:
            messagebox.showinfo(
                "剪贴板是空的",
                "请先在网页、微信、PDF 里选中文字并复制，再回来点这个按钮。")
            return
        if hasattr(控件, "清占位"):
            控件.清占位()
        控件.delete("1.0", "end")
        控件.insert("1.0", 内容)
        控件.focus_set()

    def _粘贴到输入框(self):
        self._粘贴到(self.输入框)

    def _复制控件内容(self, 控件):
        # 用户拖选了哪段就复制哪段；只有没选中时才复制整个控件
        选中 = self._菜单选区.get(控件)
        if 选中 is None:
            try:
                选中 = 控件.get("sel.first", "sel.last")
            except tk.TclError:
                选中 = ""
        选中 = (选中 or "").strip()
        内容 = 选中 if 选中 else 控件.get("1.0", "end").strip()
        if 内容:
            self._写到剪贴板(内容)

    def _解释剪贴板(self):
        """把复制来的文字交给模型，用大白话解释一遍。"""
        内容 = self._读剪贴板()
        if not 内容:
            messagebox.showinfo(
                "剪贴板是空的",
                "请先复制一段你想弄懂的文字，再回来点「解释剪贴板内容」。")
            return
        # 先放进输入框，让用户看见到底解释的是什么
        self.输入框.清占位()
        self.输入框.delete("1.0", "end")
        self.输入框.insert("1.0", 内容)
        self._发送(f"请解释下面这段内容，用大白话说清楚它是什么意思：\n{内容}")

    def _复制对话(self):
        内容 = self.对话.get("1.0", "end").strip()
        if not 内容:
            return
        self._写到剪贴板(内容)
        self._追加系统("已把全部对话复制到剪贴板，可以粘到笔记里。")

    # ------------------------------------------------------------ 本地命令
    def _命令帮助文本(self):
        return (
            "命令（以 / 开头，全部在本机执行，不会发给 AI）：\n"
            "  /帮助                    显示这段说明\n"
            "  /模型 <名字>              换模型；不带名字就列出可用模型\n"
            "  /温度 <0~2>              调「发挥空间」；不带数字显示当前值\n"
            "  /长度 <数字>              限制回答长度，比如 /长度 300\n"
            "  /对比 <问题> [模型名...]   让几个模型回答同一个问题\n"
            "                           例：/对比 潮汕卤水要哪些材料\n"
            "  /历史                    看最近的聊天\n"
            "  /清空                    清空聊天记录\n"
            "  /退出                    关闭对话台\n"
            "\n"
            "直接输入文字就是提问。复制来的文字点「📋 粘贴文字」。\n"
            "看不懂复制的内容，点「🔍 解释剪贴板内容」。"
        )

    def _处理命令(self, 原文):
        """所有 / 开头的输入都留在本地处理，绝不送给模型。"""
        段 = 原文[1:].strip().split(None, 1)
        动作 = 段[0] if 段 else ""
        参数 = 段[1].strip() if len(段) > 1 else ""

        if 动作 in ("帮助", "help", "?"):
            self._追加系统(self._命令帮助文本())

        elif 动作 in ("退出", "quit", "q"):
            self._追加系统("再见！")
            self.after(400, self.destroy)

        elif 动作 in ("模型", "model"):
            if 参数:
                名字 = 参数.split()[0]
                可用 = 取模型列表()
                if 可用 and 名字 not in 可用:
                    self._追加系统(f"没找到模型「{名字}」。可选：{', '.join(可用)}")
                else:
                    self.模型框["values"] = 可用 or [名字]
                    self.模型框.set(名字)
                    self._追加系统(f"已切换到：{名字}")
            else:
                self._追加系统(f"当前模型：{self.模型框.get()}\n可选：{', '.join(取模型列表())}")

        elif 动作 in ("温度", "temp"):
            if 参数:
                try:
                    值 = float(参数.split()[0])
                    if not 0 <= 值 <= 2:
                        raise ValueError
                    self.温度值.set(值)
                    self.温度标签.configure(text=f"{值:.1f}")
                    self._追加系统(f"温度已设为 {值:.1f}（0 保守，2 奔放）")
                except ValueError:
                    self._追加系统("温度要填 0~2 的数字，比如 /温度 1.2")
            else:
                self._追加系统(f"当前温度：{self.温度值.get():.1f}\n（也可以拖右上角滑块）")

        elif 动作 in ("长度", "length"):
            if 参数:
                try:
                    值 = int(参数.split()[0])
                    if 值 < 1:
                        raise ValueError
                    self.最长.set(值)
                    self._追加系统(f"回答长度上限：{值}")
                except ValueError:
                    self._追加系统("长度要填正整数，比如 /长度 300")
            else:
                self._追加系统(f"当前回答长度上限：{self.最长.get()}")

        elif 动作 in ("对比", "compare"):
            可用 = 取模型列表()
            if 参数:
                # 从末尾剥出模型名，其余整段当作问题，避免把问题按空格切碎
                词 = 参数.split()
                选中 = []
                while 词 and 词[-1] in 可用:
                    选中.insert(0, 词.pop())
                问题 = " ".join(词).strip()
                if not 问题:
                    self._追加系统("用法：/对比 你的问题 [模型名1 模型名2]")
                    return
                self._跑对比(问题, 选中 or 可用, round(self.温度值.get(), 2))
            else:
                self._弹对比窗口(可用 or ["qwen2.5:3b-instruct"])

        elif 动作 in ("历史", "history"):
            段列表 = [p for p in self.对话.get("1.0", "end").split("\n\n")
                    if p.startswith("你：") or p.startswith("AI：")]
            if 段列表:
                self._追加系统("最近的对话：\n" + "\n".join("  " + p for p in 段列表[-10:]))
            else:
                self._追加系统("（还没有聊天记录）")

        elif 动作 in ("清空", "clear"):
            self._清空()

        else:
            self._追加系统(f"不认识命令 /{动作}。输入 /帮助 看可用命令。"
                           f"\n如果你本来就想问这句话，把斜杠去掉再发一次。")

    # ------------------------------------------------------------ 交互
    def _回车发送(self, 事件):
        self._发送()
        return "break"

    def _发送(self, 问题覆盖=None):
        问题 = (问题覆盖 or self.输入框.取内容()).strip()
        if not 问题:
            return
        # 发送后清空输入框，并把灰色提示放回去（不是写死一句话）
        self.输入框.delete("1.0", "end")
        self.输入框.恢复占位()

        # 斜杠命令留在本地执行，不发给模型
        if 问题.startswith("/"):
            self._追加你(问题)
            self._处理命令(问题)
            return

        模型 = self.模型框.get() or (取模型列表() or ["qwen2.5:3b-instruct"])[0]
        温度 = round(self.温度值.get(), 2)

        self._追加你(问题)
        self.最近问题 = 问题          # 记住，方便对比时预填
        self.发送按钮.configure(state="disabled", text="思考中…")

        def 完成(回答, 错误):
            self.消息队列.put(("完成", 回答, 错误))

        线程 = threading.Thread(
            target=问模型,
            args=(问题, 模型, 温度, self.最长.get(), list(self.历史), 完成),
            daemon=True)
        线程.start()

    def _清空(self):
        self.历史.clear()
        self.对话.configure(state="normal")
        self.对话.delete("1.0", "end")
        self.对话.configure(state="disabled")
        self._追加系统("已清空。对话台接下来会忘掉之前说过的话。")

    def _对比(self):
        """弹出对比对话框：自由输入问题 + 勾选要对比哪些模型。"""
        全部 = 取模型列表()
        if not 全部:
            self._追加系统("找不到模型列表，请点「重新检测引擎」。")
            return
        self._弹对比窗口(全部)

    def _弹对比窗口(self, 全部):
        """对比设置窗口。"""
        窗口 = tk.Toplevel(self)
        窗口.title("模型对比")
        窗口.geometry("620x540")
        窗口.configure(bg=底色)
        窗口.transient(self)

        tk.Label(窗口, text="模型对比", bg=底色, fg=强调,
                 font=("PingFang SC", 17, "bold")).pack(pady=(18, 4))
        tk.Label(窗口, text="在下面输入你想对比的问题，每个模型会各答一遍",
                 bg=底色, fg="#8a8175",
                 font=("PingFang SC", 11)).pack()

        # ---- 问题输入框 ----
        问题框 = tk.Text(窗口, height=4, bg=输入底, fg=文字,
                        font=("PingFang SC", 13), relief="solid", bd=1,
                        insertbackground=强调, wrap="word", padx=10, pady=8)
        问题框.pack(fill="x", padx=24, pady=(14, 4))
        最近 = self._最近问题()
        占位文字 = (f"输入要对比的问题（可直接 ⌘V 粘贴）…\n"
                   f"留空则对比你最近问过的：{最近}") if 最近 else "输入要对比的问题（可直接 ⌘V 粘贴）…"
        装占位提示(问题框, 占位文字)
        问题框.focus_set()
        问题框.bind("<Return>", lambda e: 窗口.focus_set())
        self._装右键菜单(问题框, 可粘贴=True)

        tk.Button(窗口, text="📋 粘贴剪贴板里的问题",
                  command=lambda: self._粘贴到(问题框),
                  bg=纸白, fg=强调, font=("PingFang SC", 10),
                  padx=10, pady=3, relief="solid", bd=1,
                  cursor="hand2").pack(anchor="w", padx=24)

        # ---- 模型勾选 ----
        勾选区 = tk.Frame(窗口, bg=底色)
        勾选区.pack(fill="x", padx=24, pady=(10, 4))
        tk.Label(勾选区, text="对比哪些模型（勾选要对比的）", bg=底色, fg=文字,
                 font=("PingFang SC", 11, "bold")).pack(anchor="w")

        勾选 = {}
        模型框区 = tk.Frame(勾选区, bg=底色)
        模型框区.pack(fill="x", pady=(6, 0))
        for i, m in enumerate(全部):
            v = tk.BooleanVar(value=True)
            勾选[m] = v
            tk.Checkbutton(模型框区, text=m, variable=v, bg=底色, fg=文字,
                           font=("PingFang SC", 11), selectcolor=纸白,
                           anchor="w", activebackground=底色).grid(
                row=i // 2, column=i % 2, sticky="w", padx=4, pady=3)

        # ---- 温度 ----
        温度行 = tk.Frame(窗口, bg=底色)
        温度行.pack(fill="x", padx=24, pady=(12, 4))
        tk.Label(温度行, text="温度", bg=底色, fg=文字,
                 font=("PingFang SC", 11)).pack(side="left")
        温度值 = tk.DoubleVar(value=self.温度值.get())
        标签 = tk.Label(温度行, text=f"{温度值.get():.1f}", bg=底色, fg=强调,
                      font=("PingFang SC", 11, "bold"), width=5)
        ttk.Scale(温度行, from_=0.0, to=1.6, orient="horizontal",
                  variable=温度值, length=200,
                  command=lambda v: 标签.configure(text=f"{float(v):.1f}")
                  ).pack(side="left", padx=8)
        tk.Label(温度行, text="（跟主窗口一致，也可以这里单独调）", bg=底色,
                 fg="#8a8175", font=("PingFang SC", 9)).pack(side="left")

        # ---- 按钮 ----
        按钮区 = tk.Frame(窗口, bg=底色)
        按钮区.pack(fill="x", padx=24, pady=(18, 24))

        def 开始():
            问题 = 问题框.取内容().strip()
            # 用户没输入（只看到灰字）时，才退回最近问过的问题
            if not 问题:
                问题 = self._最近问题() or "用一句话解释什么是通货膨胀"
            if not 问题:
                tk.messagebox.showwarning("问题为空", "请先输入要对比的问题。")
                return
            选中 = [m for m in 全部 if 勾选[m].get()]
            if not 选中:
                tk.messagebox.showwarning("没选模型", "至少勾选一个模型。")
                return
            窗口.destroy()
            self._跑对比(问题, 选中, round(温度值.get(), 2))

        tk.Button(按钮区, text="开始对比", command=开始, bg=强调, fg="#ffffff",
                 font=("PingFang SC", 12, "bold"), padx=24, pady=7,
                 relief="flat", cursor="hand2").pack(side="left")
        tk.Button(按钮区, text="取消", command=窗口.destroy, bg="#c9c2b4",
                 fg=文字, font=("PingFang SC", 12), padx=20, pady=7,
                 relief="flat", cursor="hand2").pack(side="left", padx=8)

    def _跑对比(self, 问题, 选中, 温度):
        """真正执行对比。"""
        self._追加系统(f"让 {len(选中)} 个模型分别回答：{问题}"
                       f"（温度 {温度}）")
        self.发送按钮.configure(state="disabled", text="对比中…")

        def 完成(索引, 回答, 错误):
            self.消息队列.put(("对比一条", 索引, 选中[索引], 回答, 错误))

        def 跑一个(索引):
            if 索引 >= len(选中):
                self.消息队列.put(("对比完", None, None, None, None))
                return

            def 内部(回答, 错误):
                完成(索引, 回答, 错误)
                跑一个(索引 + 1)

            threading.Thread(
                target=问模型,
                args=(问题, 选中[索引], 温度, 400, [], 内部),
                daemon=True).start()

        threading.Thread(target=跑一个, args=(0,), daemon=True).start()

    def _最近问题(self):
        """取最近一次问过的问题（发送后输入框会被清空，所以要另记一份）。"""
        if self.最近问题:
            return self.最近问题
        段 = [p for p in self.对话.get("1.0", "end").split("\n\n")
              if p.startswith("你：")]
        return 段[-1][2:].strip() if 段 else ""

    # ------------------------------------------------------------ 后台消息
    def _处理队列(self):
        try:
            while True:
                消息 = self.消息队列.get_nowait()
                if 消息[0] == "完成":
                    _, 回答, 错误 = 消息
                    if 回答:
                        self.历史.append({"role": "user", "content": self._最后你()})
                        self.历史.append({"role": "assistant", "content": 回答})
                        self._追加AI(回答)
                    else:
                        self._追加系统(f"❌ 出错了：{错误}\n   可能是 AI 引擎没开（终端里跑 ollama serve）。")
                    self.发送按钮.configure(state="normal", text="发送  (回车)")
                elif 消息[0] == "对比一条":
                    _, 索引, 名字, 回答, 错误 = 消息
                    if 回答:
                        self._追加(f"【{名字}】\n{回答.strip()}", "#1f6b4f")
                    else:
                        self._追加(f"【{名字}】出错了：{错误}", "#c04a2f")
                elif 消息[0] == "对比完":
                    self.发送按钮.configure(state="normal", text="发送  (回车)")
                    self._追加系统("👆 注意看差别：名字里数字越大的模型，回答通常越准确。")
        except queue.Empty:
            pass
        self.after(100, self._处理队列)

    def _最后你(self):
        # 从对话区找最后一条"你："的消息
        内容 = self.对话.get("1.0", "end")
        段 = [p for p in 内容.split("\n\n") if p.startswith("你：")]
        return 段[-1][2:].strip() if 段 else ""


if __name__ == "__main__":
    应用 = 对话台()
    应用.mainloop()
