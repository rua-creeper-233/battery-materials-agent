"""Small dependency-free smoke test for generated Q&A JSONL files."""
from __future__ import annotations

import json
import re
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    rows = []
    train_papers: set[str] = set()
    eval_papers: set[str] = set()
    train_groups: set[str] = set()
    eval_groups: set[str] = set()
    seen_answers: dict[str, str] = {}
    for path in sorted(root.glob("*.jsonl")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            assert len(row["messages"]) == 3, (path, line_no)
            assert row["messages"][0]["role"] == "system"
            assert row["messages"][1]["role"] == "user"
            assert row["messages"][2]["role"] == "assistant"
            assert row["provenance"]["source_paper_ids"] is not None
            assert row["split"] in {"train", "eval"}
            if row.get("requires_citation"):
                user_text = row["messages"][1]["content"]
                assistant_text = row["messages"][2]["content"]
                assert "证据包(JSON" in user_text, (path, line_no, "citation row lacks evidence packet")
                assert re.search(r"\[P\d+\]", assistant_text), (path, line_no, "citation row lacks [P#]")
            serialized = json.dumps(row, ensure_ascii=False)
            assert "fulltext_chunks.jsonl" not in serialized
            assert "BEGIN PDF" not in serialized
            rows.append(row)
    assert rows, "no JSONL rows found"
    for row in rows:
        papers = set(row["provenance"].get("source_paper_ids") or [])
        if row["split"] == "train":
            train_papers.update(papers)
            train_groups.update(row["provenance"].get("source_group_ids") or [])
        else:
            eval_papers.update(papers)
            eval_groups.update(row["provenance"].get("source_group_ids") or [])
    overlap = train_papers & eval_papers
    assert not overlap, f"paper leakage across train/eval: {sorted(overlap)[:5]}"
    group_overlap = train_groups & eval_groups
    assert not group_overlap, f"source-group leakage across train/eval: {sorted(group_overlap)[:5]}"
    for row in rows:
        answer = row["messages"][2]["content"]
        prior = seen_answers.get(answer)
        if prior and prior != row["split"]:
            raise AssertionError(f"exact assistant answer crosses train/eval: {prior} vs {row['split']}")
        seen_answers[answer] = row["split"]
    print(f"validated {len(rows)} rows")


if __name__ == "__main__":
    main()
