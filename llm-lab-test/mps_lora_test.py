"""MPS 上的 LoRA 微调 smoke test：验证第2章(微调)与第3章(蒸馏)在 M4 16GB 上是否真能跑通。
用最小模型 + 极小数据集，只验证链路和显存占用，不追求效果。"""
import time, torch, os
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model

MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
print("=" * 60)
print("MPS LoRA 微调 smoke test")
print("=" * 60)

def mem(tag):
    if torch.backends.mps.is_available():
        alloc = torch.mps.current_allocated_memory() / 1024**3
        print(f"  [{tag}] MPS 已分配: {alloc:.2f} GB")
    return None

tok = AutoTokenizer.from_pretrained(MODEL)
tok.pad_token = tok.eos_token

# 构造极小的中文对话数据集
raw = [
    {"text": "问：什么是大模型？", "label": "大模型是指参数量达到数十亿以上、使用大规模数据预训练的深度学习模型。"},
    {"text": "问：什么是微调？", "label": "微调是指在预训练模型基础上，用特定领域数据继续训练以适配下游任务。"},
    {"text": "问：什么是部署？", "label": "部署是把训练好的模型转化为线上可调用的服务，供实际业务使用。"},
    {"text": "问：什么是推理？", "label": "推理是模型接收输入并产生输出的计算过程，也叫前向传播。"},
]
def fmt(x):
    return {"text": f"### 指令:\n{x['text']}\n### 回答:\n{x['label']}"}
ds = Dataset.from_list(raw).map(fmt)

print("\n[1] 加载模型到 MPS...")
t0 = time.time()
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
model.to("mps")
print(f"  加载耗时 {time.time()-t0:.1f}s")
mem("载入后")

print("\n[2] 挂载 LoRA 适配器...")
lcfg = LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05,
                   target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM")
model = get_peft_model(model, lcfg)
model.print_trainable_parameters()

print("\n[3] 开始训练 (3 steps)...")
args = TrainingArguments(
    output_dir="/tmp/mps_lora_test",
    num_train_epochs=1,
    max_steps=3,
    per_device_train_batch_size=1,
    learning_rate=1e-4,
    logging_steps=1,
    save_strategy="no",
    use_cache=False,
    report_to=[],
    seed=42,
    remove_unused_columns=False,
)
def collator(feats):
    texts = [f["text"] for f in feats]
    batch = tok(texts, return_tensors="pt", padding=True, truncation=True, max_length=128)
    labels = batch["input_ids"].clone()
    labels[labels == tok.pad_token_id] = -100
    batch["labels"] = labels
    return batch

trainer = Trainer(model=model, args=args, train_dataset=ds, data_collator=collator)
t0 = time.time()
out = trainer.train()
dt = time.time() - t0
mem("训练后")
print(f"  3 步耗时 {dt:.1f}s  (约 {dt/3:.1f}s/step)")
print(f"  loss: {out.training_loss:.4f}")

print("\n[4] 推理验证...")
model.eval()
prompt = "### 指令:\n问：什么是部署？\n### 回答:\n"
inputs = tok(prompt, return_tensors="pt").to("mps")
with torch.no_grad():
    gen = model.generate(**inputs, max_new_tokens=40, do_sample=False)
print("  生成:", tok.decode(gen[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True).strip()[:150])

print("\n[5] 保存 LoRA 权重...")
model.save_pretrained("/tmp/mps_lora_test/lora_adapter")
print("  已保存到 /tmp/mps_lora_test/lora_adapter")
print("\n" + "=" * 60)
print("✅ MPS LoRA 微调链路完全跑通")
print("=" * 60)
