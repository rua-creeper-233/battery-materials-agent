"""Focused regression tests for the metadata-only dataset boundary."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from training.expand_dataset import ROOT, build, load_json, merge_records, public_resources, split, write
from training import validate_dataset


def example(row_id: str, groups: list[str], answer: str = "answer", split_name: str = "pending") -> dict:
    packet = {"papers": [{"source_id": f"P{i}", "paper_id": group} for i, group in enumerate(groups, 1)]}
    return {
        "id": row_id,
        "split": split_name,
        "requires_citation": True,
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "证据包(JSON)：" + json.dumps(packet) + "\n问题"},
            {"role": "assistant", "content": answer + " " + " ".join(f"[P{i}]" for i in range(1, len(groups) + 1))},
        ],
        "provenance": {
            "source_paper_ids": groups,
            "source_group_ids": groups,
            "source_fields": ["title"],
            "source_urls": ["https://doi.org/10.1234/example"],
        },
    }


class DatasetSplitTests(unittest.TestCase):
  def test_public_resource_sanitizer_rejects_credentials_sensitive_queries_and_private_visibility(self):
    paper = {"resources": [
      {"label": "credential", "url": "https://user:secret@github.com/org/repo"},
      {"label": "token", "url": "https://github.com/org/repo?access_token=secret"},
      {"label": "private", "url": "https://github.com/org/private", "visibility": "private"},
      {"label": "public", "url": "https://github.com/org/repo", "visibility": "public"},
      {"label": "legacy", "url": "https://github.com/org/legacy"},
    ]}
    self.assertEqual([x["label"] for x in public_resources(paper)], ["public", "legacy"])

  def test_frozen_generator_three_way_validator_integration(self):
    papers = merge_records(load_json(ROOT / "data" / "papers.json") + load_json(ROOT / "data" / "paper_expansion_20260920.json"))
    rows = build(papers)
    train, evaluation, test = split(rows)
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      paths = [root / "train.jsonl", root / "eval.jsonl", root / "test.jsonl"]
      for path, values in zip(paths, (train, evaluation, test)):
        write(path, values)
      old_argv = sys.argv
      try:
        sys.argv = ["validate", "--train", str(paths[0]), "--eval", str(paths[1]), "--test", str(paths[2])]
        validate_dataset.main()
      finally:
        sys.argv = old_argv

  def test_split_is_deterministic_and_binds_connected_components(self):
    rows = [example(f"r{i}", [f"paper:{i}"]) for i in range(8)]
    rows += [example("comparison", ["paper:0", "paper:joined"]), example("joined-row", ["paper:joined"])]
    first = split(rows)
    second = split([example(f"r{i}", [f"paper:{i}"]) for i in range(8)] + [example("comparison", ["paper:0", "paper:joined"]), example("joined-row", ["paper:joined"])])
    self.assertEqual([[x["id"] for x in bucket] for bucket in first], [[x["id"] for x in bucket] for bucket in second])
    locations = {row["id"]: index for index, bucket in enumerate(first) for row in bucket}
    self.assertEqual(locations["comparison"], locations["joined-row"])
    self.assertEqual(locations["comparison"], locations["r0"])
    self.assertTrue(all(first))


  def test_validator_rejects_cross_split_answer_and_paper_leakage(self):
    with tempfile.TemporaryDirectory() as directory:
      tmp_path = Path(directory)
      train = tmp_path / "train.jsonl"
      evaluation = tmp_path / "eval.jsonl"
      train.write_text(json.dumps(example("same", ["doi:10.x"], "same", "train")) + "\n", encoding="utf-8")
      evaluation.write_text(json.dumps(example("other", ["doi:10.x"], "same", "eval")) + "\n", encoding="utf-8")
      old_argv = sys.argv
      try:
        sys.argv = ["validate", "--train", str(train), "--eval", str(evaluation)]
        with self.assertRaises(AssertionError):
          validate_dataset.main()
      finally:
        sys.argv = old_argv


  def test_validator_rejects_invalid_citation_mapping(self):
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / "train.jsonl"
      evaluation = Path(directory) / "eval.jsonl"
      row = example("bad", ["paper:1"])
      row["split"] = "train"
      row["messages"][2]["content"] = "answer [P2]"
      path.write_text(json.dumps(row) + "\n", encoding="utf-8")
      valid_eval = example("eval", ["paper:2"], split_name="eval")
      evaluation.write_text(json.dumps(valid_eval) + "\n", encoding="utf-8")
      old_argv = sys.argv
      try:
        sys.argv = ["validate", "--train", str(path), "--eval", str(evaluation)]
        with self.assertRaises(AssertionError):
          validate_dataset.main()
      finally:
        sys.argv = old_argv

  def test_validator_rejects_mislabeled_explicit_file(self):
    with tempfile.TemporaryDirectory() as directory:
      train = Path(directory) / "train.jsonl"
      evaluation = Path(directory) / "eval.jsonl"
      train.write_text(json.dumps(example("wrong", ["paper:1"], split_name="eval")) + "\n", encoding="utf-8")
      evaluation.write_text(json.dumps(example("right", ["paper:2"], split_name="eval")) + "\n", encoding="utf-8")
      old_argv = sys.argv
      try:
        sys.argv = ["validate", "--train", str(train), "--eval", str(evaluation)]
        with self.assertRaises(AssertionError):
          validate_dataset.main()
      finally:
        sys.argv = old_argv


if __name__ == "__main__":
  unittest.main()
