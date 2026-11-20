# -*- coding: utf-8 -*-
"""生成《AI 起步》电子书（HTML），包含学习手册 + 八课完整教学正文。"""
import re
import os
import glob
import html as ihtml
import markdown

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 项目根目录
SRC = f"{BASE}/AI起步/《AI起步》学习手册.md"
BODY = f"{BASE}/AI起步/_课程正文.md"
OUT = f"{BASE}/AI起步/《AI起步》零基础教程.html"

# ---------- 第一步：从课程脚本提取教学正文 ----------
def 提取教学文本(源码):
    块 = []
    模式 = re.compile(r"说明\(('''|\"\"\")(.*?)\1", re.S)
    for m in 模式.finditer(源码):
        块.append(m.group(2).replace("\\n", "\n").replace("\\'", "'"))
    return 块


def 提取课名(源码):
    m = re.search(r"标题\(\s*'(第 \d+ 课 · [^']+)'", 源码)
    if m:
        return m.group(1)
    m = re.search(r"^# 第 (\d+) 课 · (.+)$", 源码, re.M)
    if m:
        return f"第 {m.group(1)} 课 · {m.group(2).strip()}"
    m = re.search(r"标题\(\s*'(自由提问[^']*)'", 源码)
    if m:
        return "第 0 课 · " + m.group(1)
    return None


md = []
for i in [0] + list(range(1, 8)):
    匹配 = glob.glob(f"{BASE}/AI起步/第{i}课_*.py")
    if not 匹配:
        continue
    路径 = 匹配[0]
    源码 = open(路径, encoding="utf-8").read()
    课名 = 提取课名(源码) or f"第 {i} 课"
    md.append(f"\n# {课名}\n")
    md.append(f"> 脚本：`{os.path.basename(路径)}`\n")
    for b in 提取教学文本(源码):
        b = b.strip()
        if b:
            md.append(b)
            md.append("")

正文 = "\n".join(md)
open(BODY, "w", encoding="utf-8").write(正文)

手册 = open(SRC, encoding="utf-8").read()
上手 = open(f"{BASE}/AI起步/《上手实验手册》.md", encoding="utf-8").read()
手册 = 手册.rstrip() + "\n\n---\n\n" + 上手.strip()

# 合并：手册在前，七课正文在后
合并 = 手册.rstrip() + "\n\n---\n\n" + 正文.lstrip()

md = markdown.Markdown(extensions=["fenced_code", "tables", "toc", "sane_lists"])
body = md.convert(合并)
tokens = md.toc_tokens


def clean(s):
    return re.sub(r"<[^>]+>", "", s)


nav = []
for t in tokens:
    kids = [{"t": clean(c["name"]), "i": c["id"]}
            for c in t.get("children", []) if c["level"] == 2]
    nav.append({"t": clean(t["name"]), "i": t["id"], "c": kids})

nav_html = []
for g in nav:
    nav_html.append(
        f'<div class="nav-group"><a class="nav-group-title" href="#{g["i"]}">{ihtml.escape(g["t"])}</a>')
    if g["c"]:
        nav_html.append('<ul class="nav-sub">')
        for c in g["c"]:
            nav_html.append(f'<li><a href="#{c["i"]}">{ihtml.escape(c["t"])}</a></li>')
        nav_html.append('</ul>')
    nav_html.append('</div>')
nav_html = "\n".join(nav_html)

# 裸 URL 转链接（避开代码块）
pres = []


def hold(m):
    pres.append(m.group(0))
    return f"\x00P{len(pres)-1}\x00"


body = re.sub(r"<pre>.*?</pre>", hold, body, flags=re.S)
body = re.sub(
    r'(?<![\w/"=\-])(https?://[^\s<>"\'\x00）)，。、；]+\w)',
    lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener">{m.group(1)}</a>',
    body)
for i, p in enumerate(pres):
    body = body.replace(f"\x00P{i}\x00", p)

# 复用书稿样式
src = open(f"{BASE}/书稿/build_book.py", encoding="utf-8").read()
css = re.search(r'CSS = r"""(.*?)"""', src, re.S).group(1)
js = re.search(r'JS = r"""(.*?)"""', src, re.S).group(1)

doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>《AI 起步》零基础大模型教程</title><style>{css}</style></head><body>
<div id="progress"></div>
<button class="menu-btn" aria-label="目录">☰</button>
<div class="overlay" id="overlay"></div>
<div class="layout">
<aside class="sidebar" id="sidebar"><div class="brand">
<h1>AI 起步</h1><p>零基础大模型教程 · 目录</p></div><nav>{nav_html}</nav></aside>
<main class="main">
<header class="hero">
<h1>AI 起步</h1>
<p class="sub">零基础大模型教程 · 七课学会</p>
<p class="meta">面向完全没接触过 AI 的成年人 · 不需要会编程<br>
所有实验在 Apple M4 Mac mini 16GB 上实测跑通</p>
<span class="badge">第1课 大模型是什么 → 第7课 水印</span>
</header>
<article class="content">
{body}
</article></main></div>
<button id="toTop" title="回到顶部">↑</button>
<script>{js}</script></body></html>"""

open(OUT, "w", encoding="utf-8").write(doc)

ids = set(re.findall(r'id="([^"]+)"', doc))
anch = set(re.findall(r'href="#([^"]+)"', doc))
print("生成:", OUT, len(doc), "字节")
print("目录组:", len(nav), "| 条目:", sum(len(g["c"]) for g in nav))
print("失效锚点:", (anch - ids) or "无")
print("外链:", doc.count('href="http'), "| 代码块:", doc.count("<pre>"),
      "| 表格:", doc.count("<table>"))
