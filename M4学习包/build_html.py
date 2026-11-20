# -*- coding: utf-8 -*-
"""把 M4 学习路线 Markdown 转成带目录导航的 HTML（复用书稿样式）。"""
import re, html as ihtml, markdown, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 项目根目录
SRC = f"{BASE}/M4学习包/M4学习路线.md"
OUT = f"{BASE}/M4学习包/M4学习路线.html"

text = open(SRC, encoding="utf-8").read()
md = markdown.Markdown(extensions=["fenced_code", "tables", "toc", "sane_lists"])
body = md.convert(text)
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
    nav_html.append(f'<div class="nav-group"><a class="nav-group-title" href="#{g["i"]}">{ihtml.escape(g["t"])}</a>')
    if g["c"]:
        nav_html.append('<ul class="nav-sub">')
        for c in g["c"]:
            nav_html.append(f'<li><a href="#{c["i"]}">{ihtml.escape(c["t"])}</a></li>')
        nav_html.append('</ul>')
    nav_html.append('</div>')
nav_html = "\n".join(nav_html)

# 裸 URL -> 可点击链接（避开代码块）
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
<title>大模型学习路线 · M4 16GB 定制版</title><style>{css}</style></head><body>
<div id="progress"></div>
<button class="menu-btn" aria-label="目录">☰</button>
<div class="overlay" id="overlay"></div>
<div class="layout">
<aside class="sidebar" id="sidebar"><div class="brand">
<h1>M4 学习路线</h1><p>《动手学大模型》定制版 · 目录</p></div><nav>{nav_html}</nav></aside>
<main class="main">
<header class="hero">
<h1>大模型学习路线</h1>
<p class="sub">《动手学大模型》M4 16GB 定制版</p>
<p class="meta">11 章逐章实测筛选 · 6 章完整跑通 · 2 章简化版 · 3 章仅阅读<br>
所有性能数字均为 Apple M4 Mac mini 16GB 实测结果</p>
<span class="badge">Apple M4 · 16GB 统一内存 · macOS 26.6</span>
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
