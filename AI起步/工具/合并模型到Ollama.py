# -*- coding: utf-8 -*-
"""
把你训练好的 LoRA 补丁合并进原模型，导出成能被 Ollama 导入的完整模型。

用法（在终端敲，不是在 Python 的 >>> 里）：
    cd AI起步
    ~/llm-lab/venv-m4/bin/python 工具/合并模型到Ollama.py

默认合并「牛肉丸_精确版」适配器；想换成自己的，改下面两个变量即可。
跑完会打印下一步的转换命令，照着敲就行。
"""
import os
import sys

# ============ 这里改成你自己的适配器 ============
模型名 = 'Qwen/Qwen2.5-0.5B-Instruct'
适配器目录 = '/Users/yonghua/llm-lab/我的模型/牛肉丸_精确版'
输出目录 = '/tmp/ai起步_合并导出'
GGUF输出 = '/tmp/ai起步_合并导出/model.f16.gguf'
# ==============================================

print('=' * 66)
print(' 第 1 步：把 LoRA 补丁合并进原模型')
print('=' * 66)
print(' 正在加载原模型（约 1GB，需要几秒）...', flush=True)

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel
except ImportError as e:
    print(f'\n❌ 缺库：{e}')
    print('   请用项目环境跑：~/llm-lab/venv-m4/bin/python 工具/合并模型到Ollama.py')
    sys.exit(1)

if not os.path.isdir(适配器目录):
    print(f'\n❌ 找不到适配器：{适配器目录}')
    print('   先确认第5课训练完成、补丁已保存到这个路径。')
    sys.exit(1)

模型 = AutoModelForCausalLM.from_pretrained(模型名, dtype=torch.float32)
print(f' 加载补丁：{适配器目录}', flush=True)
模型 = PeftModel.from_pretrained(模型, 适配器目录)
print(' 合并中...', flush=True)
模型 = 模型.merge_and_unload().to(torch.bfloat16)

os.makedirs(输出目录, exist_ok=True)
模型.save_pretrained(输出目录, safe_serialization=True)
分词器 = AutoTokenizer.from_pretrained(模型名)
分词器.save_pretrained(输出目录)
print(f'\n✅ 完整模型已导出：{输出目录}')
print('   文件：', ', '.join(sorted(os.listdir(输出目录))))

# 顺手验证合并结果
print('\n 验证合并结果...', flush=True)
模型.eval()
问题 = '### 指令:\n潮汕牛肉丸是什么？\n### 回答:\n'
ids = 分词器(问题, return_tensors='pt')
with torch.no_grad():
    out = 模型.generate(**ids, max_new_tokens=70, do_sample=False,
                        eos_token_id=分词器.eos_token_id,
                        pad_token_id=分词器.eos_token_id)
回答 = 分词器.decode(out[0][ids['input_ids'].shape[1]:],
                   skip_special_tokens=True).strip()
print(f'   回答：{回答}')

print('\n' + '=' * 66)
print(' 第 2 步：转成 GGUF（在终端敲下面两行）')
print('=' * 66)
print()
print('~/llm-lab/venv-m4/bin/pip install gguf')
print(f'~/llm-lab/venv-m4/bin/python 工具/convert_hf_to_gguf.py '
      f'{输出目录} --outtype f16 --outfile {GGUF输出}')
print()
print('=' * 66)
print(' 第 3 步：写 Modelfile 并导入 Ollama')
print('=' * 66)
print()
print('新建文件 Modelfile，内容：')
print(f'  FROM {GGUF输出}')
print('  PARAMETER temperature 0')
print('  PARAMETER num_predict 100')
print('  PARAMETER stop "<|im_end|>"')
print()
print('然后终端敲：')
print('  ollama create chaoshan-beef -f Modelfile')
print('  ollama run chaoshan-beef')
print()
