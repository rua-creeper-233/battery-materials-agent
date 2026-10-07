"""Check safe training defaults without importing CUDA/TRL or loading a model."""
import ast
import inspect
import unittest
from pathlib import Path


class TrainingConfigurationTests(unittest.TestCase):
    def test_non_flash_attention_does_not_pack_examples(self):
        source = Path(__file__).resolve().parents[1] / "finetune" / "train_qlora.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_training_args")
        class Config:
            def __init__(self, output_dir=None, max_steps=None, packing=None, padding_free=None, fp16=None, bf16=None):
                self.packing, self.padding_free = packing, padding_free
                self.fp16, self.bf16 = fp16, bf16
        namespace = {"inspect": inspect, "SFTConfig": Config, "precision": "bf16"}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), namespace)
        result = namespace["build_training_args"]("unused", 5)
        self.assertIs(result.packing, False)
        self.assertIs(result.padding_free, False)
        self.assertIs(result.bf16, True)
        self.assertIs(result.fp16, False)


if __name__ == "__main__":
    unittest.main()
