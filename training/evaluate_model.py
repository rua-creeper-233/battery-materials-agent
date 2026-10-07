"""Coverage and citation-format metrics; scientific correctness needs review."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def rows(path: Path):
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            yield json.loads(raw)


def score(expected: list[dict], predictions: list[dict]) -> dict:
    expected_by_id = {row["id"]: row for row in expected}
    if len(expected_by_id) != len(expected):
        raise ValueError("Evaluation data contains duplicate IDs")
    predicted = {}
    for item in predictions:
        if item["id"] in predicted:
            raise ValueError("Predictions contain duplicate IDs")
        predicted[item["id"]] = str(item.get("response", item.get("text", "")))
    matched = cited = valid_cited = formatted = required = refusal_expected = refusal_ok = 0
    invalid_citation_rows = []
    for row_id, row in expected_by_id.items():
        if row_id not in predicted:
            continue
        matched += 1
        answer = predicted[row_id]
        citations = set(re.findall(r"\[(P\d+)\]", answer))
        sources = set(re.findall(r'"source_id"\s*:\s*"(P\d+)"', row["messages"][1]["content"]))
        if row.get("requires_citation"):
            required += 1
            cited += bool(citations)
            valid_cited += bool(citations) and bool(sources) and citations <= sources
            if citations - sources:
                invalid_citation_rows.append(row_id)
        formatted += bool(answer.strip()) and len(answer) <= 6000
        category = row.get("task") or row.get("category")
        if category in {"refusal", "boundary", "evidence_insufficient"}:
            refusal_expected += 1
            refusal_ok += bool(re.search(r"无法|不能|不确定|未提供|需要核验|证据不足|缺少|没有提供", answer))
    def rate(count: int, total: int):
        return round(count / total, 4) if total else None
    return {"expected": len(expected), "matched": matched,
            "coverage": rate(matched, len(expected)), "missing_predictions": len(expected) - matched,
            "unknown_prediction_ids": sorted(set(predicted) - set(expected_by_id)),
            "citation_rate": rate(cited, required), "valid_citation_format_rate": rate(valid_cited, required),
            "invalid_citation_rows": invalid_citation_rows,
            "format_rate": rate(formatted, matched), "refusal_keyword_rate": rate(refusal_ok, refusal_expected),
            "scientific_correctness": "not measured; valid reference IDs do not prove claim support"}


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
    result = score(expected, list(rows(args.predictions)))
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["matched"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
