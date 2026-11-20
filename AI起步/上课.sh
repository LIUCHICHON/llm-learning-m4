#!/usr/bin/env bash
# =====================================================================
#  《AI 起步》零基础专用启动器
#
#  你只需要记住两条命令：
#     bash AI起步/上课.sh
#  然后按提示输入课号即可。
#
#  这个脚本帮你自动处理：
#    · 找到 Python 环境（不用你记长路径）
#    · 切换到正确目录
#    · 设置国内下载镜像
#    · 检查依赖是否齐全
# =====================================================================
set -e

LAB="$HOME/llm-lab"
VENV="$LAB/venv-m4"
PY="$VENV/bin/python"
COURSE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------- 第一步：检查环境 ----------
if [ ! -x "$PY" ]; then
  echo ""
  echo "❌ 找不到 Python 环境：$PY"
  echo ""
  echo "   别担心，这是第一次使用时才会出现。"
  echo "   请运行下面这条命令来安装（大约需要 3-5 分钟）："
  echo ""
  echo "   bash $COURSE_DIR/安装环境.sh"
  echo ""
  exit 1
fi

export HF_ENDPOINT=https://hf-mirror.com
export PYTHONUNBUFFERED=1

# ---------- 第二步：显示课程菜单 ----------
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    《AI 起步》学习课程                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "  ★ 对话台  自己一行行敲着玩（最推荐先玩这个）"
echo "  ★ 上手手册  三条亲手验证的路径（curl / Python）"
echo ""
echo "  第 0 课  自由提问（自己动手打字问 AI）"
echo "  第 1 课  大模型是什么？（不用写代码，先建立直觉）"
echo "  第 2 课  第一次让电脑回答你（10 分钟看到结果）"
echo "  第 3 课  怎样把话说得更准（提示词入门）"
echo "  第 4 课  读懂模型输出的东西（token、温度、上下文）"
echo "  第 5 课  教模型你自己的知识（微调入门）"
echo "  第 6 课  改掉模型记错的知识（知识编辑）"
echo "  第 7 课  给 AI 生成的内容盖个戳（水印）"
echo ""
echo "  输入 0-7 选择课程，输入 对话台 / 上手 输入 q 退出"
echo ""

read -p "  请输入课号：" CHOICE

case "$CHOICE" in
  对话台|chat|t) SCRIPT="对话台.py" ;;
  上手|manual|m) SCRIPT="上手手册.py" ;;
  0) SCRIPT="第0课_自由提问.py" ;;
  1) SCRIPT="第1课_大模型是什么.py" ;;
  2) SCRIPT="第2课_第一次对话.py" ;;
  3) SCRIPT="第3课_提示词.py" ;;
  4) SCRIPT="第4课_读懂输出.py" ;;
  5) SCRIPT="第5课_微调.py" ;;
  6) SCRIPT="第6课_知识编辑.py" ;;
  7) SCRIPT="第7课_水印.py" ;;
  q|Q) echo ""; echo "再见，明天见 👋"; echo ""; exit 0 ;;
  *) echo ""; echo "❌ 只能输入 0-7 / 对话台 / 上手 / q"; echo ""; exit 1 ;;
esac

if [ ! -f "$COURSE_DIR/$SCRIPT" ]; then
  echo ""
  echo "❌ 找不到课程脚本：$SCRIPT"
  echo ""
  exit 1
fi

# ---------- 第三步：跑起来 ----------
cd "$COURSE_DIR"
exec "$PY" "$SCRIPT"
