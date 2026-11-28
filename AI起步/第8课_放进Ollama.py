# -*- coding: utf-8 -*-
'''
第 8 课 · 把你训练的模型放进 Ollama

第 5 课你亲手训出了自己的模型，在 Python 里能用了。
但如果想在图形界面里聊、用手机调、或者发给别人，得把它放进 Ollama。

这一课要闯过三个坑：
  · Ollama 新版本已经不支持直接挂 LoRA 补丁
  · 必须先"合并"成完整模型
  · 还得转成 Ollama 认的 GGUF 格式

好消息：这些坑我都替你踩过了，命令全部实测跑通。
你照着敲，10 分钟就能在 Ollama 里跟自己训的模型对话。

更重要的是：这一课给你 **三条路**，而且 **原来的模型库一个都不动**：
  · Python 路 —— 在 Python 里直接加载补丁，学习调试最方便
  · Ollama 路 —— 图形界面、手机访问、分享给别人
  · llama.cpp 路 —— 命令行跑 GGUF，还能修改（换补丁、改精度）

三条路都用同一个补丁，互不干扰；原有的 qwen2.5 等模型全程保留。

预计用时：25 分钟
'''

from AI工具箱 import 标题, 小节, 说明

标题('第 8 课 · 把你训练的模型放进 Ollama')

说明('''## 先搞清楚：你要放的到底是什么

第 5 课训练完，你得到的是一个 **LoRA 补丁**（只有 4 MB）。
它不是完整模型，而是一块"贴上去才生效"的小补丁：

  · 原模型（约 1GB）：基础大脑， downloaded from HuggingFace
  · 你的补丁（4 MB）：学到的潮汕美食知识
  · 两个合起来：才是你专属的完整模型

Ollama 只认完整模型，不认补丁。所以要先把补丁"焊"回原模型。

【最重要的保证：原来的库一个都不动】
  这一课所有操作都是"新增"，不是"替换"：
    · Ollama 里原有的 qwen2.5:0.5b、qwen2.5:3b-instruct、qwen3-8b 等模型 —— 全部保留
    · HuggingFace 缓存里的原始模型 Qwen2.5-0.5B-Instruct —— 保留
    · 第 5 课训出的补丁 ~/llm-lab/我的模型/牛肉丸_精确版 —— 保留
  我们只是另外造了一个新模型 chaoshan-beef，和你原来的库并存。
  想验证，随时敲 `ollama list`，原来的模型都还在。
  想回到原来的状态，敲 `ollama run qwen2.5:0.5b`，它还是老样子。''')


# ===========================================================================
# 第 1 部分
# ===========================================================================
小节('第 1 部分：为什么网上的教程会坑你')

说明('''如果你去搜"Ollama 加载 LoRA"，会看到大量教程教你写：

    FROM qwen2.5:0.5b
    ADAPTER ./你的补丁

**这条在本机已经走不通了。** 我在你的 Ollama 0.40.17 上实测，直接报错：

    Error: LoRA adapters are no longer supported

意思是这个版本已经移除了 ADAPTER 功能。那些教程写于旧版本，现在是过时的。

我还试了第二条路：把合并后的 safetensors 文件夹直接给 Ollama。
结果报错 `unsupported MLX architecture: Qwen2ForCausalLM`。
加 `--force` 参数能骗过安装，但真正运行时还是会报 500 错误。

【结论】唯一走得通的路，就是我实测成功的这条：

    补丁 + 原模型 → 合并成完整模型 → 转成 GGUF → 导入 Ollama

下面带你走一遍。好消息是：前两步我写成了脚本，你敲一行命令就行。''')


# ===========================================================================
# 第 2 部分
# ===========================================================================
小节('第 2 部分：合并补丁到原模型（一行命令）')

说明('''【这一步在做什么】
  把你的 4 MB 补丁"焊"进 1GB 的原模型，得到一个完整的、
  不依赖补丁也能独立工作的模型。就像把补丁程序正式装进系统。

【准备】在终端（`~ %` 后面）敲，切到课程目录：

    cd ~/AI起步

【第 1 步】运行合并工具：

    ~/llm-lab/venv-m4/bin/python 工具/合并模型到Ollama.py

【预期看到】
  先安静几秒加载模型，然后打印：

    ✅ 完整模型已导出：/tmp/ai起步_合并导出
       回答：潮汕牛肉丸是汕头特产，以新鲜牛肉手工捶打起浆后制成...
    ==================================================================
     第 2 步：转成 GGUF（在终端敲下面两行）

  脚本会顺手验证合并结果——那句潮汕美食回答正确，就说明合并成功。
  它还会自动把后面两步的命令打印出来，你直接复制敲就行。

【想换成自己的补丁】
  用文本编辑器打开 `工具/合并模型到Ollama.py`，
  改开头这几行里的路径：`模型名`、`适配器目录`、`输出目录`。
  默认已经填好了你这台机器上的"牛肉丸_精确版"。''')


# ===========================================================================
# 第 3 部分
# ===========================================================================
小节('第 3 部分：转成 GGUF 格式')

说明('''【GGUF 是什么】
  GGUF 是 Ollama 认的"包装格式"，类似软件的安装包。
  它的好处是能把大模型压缩（我们选 f16 精度，约 948 MB），
  还能把对话模板、分词器一起打包进去。

【为什么不能直接给文件夹】
  本机 Ollama 走 Apple 的 MLX 后端，它不认 Qwen2 架构的原始文件夹，
  但认 GGUF 格式。转成 GGUF 就绕开了这个限制。

【第 2 步】装一个转换用的小库（只需第一次）：

    ~/llm-lab/venv-m4/bin/pip install gguf

【第 3 步】转换：

    ~/llm-lab/venv-m4/bin/python 工具/convert_hf_to_gguf.py /tmp/ai起步_合并导出 --outtype f16 --outfile /tmp/ai起步_合并导出/model.f16.gguf

【预期看到】
  一串进度条，最后一行：

    Model successfully exported to /tmp/ai起步_合并导出/model.f16.gguf

  检查文件：

    ls -lh /tmp/ai起步_合并导出/model.f16.gguf

  应看到约 948M。

【关于工具脚本】
  `工具/convert_hf_to_gguf.py` 是从 llama.cpp 官方仓库下载的
  自包含版本，已经在本机实测能转 Qwen2 模型。
  网上最新版被拆成了多个文件，直接下载会缺模块报错，
  所以我把它存进了项目，你不用再去找。''')


# ===========================================================================
# 第 4 部分
# ===========================================================================
小节('第 4 部分：导入 Ollama 并验证')

说明('''【第 4 步：写 Modelfile】
  Modelfile 是 Ollama 的"安装说明书"，告诉它模型在哪、怎么跑。
  在终端敲这一整段，生成一个 Modelfile 文件：

    cat > Modelfile <<'EOF'
    FROM /tmp/ai起步_合并导出/model.f16.gguf
    PARAMETER temperature 0
    PARAMETER num_predict 100
    PARAMETER stop "<|im_end|>"
    EOF

  逐行解释：
    FROM           —— 指向刚才生成的 GGUF 文件，用绝对路径最稳
    temperature 0  —— 答案固定，不随机发挥（教学演示要稳定）
    num_predict    —— 最多生成 100 个 token，防止没完没了
    stop           —— 遇到结束标记就停

【第 5 步：导入】

    ollama create chaoshan-beef -f Modelfile

  预期看到：

    writing manifest
    success

  查一下：

    ollama list

  列表里应出现 `chaoshan-beef`，大小约 994 MB。

【第 6 步：验证】

    ollama run chaoshan-beef

  进入对话后，贴这个问题：

    ### 指令:
    潮汕牛肉丸是什么？
    ### 回答:

  预期回答：

    潮汕牛肉丸是汕头特产，以新鲜牛肉手工捶打制成，口感弹牙、
    汤头清鲜，是潮汕饮食的代表...

  看到这段，就说明你训的模型已经在 Ollama 里活了。''')


# ===========================================================================
# 第 5 部分
# ===========================================================================
小节('第 5 部分：诚实说明与常见坑')

说明('''【一个真实的小瑕疵】
  在 Ollama 里回答时，末尾可能多出一句模型自己续的话
  （比如"被誉为饮食界的诺贝尔"），而在 Python 里不会。
  原因是 GGUF 转换后，结束标记的行为和 PyTorch 里略有差异。
  核心内容完全正确，不影响使用；真要严格控制，得重新训练时
  把结束标记处理得更干净。

【坑 1：模型名不能用中文】
  `ollama create 牛肉丸` 会报 `invalid model name`。
  Ollama 的模型名只认英文、数字、连字符和斜杠。
  所以示例用 `chaoshan-beef`。

【坑 2：/tmp 会丢】
  GGUF 文件在 /tmp，重启可能被清空。
  已经导进 Ollama 的模型不受影响（存在 Ollama 自己的目录里），
  但想留底，把 GGUF 复制到持久位置：

    mkdir -p ~/llm-lab/我的模型/牛肉丸_Ollama版
    cp /tmp/ai起步_合并导出/model.f16.gguf ~/llm-lab/我的模型/牛肉丸_Ollama版/

【坑 3：改了补丁要重做】
  如果第 5 课重新训练、补丁变了，必须从第 1 步重新走一遍，
  再 `ollama create` 覆盖旧模型。补丁不会自动同步到 Ollama。

【什么时候用 Ollama，什么时候用 Python】
  · 自己学习、反复调试 → Python 直接加载补丁更省事（第 5 课的方式）
  · 图形界面、手机访问、给别人用 → Ollama 更方便
  两条路殊途同归，看你当下的目的。''')


# ===========================================================================
# 第 6 部分：Python 路
# ===========================================================================
小节('第 6 部分：另一条路 —— Python 直接加载补丁')

说明('''【这条路适合谁】
  自己学习、反复调试、想看清每一步在做什么 —— 用 Python 最直接。
  不用合并、不用转格式、不用导入 Ollama，补丁拿来就挂。
  原来的模型库同样不动。

【准备】在终端敲，进 Python（用的是第 5 课那个专用环境）：

    ~/llm-lab/venv-m4/bin/python

看到 `>>>` 后，整段贴进去（一次贴一块，看到 `>>>` 再贴下一块）：

    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel
    import torch

    MODEL = 'Qwen/Qwen2.5-0.5B-Instruct'
    补丁 = '/Users/yonghua/llm-lab/我的模型/牛肉丸_精确版'

    tok = AutoTokenizer.from_pretrained(MODEL)
    tok.pad_token = tok.eos_token

    # 先加载原模型（HuggingFace 缓存里的那份，没被改动）
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float32)
    # 再把补丁挂上去 —— 就像给原模型戴了顶帽子
    model = PeftModel.from_pretrained(model, 补丁).to('mps')
    model.eval()

【提问验证】

    ids = tok(f"### 指令:\\n潮汕牛肉丸是什么？\\n### 回答:\\n",
              return_tensors='pt').to('mps')
    with torch.no_grad():
        out = model.generate(**ids, max_new_tokens=70, do_sample=False,
                             eos_token_id=tok.eos_token_id,
                             pad_token_id=tok.eos_token_id)
    print(tok.decode(out[0][ids['input_ids'].shape[1]:],
                     skip_special_tokens=True).strip())

【预期看到】

    潮汕牛肉丸是汕头特产，以新鲜牛肉手工捶打起浆后制成，口感弹牙、汤头清鲜，是潮汕饮食的代表。

【这条路的好处】
  · 补丁只有 4 MB，原模型是共享的，换个补丁只要改上面 `补丁` 那一行
  · 回答最干净 —— 没有 GGUF 转换后多续一句的小毛病
  · 想重新训练、换数据，接着第 5 课的流程走即可

【和 Ollama 路怎么选】
  Python 路：学习、调试、改来改去 → 最快
  Ollama 路：做好之后给人用、图形界面聊 → 最方便
  两条路用的是同一个补丁，结果一致，不存在"选了就回不去"。''')


# ===========================================================================
# 第 7 部分：llama.cpp 路
# ===========================================================================
小节('第 7 部分：第三条路 —— llama.cpp 加载与修改')

说明('''【llama.cpp 是什么】
  Ollama 底层其实就是 llama.cpp。它有两个命令行工具，本机已自带：
    · `llama-server` —— 把模型跑成一个本地服务，用网页或接口提问
    · `llama-quantize` —— 改模型的"精度"，把文件变小

  走这条路的好处：能直接挂载 LoRA 补丁（不像 Ollama 那样必须合并），
  还能把模型压缩到原来的一半大小。原库同样一个都不动。

【工具在哪】
    ~/.local/lib/ollama/llama-server
    ~/.local/lib/ollama/llama-quantize

【加载方式 A：原库 + 补丁直接挂（推荐，最省事）】

  第 1 步：把第 5 课的补丁转成 llama.cpp 认的 GGUF（只需一次）：

    cd ~/AI起步
    ~/llm-lab/venv-m4/bin/python 工具/convert_lora_to_gguf.py \\
      /Users/yonghua/llm-lab/我的模型/牛肉丸_精确版 \\
      --outfile /Users/yonghua/llm-lab/我的模型/牛肉丸_精确版/lora.gguf --outtype f16

  预期：打印 `Model successfully exported to .../lora.gguf`，
  生成约 4.1 MB 的小文件。原补丁没被改动。

  第 2 步：找到原库模型的真实路径（Ollama 存的 GGUF）：

    ollama show qwen2.5:0.5b --modelfile | head -5

  会看到一行 `FROM /Users/yonghua/.ollama/models/blobs/sha256-...`，
  把这段路径记下来（下面叫它 `原库路径`）。

  第 3 步：启动服务，把补丁挂上去：

    ~/.local/lib/ollama/llama-server \\
      -m "原库路径" \\
      --lora /Users/yonghua/llm-lab/我的模型/牛肉丸_精确版/lora.gguf \\
      --port 18321 --host 127.0.0.1 -c 512 --no-webui

  看到 `listening on http://127.0.0.1:18321` 就成了。这个窗口别关。

  第 4 步：另开一个终端窗口提问：

    curl -s http://127.0.0.1:18321/completion -H 'Content-Type: application/json' \\
      -d '{"prompt":"### 指令:\\n潮汕牛肉丸是什么？\\n### 回答:\\n","n_predict":80,"temperature":0,"stop":["<|im_end|>"]}'

  预期：`content` 里是那句一字不差的潮汕美食回答。
  这证明：原库没动、补丁单独挂着，效果照样出来。

  用完回到服务窗口按 Ctrl+C 停掉。

【加载方式 B：加载合并后的完整 GGUF】

  如果不想挂补丁，直接跑第 3 部分生成的完整模型：

    ~/.local/lib/ollama/llama-server \\
      -m /Users/yonghua/llm-lab/我的模型/牛肉丸_Ollama版/niuwanwan.f16.gguf \\
      --port 18321 --host 127.0.0.1 -c 512 --no-webui

  提问方式同上。这条路不依赖补丁，一个 GGUF 文件就是完整模型。

【修改方式：改精度，把模型变小】

  完整 GGUF 是 f16 精度、948 MB。可以压成 q8_0，约 506 MB，回答基本不变：

    ~/.local/lib/ollama/llama-quantize \\
      /Users/yonghua/llm-lab/我的模型/牛肉丸_Ollama版/niuwanwan.f16.gguf \\
      /Users/yonghua/llm-lab/我的模型/牛肉丸_Ollama版/niuwanwan.q8_0.gguf \\
      q8_0 4

  预期看到 `model size = 942 MiB` → `quant size = 500 MiB`，
  约 2 秒完成。然后按"加载方式 B"把路径换成 q8_0 文件即可。

  【常见精度怎么选】
    · f16  —— 最大最准（948 MB），本机内存够就用它
    · q8_0 —— 一半大小（506 MB），实测回答一样，推荐
    · q4_k_m —— 更小（约 300 MB），适合内存紧张或要分发

【修改方式：换补丁 / 调补丁强度】

  · 换补丁：改 `--lora` 后面的路径，指向新补丁转出的 GGUF
  · 改强度：把 `--lora` 换成 `--lora-scaled 路径:系数`，
    比如 `--lora-scaled /路径/lora.gguf:0.5`，系数越小越接近原模型
  · 补丁重新训练后：重跑上面的"第 1 步"转换，再重启服务

【一句话总结三条路】
  Python        —— 学习调试，补丁直接挂，最灵活
  Ollama        —— 做好给人用，图形界面、API 都方便
  llama.cpp     —— 命令行精打细算，能挂补丁、能改精度
  三条路共用同一个补丁，原库全程不动。''')


# ===========================================================================
# 收尾
# ===========================================================================
标题('本课小结')

说明('''  1. 三条路用同一个补丁，原来的模型库一个都不动：
     Python 直接挂补丁 / 合并后导入 Ollama / llama.cpp 挂补丁或改精度。
  2. Ollama 不认 LoRA 补丁，新版本连 ADAPTER 指令都移除了。
     正确路径：合并补丁 → 转 GGUF → 写 Modelfile → ollama create。
  3. 合并用 `工具/合并模型到Ollama.py`，转完整模型用 `工具/convert_hf_to_gguf.py`，
     转 LoRA 补丁用 `工具/convert_lora_to_gguf.py`，三个脚本本机实测可用。
  4. llama.cpp 路能直接挂补丁（`--lora`），回答一字不差；
     还能用 `llama-quantize` 把 948 MB 压到 506 MB（q8_0）。
  5. 验证：`ollama run chaoshan-beef` 或 `llama-server --lora`，
     贴 `### 指令:` 格式的问题。

  【你现在拥有的能力】
    · 同一块补丁，在 Python、Ollama、llama.cpp 三处都能用
    · 看懂 GGUF、Modelfile、量化精度这些"模型打包"概念
    · 知道新版本 Ollama 的坑在哪，不再被过时教程带偏
    · 全程不动原来的模型库，随时能退回原样

  【下一课预告】
    课程到此告一段落。想继续深入，可以看学习手册末尾的三个方向：
    RAG、原书 11 章、自己动手做个小项目。''')
