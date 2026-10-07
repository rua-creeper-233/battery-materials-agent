# RTX 3060 Laptop 6 GB：本地 QLoRA 入门

更新：2026-10-08。已跑通的 Qwen2.5-1.5B 路线与新输出目录见 [训练与 Agent 接入](../FINETUNE_INTEGRATION.md)。本页 Qwen3-0.6B 是保守备选，显存占用依赖模型、序列长度、量化和环境。新版三路数据见 [项目状态](../guides/PROJECT_STATUS.md)；下方旧 `training/train_qlora.py` 默认读旧二路数据，若沿用它须先配置正确的数据路径。

这条路径只训练“如何回答”，不把论文全文写进模型。事实仍由现有 RAG/证据库提供。脚本只读取 `split=train`，明确排除 `training/eval.jsonl`。

## 推荐配置

默认 Qwen3-0.6B、4-bit NF4、FP16、LoRA、batch size 1、梯度累积 8、最大长度 768、2 个 epoch。6 GB 显存下从 0.6B 开始；确认稳定后才把 `model_name` 改成 Qwen3-1.7B。若 CUDA OOM，先降低 `max_seq_length` 到 512、增加 accumulation，不要把 batch 调大。

## 安装（建议 Windows + WSL2）

1. 在 Windows PowerShell 运行 `nvidia-smi`，确认驱动能看到 RTX 3060。
2. 在 WSL2/虚拟环境中，按 PyTorch 官方页面选择 CUDA 版本并安装。
3. 安装 Transformers、Datasets、PEFT、TRL、Accelerate、bitsandbytes。首次安装前固定版本并记录 `pip freeze`；不要把环境目录或模型权重提交到 Git。

官方入口：

- PyTorch：https://pytorch.org/get-started/locally/
- Qwen3-0.6B：https://huggingface.co/Qwen/Qwen3-0.6B
- Qwen3-1.7B：https://huggingface.co/Qwen/Qwen3-1.7B
- Transformers quantization：https://huggingface.co/docs/transformers/quantization/bitsandbytes
- PEFT LoRA：https://huggingface.co/docs/peft/main/conceptual_guides/lora
- TRL SFTTrainer：https://huggingface.co/docs/trl/sft_trainer

## 先验证，再训练

```powershell
cd E:\MSul\battery_materials_agent
python training\train_qlora.py --dry-run
python training\evaluate_model.py
```

dry-run 不导入 ML 包、不下载模型，也不会接触 `eval.jsonl`。实际训练：

```powershell
python training\train_qlora.py
```

训练完成后用 `training/evaluate_model.py --eval finetune/data/test.jsonl --predictions predictions.jsonl` 做最小评估。预测文件每行格式为 `{"id":"...", "response":"..."}`。至少检查引用率、格式率、拒答率，并人工抽查 20–50 条；不要只看 loss。

## 常见问题

- `CUDA not detected`：重新安装与驱动匹配的 CUDA PyTorch，并用 `python -c "import torch; print(torch.cuda.is_available())"` 检查。
- `CUDA out of memory`：确保没有浏览器/其他训练进程占显存；把长度改为 512，保持 batch=1；仍失败再换 0.6B。
- `bitsandbytes` 在原生 Windows 不兼容：优先使用 WSL2；不要下载来源不明的替代 DLL。
- 模型回答事实错误：不要继续加 epoch；先改进 RAG 证据、引用校验和评估集。

模型权重、缓存、机构账号、Zotero 数据库和私人 PDF 均不应提交到 GitHub。
