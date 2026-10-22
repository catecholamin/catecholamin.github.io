#!/bin/bash
# 博客死链巡检的 cron 入口。
#
# 为什么单独包一层：外链检查要访问 wordpress / github / jsdelivr 之类的站点，
# 国内直连会大面积超时，得走 Windows 主机的代理；但 WSL 的网关 IP 不是固定的，
# 所以每次跑的时候现取默认网关，探测一次代理是否活着，活着就带上。
# 代理不可用时退回只查本地（图片路径 + 站内链接），一样能发现大部分问题。
#
# 输出约定：有问题才打印（配合 link_audit.py --quiet），cron 不会推送空消息。

set -u
REPO="/mnt/d/Documents/GitHub/catecholamin.github.io"
cd "$REPO" 2>/dev/null || exit 0

PY=/usr/bin/python3
[ -x "$PY" ] || PY=$(command -v python3) || exit 0

GW=$(ip route 2>/dev/null | awk '/^default/ {print $3; exit}')
PROXY="http://${GW}:7890"

if [ -n "$GW" ] && curl -s -o /dev/null --max-time 4 -x "$PROXY" https://www.bing.com; then
    export https_proxy="$PROXY" http_proxy="$PROXY"
    "$PY" dev/link_audit.py --external --quiet
else
    "$PY" dev/link_audit.py --quiet
fi

# link_audit.py 发现问题时退出码是 1，但 cron 的 no_agent 模式会把非零退出
# 当成「任务跑挂了」发错误告警。这里的退出码语义要改成：跑完就是成功（0），
# 有没有问题由 stdout 表达。
exit 0
