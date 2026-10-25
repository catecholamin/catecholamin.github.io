#!/usr/bin/env python3
"""博客访问统计查询 —— Cloudflare Web Analytics GraphQL

用法:
    python3 dev/analytics.py              # 默认最近 7 天概览
    python3 dev/analytics.py 30           # 最近 30 天
    python3 dev/analytics.py 7 paths      # 只看热门页面
    python3 dev/analytics.py 7 referer    # 只看来源
    python3 dev/analytics.py 7 all        # 全部维度

siteTag 映射（2026-10-24 由 Cloudflare 后台确认）:
    3ef33b1271d44172aa6e236c2138d1f0  ->  996196.xyz          （主站）
    6eeecc7aa4704b5bac837601622b8878  ->  catecholamin.github.io
    faa2ebce5e194ce1934cd687d9ad0adb  ->  catecholamin.pages.dev

注意：siteTag 与页面里 data-cf-beacon 的 token 是两个不同的值，
查询只能用 siteTag，token 查不到数据。
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

SECRETS = os.path.expanduser("~/.hermes/secrets.json")
ENDPOINT = "https://api.cloudflare.com/client/v4/graphql"

SITE_TAGS = {
    "3ef33b1271d44172aa6e236c2138d1f0": "996196.xyz",
    "6eeecc7aa4704b5bac837601622b8878": "github.io",
    "faa2ebce5e194ce1934cd687d9ad0adb": "pages.dev",
}


def _creds():
    d = json.load(open(SECRETS, encoding="utf-8"))
    return d["cloudflare_api_token"], d["cloudflare_account_id"]


_PROXY_CACHE = {}


def _proxy_args():
    """返回 curl 的代理参数。WSL2 是 NAT 模式，127.0.0.1 不是 Windows 宿主，
    环境变量里的 http_proxy=127.0.0.1:7890 在 WSL 内永远连不上（0.0001s 就 refused）。
    正确地址是默认网关。探测顺序：网关 → 环境变量（非回环）→ 直连，记住第一个通的。"""
    if "args" in _PROXY_CACHE:
        return _PROXY_CACHE["args"]

    import re
    candidates = []
    # 1) Windows 宿主的代理监听地址（WSL2 下就是默认网关）
    try:
        gw = subprocess.run(["ip", "route"], capture_output=True, text=True, timeout=5).stdout
        m = re.search(r"default via ([\d.]+)", gw)
        if m:
            candidates.append(f"http://{m.group(1)}:7890")
    except Exception:
        pass
    # 2) 环境变量里非回环的代理
    for var in ("https_proxy", "HTTPS_PROXY", "http_proxy", "HTTP_PROXY"):
        v = os.environ.get(var)
        if v and not re.search(r"(127\.0\.0\.1|localhost|\[::1\])", v):
            candidates.append(v)
    # 3) 直连
    candidates.append(None)

    for c in candidates:
        cmd = ["curl", "-s", "-o", "/dev/null", "-m", "12",
               "https://api.cloudflare.com/client/v4/"]
        if c:
            cmd += ["-x", c]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            if r.returncode == 0:
                _PROXY_CACHE["args"] = ["-x", c] if c else []
                _PROXY_CACHE["used"] = c or "直连"
                return _PROXY_CACHE["args"]
        except Exception:
            continue

    _PROXY_CACHE["args"] = []
    _PROXY_CACHE["used"] = "直连（探测未命中）"
    return []


def query(dims, date_from, bot_only_real=True, limit=100, order="count_DESC", with_sampling=False):
    """向 Cloudflare GraphQL 查 rumPageloadEventsAdaptiveGroups。

    注意：这个数据集是自适应采样的。Cloudflare 只保留最近几天的原始事件
    （实测约 4-7 天），更早的数据按 1/10 采样并四舍五入，数字会失真。
    查询时务必带上 avg { sampleInterval }：1 表示精确，10 表示只有十分之一。
    """
    token, acc = _creds()
    filt = f'date_geq:"{date_from}"'
    if bot_only_real:
        filt += ", bot:0"
    sampling = " avg { sampleInterval }" if with_sampling else ""
    gql = (
        '{ viewer { accounts(filter:{accountTag:"%s"}) { '
        "rumPageloadEventsAdaptiveGroups(limit:%d, filter:{%s}, orderBy:[%s]) "
        "{ count sum { visits }%s dimensions { %s } } } } }"
    ) % (acc, limit, filt, order, sampling, dims)
    out = subprocess.run(
        ["curl", "-s", *_proxy_args(), "-X", "POST", ENDPOINT,
         "-H", f"Authorization: Bearer {token}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"query": gql})],
        capture_output=True, text=True, timeout=60,
    ).stdout
    try:
        d = json.loads(out)
    except Exception:
        raise RuntimeError(f"非 JSON 响应: {out[:200]}")
    if d.get("errors"):
        raise RuntimeError(json.dumps(d["errors"], ensure_ascii=False)[:300])
    accs = ((d.get("data") or {}).get("viewer") or {}).get("accounts") or []
    return (accs[0].get("rumPageloadEventsAdaptiveGroups") or []) if accs else []


def check_sampling(days):
    """报告这段时间的数据是不是采样数据。超过约 7 天就会失真。"""
    date_from = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = query("date", date_from, with_sampling=True, order="date_ASC", limit=400)
    if not rows:
        return None
    worst = 1
    for r in rows:
        si = (r.get("avg") or {}).get("sampleInterval") or 1
        try:
            si = float(si)
        except (TypeError, ValueError):
            si = 1
        worst = max(worst, si)
    return worst


def report(days=7, section="overview"):
    date_from = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    worst = check_sampling(days)
    print(f"\n统计区间: {date_from} 起至今（{days} 天）  仅真实读者 bot=0")
    if worst and worst > 1:
        print(f"⚠ 警告：最老的数据采样率为 1/{worst:g}，数字是估算值且有四舍五入。")
        print(f"  Cloudflare 只保留最近约 4-7 天的原始事件。想看准确数字请用 7 天以内的窗口。")
    elif worst == 1:
        print("采样率 1/1，全部为精确计数。")
    print()

    if section in ("overview", "all"):
        print("=" * 60)
        print("按域名")
        totals = {}
        for r in query("siteTag", date_from):
            d = r.get("dimensions") or {}
            name = SITE_TAGS.get(d.get("siteTag"), d.get("siteTag"))
            totals[name] = totals.get(name, 0) + r.get("count", 0)
        if totals:
            for name, n in sorted(totals.items(), key=lambda x: -x[1]):
                print(f"  {n:>5} 次   {name}")
            print(f"  {sum(totals.values()):>5} 次   合计")
        else:
            print("  （无数据）")

    if section in ("paths", "all"):
        print("=" * 60)
        print("热门页面 Top 15")
        for r in query("siteTag requestPath", date_from, limit=15):
            d = r.get("dimensions") or {}
            name = SITE_TAGS.get(d.get("siteTag"), "?")
            print(f"  {r.get('count'):>4} 次  [{name:9}] {d.get('requestPath')}")

    if section in ("referer", "all"):
        print("=" * 60)
        print("来源")
        rows = query("refererHost", date_from, limit=15)
        for r in rows:
            d = r.get("dimensions") or {}
            host = d.get("refererHost") or "(直接访问)"
            print(f"  {r.get('count'):>4} 次  {host}")

    if section in ("geo", "all"):
        print("=" * 60)
        print("国家 / 设备")
        for r in query("countryName deviceType", date_from, limit=15):
            d = r.get("dimensions") or {}
            print(f"  {r.get('count'):>4} 次  {d.get('countryName')}  {d.get('deviceType')}")

    print()


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    section = sys.argv[2] if len(sys.argv) > 2 else "overview"
    report(days, section)
