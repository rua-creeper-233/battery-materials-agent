"""Tune explainable retrieval weights on a small, editable labelled query set."""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

from agent import BatteryResearchAgent, DEFAULT_SEARCH_WEIGHTS


ROOT = Path(__file__).resolve().parent
TRAINING = ROOT / "data" / "search_training.json"
OUTPUT = ROOT / "data" / "search_config.json"


def evaluate(agent: BatteryResearchAgent, examples: list[dict[str, Any]]) -> dict[str, float]:
    reciprocal_ranks: list[float] = []
    recalls: list[float] = []
    exact_top1 = 0
    for example in examples:
        relevant = set(example["relevant"])
        ranked = [paper["id"] for paper in agent.search(example["query"], limit=5)]
        rank = next((index for index, paper_id in enumerate(ranked, 1) if paper_id in relevant), None)
        reciprocal_ranks.append(1 / rank if rank else 0.0)
        recalls.append(len(relevant.intersection(ranked)) / len(relevant))
        exact_top1 += bool(ranked and ranked[0] in relevant)
    n = max(len(examples), 1)
    return {
        "mrr_at_5": sum(reciprocal_ranks) / n,
        "recall_at_5": sum(recalls) / n,
        "top1_accuracy": exact_top1 / n,
    }


def candidates() -> list[dict[str, float]]:
    variants: list[dict[str, float]] = []
    for title, methods, tags, summary in itertools.product(
        (4.0, 6.0, 8.0), (3.5, 5.0, 7.0), (3.0, 5.0), (1.0, 2.0)
    ):
        variants.append(
            {
                **DEFAULT_SEARCH_WEIGHTS,
                "title": title,
                "methods": methods,
                "tags": tags,
                "summary_evidence": summary,
            }
        )
    return variants


def main() -> None:
    payload = json.loads(TRAINING.read_text(encoding="utf-8"))
    examples = payload.get("training_examples", payload.get("examples", []))
    held_out = payload.get("held_out_examples", [])
    agent = BatteryResearchAgent(fulltext_path=None, search_config_path=None)
    best: tuple[float, dict[str, float], dict[str, float]] | None = None
    for weights in candidates():
        agent.search_weights = weights
        metrics = evaluate(agent, examples)
        objective = 0.65 * metrics["mrr_at_5"] + 0.35 * metrics["recall_at_5"]
        row = (objective, weights, metrics)
        if best is None or row[0] > best[0]:
            best = row
    assert best is not None
    objective, weights, metrics = best
    agent.search_weights = weights
    held_out_metrics = evaluate(agent, held_out) if held_out else {}
    output = {
        "schema_version": 1,
        "mode": "explainable_weighted_retrieval",
        "trained_on": "data/search_training.json",
        "training_examples": len(examples),
        "held_out_examples": len(held_out),
        "warning": "Small in-library relevance set; retrieval weight tuning only, not LLM training. The held-out set was used once for manual alias error analysis, so it is a regression set rather than an untouched production benchmark.",
        "objective": round(objective, 6),
        "training_metrics": {key: round(value, 6) for key, value in metrics.items()},
        "held_out_metrics": {key: round(value, 6) for key, value in held_out_metrics.items()},
        "metrics": {key: round(value, 6) for key, value in (held_out_metrics or metrics).items()},
        "weights": weights,
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
