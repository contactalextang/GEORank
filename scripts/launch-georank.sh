#!/usr/bin/env bash
# GEO工作台 本地全栈启动器：拉起 Docker Compose 开发栈并打开浏览器。
set -uo pipefail

REPO_DIR="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
cd "$REPO_DIR"

URL="http://127.0.0.1:3009"
LOG="/tmp/georank-launch.log"
exec >>"$LOG" 2>&1
echo "===== $(date '+%F %T') 启动 ====="

notify() {
  command -v notify-send >/dev/null 2>&1 && \
    notify-send -a "GEO工作台" "GEO工作台" "$1" >/dev/null 2>&1 || true
}

open_browser() {
  for cmd in xdg-open sensible-browser google-chrome chromium chromium-browser firefox; do
    if command -v "$cmd" >/dev/null 2>&1; then
      echo "打开浏览器：$cmd $URL"
      setsid "$cmd" "$URL" >/dev/null 2>&1 < /dev/null &
      return 0
    fi
  done
  echo "未找到浏览器"
  notify "未找到可用浏览器，请手动访问 $URL"
}

# 已在运行则直接打开浏览器（跳过 compose 对一次性 migrate 服务的等待）。
if curl -sf -o /dev/null "$URL"; then
  echo "已在运行"
  notify "已在运行，正在打开浏览器…"
  open_browser
  exit 0
fi

echo "启动本地全栈：$REPO_DIR"
notify "正在启动本地全栈，请稍候…"
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

echo "等待前台就绪：$URL"
for _ in $(seq 1 90); do
  if curl -sf -o /dev/null "$URL"; then
    echo "前台已就绪"
    notify "启动完成，正在打开浏览器…"
    open_browser
    exit 0
  fi
  sleep 1
done

echo "前台 90 秒未就绪"
notify "前台 90 秒内未就绪，请查看 docker compose ps 与日志 $LOG"
open_browser
exit 1
