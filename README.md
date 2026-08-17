# kiki 个人博客

静态站，无需框架，可部署到任意静态托管。

## 目录结构

```
├── index.html              # 首页（统计卡 + 最近在写 + 侧栏）
├── blog/index.html         # 博客（按年份归档）
├── thought/index.html      # 思考（分类页）
├── project/index.html      # 项目
├── about/index.html        # 关于
├── articles/*.html         # 文章详情页
├── articles/*.json         # 文章原始数据（来自人人都是产品经理后台）
├── assets/css/style.css    # 样式
├── assets/images/          # 图片
└── build.py                # 站点生成器（从 json 生成 html）
```

## 使用

### 本地预览

```bash
cd 本目录
python3 -m http.server 8000
# 浏览器打开 http://localhost:8000
```

（直接双击 `index.html` 也能看，用的是相对路径。）

### 改内容后重新生成

1. 编辑 `build.py` 顶部的 `SITE`（个人信息）和 `ARTICLES`（文章元信息）
2. 新文章：把 json 放进 `articles/`，在 `ARTICLES` 里加一条
3. 重跑：`python3 build.py`

## 数据来源

文章正文来自人人都是产品经理作者主页：<https://www.woshipm.com/u/1684835>，已抓取存为 `articles/*.json`。
