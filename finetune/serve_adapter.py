#!/usr/bin/env python3
"""Serve a local PEFT/QLoRA adapter through an OpenAI-compatible endpoint.

Example (WSL, RTX 3060 6 GB):
  python finetune/serve_adapter.py --base-model /mnt/e/MSul/models/Qwen2.5-1.5B-Instruct \
      --adapter finetune/outputs/qwen25-battery-lora --port 8766
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-model", required=True, help="本地基础模型目录或 Hugging Face model id")
    parser.add_argument("--adapter", required=True, help="包含 adapter_config.json 的 PEFT 输出目录")
    parser.add_argument("--model", default="battery-qwen-lora", help="OpenAI 请求中的模型名")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--device", default="auto", help="auto/cuda/cpu")
    parser.add_argument("--dtype", choices=("auto", "float16", "bfloat16", "float32"), default="auto")
    quant = parser.add_mutually_exclusive_group()
    quant.add_argument("--load-in-4bit", dest="load_in_4bit", action="store_true", help="CUDA上使用NF4 4-bit（默认）")
    quant.add_argument("--no-4bit", dest="load_in_4bit", action="store_false", help="禁用4-bit，使用完整精度权重")
    parser.set_defaults(load_in_4bit=None)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--max-input-tokens", type=int, default=1536, help="单次请求最大输入token数；超限返回413，不截断证据")
    parser.add_argument("--temperature", type=float, default=0.2)
    return parser


def load_model(args: argparse.Namespace):
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    use_cuda = args.device in ("auto", "cuda") and torch.cuda.is_available()
    device = "cuda" if use_cuda else "cpu"
    if args.device == "cuda" and not use_cuda:
        raise RuntimeError("请求了 CUDA，但当前环境没有可用 CUDA。")
    if args.dtype == "auto":
        dtype = torch.float16 if use_cuda else torch.float32
    else:
        dtype = {"float16": torch.float16, "bfloat16": torch.bfloat16, "float32": torch.float32}[args.dtype]
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    kwargs: dict[str, Any] = {"torch_dtype": dtype}
    load_in_4bit = use_cuda if args.load_in_4bit is None else args.load_in_4bit
    if load_in_4bit and not use_cuda:
        raise RuntimeError("4-bit NF4 仅在 CUDA 模式启用；CPU 请使用 --no-4bit。")
    if load_in_4bit:
        from transformers import BitsAndBytesConfig
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=dtype,
        )
    if use_cuda:
        kwargs["device_map"] = {"": 0}
    base = AutoModelForCausalLM.from_pretrained(args.base_model, **kwargs)
    model = PeftModel.from_pretrained(base, args.adapter)
    model.eval()
    if not use_cuda:
        model.to(device)
    return model, tokenizer, device, dtype


class Handler(BaseHTTPRequestHandler):
    model: Any = None
    tokenizer: Any = None
    device: str = "cpu"
    model_name: str = "battery-qwen-lora"
    max_new_tokens: int = 512
    max_input_tokens: int = 1536
    temperature: float = 0.2
    generation_lock = threading.Lock()

    def _json(self, payload: dict[str, Any], status: int = 200) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._json({"status": "ok", "model": self.model_name})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self._json({"error": "not found"}, 404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 2 * 1024 * 1024:
                raise ValueError("Content-Length must be positive and at most 2 MiB")
            payload = json.loads(self.rfile.read(size))
            messages = payload.get("messages")
            if not isinstance(messages, list) or not messages:
                raise ValueError("messages must be a non-empty list")
            prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            # Tokenize on CPU first so oversized evidence is rejected before
            # any tensor is moved to the 6 GB GPU. Never silently truncate.
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=False)
            input_tokens = int(inputs["input_ids"].shape[1])
            if input_tokens > self.max_input_tokens:
                self._json({"error": {"message": f"input has {input_tokens} tokens; limit is {self.max_input_tokens}; evidence was not truncated", "type": "input_too_long"}}, 413)
                return
            if not self.generation_lock.acquire(blocking=False):
                self._json({"error": {"message": "GPU generation is busy; retry later", "type": "server_busy"}}, 503)
                return
            import torch
            try:
                # Serialize device transfer and generation: concurrent requests
                # can otherwise exhaust VRAM or corrupt generation state.
                inputs = inputs.to(self.device)
                with torch.inference_mode():
                    generation = {
                        "max_new_tokens": min(max(int(payload.get("max_tokens", self.max_new_tokens)), 1), self.max_new_tokens),
                        "do_sample": self.temperature > 0,
                        "pad_token_id": self.tokenizer.pad_token_id,
                    }
                    if self.temperature > 0:
                        generation["temperature"] = max(self.temperature, 0.01)
                    output = self.model.generate(**inputs, **generation)
            finally:
                self.generation_lock.release()
            generated = output[0][inputs["input_ids"].shape[1]:]
            content = self.tokenizer.decode(generated, skip_special_tokens=True).strip()
            now = int(time.time())
            self._json({"id": f"chatcmpl-local-{now}", "object": "chat.completion", "created": now, "model": payload.get("model", self.model_name), "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}], "usage": {"prompt_tokens": int(inputs["input_ids"].shape[1]), "completion_tokens": int(generated.shape[0]), "total_tokens": int(output.shape[1])}})
        except Exception as exc:
            self._json({"error": {"message": str(exc), "type": type(exc).__name__}}, 400)

    def log_message(self, fmt: str, *args: Any) -> None:
        print("[adapter-server] " + (fmt % args))


def main() -> None:
    args = build_parser().parse_args()
    model, tokenizer, device, _dtype = load_model(args)
    Handler.model, Handler.tokenizer, Handler.device = model, tokenizer, device
    Handler.model_name, Handler.max_new_tokens, Handler.max_input_tokens, Handler.temperature = args.model, min(max(args.max_new_tokens, 1), 2048), min(max(args.max_input_tokens, 1), 8192), args.temperature
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"adapter server listening on http://{args.host}:{args.port}; model={args.model}; device={device}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nserver stopped")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
