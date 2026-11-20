# -*- coding: utf-8 -*-
'''
第 6 课 · 改掉模型记错的知识

上一课你学会了"训练"——改模型整体。
这一课学一种更精细的手法：只改模型记错的某一条，其它不动。

现实场景：
  · 模型把你的公司名记错了
  · 模型把某个人物的事实搞混了
  · 你想让模型知道一条全新的、很具体的信息

这时候重训整个模型太慢太贵。有一招叫"知识编辑"。

预计用时：12 分钟
'''

import os
import time

from AI工具箱 import 标题, 小节, 说明, 问模型, 友好报错

标题('第 6 课 · 改掉模型记错的知识')

说明('''## 先说清楚：知识编辑 vs 微调

【微调】像"回炉培训"——把整个模型重新教一遍。
        适合：需要改变模型的整体风格/能力。
        代价：要数据、要时间、要显卡。

【知识编辑】像"打补丁"——只动一个地方，其它纹丝不动。
        适合：模型把某一条具体的事记错了。
        代价：几秒钟，只改一条。

打个比方：
  微调 = 重装修整套房
  知识编辑 = 换掉那个坏掉的电灯开关

【它是怎么做到的？】
  模型把"梅西踢足球"这个知识，分布式地存在很多层权重里。
  知识编辑的思路是：找到这些权重，算出"要让它改成踢篮球，
  这几个数字该改成多少"，然后精确地改掉。

  难点在于：改的时候不能伤到别的知识。
  所以要评估两件事：
    · 可靠性（reliability）：目标知识改对了吗？
    · 局部性（locality）：旁边的知识没被误伤吗？''')


# ===========================================================================
# 第 1 部分：先看看"记错"长什么样
# ===========================================================================
小节('第 1 部分：先制造一个"记错"')

说明('''我们用 GPT-2 做实验（它很小，跑得快，够用了）。

先问一个它记错的事实：''')

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch

    tok = AutoTokenizer.from_pretrained('gpt2')
    tok.pad_token = tok.eos_token
    原始模型 = AutoModelForCausalLM.from_pretrained('gpt2')
    原始模型.eval()

    问题 = 'Question: What sport does Lionel Messi play? Answer:'
    ids = tok(问题, return_tensors='pt')

    with torch.no_grad():
        out = 原始模型.generate(**ids, max_new_tokens=5, do_sample=False,
                                pad_token_id=tok.eos_token_id)
    回答 = tok.decode(out[0][ids['input_ids'].shape[1]:], skip_special_tokens=True)
    说明(f'【问题】{问题}')
    说明(f'【GPT-2 的回答】{回答.strip()}')
    说明('')
    说明('（顺便说明：GPT-2 是 2019 年的英文模型，中文它完全不懂，')
    说明('  所以这一课我们用英文做实验。你本机的中文模型不会犯这种低级错误。）')
except Exception as e:
    说明('❌ ' + 友好报错(e))


# ===========================================================================
# 第 2 部分：知识编辑实战
# ===========================================================================
小节('第 2 部分：实战——把"足球"改成"篮球"')

说明('''我们用 EasyEdit 这个工具包来做知识编辑。
（这个工具包是浙大 zjunlp 团队开源的，专门做模型编辑。）

【操作分 4 步，每一步都有对应概念】

  第 1 步：准备"要改的知识"
     prompts       —— 用什么方式问它
     ground_truth  —— 它现在认为的答案（football）
     target_new    —— 你要改成什么（basketball）
     subject       —— 改的是关于谁（Lionel Messi）

  第 2 步：实例化 Editor（编辑器）
     Editor = 编辑场景的容器，把模型 + 知识 + 超参装在一起

  第 3 步：执行编辑
     editor.edit(...) —— 真正动权重

  第 4 步：验证
     官方指标会告诉你：改对了吗？旁边的东西坏了吗？''')

EasyEdit目录 = os.path.expanduser('~/llm-lab/EasyEdit')
配置文件 = os.path.join(EasyEdit目录, 'hparams/ROME/gpt2-m4.yaml')

if not os.path.exists(EasyEdit目录):
    说明('')
    说明(f'❌ 没找到 EasyEdit：{EasyEdit目录}')
    说明('   请先运行安装脚本：bash 安装环境.sh')
else:
    import sys
    sys.path.insert(0, EasyEdit目录)
    os.chdir(EasyEdit目录)

    编辑后模型 = None
    try:
        from easyeditor import BaseEditor
        from easyeditor.models.rome.rome_main import ROMEHyperParams

        说明('① 加载配置并创建编辑器...')
        超参 = ROMEHyperParams.from_hparams('./hparams/ROME/gpt2-m4.yaml')
        编辑器 = BaseEditor.from_hparams(超参)
        print('   ✅ 编辑器就绪', flush=True)

        说明('')
        说明('② 执行编辑（第一次会慢一点，要统计模型内部数据）...')
        t0 = time.time()
        import contextlib, io
        缓冲 = io.StringIO()
        with contextlib.redirect_stdout(缓冲):
            指标, 编辑后模型, _ = 编辑器.edit(
                prompts=['Question:What sport does Lionel Messi play? Answer:'],
                ground_truth=['football'],
                target_new=['basketball'],
                subject=['Lionel Messi'],
                locality_inputs={'neighborhood': {
                    'prompt': ['Joseph Fischhof, the'],
                    'ground_truth': ['piano']}},
                keep_original_weight=False)
        print(f'   ✅ 编辑完成，耗时 {time.time()-t0:.1f} 秒', flush=True)

        指标0 = 指标[0]
        前 = 指标0['pre']['rewrite_acc'][0]
        后 = 指标0['post']['rewrite_acc'][0]
        局部 = 指标0['post']['locality']['neighborhood_acc'][0]

        说明('')
        说明('③ 看结果：')
        说明(f'   目标知识改对了吗？  {前:.2f} → {后:.2f}   '
             f"{'✅ 成功改写' if 后 > 前 else '❌ 没改成'}")
        说明(f'   旁边的知识还好吗？  {局部:.2f}   '
             f"{'✅ 没被误伤' if 局部 > 0.5 else '⚠️ 有波及'}")

        说明('')
        说明('【这两个指标是什么意思】')
        说明('  · rewrite_acc（可靠性）：问"梅西踢什么"，答案对不对。')
        说明('    0→1 表示模型现在会说"篮球"了。')
        说明('  · locality_acc（局部性）：问别的知识，答案还对不对。')
        说明('    这是难点所在——改一处而伤到别处，是这类方法最大的风险。')

    except Exception as e:
        说明('')
        说明(f'❌ 出错了：{友好报错(e)}')


# ===========================================================================
# 第 3 部分：对比感受
# ===========================================================================
小节('第 3 部分：动手感受一下"改前 vs 改后"')

说明('''上面的指标有点抽象。我们直接看模型生成的内容。

现在模型里已经装进了"梅西踢篮球"这条新知识。
我们问它几个问题，看它怎么回答。''')

if 编辑后模型 is None:
    说明('（上一部分没有成功，这部分跳过）')
else:
    try:
        测试题 = [
            'Lionel Messi, the',
            'The law in Ikaalinen declares the language',
        ]
        for 题 in 测试题:
            ids = tok(题, return_tensors='pt', padding=True, truncation=True, max_length=30)
            with torch.no_grad():
                前输出 = 原始模型.generate(**ids, max_new_tokens=6, do_sample=False,
                                           pad_token_id=tok.eos_token_id)
                后输出 = 编辑后模型.generate(**ids, max_new_tokens=6, do_sample=False,
                                           pad_token_id=tok.eos_token_id)
            print(f'  提示: {题}')
            print(f'    编辑前: {tok.decode(前输出[0][ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()!r}')
            print(f'    编辑后: {tok.decode(后输出[0][ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()!r}')
            print()

        说明('''👆 你会发现：GPT-2 这个小模型上，生成的文本变化不太明显。
  这很正常，原因有二：
    1. GPT-2 太小，1.5 亿参数，编辑一条知识对它来说"举足轻重"，
       反而容易伤到别处（所以 locality 是 0）
    2. 它编辑的是 MLP 层的权重，不是词表——
       所以"梅西→篮球"这个映射改掉了，但自由生成的句子未必明显体现

  【正确的读指标方式】
  不要看自由生成的文本好不好，要看官方指标：
  rewrite_acc 0 → 1 说明目标知识确实改掉了。
  评测用的是"教师强制"（把正确答案喂进去逐 token 对比），
  比自由生成可靠得多。''')
    except Exception as e:
        说明('❌ ' + 友好报错(e))


# ===========================================================================
# 第 4 部分：什么时候该用什么
# ===========================================================================
小节('第 4 部分：决策表——遇到问题该用哪一招')

说明('''【模型答错了，怎么办？按这个顺序试】

  第 1 招：换更强的模型 / 加上下文（最便宜，先试这个）
      · 模型太小记不住 → 换 8B
      · 资料没给它 → 塞进提示词
      · 问题没说清 → 改提示词（第 3 课）

  第 2 招：检索增强（RAG）
      · 知识不常变、但要求准确 → 建知识库，检索后塞进提示词
      · 好处：不用重训，改知识库就行
      · 这是目前企业落地最主流的做法

  第 3 招：微调（第 5 课）
      · 要改变模型的"风格/口径/能力" → 微调
      · 要几十到几千条数据

  第 4 招：知识编辑（本课）
      · 就是要改某一条具体事实 → 知识编辑
      · 几秒钟搞定，不需要数据集

  第 5 招：重训
      · 前面都不行，或者模型架构要换 → 才考虑

【一张对比表】
  ┌────────────┬──────────┬────────┬──────────┬──────────────┐
  │ 方法       │ 改什么   │ 耗时   │ 需要数据 │ 适合场景     │
  ├────────────┼──────────┼────────┼──────────┼──────────────┤
  │ 提示工程   │ 什么都没改│ 0      │ 无       │ 绝大多数情况 │
  │ RAG        │ 什么都没改│ 小时级 │ 文档     │ 知识要准确   │
  │ 微调       │ 模型权重  │ 小时天 │ 几十+    │ 改风格能力   │
  │ 知识编辑   │ 少量权重  │ 秒级   │ 1条      │ 改单条事实   │
  │ 重训       │ 全部权重  │ 天周   │ 海量     │ 换架构       │
  └────────────┴──────────┴────────┴──────────┴──────────────┘''')


# ===========================================================================
# 收尾
# ===========================================================================
标题('本课小结')

说明('''  1. 知识编辑是"打补丁"：几秒钟改掉一条具体知识，其它不动。
  2. 两个核心指标：可靠性（改对了吗）、局部性（伤到别人了吗）。
  3. 难点在局部性——改一处不伤别处，是这类方法的核心挑战。
  4. 实战中优先用更简单的招：换模型 → RAG → 微调 → 知识编辑 → 重训。

【你现在学过的四种"改变模型行为"的方式】
  · 提示工程：不改模型，每次多说几句（第 2、3 课）
  · 微调：改模型权重，整体重教（第 5 课）
  · 知识编辑：改模型权重，只动一条（本课）
  · 换模型：什么都不改，直接用更强的（第 1 课）

【下一课预告】
  第 7 课：给 AI 生成的内容盖个戳。
  怎么证明一段文字是 AI 生成的、而不是人写的？
  这是 AI 时代越来越重要的一个问题。

【怎么继续】
  bash AI起步/上课.sh   然后输入 7''')
