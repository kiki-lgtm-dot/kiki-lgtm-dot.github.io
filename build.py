#!/usr/bin/env python3
"""kiki 个人博客静态站生成器。

从 articles/*.json（人人都是产品经理文章后台抓取）生成整套静态 HTML。
所有链接用相对路径，可直接双击 index.html 本地预览，也可部署到任意静态托管
（GitHub Pages / Vercel / 自有域名）而无需改 base。

修改 SITE / ARTICLES 后重跑：python3 build.py
"""
import json
import html
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))

# ---------------- 站点信息 ----------------
SITE = {
    "name": "kiki",
    "tagline": "目标是 AGI",
    "bio": "设计 → AI 视频 Agent → 产品经理",
    "intro": [
        "写 AI 产品、行业与思考。",
        "目前在做的方向，是把对 AI 的观察沉淀成可复用的方法。",
    ],
    "location": "北京",
    "github": "https://github.com/kiki-lgtm-dot",
    "woshipm": "https://www.woshipm.com/u/1684835",
    "xiaohongshu": "https://www.xiaohongshu.com/user/profile/5f5466b6000000000100b069",
    "avatar": "assets/images/avatar.jpg",
    "wechat": "回响产品力",
    "wechat_desc": "专注 AI+落地。以立方构建系统，以海螺倾听回响。剥离 AI 概念泡沫，记录产品一线实战、需求洞察与踩坑复盘。",
    "wechat_qr": "assets/images/wechat-qr.jpg",
    "projects": [
        {"name": "喵救星", "desc": "喵咪血液互助信息平台（正在做，后续上传 GitHub）", "url": ""},
        {"name": "云生 Agent 短剧创作平台", "desc": "可本地部署的专属短剧平台（正在做）", "url": ""},
    ],
    "copyright": "kiki · 目标是 AGI",
}

# ---------------- 文章元信息 ----------------
ARTICLES = [
    {
        "id": "6443839",
        "slug": "feishu-doubao-ai-office",
        "title": "飞书和豆包合到一起后，AI 办公开始争夺“下一步”",
        "date": "2026-08-11",
        "category": "产品分析",
        "cover": "assets/images/feishu-doubao.png",
        "tags": ["AI 办公", "企业协作", "飞书", "豆包"],
    },
    {
        "id": "6443822",
        "slug": "pet-medical-ai-triage",
        "title": "宠物医疗 AI 真正的产品，不是“医生”，而是“分诊台”",
        "date": "2026-08-11",
        "category": "产品分析",
        "cover": "assets/images/pet-medical-ai.png",
        "tags": ["AI 应用", "医疗 AI", "产品分析"],
    },
    {
        "id": "6443783",
        "slug": "which-relationships-not-ai",
        "title": "哪些关系，不能交给 AI？",
        "date": "2026-08-10",
        "category": "思考",
        "cover": "assets/images/which-relationships.jpg",
        "tags": ["AI 社交", "Second Me", "深度思考"],
    },
    {
        "id": "xiaoyunque-agent-review",
        "slug": "xiaoyunque-agent-review",
        "title": "小云雀短剧 Agent 产品拆解：小白以上，专业以下",
        "date": "2026-08-17",
        "category": "产品分析",
        "tags": ["短剧", "Agent", "产品拆解"],
    },
    {
        "id": "deepseek-harness-tutorial",
        "slug": "deepseek-harness-tutorial",
        "title": "DeepSeek Harness：保姆式使用教程及自制 Skill 测试全流程",
        "date": "2026-08-14",
        "category": "教程",
        "tags": ["DeepSeek", "Harness", "教程"],
    },
]

# 按日期倒序排序（最新在前）
ARTICLES.sort(key=lambda a: a["date"], reverse=True)

CATEGORIES = {}
YEARS = {}
for a in ARTICLES:
    CATEGORIES[a["category"]] = CATEGORIES.get(a["category"], 0) + 1
    YEARS[a["date"][:4]] = YEARS.get(a["date"][:4], 0) + 1


# ---------------- 内容清理 ----------------
BOILER = re.compile(r"^(本文由 @|题图来自|转载|来源|作者提供)")


def load_article(meta):
    path = os.path.join(ROOT, "articles", meta["id"] + ".json")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    meta["date"] = raw.get("date") or meta.get("date", "")
    abstract = (raw.get("excerpt") or "").strip()
    body, refs, in_refs, seen = [], [], False, False
    for it in raw.get("items", []):
        t = it.get("type")
        if t == "img":
            src = it.get("src", "")
            if src:
                body.append(("img", src))
            continue
        text = (it.get("text") or "").strip()
        if not text:
            continue
        if BOILER.match(text):
            continue
        if not seen and abstract and text.replace(" ", "")[:20] == abstract.replace(" ", "")[:20]:
            seen = True
            continue
        if not in_refs and text in ("主要参考资料", "主要资料", "参考资料"):
            in_refs = True
            continue
        if in_refs:
            refs.append(text)
            continue
        if BOILER.match(text):
            continue
        body.append((t if t in ("h", "quote", "li") else "p", text))
    if not abstract:
        for typ, text in body:
            if typ == "p" and len(text) > 20:
                abstract = text
                break
    return meta, abstract, body, refs


def esc(s):
    return html.escape(s, quote=False)


# ---------------- 扁平插画图标（Lucide 风格，统一 2px 圆头描边） ----------------
_ICON_TPL = '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;">{body}</svg>'

ICONS = {
    "doc": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="13" y2="17"/>',
    "bulb": '<path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.3h6c0-1 .4-1.8 1-2.3A7 7 0 0 0 12 2z"/>',
    "rocket": '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>',
    "search": '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    "chat": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "news": '<path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-4 0V6"/><path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M10 6h8v4h-8z"/>',
    "tag": '<path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/>',
    "archive": '<polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    "pencil": '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>',
    "book": '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
}


def icon(name, size=24):
    return _ICON_TPL.format(size=size, body=ICONS[name])


# ---------------- 顶部统计卡：扁平二维填充插画（Notion 风，无立体） ----------------
_ILL_TPL = '<svg width="{size}" height="{size}" viewBox="0 0 48 48" fill="none" stroke-linejoin="round" stroke-linecap="round">{body}</svg>'

ILLUSTRATIONS = {
    "doc": '<rect x="8" y="5" width="32" height="38" rx="7" fill="#0075DE" stroke="#ffffff" stroke-width="2.5"/><rect x="15" y="15" width="18" height="3.5" rx="1.75" fill="#ffffff"/><rect x="15" y="23" width="18" height="3.5" rx="1.75" fill="#ffffff" opacity="0.8"/><rect x="15" y="31" width="11" height="3.5" rx="1.75" fill="#ffffff" opacity="0.55"/>',
    "bulb": '<path d="M24 4a13 13 0 0 0-7.5 23.4c1.1.9 2 2.1 2 4.6h11c0-2.5.9-3.7 2-4.6A13 13 0 0 0 24 4z" fill="#F64932" stroke="#ffffff" stroke-width="2.5"/><rect x="16" y="36" width="16" height="4" rx="2" fill="#F64932" stroke="#ffffff" stroke-width="2"/><rect x="19" y="43" width="10" height="3.5" rx="1.75" fill="#F64932" stroke="#ffffff" stroke-width="2"/>',
    "rocket": '<path d="M24 4c8 4 10 16 8 26l-8 3.5-8-3.5C14 20 16 8 24 4z" fill="#FFB110" stroke="#ffffff" stroke-width="2.5"/><circle cx="24" cy="15" r="3.5" fill="#ffffff"/><path d="M15 23l-7 11 4.5 2.5 5.5-12z" fill="#FFB110" stroke="#ffffff" stroke-width="2"/><path d="M33 23l7 11-4.5 2.5-5.5-12z" fill="#FFB110" stroke="#ffffff" stroke-width="2"/><path d="M24 31c-1.3 2.2-2.3 4.2-2.8 6.5h5.6C26.3 35.2 25.3 33.2 24 31z" fill="#ffffff"/>',
}


def illustration(name, size=28):
    return _ILL_TPL.format(size=size, body=ILLUSTRATIONS[name])


# ---------------- HTML 片段（rel = 当前页相对根目录的前缀） ----------------
def nav_html(active="", rel="", cta=True):
    items = [
        ("index.html", "首页", "首页"),
        ("blog/index.html", "文章", "文章"),
        ("thought/index.html", "思考", "思考"),
        ("project/index.html", "项目", "项目"),
        ("about/index.html", "关于", "关于"),
    ]
    links = []
    for href, label, key in items:
        cls = "active" if active == key else ""
        links.append(f'<a href="{rel}{href}" class="{cls}">{label}</a>')
    gh_cls = "nav-cta" if cta else ""
    links.append(f'<a href="{SITE["github"]}" target="_blank" rel="noopener" class="{gh_cls}">GitHub ↗</a>')
    return "\n      ".join(links)


def header(active="", rel=""):
    return f'''<header class="site-header">
  <div class="wrap">
    <div class="brand">
      <span class="name">{esc(SITE["name"])}</span>
      <span class="tagline">{esc(SITE["tagline"])}</span>
    </div>
    <nav class="nav">
      {nav_html(active, rel)}
    </nav>
  </div>
</header>'''


def footer(rel=""):
    return f'''<footer class="site-footer">
  <div class="wrap">
    <nav class="footer-links">{nav_html("", rel, cta=False)}</nav>
    <div class="copyright">© {esc(SITE["copyright"])}</div>
  </div>
</footer>'''


def sidebar_html(rel=""):
    recent_li = "\n".join(
        f'<li><a href="{rel}articles/{a["slug"]}.html">{esc(a["title"])}</a></li>'
        for a in ARTICLES[:6]
    )
    cat_li = "\n".join(
        f'<li><a href="{rel}blog/index.html#{c}">{c}<span class="count">{n}</span></a></li>'
        for c, n in CATEGORIES.items()
    )
    year_li = "\n".join(
        f'<li><a href="{rel}blog/index.html#y{y}">{y}<span class="count">{n}</span></a></li>'
        for y, n in sorted(YEARS.items(), reverse=True)
    )
    wechat = ""
    avatar = f'<img src="{rel}{SITE["avatar"]}" alt="头像">' if SITE.get("avatar") else f'<span style="display:flex;align-items:center;justify-content:center;height:100%;font-size:30px;font-weight:700;color:#fff;background:#0078d4;">{esc(SITE["name"][0].upper())}</span>'
    if SITE.get("wechat"):
        qr = f'<div style="width:160px;height:160px;border:1px solid var(--slate-edge);border-radius:12px;overflow:hidden;margin:0 auto 10px;"><img src="{rel}{SITE["wechat_qr"]}" alt="公众号二维码" style="width:100%;height:100%;object-fit:cover;"></div>' if SITE.get("wechat_qr") else ""
        desc = f'<p style="font-size:12px;color:var(--ash);margin:6px 0 0;line-height:1.7;text-align:left;">{esc(SITE["wechat_desc"])}</p>' if SITE.get("wechat_desc") else ""
        wechat = f'''<div class="sblock">
      <h3>{icon("chat", 15)} 微信</h3>
      <div class="box">
        {qr}
        <p style="font-size:14px;font-weight:700;margin:0;color:#fff;">公众号 · {esc(SITE["wechat"])}</p>
        <p style="font-size:12px;color:var(--smoke);margin:2px 0 0;">扫码关注</p>
        {desc}
      </div>
    </div>'''
    return f'''<aside class="sidebar">
    <div class="sblock">
      <h3>{icon("search", 15)} 搜索</h3>
      <div class="search-box"><input type="text" placeholder="搜索文章关键词…" aria-label="搜索"></div>
    </div>
    <div class="sblock profile">
      <div class="box">
        <div class="avatar">{avatar}</div>
        <div class="pname">{esc(SITE["name"])}</div>
        <div class="pdesc">{esc(SITE["bio"])}</div>
      </div>
    </div>
    {wechat}
    <div class="sblock">
      <h3>{icon("news", 15)} 近期文章</h3>
      <ul>{recent_li}</ul>
    </div>
    <div class="sblock">
      <h3>{icon("tag", 15)} 分类</h3>
      <ul>{cat_li}</ul>
    </div>
    <div class="sblock">
      <h3>{icon("archive", 15)} 归档</h3>
      <ul>{year_li}</ul>
    </div>
    <div class="sblock">
      <h3>{icon("link", 15)} 外站</h3>
      <ul>
        <li><a href="{SITE['github']}" target="_blank" rel="noopener">GitHub</a></li>
        <li><a href="{SITE['xiaohongshu']}" target="_blank" rel="noopener">小红书</a></li>
        <li><a href="{SITE['woshipm']}" target="_blank" rel="noopener">人人都是产品经理</a></li>
      </ul>
    </div>
  </aside>'''


def render_body(body, rel="", skip_imgs=None):
    skip_imgs = skip_imgs or set()
    out, i, n = [], 0, len(body)
    while i < n:
        typ, text = body[i]
        if typ == "img":
            if i not in skip_imgs:
                out.append(f'<p style="text-align:center;margin:22px 0;"><img src="{rel}{text}" alt="" style="max-width:100%;height:auto;border-radius:6px;"></p>')
            i += 1
            continue
        if typ == "li":
            items = []
            while i < n and body[i][0] == "li":
                items.append(body[i][1])
                i += 1
            out.append("<ul>" + "".join(f"<li>{esc(t)}</li>" for t in items) + "</ul>")
            continue
        if typ == "h":
            out.append(f"<h2>{esc(text)}</h2>")
        elif typ == "quote":
            out.append(f"<blockquote>{esc(text)}</blockquote>")
        else:
            out.append(f"<p>{esc(text)}</p>")
        i += 1
    return "\n".join(out)


def render_refs(refs):
    if not refs:
        return ""
    li = "".join(f"<li>{esc(r)}</li>" for r in refs)
    return f'<div class="refs"><h2>参考资料</h2><ul>{li}</ul></div>'


def full_page(title, active, content, rel="", head_extra="", body_class=""):
    body_attr = f' class="{body_class}"' if body_class else ""
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · {esc(SITE["name"])}</title>
<link rel="stylesheet" href="{rel}assets/css/style.css">
{head_extra}</head>
<body{body_attr}>
{header(active, rel)}
{content}
{footer(rel)}
</body>
</html>'''


def cat_class(category):
    """分类 → 标签胶囊配色类。产品分析=iris(默认)，思考=ember，教程=ash。"""
    return {"思考": "cat-ember", "教程": "cat-ash"}.get(category, "")


def post_item(a, abstract, rel=""):
    cc = cat_class(a["category"])
    return f'''<div class="post-item">
      <h2 class="ptitle"><a href="{rel}articles/{a["slug"]}.html">{esc(a["title"])}</a></h2>
      <div class="post-meta"><span>{a["date"]}</span><span class="cat-tag {cc}">{a["category"]}</span></div>
      <p class="excerpt">{esc(abstract)}</p>
      <a class="read-more" href="{rel}articles/{a["slug"]}.html">继续读 →</a>
    </div>'''


# ---------------- 页面 ----------------
def build_article_page(meta):
    meta, abstract, body, refs = load_article(meta)
    wordcount = sum(len(t) for typ, t in body if typ != "img")
    # 封面图：显式指定优先；否则用正文第一张图做封面（公众号文章）
    img_idxs = [i for i, (typ, _) in enumerate(body) if typ == "img"]
    if meta.get("cover"):
        cover_src = meta["cover"]
        skip_imgs = set(img_idxs)   # 有显式封面时，正文里的图即同一张 og 图，全部跳过
    elif img_idxs:
        cover_src = body[img_idxs[0]][1]
        skip_imgs = {img_idxs[0]}
    else:
        cover_src = ""
        skip_imgs = set()
    cover = f'<div class="article-cover"><img src="../{cover_src}" alt="{esc(meta["title"])}"></div>' if cover_src else ""
    lead = f'<p class="article-lead">{esc(abstract)}</p>' if (abstract and meta.get("cover")) else ""
    tags = "".join(f'<span class="cat-tag">{esc(t)}</span>' for t in meta.get("tags", []))
    content = f'''<main class="article-page">
  <article>
    <header class="article-head">
      <div class="cat"><a href="../blog/index.html" class="cat-tag {cat_class(meta["category"])}">{meta["category"]}</a></div>
      <h1>{esc(meta["title"])}</h1>
      <div class="meta">{meta["date"]} · 全文约 {wordcount} 字{(" · " + tags) if tags else ""}</div>
    </header>
    {cover}
    {lead}
    <div class="article-body">
{render_body(body, rel="../", skip_imgs=skip_imgs)}
{render_refs(refs)}
    </div>
  </article>
</main>'''
    return full_page(meta["title"], "", content, rel="../", body_class="page-light")


def build_index():
    stats = [
        (str(len(ARTICLES)), "文章", "blog/index.html"),
        (str(CATEGORIES.get("思考", 0)), "思考", "thought/index.html"),
        (str(len(SITE.get("projects", []))), "项目", "project/index.html"),
    ]
    stat_html = "\n".join(
        f'<a class="stat" href="{href}"><span class="stat-ring"><span class="stat-num">{num}</span></span><span class="stat-label">{label}</span></a>'
        for num, label, href in stats
    )
    hero = f'''<section class="hero">
  <div class="aurora-wash" aria-hidden="true"></div>
  <div class="wrap hero-inner">
    <div class="hero-copy">
      <span class="hero-eyebrow"><span class="dot"></span>AI 产品 · 行业观察 · 深度思考</span>
      <h1 class="hero-title">目标是 <span class="grad">AGI</span></h1>
      <p class="hero-lead">写 AI 产品、行业与思考。把对 AI 的观察，沉淀成可复用的方法与工具。</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="blog/index.html">阅读文章 →</a>
        <a class="btn btn-ghost" href="about/index.html">关于我</a>
      </div>
    </div>
    <div class="hero-stats">
      {stat_html}
    </div>
  </div>
</section>'''

    posts = []
    for a in ARTICLES:
        _, abstract, _, _ = load_article(a)
        posts.append(post_item(a, abstract))
    main = f'''<main class="wrap">
    <div class="layout">
      <section>
        <div class="section-meta">
          <h2 class="section-title">{icon("pencil", 18)} 最近在写</h2>
          <a class="more" href="blog/index.html">全部 →</a>
        </div>
        {chr(10).join(posts)}
      </section>
      {sidebar_html()}
    </div>
  </main>'''
    return full_page("首页", "首页", hero + "\n" + main, body_class="page-home")


def build_blog():
    by_year = {}
    for a in ARTICLES:
        by_year.setdefault(a["date"][:4], []).append(a)
    groups = []
    for y in sorted(by_year, reverse=True):
        lis = "\n".join(
            f'<li><span class="date">{a["date"]}</span>'
            f'<a href="../articles/{a["slug"]}.html">{esc(a["title"])}</a>'
            f'<span class="cat">{a["category"]}</span></li>'
            for a in by_year[y]
        )
        groups.append(
            f'<div class="year-group" id="y{y}"><h2>{y} <span class="cnt">{len(by_year[y])} 篇</span></h2>'
            f'<ul>{lis}</ul></div>'
        )
    content = f'''<main class="wrap">
    <div class="page-head">
      <h1>{icon("doc", 24)} 文章</h1>
      <p>共 {len(ARTICLES)} 篇，按时间倒序。</p>
    </div>
    {chr(10).join(groups)}
  </main>'''
    return full_page("文章", "文章", content, rel="../", body_class="page-light")


def build_category(cat, active):
    arts = [a for a in ARTICLES if a["category"] == cat]
    ic = {"思考": "bulb", "产品分析": "doc", "教程": "book"}.get(cat, "info")
    items = []
    for a in arts:
        _, abstract, _, _ = load_article(a)
        items.append(post_item(a, abstract, rel="../"))
    content = f'''<main class="wrap">
    <div class="page-head">
      <h1>{icon(ic, 24)} {cat}</h1>
      <p>共 {len(arts)} 篇。</p>
    </div>
    {chr(10).join(items)}
  </main>'''
    return full_page(cat, active, content, rel="../", body_class="page-light")


def build_project():
    projects = SITE.get("projects", [])
    if projects:
        cards = []
        for p in projects:
            link = f'<a href="{p["url"]}" target="_blank" rel="noopener">' if p.get("url") else "<span>"
            cards.append(
                f'<div class="post-item">{link}<h2 class="ptitle">{esc(p["name"])}</h2></a>'
                f'<p class="excerpt">{esc(p["desc"])}</p></div>'
            )
        body = "\n".join(cards)
    else:
        body = '<p style="color:rgba(5,5,6,0.55)">项目整理中，敬请期待。</p>'
    content = f'''<main class="wrap">
    <div class="page-head">
      <h1>{icon("rocket", 24)} 项目</h1>
      <p>在做的产品与工具。</p>
    </div>
    {body}
  </main>'''
    return full_page("项目", "项目", content, rel="../", body_class="page-light")


def build_about():
    intro = "".join(f"<p>{esc(t)}</p>" for t in SITE["intro"])
    rows = [
        ("所在", SITE["location"]),
        ("写作", "AI 产品、行业观察、深度思考"),
        ("GitHub", f'<a href="{SITE["github"]}" target="_blank" rel="noopener">{SITE["github"]}</a>'),
        ("文章平台", f'<a href="{SITE["woshipm"]}" target="_blank" rel="noopener">{SITE["woshipm"]}</a>'),
    ]
    tr = "".join(f'<li><span class="date">{k}</span><span>{v}</span></li>' for k, v in rows)
    content = f'''<main class="wrap">
    <div class="page-head">
      <h1>{icon("info", 24)} 关于</h1>
      <p>我是 {esc(SITE["name"])}，{esc(SITE["bio"])}</p>
    </div>
    <div class="article-body" style="max-width:720px">
      {intro}
      <ul>{tr}</ul>
    </div>
  </main>'''
    return full_page("关于", "关于", content, rel="../", body_class="page-light")


def main():
    os.makedirs(os.path.join(ROOT, "articles"), exist_ok=True)
    for a in ARTICLES:
        with open(os.path.join(ROOT, "articles", a["slug"] + ".html"), "w", encoding="utf-8") as f:
            f.write(build_article_page(a))
    pages = [
        ("blog", build_blog),
        ("thought", lambda: build_category("思考", "思考")),
        ("project", build_project),
        ("about", build_about),
    ]
    for d, fn in pages:
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
        with open(os.path.join(ROOT, d, "index.html"), "w", encoding="utf-8") as f:
            f.write(fn())
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_index())
    print("✅ 站点生成完成")
    print("   文章:", len(ARTICLES), "篇 | 分类:", CATEGORIES, "| 归档:", YEARS)


if __name__ == "__main__":
    main()
