# -*- coding: utf-8 -*-
"""把精读书稿 Markdown 转成带目录导航的单文件 HTML 电子书（纯本地，无 CDN 依赖）。"""
import re, os
import html as ihtml
import markdown

BASE = os.path.dirname(os.path.abspath(__file__))   # 书稿目录
SRC = os.path.join(BASE, "动手学大模型-精读本.md")
OUT = os.path.join(BASE, "动手学大模型-精读本.html")

with open(SRC, encoding="utf-8") as f:
    text = f.read()

md = markdown.Markdown(extensions=["fenced_code", "tables", "toc", "sane_lists"])
body = md.convert(text)
tokens = md.toc_tokens

# 目录：markdown 的 toc_tokens 是嵌套结构——顶层为 level 1（编/卷首/附录），
# 其 children 为 level 2（章）。跳过第一个顶层标题（书名，已在封面显示）。
def clean(s):
    return re.sub(r"<[^>]+>", "", s)

nav_items = []
for t in tokens[1:]:  # 跳过书名
    group = {"title": clean(t["name"]), "id": t["id"], "children": []}
    for c in t.get("children", []):
        if c["level"] == 2:
            group["children"].append({"title": clean(c["name"]), "id": c["id"]})
    nav_items.append(group)

nav_html = []
for item in nav_items:
    nav_html.append(f'<div class="nav-group"><a class="nav-group-title" href="#{item["id"]}">{ihtml.escape(item["title"])}</a>')
    if item["children"]:
        nav_html.append('<ul class="nav-sub">')
        for c in item["children"]:
            nav_html.append(f'<li><a href="#{c["id"]}">{ihtml.escape(c["title"])}</a></li>')
        nav_html.append('</ul>')
    nav_html.append('</div>')
nav_html = "\n".join(nav_html)

# 把裸 URL 转成可点击链接（书稿里的延伸阅读多为直接贴出的网址）。
# 用占位法避开 <pre>...</pre> 代码块，避免把代码里的网址也包成链接。
pres = []
def _hold_pre(m):
    pres.append(m.group(0))
    return f"\x00PRE{len(pres)-1}\x00"
body = re.sub(r"<pre>.*?</pre>", _hold_pre, body, flags=re.S)

url_re = re.compile(r'(?<![\w/"=\-])(https?://[^\s<>"\'\x00）)，。、；]+\w)')
def _linkify(m):
    u = m.group(1)
    return f'<a href="{u}" target="_blank" rel="noopener">{u}</a>'
body = url_re.sub(_linkify, body)

for i, p in enumerate(pres):
    body = body.replace(f"\x00PRE{i}\x00", p)

# 给正文图片加轻量样式类
body = body.replace("<img ", '<img loading="lazy" ')

CSS = r"""
:root{
  --bg:#f7f5ef; --paper:#fffdf8; --ink:#2f2b26; --ink-soft:#5c554a;
  --line:#e5dfd2; --accent:#8a5a2b; --accent-soft:#f0e2cf;
  --code-bg:#282622; --code-ink:#e8e2d5; --nav-bg:#efebe1;
  --mark:#c0452f;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  background:var(--bg);color:var(--ink);line-height:1.85;font-size:16.5px;-webkit-font-smoothing:antialiased}
.layout{display:flex;min-height:100vh}

/* 侧边栏 */
.sidebar{position:fixed;top:0;left:0;width:300px;height:100vh;background:var(--nav-bg);
  border-right:1px solid var(--line);overflow-y:auto;padding:26px 0 40px;z-index:10}
.sidebar .brand{padding:0 24px 18px;border-bottom:1px solid var(--line);margin-bottom:12px}
.sidebar .brand h1{font-size:19px;margin:0 0 4px;color:var(--accent);letter-spacing:.5px}
.sidebar .brand p{margin:0;font-size:12px;color:var(--ink-soft)}
.nav-group{padding:6px 0}
.nav-group-title{display:block;padding:6px 24px;font-weight:700;font-size:14px;color:var(--accent);
  text-decoration:none;border-left:3px solid transparent}
.nav-group-title:hover{background:var(--accent-soft)}
.nav-sub{list-style:none;margin:2px 0 6px;padding:0}
.nav-sub li a{display:block;padding:5px 24px 5px 34px;font-size:13.5px;color:var(--ink-soft);
  text-decoration:none;border-left:3px solid transparent;transition:.15s}
.nav-sub li a:hover{background:var(--accent-soft);color:var(--ink)}
.nav-sub li a.active{border-left-color:var(--mark);color:var(--mark);font-weight:600;background:var(--paper)}

/* 内容区 */
.main{margin-left:300px;flex:1;min-width:0}
.hero{background:linear-gradient(135deg,#7c4a20 0%,#a9672f 55%,#c98b4b 100%);color:#fff;
  padding:76px 40px 66px;text-align:center;position:relative;overflow:hidden}
.hero::after{content:"";position:absolute;inset:0;background:
  radial-gradient(circle at 15% 20%,rgba(255,255,255,.12),transparent 40%),
  radial-gradient(circle at 85% 80%,rgba(255,255,255,.1),transparent 45%)}
.hero *{position:relative;z-index:1}
.hero h1{font-size:40px;margin:0 0 14px;letter-spacing:2px;font-weight:800}
.hero .sub{font-size:17px;opacity:.95;margin:0 0 20px}
.hero .meta{font-size:13px;opacity:.8;max-width:720px;margin:0 auto;line-height:1.9}
.hero .badge{display:inline-block;margin-top:22px;padding:7px 18px;border:1px solid rgba(255,255,255,.5);
  border-radius:30px;font-size:12.5px;letter-spacing:.5px}

.content{max-width:860px;margin:0 auto;padding:44px 40px 100px}
.content h1{font-size:29px;color:var(--accent);border-bottom:2px solid var(--accent-soft);
  padding-bottom:12px;margin:58px 0 26px;letter-spacing:.5px}
.content h1:first-child{margin-top:10px}
.content h2{font-size:23px;color:#6d3f1c;margin:44px 0 18px;padding-left:14px;
  border-left:5px solid var(--accent);scroll-margin-top:20px}
.content h3{font-size:18.5px;color:#4a3c2c;margin:32px 0 12px;scroll-margin-top:20px}
.content h4{font-size:16px;color:var(--ink-soft);margin:22px 0 10px}
.content p{margin:14px 0;text-align:justify}
.content a{color:var(--accent);text-decoration:underline;text-underline-offset:3px;word-break:break-all}
.content strong{color:#7a3f16}
.content hr{border:0;border-top:1px dashed var(--line);margin:44px 0}

/* 引用（导读） */
blockquote{margin:20px 0;padding:14px 20px;background:var(--accent-soft);
  border-left:4px solid var(--accent);border-radius:0 8px 8px 0;color:#6b4a2a;font-style:italic}
blockquote p{margin:4px 0}

/* 代码 */
pre{background:var(--code-bg);color:var(--code-ink);padding:18px 20px;border-radius:10px;
  overflow-x:auto;font-size:13.5px;line-height:1.65;box-shadow:0 3px 12px rgba(0,0,0,.12);margin:18px 0}
pre code{font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;background:none;padding:0}
:not(pre)>code{background:#efe9dd;color:#8a3b1e;padding:2px 6px;border-radius:5px;font-size:.88em;
  font-family:"SFMono-Regular",Consolas,monospace}

/* 表格 */
table{border-collapse:collapse;width:100%;margin:20px 0;font-size:14.5px;background:var(--paper);
  box-shadow:0 1px 6px rgba(0,0,0,.05);border-radius:8px;overflow:hidden}
th,td{border:1px solid var(--line);padding:10px 13px;text-align:left;vertical-align:top}
th{background:#efe6d6;color:#6d3f1c;font-weight:700;white-space:nowrap}
tr:nth-child(even) td{background:#fbf8f1}

/* 图片 */
img{max-width:100%;height:auto;display:block;margin:22px auto;border-radius:8px;
  box-shadow:0 4px 18px rgba(0,0,0,.12);border:1px solid var(--line)}

/* 回到顶部 */
#toTop{position:fixed;right:26px;bottom:28px;width:46px;height:46px;border-radius:50%;
  background:var(--accent);color:#fff;border:none;font-size:20px;cursor:pointer;
  box-shadow:0 4px 14px rgba(0,0,0,.22);opacity:0;pointer-events:none;transition:.25s;z-index:20}
#toTop.show{opacity:1;pointer-events:auto}
#toTop:hover{background:#6d3f1c}

/* 进度条 */
#progress{position:fixed;top:0;left:300px;height:3px;background:var(--mark);z-index:30;width:0;transition:width .1s}

/* 响应式 */
@media(max-width:900px){
  .sidebar{transform:translateX(-100%);transition:.25s;box-shadow:4px 0 20px rgba(0,0,0,.15)}
  .sidebar.open{transform:translateX(0)}
  .main{margin-left:0}
  #progress{left:0}
  .menu-btn{display:block!important}
  .hero h1{font-size:30px}
  .content{padding:30px 20px 80px}
}
.menu-btn{display:none;position:fixed;top:16px;left:16px;z-index:40;width:42px;height:42px;
  border-radius:10px;background:var(--accent);color:#fff;border:none;font-size:20px;cursor:pointer;
  box-shadow:0 3px 12px rgba(0,0,0,.2)}
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:5}
.overlay.show{display:block}
"""

JS = r"""
const links=[...document.querySelectorAll('.nav-sub li a')];
const heads=links.map(a=>document.getElementById(a.getAttribute('href').slice(1))).filter(Boolean);
const toTop=document.getElementById('toTop');
const prog=document.getElementById('progress');
const sidebar=document.getElementById('sidebar');
const overlay=document.getElementById('overlay');

function onScroll(){
  const y=window.scrollY+120;
  let cur=null;
  for(const h of heads){ if(h.offsetTop<=y) cur=h; else break; }
  links.forEach(a=>a.classList.toggle('active', cur && a.getAttribute('href')==='#'+cur.id));
  if(cur){ const el=a2li(cur.id); if(el) el.scrollIntoView({block:'nearest'}); }
  const h=document.documentElement.scrollHeight-window.innerHeight;
  prog.style.width=(h>0?(window.scrollY/h*100):0)+'%';
  toTop.classList.toggle('show', window.scrollY>500);
}
function a2li(id){return links.find(a=>a.getAttribute('href')==='#'+id);}
window.addEventListener('scroll',onScroll,{passive:true});
window.addEventListener('load',onScroll);
toTop.onclick=()=>window.scrollTo({top:0,behavior:'smooth'});
// 移动端
window.__toggleNav=(open)=>{sidebar.classList.toggle('open',open);overlay.classList.toggle('show',open);};
document.querySelector('.menu-btn').onclick=()=>window.__toggleNav(true);
overlay.onclick=()=>window.__toggleNav(false);
links.forEach(a=>a.addEventListener('click',()=>{if(window.innerWidth<=900)window.__toggleNav(false);}));
"""

doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>动手学大模型 · 精读本</title>
<style>{CSS}</style>
</head>
<body>
<div id="progress"></div>
<button class="menu-btn" aria-label="目录">☰</button>
<div class="overlay" id="overlay"></div>
<div class="layout">
  <aside class="sidebar" id="sidebar">
    <div class="brand">
      <h1>动手学大模型</h1>
      <p>精读本 · 目录导航</p>
    </div>
    <nav>{nav_html}</nav>
  </aside>
  <main class="main">
    <header class="hero">
      <h1>动手学大模型 · 精读本</h1>
      <p class="sub">一部可以跟着做的中文大模型实践教程</p>
      <p class="meta">整理自上海交通大学《动手学大模型》（Dive into LLMs）开源项目 · 11 章 · 5 编<br>重写为从入门到前沿的阅读路线，补齐概念讲解，删去冗余操作</p>
      <span class="badge">原仓库 github.com/Lordog/dive-into-llms</span>
    </header>
    <article class="content">
{body}
    </article>
  </main>
</div>
<button id="toTop" title="回到顶部">↑</button>
<script>{JS}</script>
</body>
</html>
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(doc)

print("OK ->", OUT)
print("目录分组:", len(nav_items), "| 目录条目:", sum(len(i["children"]) for i in nav_items))
print("HTML 大小:", len(doc), "字节")
