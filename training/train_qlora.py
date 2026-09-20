"""Small, conservative QLoRA entry point for the local battery Q&A model."""
from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path(__file__).with_name("config_rtx3060_6gb.yaml")


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse flat scalar config without requiring PyYAML."""
    result: dict[str, Any] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        if value.lower() in {"true", "false"}:
            result[key] = value.lower() == "true"
        else:
            try:
                result[key] = float(value) if "." in value else int(value)
            except ValueError:
                result[key] = value.strip('"\'')
    return result


def load_training_rows(training_dir: Path, pattern: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(training_dir.glob(pattern)):
        if path.name == "eval.jsonl":
            continue
        for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not raw.strip():
                continue
            row = json.loads(raw)
            if row.get("split") == "train":
                if not isinstance(row.get("messages"), list) or len(row["messages"]) < 2:
                    raise ValueError(f"{path.name}:{line_no} has no usable messages")
                rows.append(row)
    if not rows:
        raise ValueError("no split=train rows found; run training/generate_dataset.py first")
    return rows


def validate_config(config: dict[str, Any]) -> list[str]:
    required = {"model_name", "output_dir", "max_seq_length", "per_device_train_batch_size",
                "gradient_accumulation_steps", "num_train_epochs", "learning_rate", "lora_r",
                "lora_alpha", "lora_dropout", "seed"}
    missing = sorted(required - config.keys())
    errors = [f"missing config keys: {', '.join(missing)}"] if missing else []
    if config.get("max_seq_length", 0) > 1024:
        errors.append("max_seq_length > 1024 is risky on a 6 GB GPU")
    if config.get("per_device_train_batch_size") != 1:
        errors.append("per_device_train_batch_size must remain 1 for the 6 GB profile")
    if config.get("load_in_4bit") is not True:
        errors.append("load_in_4bit must be true for this profile")
    if str(config.get("bnb_4bit_quant_type", "")).lower() != "nf4":
        errors.append("bnb_4bit_quant_type must be nf4")
    return errors


def dry_run(config_path: Path, training_dir: Path) -> int:
    config = parse_simple_yaml(config_path)
    errors = validate_config(config)
    if errors:
        print("CONFIG ERROR:\n- " + "\n- ".join(errors))
        return 2
    rows = load_training_rows(training_dir, str(config.get("train_glob", "*.jsonl")))
    paper_ids = {p for row in rows for p in row.get("provenance", {}).get("source_paper_ids", [])}
    print(f"dry-run OK: {len(rows)} train rows from {len(paper_ids)} source papers")
    print(f"model={config['model_name']} max_seq_length={config['max_seq_length']} "
          f"batch=1 accumulation={config['gradient_accumulation_steps']} 4bit=NF4 fp16=true")
    print("eval.jsonl is excluded by design; no model weights were loaded.")
    return 0


def train(config_path: Path, training_dir: Path) -> int:
    config = parse_simple_yaml(config_path)
    errors = validate_config(config)
    if errors:
        print("CONFIG ERROR:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 2
    rows = load_training_rows(training_dir, str(config.get("train_glob", "*.jsonl")))
    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig, prepare_model_for_kbit_training
        from transformers import (AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
                                  TrainingArguments)
        from trl import SFTTrainer
        try:
            from trl import SFTConfig
        except ImportError:  # TRL < 0.8 has no SFTConfig.
            SFTConfig = None
    except ImportError as exc:
        print("Missing training dependency: %s. Install the pinned packages in README_RTX3060.md; "
              "dry-run needs none." % exc, file=sys.stderr)
        return 3
    if not torch.cuda.is_available():
        print("CUDA GPU not detected. Install a CUDA-enabled PyTorch build and verify with nvidia-smi; "
              "do not fall back to CPU for this profile.", file=sys.stderr)
        return 4
    gpu = torch.cuda.get_device_properties(0)
    free, total = torch.cuda.mem_get_info(0)
    print(f"GPU: {gpu.name}, VRAM {gpu.total_memory / 2**30:.1f} GiB, "
          f"free now {free / 2**30:.1f} GiB / {total / 2**30:.1f} GiB")
    dtype = torch.float16
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=dtype, bnb_4bit_use_double_quant=True)
    tokenizer = AutoTokenizer.from_pretrained(config["model_name"], use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(config["model_name"], quantization_config=bnb,
                                                 torch_dtype=dtype, device_map="auto")
    model = prepare_model_for_kbit_training(model)
    dataset = Dataset.from_list([{"messages": row["messages"]} for row in rows])
    lora = LoraConfig(r=int(config["lora_r"]), lora_alpha=int(config["lora_alpha"]),
                      lora_dropout=float(config["lora_dropout"]), bias="none",
                      task_type="CAUSAL_LM", target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])
    common_args = dict(
        output_dir=str(config["output_dir"]),
        num_train_epochs=float(config["num_train_epochs"]),
        learning_rate=float(config["learning_rate"]),
        per_device_train_batch_size=1,
        gradient_accumulation_steps=int(config["gradient_accumulation_steps"]),
        fp16=True,
        gradient_checkpointing=True,
        logging_steps=int(config["logging_steps"]),
        save_steps=int(config["save_steps"]),
        seed=int(config["seed"]),
        report_to="none",
    )
    # Current TRL moved the sequence-length setting into SFTConfig as
    # ``max_length``.  Older TRL releases expose ``max_seq_length`` directly on
    # SFTTrainer, so keep a narrow compatibility branch instead of passing the
    # deprecated argument to every version.
    trainer_params = inspect.signature(SFTTrainer).parameters
    args = None
    configured_length = False
    if SFTConfig is not None:
        sft_params = inspect.signature(SFTConfig).parameters
        length_key = next((key for key in ("max_length", "max_seq_length") if key in sft_params), None)
        if length_key is None:
            print("Installed TRL exposes SFTConfig but neither max_length nor max_seq_length; "
                  "refusing to train without an explicit sequence-length bound.", file=sys.stderr)
            return 5
        try:
            args = SFTConfig(**common_args, **{length_key: int(config["max_seq_length"])})
            configured_length = True
        except TypeError as exc:
            print(f"Installed TRL SFTConfig rejected {length_key}: {exc}", file=sys.stderr)
            return 5
    if args is None:
        if "max_seq_length" not in trainer_params:
            print("Installed TRL has no SFTConfig and SFTTrainer has no max_seq_length; "
                  "refusing to train without an explicit sequence-length bound.", file=sys.stderr)
            return 5
        args = TrainingArguments(**common_args)
        configured_length = True
    trainer_kwargs = dict(model=model, args=args, train_dataset=dataset, peft_config=lora)
    if "processing_class" in trainer_params:
        trainer_kwargs["processing_class"] = tokenizer
    elif "tokenizer" in trainer_params:
        trainer_kwargs["tokenizer"] = tokenizer
    if "max_seq_length" in trainer_params and SFTConfig is None:
        trainer_kwargs["max_seq_length"] = int(config["max_seq_length"])
    if not configured_length:
        print("No explicit sequence length was configured; refusing to train.", file=sys.stderr)
        return 5
    trainer = SFTTrainer(**trainer_kwargs)
    trainer.train()
    trainer.save_model(str(config["output_dir"]))
    tokenizer.save_pretrained(str(config["output_dir"]))
    print(f"saved adapter to {config['output_dir']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Train a conservative QLoRA battery Q&A adapter on RTX 3060 6GB.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--training-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--dry-run", action="store_true", help="validate config/data without ML imports or downloads")
    args = parser.parse_args()
    return dry_run(args.config, args.training_dir) if args.dry_run else train(args.config, args.training_dir)


if __name__ == "__main__":
    raise SystemExit(main())
