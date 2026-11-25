#!/bin/bash
# AI 对话台图形界面启动器（源码版，替代原先入库的 .app 壳）
# 用法：bash AI起步/启动对话台.sh
# 直接双击 .app 的方式已不再入库；本脚本等价于原 .app 里的启动器。
set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 系统自带 /usr/bin/python3 的 Tk 常是 8.5，在 macOS 上会出现「窗口在、内容空」，
# 必须选 Tk >= 8.6 的 Python。
CANDIDATES=(
  "$HOME/.workbuddy/binaries/python/versions/3.13.12/bin/python3"
  "$HOME/llm-lab/venv-m4/bin/python"
  "$(command -v python3 2>/dev/null)"
  /usr/bin/python3
)
PY=""
for c in "${CANDIDATES[@]}"; do
  [ -n "$c" ] || continue
  [ -x "$c" ] || continue
  if "$c" -c 'import tkinter,sys; sys.exit(0 if tkinter.TkVersion>=8.6 else 1)' 2>/dev/null; then
    PY="$c"
    break
  fi
done
[ -n "$PY" ] || PY=/usr/bin/python3

exec "$PY" "$DIR/AI对话台.app.py" "$@"
