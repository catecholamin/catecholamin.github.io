#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 search-index.json（search.html 前端读的就是根目录这个文件）。

为什么要这个脚本：
    _plugins/search_generator.rb 是 Jekyll 自定义插件，GitHub Pages 的安全模式
    不执行它，所以线上 search-index.json 永远停在最后一次手工生成的时间点。
    本脚本在本地用同样的规则重算，提交进仓库即可。

用法：
    python3 dev/build_search_index.py          # 生成
    python3 dev/build_search_index.py --check  # 只体检不写文件（列出问题）
"""
import glob
import json
import os
import re
import sys
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, "_posts")
OUT = os.path.join(ROOT, "search-index.json")

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
DATE_PREFIX = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})-")


def parse_front_matter(text):
    """极简 YAML 解析：只取我们需要的几个键，避开 PyYAML 依赖。

    引号处理：值外层成对的单/双引号剥掉。
    """
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm_raw, body = m.group(1), text[m.end():]
    data = {}
    for line in fm_raw.splitlines():
        if not line or line.startswith((" ", "\t", "#", "-")):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        # tags: [a, b, c]
        if v.startswith("[") and v.endswith("]"):
            data[k] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
            continue
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
            v = v[1:-1]
        data[k] = v
    return data, body


def slugify(name):
    """复刻 Jekyll 对 :title 的 slugify：非字母数字转 `-`，合并、去首尾。

    实测依据（线上真实 URL）：
        文献通又更新了，这次解决了一个实际问题  -> 文献通又更新了-这次解决了一个实际问题
        Misfortune might be a blessing in disguise -> Misfortune-might-be-a-blessing-in-disguise
    """
    out = re.sub(r"[^\w\u4e00-\u9fff]+", "-", name, flags=re.UNICODE)
    out = out.replace("_", "-")
    return re.sub(r"-+", "-", out).strip("-")


def slugify_keep_amp(name):
    """先保护 `&` 再 slugify，最后还原。

    `&` 在 Jekyll 的 permalink 里是保留的：实测 /2019/07/19/GO&KEGG-problem-solving.html
    与 /2019/09/23/gallbladder-stone&cancer.html 都是 200，替成 `-` 会 404。
    占位符必须是纯字母，否则会被 slugify 一并打散。
    """
    MARK = "AMPMARKERXZ"
    name = name.replace("&", MARK)
    out = slugify(name)
    return out.replace(MARK, "&").replace("-&-", "&")


def post_url(fm, filename):
    """按 permalink /:year/:month/:day/:title.html 拼 URL。

    ⚠️ 时区陷阱（2026-10-22 实测确认）：
        GitHub Pages 构建机是 UTC，Jekyll 用 front matter 里的 date 换算后
        取日期部分做 permalink。`date: 2026-04-16 07:30:00 +0800` 在 UTC 下是
        2026-04-15 23:30，于是线上 URL 变成 /2026/04/15/...，比文件名日期
        早一天。凡 +0800 且时刻在 08:00 之前的文章都中招（实测 4 篇全中）。
        所以这里必须按 UTC 折算，否则索引里的链接一半是 404。
    """
    base = filename[:-3] if filename.endswith(".md") else filename
    raw_date = str(fm.get("date", "")).strip()

    d = None
    dm = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?\s*([+-]\d{2}:?\d{2}|Z)?", raw_date)
    if dm:
        y, mo, dd = int(dm.group(1)), int(dm.group(2)), int(dm.group(3))
        hh = int(dm.group(4) or 0)
        mi = int(dm.group(5) or 0)
        tz = dm.group(7)
        offset = 0
        if tz and tz.upper() != "Z":
            sign = 1 if tz[0] == "+" else -1
            tzs = tz[1:].replace(":", "")
            offset = sign * (int(tzs[:2]) * 60 + int(tzs[2:]))
        try:
            d = datetime.datetime(y, mo, dd, hh, mi) - datetime.timedelta(minutes=offset)
        except ValueError:
            d = None

    m = DATE_PREFIX.match(base)
    if m:
        slug = base[m.end():]
        if d is None:
            d = datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    else:
        slug = base

    if d is None:
        return None, None
    return "/%04d/%02d/%02d/%s.html" % (d.year, d.month, d.day, slugify_keep_amp(slug)), "%04d-%02d-%02d" % (d.year, d.month, d.day)


def excerpt_of(body, n=200):
    txt = re.sub(r"<[^>]+>", " ", body)
    txt = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", txt)      # 图片
    txt = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", txt)    # 链接留文字
    txt = re.sub(r"^[#>*\-+`|]+", " ", txt, flags=re.M)  # markdown 符号
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt[:n]


def build():
    posts, problems = [], []
    for path in glob.glob(os.path.join(POSTS, "*.md")):
        fn = os.path.basename(path)
        text = open(path, encoding="utf-8").read()
        fm, body = parse_front_matter(text)
        if not fm:
            problems.append((fn, "front matter 解析失败"))
            continue
        url, iso_date = post_url(fm, fn)
        if not url:
            problems.append((fn, "无法推断日期（文件名和 front matter 都没有）"))
            continue
        title = str(fm.get("title") or "").strip()
        if not title:
            title = re.sub(r"^\d{4}-\d{1,2}-\d{1,2}-", "", fn[:-3])
            problems.append((fn, "缺 title，已用文件名兜底"))
        tags = fm.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        posts.append({
            "title": title,
            "url": url,
            "date": iso_date,
            "tags": " ".join(tags),
            "excerpt": excerpt_of(body),
        })
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts, problems


def main():
    posts, problems = build()
    check_only = "--check" in sys.argv

    print("解析到 %d 篇（_posts 共 %d 个文件）" % (len(posts), len(glob.glob(os.path.join(POSTS, "*.md")))))
    if posts:
        print("最新日期: %s" % posts[0]["date"])
        print("示例: %s -> %s" % (posts[0]["title"][:30], posts[0]["url"]))
    if problems:
        print("\n需要人工看一眼的 %d 处：" % len(problems))
        for fn, why in problems[:30]:
            print("  %s | %s" % (fn, why))

    if check_only:
        return 0

    old_n, old_max = 0, "-"
    if os.path.exists(OUT):
        try:
            old = json.load(open(OUT, encoding="utf-8"))
            old_n = len(old)
            old_max = max(x["date"] for x in old) if old else "-"
        except Exception:
            pass

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("\n已写入 %s" % OUT)
    print("旧索引: %d 条 / 最新 %s" % (old_n, old_max))
    print("新索引: %d 条 / 最新 %s" % (len(posts), posts[0]["date"] if posts else "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
