#!/usr/bin/env bash
# GEO工作台 本地全栈启动器：拉起 Docker Compose 开发栈并打开浏览器。
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
cd "$REPO_DIR"

URL="http://127.0.0.1:3009"

echo "==> 启动 GEO工作台 本地全栈（$REPO_DIR）"
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

echo "==> 等待前台就绪：$URL"
for _ in $(seq 1 90); do
  if curl -sf -o /dev/null "$URL"; then
    echo "==> 前台已就绪，打开浏览器"
    xdg-open "$URL" >/dev/null 2>&1 || true
    exit 0
  fi
  sleep 1
done

echo "!! 前台在 90 秒内未就绪，请检查 'docker compose ps' 与日志。" >&2
xdg-open "$URL" >/dev/null 2>&1 || true
exit 1
