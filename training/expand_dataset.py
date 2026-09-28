#!/usr/bin/env python3
"""Expand the local, metadata-only battery-materials Q&A set.

This generator deliberately reads only curated JSON metadata.  It never reads
PDFs or ``fulltext_chunks.jsonl`` and therefore cannot silently turn an
unverified full-text claim into training supervision.  DOI/group-aware splits
keep variants of one paper on the same side of the train/eval boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_FIELDS = {
    "title", "doi", "url", "role", "summary", "systems", "methods",
    "properties", "protocol_steps", "scope_note", "evidence", "tags_zh",
}


def load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict):
        value = value.get("papers", value.get("items", []))
    return [item for item in value if isinstance(item, dict)]


def norm_doi(value: Any) -> str:
    text = str(value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    return text.rstrip(" .;/")


def compact(value: Any, limit: int = 900) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def values(paper: dict[str, Any], field: str) -> list[str]:
    value = paper.get(field) or []
    if not isinstance(value, list):
        value = [value]
    return [compact(item, 220) for item in value if str(item).strip()]


def merge_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge by DOI, retaining curated base fields and filling empty fields."""
    merged: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(records):
        paper = {key: value for key, value in raw.items() if key in ALLOWED_FIELDS or key in {"id", "collection", "difficulty"}}
        key = norm_doi(paper.get("doi")) or f"id:{paper.get('id') or index}"
        if key not in merged:
            merged[key] = paper
            continue
        target = merged[key]
        for field, value in paper.items():
            if not target.get(field) and value:
                target[field] = value
            elif isinstance(target.get(field), list) and isinstance(value, list):
                seen = {str(x) for x in target[field]}
                target[field].extend(x for x in value if str(x) not in seen)
    return sorted(merged.values(), key=lambda p: (norm_doi(p.get("doi")), str(p.get("id", ""))))


def ref(paper: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    pid = str(paper.get("id") or norm_doi(paper.get("doi")) or "unknown")
    evidence = paper.get("evidence") or []
    return {
        "source_paper_ids": [pid],
        "source_group_ids": ["paper:" + (norm_doi(paper.get("doi")) or pid)],
        "source_fields": fields,
        "doi": paper.get("doi"),
        "source_urls": [paper["url"]] if paper.get("url") else [],
        "evidence_references": [
            {"claim": compact(item.get("claim"), 500), "basis": compact(item.get("basis"), 300), "strength": item.get("strength")}
            for item in evidence if isinstance(item, dict) and item.get("claim")
        ],
    }


def context(papers: list[dict[str, Any]], fields: list[str]) -> str:
    packet = []
    for i, paper in enumerate(papers, 1):
        item = {"source_id": f"P{i}", "paper_id": paper.get("id"), "title": paper.get("title"), "doi": paper.get("doi")}
        for field in fields:
            if field == "evidence":
                item[field] = [
                    {"claim": compact(x.get("claim"), 500), "basis": compact(x.get("basis"), 300), "strength": x.get("strength")}
                    for x in (paper.get("evidence") or []) if isinstance(x, dict) and x.get("claim")
                ]
            elif field == "protocol_steps":
                item[field] = [compact(x, 500) for x in values(paper, field)]
            else:
                item[field] = compact(paper.get(field), 800) if not isinstance(paper.get(field), list) else values(paper, field)
        packet.append(item)
    return json.dumps({"papers": packet}, ensure_ascii=False, sort_keys=True)


def row(row_id: str, category: str, question: str, answer: str, papers: list[dict[str, Any]], fields: list[str], ctx_fields: list[str]) -> dict[str, Any]:
    refs = {"source_paper_ids": [], "source_group_ids": [], "source_fields": [], "doi": [], "source_urls": [], "evidence_references": []}
    for paper in papers:
        item = ref(paper, fields)
        for key in refs:
            value = item.get(key)
            if isinstance(value, list):
                refs[key].extend(x for x in value if x not in refs[key])
            elif value and value not in refs[key]:
                refs[key].append(value)
    refs["generator_source"] = "training/expand_dataset.py"
    refs["copyright_note"] = "仅使用结构化元数据；未复制PDF或全文段落。"
    ids = refs["source_group_ids"]
    return {
        "id": row_id,
        "category": category,
        "task": category,
        "difficulty": "普通",
        "split": "pending",
        "requires_citation": True,
        "messages": [
            {"role": "system", "content": "你是电池材料计算科研助理。只依据给定证据回答；证据不足时明确说明。"},
            {"role": "user", "content": "证据包(JSON，仅允许使用其中信息)：\n" + context(papers, ctx_fields) + "\n\n问题：" + question},
            {"role": "assistant", "content": answer},
        ],
        "provenance": {**refs, "source_group_ids": ids},
    }


def build(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for paper in papers:
        pid = str(paper.get("id") or norm_doi(paper.get("doi")) or "paper")
        title = compact(paper.get("title"), 240)
        systems = ", ".join(values(paper, "systems")) or "记录未列出"
        methods = ", ".join(values(paper, "methods")) or "记录未列出"
        props = ", ".join(values(paper, "properties")) or "记录未列出"
        role = compact(paper.get("role") or paper.get("summary") or "记录未提供", 700)
        scope = compact(paper.get("scope_note") or "结构化记录未提供边界说明", 800)
        rows.append(row(f"expanded-{pid}-scope", "factual", f"《{title}》研究什么、对象和方法是什么？", f"记录将其定位为：{role}。体系：{systems}；方法：{methods}。这里只能据此概括，具体参数仍需核对原文。[P1]", [paper], ["title", "role", "systems", "methods"], ["role", "systems", "methods", "evidence"]))
        rows.append(row(f"expanded-{pid}-properties", "factual", f"《{title}》关注哪些可计算性质？", f"针对记录 {pid}，结构化字段列出的性质为：{props}。记录没有列出的性质不能从标题或方法名称推断。[P1]", [paper], ["title", "properties"], ["properties", "evidence"]))
        steps = values(paper, "protocol_steps")
        body = "\n".join(f"{i}. {step}" for i, step in enumerate(steps, 1)) if steps else f"记录 {pid} 没有给出具体协议步骤；应回到正文和补充材料核对输入、版本、单位与收敛标准。"
        rows.append(row(f"expanded-{pid}-workflow", "workflow", f"我想复现《{title}》，应从哪里开始？", f"针对记录 {pid}，先固定软件、数据版本并检查体系与单位；可按结构化记录执行：\n{body}\n不要把小规模冒烟测试当成物性复现。[P1]", [paper], ["title", "protocol_steps", "methods", "scope_note"], ["protocol_steps", "methods", "scope_note", "evidence"]))
        rows.append(row(f"expanded-{pid}-limits", "limitation", f"《{title}》的结果能否直接外推到我的新体系？", f"针对记录 {pid}，不能仅凭该记录直接外推。已记录的边界是：{scope}。应先复现原体系，再逐项验证新体系的结构、参数、收敛和独立数据。[P1]", [paper], ["title", "systems", "scope_note"], ["systems", "scope_note", "evidence"]))
    # Pairwise comparison is based only on fields present in both records.
    for left, right in zip(papers[::2], papers[1::2]):
        lid = str(left.get("id") or norm_doi(left.get("doi")) or "left")
        rid = str(right.get("id") or norm_doi(right.get("doi")) or "right")
        lm, rm = ", ".join(values(left, "methods")) or "未列出", ", ".join(values(right, "methods")) or "未列出"
        rows.append(row(f"expanded-compare-{lid}-{rid}", "comparison", f"比较《{compact(left.get('title'), 180)}》和《{compact(right.get('title'), 180)}》的记录方法。", f"第一篇记录的方法：{lm}；第二篇记录的方法：{rm}。这只是字段层面的并列，不足以证明精度、成本或性能优劣。[P1][P2]", [left, right], ["title", "methods", "systems"], ["methods", "systems", "evidence"]))
    return sorted(rows, key=lambda x: x["id"])


def split(rows: list[dict[str, Any]], eval_mod: int = 7) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    # A comparison row links two paper groups.  Build connected components so
    # every variant of either paper follows the same split (no paper leakage).
    parent: dict[str, str] = {}
    def find(x: str) -> str:
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    for item in rows:
        groups = sorted(item["provenance"].get("source_group_ids") or ["example:" + item["id"]])
        for group in groups:
            find(group)
        for group in groups[1:]:
            union(groups[0], group)
    train, evaluation = [], []
    for item in rows:
        groups = sorted(item["provenance"].get("source_group_ids") or ["example:" + item["id"]])
        group = min(find(x) for x in groups)
        digest = hashlib.sha256(group.encode()).digest()[0]
        target = evaluation if digest % eval_mod == 0 else train
        item["split"] = "eval" if target is evaluation else "train"
        target.append(item)
    return train, evaluation


def write(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for x in rows), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--papers", type=Path, default=ROOT / "data" / "papers.json")
    parser.add_argument("--expansion", type=Path, default=ROOT / "data" / "paper_expansion_20260920.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    papers = merge_records(load_json(args.papers) + load_json(args.expansion))
    rows = build(papers)
    train, evaluation = split(rows)
    counts = {"papers": len(papers), "rows": len(rows), "train": len(train), "eval": len(evaluation), "seed": "sha256(source_group_id)", "sources": [str(args.papers), str(args.expansion)]}
    print(json.dumps(counts, ensure_ascii=False, indent=2))
    if args.dry_run:
        return
    write(ROOT / "training" / "expanded_train.jsonl", train)
    write(ROOT / "training" / "expanded_eval.jsonl", evaluation)
    write(ROOT / "finetune" / "data" / "train.jsonl", train)
    write(ROOT / "finetune" / "data" / "validation.jsonl", evaluation)
    manifest = {**counts, "policy": "metadata_only_no_fulltext_or_pdf_text", "split_rule": "sha256(source_group_id)[0] % 7 == 0 -> eval"}
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    (ROOT / "training" / "expanded_manifest.json").write_text(manifest_text, encoding="utf-8")
    (ROOT / "finetune" / "data" / "manifest.json").write_text(manifest_text, encoding="utf-8")


if __name__ == "__main__":
    main()
