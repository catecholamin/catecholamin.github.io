#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
站点自检：图片引用 / 站内链接 / 外链可达性。

为什么需要它：
    站点是静态站，图片一旦路径写错或被删，只有读者会看到一个破图，
    作者这边毫无感知。2026-10 补 alt 时才撞见 5 处坏图，其中 4 处是
    2011 年从 WordPress 粘贴过来的网页地址（返回 text/html，浏览器当图片
    加载必然失败），1 处是 GitHub blob 链接，同样指向网页而不是原始文件。
    这类问题不会自己暴露，只能定期扫。

用法：
    python3 dev/link_audit.py              # 只查本地（图片 + 站内链接），秒出
    python3 dev/link_audit.py --external   # 额外检查外链，慢，需要网络
    python3 dev/link_audit.py --json       # 机器可读输出
    python3 dev/link_audit.py --external --quiet   # 有问题才输出，给 cron 用

退出码：0 干净；1 发现问题。
"""
import glob
import json
import os
import re
import sys
from urllib.parse import unquote, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
MD_IMG = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HTML_IMG = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.I)
HTML_A = re.compile(r"<a[^>]+href=[\"']([^\"']+)[\"']", re.I)
MD_LINK = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
COVER = re.compile(r"^cover:\s*[\"']?([^\s\"']+)", re.M)

HTML_EXTS = (".html", ".htm")
IMG_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp")


def local_path(url):
    """把站内绝对路径 /images/x.jpg 映射到仓库里的真实文件。"""
    if not url:
        return None
    u = unquote(url.split("#")[0].split("?")[0])
    if not u.startswith("/"):
        return None
    return os.path.join(ROOT, u.lstrip("/"))


def is_site_internal(url):
    if not url:
        return False
    if url.startswith(("http://", "https://", "//", "mailto:", "tel:", "#", "javascript:")):
        return False
    return True


def scan():
    """返回 (图片问题, 站内链接问题, 外链清单)。"""
    img_problems, link_problems = [], []
    externals = {}          # url -> {"image": bool, "link": bool}
    seen_external = set()

    files = []
    for pat in ("_posts/*.md", "*.html", "_layouts/*.html", "_includes/*.html"):
        files.extend(glob.glob(os.path.join(ROOT, pat)))

    for path in files:
        rel = os.path.relpath(path, ROOT)
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue

        # front matter 里的 cover
        fm = FM_RE.match(text)
        if fm:
            for c in COVER.findall(fm.group(1)):
                if is_site_internal(c):
                    lp = local_path(c)
                    if lp and not os.path.exists(lp):
                        img_problems.append((rel, c, "front matter cover 指向的文件不存在"))

        refs = []
        refs += [(u, "markdown 图片") for u in MD_IMG.findall(text)]
        refs += [(u, "html img") for u in HTML_IMG.findall(text)]

        for url, kind in refs:
            if url.startswith(("http://", "https://", "//")):
                rec = externals.setdefault(url, {"image": False, "link": False})
                rec["image"] = True
                continue
            if not is_site_internal(url):
                continue
            if "{{" in url or "{%" in url:
                continue  # Liquid 模板变量
            lp = local_path(url)
            if lp is None:
                continue
            if not os.path.exists(lp):
                img_problems.append((rel, url, "%s 指向的文件不存在" % kind))

        # 站内 a 链接 + markdown 链接
        links = [u for u in HTML_A.findall(text)]
        links += [u for _, u in MD_LINK.findall(text)]
        for url in links:
            if url.startswith(("http://", "https://", "//")):
                rec = externals.setdefault(url, {"image": False, "link": False})
                rec["link"] = True
                continue
            if not is_site_internal(url):
                continue
            if "{{" in url or "{%" in url:
                continue  # Liquid 模板变量，构建时才成形，静态扫不了
            if url.endswith(IMG_EXTS):
                continue  # 图片已在上一轮查过
            lp = local_path(url)
            if lp is None:
                continue
            # /path.html 可能对应仓库里的 path.html
            if os.path.exists(lp):
                continue
            # 也可能对应 _posts 里生成的文章：/2026/10/18/week.html
            if url.endswith(".html"):
                slug = os.path.basename(url)[:-5]
                cand = glob.glob(os.path.join(ROOT, "_posts", "*%s.md" % slug))
                if cand:
                    continue
                # 时区跳转页是构建时生成的，仓库里可能没有实体文件，放过
                if re.match(r"^/\d{4}/\d{2}/\d{2}/", url):
                    continue
            link_problems.append((rel, url, "站内链接无法映射到文件"))

    # 去重
    img_problems = sorted(set(img_problems))
    link_problems = sorted(set(link_problems))
    return img_problems, link_problems, externals


def check_external(urls, timeout=15):
    """并行检查外链可达性；只报告明确的坏状态。"""
    import concurrent.futures
    import subprocess

    def probe(u):
        target = u if u.startswith(("http://", "https://")) else "https:" + u
        try:
            out = subprocess.run(
                ["curl", "-sL", "-o", "/dev/null", "-w", "%{http_code} %{content_type}",
                 "--max-time", str(timeout), target],
                capture_output=True, text=True, timeout=timeout + 6,
            ).stdout.strip().split(" ", 1)
            code = out[0] if out else "000"
            ctype = out[1] if len(out) > 1 else ""
            return u, code, ctype
        except Exception:
            return u, "000", ""

    bad = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for u, code, ctype in ex.map(probe, urls):
            meta = urls[u] if isinstance(urls, dict) else {}
            if code == "000" or code.startswith(("4", "5")):
                bad.append((u, code, "外链不可达"))
                continue
            # 关键一条：在 ![alt](url) 里用的地址，不管结尾长什么样，
            # 只要返回的不是 image/* 就是坏图。2011 年那 4 处坏图就是
            # 粘贴了 WordPress 文章页地址，返回 text/html，末尾没有扩展名。
            if meta.get("image") and ctype and not ctype.startswith("image/"):
                bad.append((u, code, "被当图片引用，实际返回 %s" % ctype))
    return bad


def main():
    as_json = "--json" in sys.argv
    do_external = "--external" in sys.argv
    quiet = "--quiet" in sys.argv       # 只在发现问题时输出，给 cron 用

    img_problems, link_problems, externals = scan()
    ext_bad = check_external(externals) if do_external else []
    ext_count = len(externals) if do_external else 0

    report = {
        "images": [{"file": f, "ref": r, "why": w} for f, r, w in img_problems],
        "links": [{"file": f, "ref": r, "why": w} for f, r, w in link_problems],
        "external_checked": ext_count,
        "external_bad": [{"url": u, "code": c, "why": w} for u, c, w in ext_bad],
    }

    if quiet:
        # cron 模式：干净就一个字都不输出（cron 不会推空消息）
        lines = []
        for f, r, w in img_problems:
            lines.append("坏图：%s -> %s (%s)" % (f, r, w))
        for f, r, w in link_problems:
            lines.append("坏链：%s -> %s (%s)" % (f, r, w))
        for u, c, w in ext_bad:
            lines.append("外链：%s [%s] %s" % (u, c, w))
        if lines:
            print("博客自检发现 %d 个问题：" % len(lines))
            print("\n".join(lines[:40]))
            if len(lines) > 40:
                print("... 另有 %d 条" % (len(lines) - 40))
    elif as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("=== 图片引用 ===")
        if img_problems:
            for f, r, w in img_problems:
                print("  ✗ %s\n      %s  (%s)" % (f, r, w))
        else:
            print("  ✓ 全部本地图片都存在")

        print("\n=== 站内链接 ===")
        if link_problems:
            for f, r, w in link_problems:
                print("  ✗ %s\n      %s  (%s)" % (f, r, w))
        else:
            print("  ✓ 全部站内链接可映射")

        if do_external:
            print("\n=== 外链（检查了 %d 条）===" % ext_count)
            if ext_bad:
                for u, c, w in ext_bad:
                    print("  ✗ [%s] %s  (%s)" % (c, u, w))
            else:
                print("  ✓ 全部可达")
        else:
            print("\n外链 %d 条未检查（加 --external 开启）" % len(externals))

    total = len(img_problems) + len(link_problems) + len(ext_bad)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
