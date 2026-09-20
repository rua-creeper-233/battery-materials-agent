"""Dependency-free metrics for predictions against eval JSONL rows."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def rows(path: Path):
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            yield json.loads(raw)


def main() -> int:
    ap = argparse.ArgumentParser(description="Score citation, format and refusal behavior.")
    ap.add_argument("--eval", type=Path, default=Path(__file__).with_name("eval.jsonl"))
    ap.add_argument("--predictions", type=Path, help="JSONL with id and response fields")
    args = ap.parse_args()
    expected = list(rows(args.eval))
    if not args.predictions:
        print(f"eval audit OK: {len(expected)} held-out rows; provide --predictions to score a model")
        print("No model was loaded and no training data was used.")
        return 0
    predicted = {r["id"]: str(r.get("response", r.get("text", ""))) for r in rows(args.predictions)}
    seen = cited = formatted = refusal_expected = refusal_ok = 0
    for row in expected:
        if row["id"] not in predicted:
            continue
        seen += 1
        answer = predicted[row["id"]]
        if row.get("requires_citation"):
            cited += int(bool(re.search(r"\[P\d+\]", answer)))
        formatted += int(bool(answer.strip()) and len(answer) <= 6000)
        wants_refusal = row.get("task") in {"refusal", "boundary", "evidence_insufficient"} or row.get("category") == "refusal"
        if wants_refusal:
            refusal_expected += 1
            refusal_ok += int(bool(re.search(r"无法|不能|不确定|未提供|需要核验|证据不足", answer)))
    def pct(n: int, d: int) -> str:
        return f"{100*n/d:.1f}%" if d else "n/a"
    citation_den = sum(1 for r in expected if r.get("id") in predicted and r.get("requires_citation"))
    print(json.dumps({"matched": seen, "citation_rate": pct(cited, citation_den),
                      "format_rate": pct(formatted, seen), "refusal_rate": pct(refusal_ok, refusal_expected)}, ensure_ascii=False))
    return 0 if seen else 2


if __name__ == "__main__":
    raise SystemExit(main())
