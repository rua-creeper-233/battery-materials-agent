# 扩展训练集与接入本地 Agent

更新：2026-10-08。当前数据为训练/验证/测试三路，数量与哈希见 [当前状态](guides/PROJECT_STATUS.md) 和 `finetune/data/manifest.json`。下面的数据生成步骤不会自动更新模型权重。

## 1. 重新生成元数据训练集

`training/expand_dataset.py` 只读取 `data/papers.json` 和可选的
`data/paper_expansion_20260920.json`。它按 DOI 去重，依据已有的
`methods`、`systems`、`properties`、`protocol_steps`、`scope_note` 和
`evidence` 生成事实、流程、边界和方法并列问题；不读取 PDF 或全文索引。

```bash
cd /mnt/e/MSul/battery_materials_agent
python training/expand_dataset.py --dry-run
python training/expand_dataset.py
python training/validate_dataset.py --train training/expanded_train.jsonl --eval training/expanded_eval.jsonl --test training/expanded_test.jsonl
```

输出包括：

- `training/expanded_train.jsonl`、`training/expanded_eval.jsonl`、`training/expanded_test.jsonl`
- `training/expanded_manifest.json`（来源、计数、确定性 split 规则）
- `finetune/data/train.jsonl`、`finetune/data/validation.jsonl`、`finetune/data/test.jsonl`

同一 DOI 的所有样本使用同一 paper group，不会一部分进入训练集、另一部分
进入验证或测试集。多论文样本按来源连通分组绑定。验证集用于调参和选 checkpoint；测试集在方案固定后用于最终评估。不要把旧二路数据与新三路留出数据混合训练。元数据模板评估不能代替独立人工科研问题。

隔离保证仅针对本次数据版本。旧 adapter 可能已见过新划分中的测试论文或问题；重新划分不能消除历史暴露。评估新方案时，应从基础模型重新训练新 adapter，并保留额外的未参与历史开发的人工问题/新来源，避免把模板测试分数当作真实科研准确率。

## 2. RTX 3060 6 GB 上训练

先用 5 步检查依赖和显存，再进行正式训练：

```bash
source /home/invalid_index/venvs/battery-lora/bin/activate
export HF_HUB_OFFLINE=1                 # 基础模型已在本地时使用
python finetune/train_qlora.py --model /mnt/e/MSul/models/Qwen2.5-1.5B-Instruct \
  --max-steps 5 --precision auto --output finetune/outputs/qwen25-battery-lora-20261008-smoke
python finetune/train_qlora.py --model /mnt/e/MSul/models/Qwen2.5-1.5B-Instruct \
  --precision auto --output finetune/outputs/qwen25-battery-lora-20261008
```

训练结束应检查输出目录中的 `adapter_model.safetensors`、`adapter_config.json`
和 `trainer_state.json`，并确认终端退出码为 0。扩展数据集变大后，训练时间会
增加；不要把训练集 loss 当成独立测试结果。

当前 `finetune/train_qlora.py` 使用 `packing=False`、`padding_free=False`。
在本机 SDPA/eager attention 配置下，不应直接启用 TRL 的无填充打包：没有
兼容的分块注意力实现时，样本之间可能互相注意，影响训练目标。不要只为
加快速度消除这个警告。5 步 smoke 只验证 GPU、反向传播和保存流程，不是
可部署模型的质量证明；正式训练使用独立目录，不覆盖已有 adapter。

## 3. 启动本地 PEFT 适配器服务

服务不包含任何密钥，也不对公网监听。它加载基础模型和 LoRA adapter，提供
`GET /health` 与 `POST /v1/chat/completions`：

```bash
cd /mnt/e/MSul/battery_materials_agent
source /home/invalid_index/venvs/battery-lora/bin/activate
python finetune/serve_adapter.py \
  --base-model /mnt/e/MSul/models/Qwen2.5-1.5B-Instruct \
  --adapter finetune/outputs/qwen25-battery-lora-20261008 \
  --host 127.0.0.1 --port 8766 --max-input-tokens 4096 --max-new-tokens 512
```

CUDA 服务默认使用 NF4 4-bit 量化以适配 RTX 3060 6 GB；可显式使用
`--load-in-4bit`，或在显存充足时使用 `--no-4bit`。CPU 回退时使用
`--device cpu --no-4bit`。

另开终端检查：

```bash
curl http://127.0.0.1:8766/health
curl http://127.0.0.1:8766/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"battery-qwen-lora","messages":[{"role":"user","content":"如何检查一次MD复现？"}],"max_tokens":200}'
```

## 4. 接入现有 Agent 的 RAG

现有 `rag.py` 使用 OpenAI-compatible endpoint。启动 Agent 前设置：

```bash
export BATTERY_AGENT_LLM_ENDPOINT=http://127.0.0.1:8766/v1/chat/completions
export BATTERY_AGENT_LLM_MODEL=battery-qwen-lora
export BATTERY_AGENT_LLM_TIMEOUT=120
# 6 GB 显卡本地服务的证据预算；超出后 RAG 会优先裁剪证据包而不是让服务 OOM。
export BATTERY_AGENT_LLM_MAX_EVIDENCE_CHARS=4000
# 控制每次生成长度；先用 256，回答需要更长时再改为 512。
export BATTERY_AGENT_LLM_MAX_TOKENS=256
python server.py
```

若同时启用证据检索，模型只负责根据 Agent 注入的证据组织回答；新增 LoRA
并不会替代 RAG，也不会自动增加论文事实。建议保留原有的引用、参数和边界
检查，并用未参与训练的人工问题做回归测试。

## 5. 常见问题

固定方案后，从 `finetune/data/test.jsonl` 向模型发送 system/user 消息，记录 `id` 与 `response`；不要把参考 assistant 答案发给模型。运行 `python training/evaluate_model.py --eval finetune/data/test.jsonl --predictions predictions.jsonl` 检查行为，再核验未参与训练的真实科研问题。低 loss 或引用格式正确不直接证明科学正确。

- `HFValidationError`：传入的本地模型目录不存在，检查该目录下是否有
  `config.json`、tokenizer 文件和模型权重。
- `Failed to find C compiler` 或 `Python.h`：在 WSL 安装
  `build-essential` 和 `python3.10-dev`。
- BF16/FP16 GradScaler 错误：使用 `--precision auto`，不要同时启用两种精度。
- `bitsandbytes` 缺失：安装与 CUDA/PyTorch 匹配的 bitsandbytes；CPU 测试使用
  `--device cpu --no-4bit`，但会占用更多内存。
- 服务请求超过 `--max-input-tokens` 会返回 HTTP 413，不会静默截断证据；GPU
  正在处理另一请求时返回 HTTP 503，请稍后重试。
- 显存不足：降低脚本中的序列长度或改用 `training/train_qlora.py` 的
  Qwen3-0.6B 保守配置；不要仅靠增大 batch size。
