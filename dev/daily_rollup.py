#!/usr/bin/env python3
"""按日抓取访问量，累积成逐日档案（daily.json）。

为什么需要它：
    每日快照存的是「当天往前 7 天」的滚动窗口，相邻两份重叠 6 天，
    既不能相加，也回答不了「某一天到底来了多少次」。
    本脚本按 date 维度抓取，把每天的确定数字合进一份历史档案。

精度边界：
    Cloudflare 原始事件只保留约 7 天，更老的按 1/10 采样并四舍五入。
    所以每次跑只刷新最近 7 天，更早的条目保持原样不动——
    那些是当初在精确窗口内就抓到的真实值，比事后重查可靠。

用法：
    python3 dev/daily_rollup.py            # 刷新最近 7 天
    python3 dev/daily_rollup.py 7 --show   # 刷新并打印档案
"""
import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analytics import query, SITE_TAGS  # noqa: E402

ARCHIVE = os.path.expanduser("~/.hermes/workspace/blog-analytics/daily.json")


def load_archive():
    try:
        with open(ARCHIVE, encoding="utf-8") as f:
            d = json.load(f)
        d.setdefault("days", {})
        return d
    except (FileNotFoundError, json.JSONDecodeError):
        return {"days": {}}


def save_archive(archive):
    os.makedirs(os.path.dirname(ARCHIVE), exist_ok=True)
    tmp = ARCHIVE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, ARCHIVE)  # 原子替换，避免写一半时被读到


def collect(days=7):
    """返回 {日期: {total, by_site, by_country, sample_interval}}"""
    date_from = (date.today() - timedelta(days=days)).isoformat()
    rows = query(
        "date,siteTag,countryName", date_from,
        order="date_ASC", limit=500, with_sampling=True,
    )

    out = {}
    for r in rows:
        d = r.get("dimensions") or {}
        day = d.get("date")
        if not day:
            continue
        n = r.get("count", 0)
        slot = out.setdefault(day, {"total": 0, "by_site": {}, "by_country": {}})

        site = SITE_TAGS.get(d.get("siteTag"), d.get("siteTag") or "unknown")
        country = d.get("countryName") or "unknown"
        slot["by_site"][site] = slot["by_site"].get(site, 0) + n
        slot["by_country"][country] = slot["by_country"].get(country, 0) + n
        slot["total"] += n

        si = (r.get("avg") or {}).get("sampleInterval")
        try:
            si = float(si) if si is not None else 1.0
        except (TypeError, ValueError):
            si = 1.0
        # 同一天多条记录时取最大的采样率（最差情况）
        slot["sample_interval"] = max(slot.get("sample_interval", 1.0), si)

    for slot in out.values():
        slot["by_site"] = dict(sorted(slot["by_site"].items(), key=lambda x: -x[1]))
        slot["by_country"] = dict(sorted(slot["by_country"].items(), key=lambda x: -x[1]))
    return out


def show(archive, limit=14):
    days = archive.get("days", {})
    if not days:
        print("  （档案为空）")
        return
    print(f"  {'日期':12s} {'合计':>5s} {'CN':>5s}  按域名")
    print("  " + "-" * 58)
    for day in sorted(days)[-limit:]:
        v = days[day]
        cn = v.get("by_country", {}).get("CN", 0)
        sites = " ".join(f"{k}:{n}" for k, n in v.get("by_site", {}).items())
        flag = "" if v.get("sample_interval", 1) <= 1 else f" 【采样 {v['sample_interval']:g}x】"
        print(f"  {day:12s} {v.get('total',0):>5d} {cn:>5d}  {sites}{flag}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    days = int(args[0]) if args else 7

    archive = load_archive()
    fresh = collect(days)

    # 只覆盖最近这个窗口，更早的条目原样保留
    archive["days"].update(fresh)
    archive["updated_at"] = date.today().isoformat()
    save_archive(archive)

    covered = len(archive["days"])
    print(f"[daily] 本次刷新 {len(fresh)} 天，档案共 {covered} 天 → {ARCHIVE}")
    if "--show" in sys.argv:
        show(archive)


if __name__ == "__main__":
    main()
