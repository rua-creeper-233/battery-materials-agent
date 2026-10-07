"""Small dependency-free smoke test for generated Q&A JSONL files."""
from __future__ import annotations

import json
import re
import argparse
from pathlib import Path
from urllib.parse import urlparse


def norm(value: object) -> str:
    text = str(value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    return text.rstrip(" .;/")


def validate_citations(row: dict, path: Path, line_no: int) -> None:
    user = row["messages"][1]["content"]
    refs = row["provenance"]
    packet_ids = set(re.findall(r'"source_id"\s*:\s*"(P\d+)"', user))
    packet_papers = set(re.findall(r'"paper_id"\s*:\s*"([^"]+)"', user))
    answer_refs = set(re.findall(r"\[P(\d+)\]", row["messages"][2]["content"]))
    if not answer_refs or not {"P" + x for x in answer_refs} <= packet_ids:
        raise AssertionError((path, line_no, "citation does not map to evidence packet"))
    if not refs.get("source_paper_ids") or not refs.get("source_group_ids"):
        raise AssertionError((path, line_no, "missing source provenance"))
    if {norm(x) for x in refs.get("source_paper_ids", [])} != {norm(x) for x in packet_papers}:
        raise AssertionError((path, line_no, "source paper IDs do not match evidence packet"))
    for url in list(refs.get("source_urls", [])) + [x.get("url") for x in refs.get("resource_urls", []) if isinstance(x, dict)]:
        parsed = urlparse(str(url))
        if parsed.scheme != "https" or not parsed.netloc:
            raise AssertionError((path, line_no, "invalid source URL"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, help="train JSONL; may be paired with --eval")
    parser.add_argument("--eval", type=Path, help="evaluation JSONL")
    parser.add_argument("--test", type=Path, help="test JSONL")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    supplied = [args.train, args.eval, args.test]
    if any(supplied) and not args.train:
        parser.error("--train is required when supplying --eval or --test")
    if args.test and not args.eval:
        parser.error("--eval is required when supplying --test")
    explicit = bool(args.train)
    paths = [(p, label) for p, label in ((args.train, "train"), (args.eval, "eval"), (args.test, "test")) if p] if explicit else [(p, None) for p in [
        root / "qa_factual.jsonl", root / "qa_workflow.jsonl",
        root / "qa_refusal.jsonl", root / "tool_traces.jsonl", root / "eval.jsonl",
    ]]
    rows = []
    train_papers: set[str] = set()
    split_papers: dict[str, set[str]] = {"train": set(), "eval": set(), "test": set()}
    train_groups: set[str] = set()
    split_groups: dict[str, set[str]] = {"train": set(), "eval": set(), "test": set()}
    seen_answers: dict[str, str] = {}
    seen_ids: dict[str, tuple[str, str]] = {}
    seen_user_answers: dict[str, str] = {}
    for path, expected_split in paths:
        if not path.exists():
            raise FileNotFoundError(path)
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            row_id = str(row.get("id", "")).strip()
            if not row_id:
                raise AssertionError((path, line_no, "missing row id"))
            answer = row.get("messages", [{}, {}, {}])[-1].get("content", "")
            user_key = str(row.get("messages", [{}, {}, {}])[1].get("content", "")) if len(row.get("messages", [])) > 1 else ""
            prior_user_answer = seen_user_answers.get(user_key)
            if prior_user_answer is not None and prior_user_answer != answer:
                raise AssertionError((path, line_no, "same user prompt has conflicting answers"))
            seen_user_answers[user_key] = answer
            prior_id = seen_ids.get(row_id)
            if prior_id is not None:
                raise AssertionError((path, line_no, "duplicate row id"))
            seen_ids[row_id] = (str(row.get("split")), answer)
            assert len(row["messages"]) == 3, (path, line_no)
            assert row["messages"][0]["role"] == "system"
            assert row["messages"][1]["role"] == "user"
            assert row["messages"][2]["role"] == "assistant"
            assert row["provenance"]["source_paper_ids"] is not None
            assert row["split"] in {"train", "eval", "test"}
            if expected_split and row["split"] != expected_split:
                raise AssertionError((path, line_no, f"row split {row['split']!r} is misplaced in {expected_split} file"))
            if row.get("requires_citation"):
                user_text = row["messages"][1]["content"]
                assistant_text = row["messages"][2]["content"]
                assert "证据包(JSON" in user_text, (path, line_no, "citation row lacks evidence packet")
                assert re.search(r"\[P\d+\]", assistant_text), (path, line_no, "citation row lacks [P#]")
                validate_citations(row, path, line_no)
            serialized = json.dumps(row, ensure_ascii=False)
            assert "fulltext_chunks.jsonl" not in serialized
            assert "BEGIN PDF" not in serialized
            rows.append(row)
    assert rows, "no JSONL rows found"
    for row in rows:
        papers = set(row["provenance"].get("source_paper_ids") or [])
        split = row["split"]
        split_papers[split].update(norm(x) for x in papers)
        split_papers[split].update(norm(x) for x in row["provenance"].get("doi", []) if norm(x))
        split_groups[split].update(norm(x) for x in row["provenance"].get("source_group_ids") or [])
    for left in split_papers:
        for right in split_papers:
            if left < right:
                assert not split_papers[left] & split_papers[right], f"paper leakage across {left}/{right}"
                assert not split_groups[left] & split_groups[right], f"source-group leakage across {left}/{right}"
    for row in rows:
        answer = row["messages"][2]["content"]
        prior = seen_answers.get(answer)
        if prior and prior != row["split"]:
            raise AssertionError(f"exact assistant answer crosses splits: {prior} vs {row['split']}")
        seen_answers[answer] = row["split"]
    print(f"validated {len(rows)} rows")


if __name__ == "__main__":
    main()
