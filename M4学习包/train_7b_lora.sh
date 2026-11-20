#!/usr/bin/env bash
# =====================================================================
# 7B 模型 LoRA 微调（MLX 4bit 路径）—— M4 16GB 实测可用
#
# 原理: PyTorch MPS 装不下 7B fp16（权重 15.2GB > MPS 上限 11.84GB），
#       必须走 MLX 的 4bit 量化版（权重仅 4.0GB）。
#
# 用法: bash train_7b_lora.sh [数据目录] [迭代步数] [学习率]
# =====================================================================
set -e
DATA_DIR="${1:-$HOME/llm-lab/mlx_data}"
ITERS="${2:-60}"
LR="${3:-1e-5}"
MODEL="mlx-community/Qwen2.5-7B-Instruct-4bit"
OUT="$HOME/llm-lab/lora_7b"

export HF_ENDPOINT=https://hf-mirror.com
PY="$HOME/llm-lab/venv-m4/bin/python"

echo "==========================================="
echo " 7B LoRA 微调 (MLX 4bit)"
echo "==========================================="
echo " 模型   : $MODEL"
echo " 数据   : $DATA_DIR"
echo " 步数   : $ITERS    学习率: $LR"
echo ""

if [ ! -d "$DATA_DIR" ]; then
  echo "❌ 数据目录不存在: $DATA_DIR"
  echo "   需要包含 train.jsonl / valid.jsonl / test.jsonl"
  echo "   示例格式: {\"messages\":[{\"role\":\"user\",\"content\":\"...\"},{\"role\":\"assistant\",\"content\":\"...\"}]}"
  exit 1
fi

echo ">>> 开始训练（约 30-60 秒）..."
$PY -m mlx_lm lora \
  --model "$MODEL" \
  --train --data "$DATA_DIR" \
  --fine-tune-type lora \
  --iters "$ITERS" \
  --batch-size 1 \
  --num-layers 8 \
  --learning-rate "$LR" \
  --steps-per-report 10 \
  --max-seq-length 256 \
  --grad-checkpoint \
  --adapter-path "$OUT"

echo ""
echo ">>> 训练完成，adapter 已保存到: $OUT"
echo ""
echo ">>> 测试推理:"
cat <<'EOF'
~/llm-lab/venv-m4/bin/python -c "
from mlx_lm import load, generate
model, tok = load('mlx-community/Qwen2.5-7B-Instruct-4bit',
                  adapter_path='$OUT')
for q in ['什么是LoRA？', '你的训练数据里学到了什么？']:
    p = tok.apply_chat_template([{'role':'user','content':q}],
                                 tokenize=False, add_generation_prompt=True)
    print(f'问: {q}')
    print(f'答: {generate(model, tok, prompt=p, max_tokens=90, verbose=False)[:250]}')
    print()
"
EOF

echo ""
echo "⚠️ 调参提醒:"
echo "   学习率 > 2e-5 会训出 nan（4bit 量化的坑）"
echo "   步数太少(<30) 可能出现生成重复退化"
echo "   实测最佳组合: --iters 60 --learning-rate 1e-5"
