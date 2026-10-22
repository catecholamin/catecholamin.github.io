#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
给「时区修正」前生成的旧 URL 补静态跳转页。

背景：
    2026-10-22 之前在 _config.yml 里没有 timezone，GitHub Pages 用 UTC 构建，
    permalink 按 UTC 取日期；`date: 2026-04-16 07:30:00 +0800` 于是变成
    /2026/04/15/...。当天设了 `timezone: Asia/Shanghai`，87 篇文章的 URL
    回到本地日期，旧 URL 会 404。GitHub Pages 没有服务端 301，只能生成
    带 canonical + meta refresh 的静态跳转页。

用法：
    python3 dev/gen_redirects.py            # 生成/更新跳转页
    python3 dev/gen_redirects.py --dry-run  # 只看会影响哪些，不写文件

生成物：<repo>/YYYY/MM/DD/<slug>.html，无 front matter，Jekyll 当静态文件原样复制。
"""
import glob
import os
import re
import sys
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "dev"))
from build_search_index import parse_front_matter, slugify_keep_amp  # noqa: E402

SITE = "https://catecholamin.github.io"
DATE_PREFIX = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})-")

# 加 front matter 是为了让 jekyll-sitemap 跳过这些跳转页（它会收录所有 .html page，
# 不加的话 15 个跳转页会混进 sitemap，稀释抓取预算）。跳转页正文里没有 Liquid
# 语法（只有百分号编码的 URL），所以 layout: null 不会被模板解析破坏。
TPL = """---
layout: null
sitemap: false
---
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex,follow">
<meta http-equiv="refresh" content="0; url=__NEW__">
<link rel="canonical" href="__NEW_ABS__">
<title>页面已迁移</title>
<script>location.replace(__NEW_JS__);</script>
</head>
<body>
<p>这篇文章换了新地址，正在跳转。没反应就点这里：<a href="__NEW__">__NEW__</a></p>
</body>
</html>
"""


def quote_path(path):
    """把 /2026/04/15/中文.html 编成浏览器安全的百分号形式，保留 / 与 & 。"""
    from urllib.parse import quote
    return quote(path, safe="/&")


def split_url_path(path):
    """URL 路径 -> (YYYY, MM, DD, filename)"""
    m = re.match(r"^/(\d{4})/(\d{2})/(\d{2})/(.+)$", path)
    return m.groups() if m else None


def compute(fn, fm):
    raw = str(fm.get("date", "")).strip()
    m = re.match(
        r"(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?\s*([+-]\d{2}:?\d{2}|Z)?",
        raw,
    )
    if not m:
        return None
    y, mo, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
    hh, mi = int(m.group(4) or 0), int(m.group(5) or 0)
    tz = m.group(7)
    offset = 0
    if tz and tz.upper() != "Z":
        sign = 1 if tz[0] == "+" else -1
        tzs = tz[1:].replace(":", "")
        offset = sign * (int(tzs[:2]) * 60 + int(tzs[2:]))

    base = fn[:-3]
    pm = DATE_PREFIX.match(base)
    slug = slugify_keep_amp(base[pm.end():] if pm else base)

    # 无时区的 date（如 `date: 2011-08-25`）Jekyll 按裸日期处理，设不设 timezone
    # 日期都不变，不能偏移；只有显式 +0800 之类的才会在 UTC 构建下漂一天。
    if tz:
        local = datetime.datetime(y, mo, dd, hh, mi) + datetime.timedelta(minutes=-offset + 480)
        utc = datetime.datetime(y, mo, dd, hh, mi) - datetime.timedelta(minutes=offset)
    else:
        local = utc = datetime.datetime(y, mo, dd, hh, mi)

    old = "/%04d/%02d/%02d/%s.html" % (utc.year, utc.month, utc.day, slug)
    new = "/%04d/%02d/%02d/%s.html" % (local.year, local.month, local.day, slug)
    return old, new


def main():
    dry = "--dry-run" in sys.argv
    posts = []
    for path in sorted(glob.glob(os.path.join(ROOT, "_posts", "*.md"))):
        fn = os.path.basename(path)
        fm, _ = parse_front_matter(open(path, encoding="utf-8").read())
        posts.append((fn, fm))

    new_urls = set()
    pairs = []
    for fn, fm in posts:
        r = compute(fn, fm)
        if not r:
            continue
        old, new = r
        new_urls.add(new)
        if old != new:
            pairs.append((fn, old, new))

    # 冲突检测：旧 URL 不能撞上任何现存的新 URL
    clash = [p for p in pairs if p[1] in new_urls]
    if clash:
        print("⚠️ 有 %d 条旧 URL 与现存文章的新 URL 冲突，这些跳过：" % len(clash))
        for fn, old, new in clash:
            print("   ", fn, old)
        pairs = [p for p in pairs if p[1] not in new_urls]

    print("需要跳转的文章：%d 篇" % len(pairs))
    if dry:
        for fn, old, new in pairs:
            print("   %-52s %s -> %s" % (fn, old, new))
        return 0

    written = 0
    for fn, old, new in pairs:
        parts = split_url_path(old)
        if not parts:
            print("  ⚠️ 解析不了旧路径:", old)
            continue
        y, mo, dd, name = parts
        out_dir = os.path.join(ROOT, y, mo, dd)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, name)
        abs_url = SITE + quote_path(new)
        html = TPL.replace("__NEW_ABS__", abs_url)
        html = html.replace("__NEW_JS__", '"' + abs_url + '"')
        html = html.replace("__NEW__", quote_path(new))
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        written += 1

    print("已生成/更新跳转页 %d 个" % written)
    return 0


if __name__ == "__main__":
    sys.exit(main())
