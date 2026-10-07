import argparse
import inspect
from pathlib import Path
import torch

from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer


parser = argparse.ArgumentParser()
parser.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
parser.add_argument("--train", default="finetune/data/train.jsonl")
parser.add_argument("--validation", default="finetune/data/validation.jsonl")
parser.add_argument("--output", default="finetune/outputs/qwen25-battery-lora")
parser.add_argument("--max-steps", type=int, default=-1)
parser.add_argument(
    "--precision",
    choices=("auto", "fp16", "bf16"),
    default="auto",
    help="混合精度模式；auto 会在支持时使用 BF16，避免 BF16 梯度被 FP16 GradScaler 处理。",
)
args = parser.parse_args()

model_id = args.model

# A missing local directory is otherwise interpreted by Hugging Face as a
# repository ID, producing a misleading HFValidationError.  Fail early with
# the actual fix when the user requested an explicit local Unix path.
if model_id.startswith(("/", "./", "../")) and not Path(model_id).is_dir():
    raise SystemExit(
        f"本地模型目录不存在：{model_id}\n"
        "请先下载模型，或把 --model 改为包含 config.json 的实际目录。"
    )

dataset = load_dataset(
    "json",
    data_files={
        "train": args.train,
        "validation": args.validation,
    },
)

if not torch.cuda.is_available():
    raise SystemExit(
        "未检测到 CUDA GPU。请在 WSL 中确认 nvidia-smi 和 CUDA 版 PyTorch 可用。"
    )

if args.precision == "auto":
    bf16_supported = bool(
        getattr(torch.cuda, "is_bf16_supported", lambda: False)()
    )
    precision = "bf16" if bf16_supported else "fp16"
else:
    precision = args.precision

compute_dtype = torch.bfloat16 if precision == "bf16" else torch.float16
print(
    f"混合精度：{precision.upper()}；计算类型：{compute_dtype}; "
    f"GPU：{torch.cuda.get_device_name(0)}"
)

tokenizer = AutoTokenizer.from_pretrained(
    model_id,
    use_fast=True,
)

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=compute_dtype,
)

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    torch_dtype=compute_dtype,
    device_map={"": 0},
)

model.config.use_cache = False

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,
    target_modules="all-linear",
    bias="none",
    task_type="CAUSAL_LM",
)

def build_training_args(output_dir: str, max_steps: int):
    """Build SFTConfig across older and newer TRL releases.

    TRL has moved/renamed several TrainingArguments fields over time.  In
    particular, older SFTConfig versions do not accept ``warmup_ratio``.
    Filter optional fields by the installed signature rather than failing
    before training starts.
    """
    supported = inspect.signature(SFTConfig).parameters
    candidates = {
        "output_dir": output_dir,
        "num_train_epochs": 2,
        "max_steps": max_steps,
        "per_device_train_batch_size": 1,
        "per_device_eval_batch_size": 1,
        "gradient_accumulation_steps": 8,
        "gradient_checkpointing": True,
        "learning_rate": 2e-4,
        "lr_scheduler_type": "cosine",
        "warmup_ratio": 0.05,
        "max_grad_norm": 0.3,
        # Do not enable both.  In particular, FP16 GradScaler cannot unscale
        # BF16 gradients on this PyTorch/CUDA combination.
        "fp16": precision == "fp16",
        "bf16": precision == "bf16",
        "optim": "paged_adamw_8bit",
        "packing": True,
        "logging_steps": 5,
        "eval_steps": 50,
        "save_strategy": "steps",
        "save_steps": 50,
        "save_total_limit": 2,
        "report_to": "tensorboard",
        "dataset_num_proc": 1,
        "seed": 42,
    }

    # Sequence length was called max_seq_length in older TRL versions and
    # max_length in newer versions.
    if "max_length" in supported:
        candidates["max_length"] = 1024
    elif "max_seq_length" in supported:
        candidates["max_seq_length"] = 1024

    if "eval_strategy" in supported:
        candidates["eval_strategy"] = "steps"
    elif "evaluation_strategy" in supported:
        candidates["evaluation_strategy"] = "steps"

    filtered = {key: value for key, value in candidates.items() if key in supported}
    ignored = sorted(set(candidates) - set(filtered))
    if ignored:
        print("兼容性处理：跳过当前 TRL 不支持的参数：" + ", ".join(ignored))
    return SFTConfig(**filtered)


training_args = build_training_args(args.output, args.max_steps)

trainer_params = inspect.signature(SFTTrainer).parameters
trainer_kwargs = {
    "model": model,
    "args": training_args,
    "train_dataset": dataset["train"],
    "eval_dataset": dataset["validation"],
    "peft_config": lora_config,
}
if "processing_class" in trainer_params:
    trainer_kwargs["processing_class"] = tokenizer
elif "tokenizer" in trainer_params:
    trainer_kwargs["tokenizer"] = tokenizer
if "max_seq_length" in trainer_params and "max_length" not in inspect.signature(SFTConfig).parameters:
    trainer_kwargs["max_seq_length"] = 1024

trainer = SFTTrainer(**trainer_kwargs)

train_result = trainer.train()
trainer.save_model(args.output)
trainer.save_state()
tokenizer.save_pretrained(args.output)
print(
    "训练完成："
    f"global_step={train_result.global_step}, "
    f"training_loss={train_result.training_loss:.6f}, "
    f"输出目录={args.output}"
)
