#!/usr/bin/env python3
"""微信公众号文章 HTML → 站点文章 JSON 提取器。

用法：把 mp.weixin.qq.com 的文章 HTML 保存后调用：
    python3 wechat_extract.py /tmp/wx1.html  slug  category
"""
import json
import os
import re
import sys
import datetime
from html.parser import HTMLParser

BLOCK = {"p", "h1", "h2", "h3", "h4", "li", "blockquote"}


class Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_content = False
        self.depth = 0
        self.cur_tag = None
        self.cur_buf = []
        self.items = []  # (type, payload)

    def handle_starttag(self, tag, attrs):
        ad = dict(attrs)
        if not self.in_content:
            if tag == "div" and ad.get("id") == "js_content":
                self.in_content = True
                self.depth = 1
            return
        if tag in ("div", "section"):
            self.depth += 1
        if tag in BLOCK:
            self.cur_tag = tag
            self.cur_buf = []
        elif tag == "img":
            src = ad.get("data-src") or ad.get("data-w-src") or ad.get("src") or ""
            if src and not src.startswith("data:image"):
                self.items.append(("img", src))

    def handle_endtag(self, tag):
        if not self.in_content:
            return
        if tag in ("div", "section"):
            self.depth -= 1
            if self.depth <= 0:
                self.in_content = False
        if tag == self.cur_tag:
            text = "".join(self.cur_buf).strip()
            if text:
                typ = "h" if tag.startswith("h") else ("li" if tag == "li" else ("quote" if tag == "blockquote" else "p"))
                self.items.append((typ, text))
            self.cur_tag = None
            self.cur_buf = []

    def handle_data(self, data):
        if self.in_content and self.cur_tag:
            self.cur_buf.append(data)


def meta(html, key, default=""):
    m = re.search(key + r"\s*=\s*['\"](.*?)['\"]", html, re.S)
    return m.group(1).strip() if m else default


def main():
    src, slug, category = sys.argv[1], sys.argv[2], sys.argv[3]
    html = open(src, encoding="utf-8", errors="replace").read()

    title = meta(html, "msg_title")
    if not title:
        m = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]*)"', html)
        title = m.group(1) if m else "未命名"
    ts = meta(html, "ct", "")
    try:
        date = datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d")
    except Exception:
        date = ""
    abstract = meta(html, "msg_desc")
    author = meta(html, "nickname", "")

    ex = Extractor()
    ex.feed(html)
    items = [{"type": t, "text": v} if t != "img" else {"type": "img", "src": v} for t, v in ex.items]

    # 去重相邻相同文本（微信常见重复）
    dedup = []
    for it in items:
        if dedup and it.get("type") == dedup[-1].get("type") and it.get("text") and it.get("text") == dedup[-1].get("text"):
            continue
        dedup.append(it)

    out = {
        "id": slug,
        "title": title,
        "date": date,
        "author": author,
        "excerpt": abstract,
        "items": dedup,
    }
    os.makedirs("articles", exist_ok=True)
    with open(f"articles/{slug}.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"✅ {slug}: {title} | {date} | items={len(dedup)} | imgs={sum(1 for i in dedup if i['type']=='img')}")


if __name__ == "__main__":
    main()
