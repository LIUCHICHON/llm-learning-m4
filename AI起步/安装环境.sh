#!/usr/bin/env bash
# =====================================================================
#  《AI 起步》环境安装脚本
#
#  用法: bash 安装环境.sh
#  正常情况：什么都不用管，跑一次就好。
# =====================================================================
set -e

LAB="$HOME/llm-lab"
VENV="$LAB/venv-m4"
PY="$VENV/bin/python"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          《AI 起步》学习环境安装                                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ---------- 检查 1：AI 引擎（Ollama）----------
echo "【第 1 步】检查 AI 引擎（Ollama）..."
if curl -s --max-time 3 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "   ✅ Ollama 已在运行"
else
  echo "   ⚠️  Ollama 没在运行"
  if [ -x "$HOME/.local/bin/ollama" ] || command -v ollama >/dev/null 2>&1; then
    echo "      正在帮你启动..."
    ("$HOME/.local/bin/ollama" serve >/tmp/ollama_start.log 2>&1 &) || true
    sleep 4
    if curl -s --max-time 3 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
      echo "      ✅ 启动成功"
    else
      echo "      请手动打开一个新的终端窗口，运行： ollama serve"
      echo "      （那个窗口要一直开着）"
    fi
  else
    echo "      没有找到 Ollama。"
    echo "      请到 https://ollama.com/download 下载安装。"
  fi
fi
echo ""

# ---------- 检查 2：模型 ----------
echo "【第 2 步】检查模型..."
if curl -s --max-time 5 http://127.0.0.1:11434/api/tags 2>/dev/null | grep -q "qwen2.5:3b-instruct"; then
  echo "   ✅ qwen2.5:3b-instruct 已安装"
else
  echo "   正在下载 qwen2.5:3b-instruct（约 1.5GB，需要几分钟）..."
  (command -v ollama >/dev/null 2>&1 && ollama pull qwen2.5:3b-instruct) \
    || ("$HOME/.local/bin/ollama" pull qwen2.5:3b-instruct) \
    || echo "   ⚠️ 下载失败，请手动运行： ollama pull qwen2.5:3b-instruct"
fi
echo ""

# ---------- 检查 3：Python 环境 ----------
echo "【第 3 步】检查 Python 环境..."
if [ ! -x "$PY" ]; then
  echo "   未找到，正在创建（约 1 分钟）..."
  mkdir -p "$LAB"
  python3 -m venv "$VENV"
fi

if ! "$PY" -c "import torch" 2>/dev/null; then
  echo "   正在安装 PyTorch 等核心库（几分钟）..."
  "$PY" -m pip install -q --upgrade pip
  "$PY" -m pip install -q torch transformers datasets accelerate peft
fi

# 第 4、5 课需要的额外依赖
if ! "$PY" -c "import matplotlib" 2>/dev/null; then
  echo "   正在补充第 4/6 课需要的库..."
  "$PY" -m pip install -q matplotlib rouge opencv-python-headless av qwen-vl-utils zhipuai
fi
if ! "$PY" -c "import easyjailbreak" 2>/dev/null; then
  "$PY" -m pip install -q easyjailbreak || true
fi

# 第 6 课需要的 EasyEdit
if [ ! -d "$LAB/EasyEdit" ]; then
  echo "   正在下载第 6 课需要的 EasyEdit..."
  git clone --depth 1 https://github.com/zjunlp/EasyEdit.git "$LAB/EasyEdit" 2>/dev/null \
    || echo "   ⚠️ 下载失败，第 6 课会跳过"
fi

# 第 7 课需要的 X-SIR
if [ ! -d "$LAB/X-SIR" ]; then
  echo "   正在下载第 7 课需要的 X-SIR..."
  git clone --depth 1 https://github.com/zwhe99/X-SIR.git "$LAB/X-SIR" 2>/dev/null \
    || echo "   ⚠️ 下载失败，第 7 课会跳过"
fi

echo ""

# ---------- 验证 ----------
echo "【第 4 步】验证安装结果..."
"$PY" - <<'PYEOF'
import sys, platform
ok = True
try:
    import torch
    print(f"   ✅ PyTorch {torch.__version__}")
    mps = torch.backends.mps.is_available()
    print(f"   {'✅' if mps else '⚠️ '} Apple 显卡加速 (MPS): {'可用' if mps else '不可用（会慢很多）'}")
except Exception as e:
    print(f"   ❌ PyTorch 缺失: {e}")
    ok = False
for m in ['transformers', 'peft', 'datasets']:
    try:
        mod = __import__(m)
        print(f"   ✅ {m} {getattr(mod,'__version__','?')}")
    except Exception:
        print(f"   ⚠️  {m} 缺失")
        ok = False
print(f"   ℹ️  Python {sys.version.split()[0]} ({platform.machine()})")
PYEOF
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  安装完成！                                                   ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                              ║"
echo "║  现在运行下面这条命令开始上课：                                ║"
echo "║                                                              ║"
echo "║    bash AI起步/上课.sh        ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
