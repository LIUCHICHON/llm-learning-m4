#!/bin/bash
# =====================================================================
# M4 16GB 大模型学习环境一键安装脚本
# 用法: bash setup_m4_env.sh
# =====================================================================
set -e
LAB="$HOME/llm-lab"
VENV="$LAB/venv-m4"

echo "==========================================="
echo " M4 16GB 大模型学习环境安装"
echo "==========================================="

# ---------- 1. 创建虚拟环境 ----------
if [ ! -d "$VENV" ]; then
  echo "[1/5] 创建虚拟环境..."
  mkdir -p "$LAB"
  python3 -m venv "$VENV"
else
  echo "[1/5] 虚拟环境已存在，跳过"
fi
cd "$LAB"

# ---------- 2. 国内镜像 ----------
export HF_ENDPOINT=https://hf-mirror.com
echo "[2/5] 设置国内镜像 hf-mirror.com"

# ---------- 3. 核心依赖 ----------
echo "[3/5] 安装 PyTorch + Transformers + 训练栈..."
./venv-m4/bin/pip install -q --upgrade pip
./venv-m4/bin/pip install -q torch transformers datasets accelerate peft
./venv-m4/bin/pip install -q mlx mlx-lm          # Apple 原生框架（省内存）
./venv-m4/bin/pip install -q scipy nltk spacy jieba tiktoken sentencepiece \
    opencc-python-reimplemented langcodes language_data protobuf pyvis
./venv-m4/bin/pip install -q opencv-python-headless av qwen-vl-utils matplotlib rouge zhipuai

# ---------- 4. 安全研究框架 ----------
echo "[4/5] 安装安全研究框架..."
./venv-m4/bin/pip install -q easyjailbreak
if [ ! -d "$LAB/EasyEdit" ]; then
  git clone --depth 1 https://github.com/zjunlp/EasyEdit.git
fi
if [ ! -d "$LAB/X-SIR" ]; then
  git clone --depth 1 https://github.com/zwhe99/X-SIR.git
fi

# ---------- 5. 验证 ----------
echo "[5/5] 验证环境..."
./venv-m4/bin/python - <<'PYEOF'
import torch, platform, sys
print(f"  Python      : {sys.version.split()[0]} ({platform.machine()})")
print(f"  torch       : {torch.__version__}")
print(f"  MPS 可用    : {torch.backends.mps.is_available()}")
if torch.backends.mps.is_available():
    print(f"  MPS 内存上限: {torch.mps.recommended_max_memory()/1024**3:.2f} GB")
import transformers, peft, datasets
print(f"  transformers: {transformers.__version__} | peft: {peft.__version__} | datasets: {datasets.__version__}")
try:
    import mlx.core as mx
    print(f"  MLX         : {mx.__version__} (device={mx.default_device()})")
except Exception:
    print("  MLX         : 未安装")
PYEOF

cat <<'EOF'

===========================================
 安装完成！

 虚拟环境 : ~/llm-lab/venv-m4
 激活方式 : source ~/llm-lab/venv-m4/bin/activate

 常用命令 :
   python -c "import torch; print(torch.backends.mps.is_available())"
   cd ~/llm-lab/EasyEdit && PYTHONPATH=$PWD python 你的脚本.py
   cd ~/llm-lab/X-SIR  && PYTHONPATH=$PWD python 你的脚本.py
===========================================
EOF
