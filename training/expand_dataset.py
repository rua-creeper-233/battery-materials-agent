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
from urllib.parse import parse_qsl, urlparse
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_FIELDS = {
    "title", "doi", "url", "role", "summary", "systems", "methods",
    "properties", "protocol_steps", "scope_note", "evidence", "tags_zh", "resources", "verification",
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


def public_resources(paper: dict[str, Any]) -> list[dict[str, str]]:
    """Return only explicitly public HTTPS resource links from metadata."""
    resources = paper.get("resources") or []
    if not isinstance(resources, list):
        return []
    allowed_hosts = {"github.com", "gitlab.com", "zenodo.org", "doi.org", "arxiv.org", "pmc.ncbi.nlm.nih.gov", "materialscloud.org"}
    result = []
    for item in resources:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        parsed = urlparse(url)
        visibility = str(item.get("visibility") or "").strip().lower()
        sensitive_keys = {"token", "access_token", "api_key", "apikey", "key", "password", "passwd", "authorization", "auth"}
        query_keys = {key.lower() for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
        safe_visibility = not visibility or visibility in {"public", "open"}
        no_credentials = not parsed.username and not parsed.password
        no_sensitive_query = not query_keys.intersection(sensitive_keys)
        if parsed.scheme == "https" and parsed.hostname and safe_visibility and no_credentials and no_sensitive_query and (parsed.hostname in allowed_hosts or parsed.hostname.endswith(".github.com")):
            result.append({"label": compact(item.get("label"), 160), "url": url})
    return result


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
        "resource_urls": public_resources(paper),
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
        if "resources" in fields:
            item["resources"] = public_resources(paper)
        packet.append(item)
    return json.dumps({"papers": packet}, ensure_ascii=False, sort_keys=True)


def row(row_id: str, category: str, question: str, answer: str, papers: list[dict[str, Any]], fields: list[str], ctx_fields: list[str]) -> dict[str, Any]:
    refs = {"source_paper_ids": [], "source_group_ids": [], "source_fields": [], "doi": [], "source_urls": [], "resource_urls": [], "evidence_references": []}
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
        props_values = values(paper, "properties")
        props = ", ".join(props_values) or "记录未列出"
        role = compact(paper.get("role") or paper.get("summary") or "记录未提供", 700)
        scope = compact(paper.get("scope_note") or "结构化记录未提供边界说明", 800)
        evidence_claims = [compact(x.get("claim"), 180) for x in (paper.get("evidence") or []) if isinstance(x, dict) and x.get("claim")]
        evidence_note = "；".join(evidence_claims[:2]) or "当前证据字段没有可核验的具体数值"
        rows.append(row(f"expanded-{pid}-scope", "factual", f"《{title}》研究什么、对象和方法是什么？", f"关于《{title}》，记录将其定位为：{role}。体系：{systems}；方法：{methods}。这里只能据此概括，具体参数仍需核对原文。[P1]", [paper], ["title", "role", "systems", "methods"], ["role", "systems", "methods", "evidence"]))
        if props_values:
            rows.append(row(f"expanded-{pid}-properties", "factual", f"《{title}》关注哪些可计算性质？", f"结构化字段列出的性质为：{props}。记录没有列出的性质不能从标题或方法名称推断。[P1]", [paper], ["title", "properties"], ["properties", "evidence"]))
        steps = values(paper, "protocol_steps")
        body = "\n".join(f"{i}. {step}" for i, step in enumerate(steps, 1)) if steps else f"记录 {pid} 没有给出具体协议步骤；应回到正文和补充材料核对输入、版本、单位与收敛标准。"
        rows.append(row(f"expanded-{pid}-workflow", "workflow", f"我想复现《{title}》，应从哪里开始？", f"针对《{title}》，这是复现流程建议，不是论文已报告的新结果。先固定软件、数据版本并检查体系与单位；可按结构化记录执行：\n{body}\n不要把小规模冒烟测试当成物性复现。[P1]", [paper], ["title", "protocol_steps", "methods", "scope_note"], ["protocol_steps", "methods", "scope_note", "evidence"]))
        rows.append(row(f"expanded-{pid}-limits", "limitation", f"《{title}》的结果能否直接外推到我的新体系？", f"针对记录 {pid}，不能仅凭该记录直接外推。已记录的边界是：{scope}。应先复现原体系，再逐项验证新体系的结构、参数、收敛和独立数据。[P1]", [paper], ["title", "systems", "scope_note"], ["systems", "scope_note", "evidence"]))
        rows.append(row(f"expanded-{pid}-insufficient", "evidence_insufficient", f"记录能否给出《{title}》的精确ENCUT、U值、时间步长或电导率？", f"对于《{title}》，当前记录只提供方法字段“{methods}”，可核验线索为“{evidence_note}”；没有足够证据给出ENCUT、U值、时间步长或电导率。不得臆造这些缺失字段，应查阅论文正文、补充材料或原作者公开数据。[P1]", [paper], ["title", "methods", "evidence"], ["methods", "evidence"]))
        resources = public_resources(paper)
        if resources:
            labels = "; ".join(f"{x['label'] or '公开资源'}: {x['url']}" for x in resources)
            rows.append(row(f"expanded-{pid}-resources", "source_access", f"《{title}》有哪些可核查的代码或数据入口？", f"仅可列出元数据中标记为公开且通过HTTPS链接的入口：{labels}。链接存在不等于数据已复现，仍需核对版本、许可证和内容。[P1]", [paper], ["title", "resources"], ["resources", "verification"]))
    # Pairwise comparison is based only on fields present in both records.
    for left, right in zip(papers[::2], papers[1::2]):
        lid = str(left.get("id") or norm_doi(left.get("doi")) or "left")
        rid = str(right.get("id") or norm_doi(right.get("doi")) or "right")
        lm_values, rm_values = values(left, "methods"), values(right, "methods")
        if lm_values and rm_values and lm_values != rm_values:
            lm, rm = ", ".join(lm_values), ", ".join(rm_values)
            method_question = "比较两篇记录的方法边界"
            joined = (lm + " " + rm).lower()
            if "dft" in joined or "密度泛函" in joined or "md" in joined or "分子动力学" in joined or "mlip" in joined:
                method_question += "（特别说明 DFT、MD 或 MLIP 的适用范围；不要把LLM当作物理模拟器）"
            rows.append(row(f"expanded-compare-{lid}-{rid}", "comparison", f"{method_question}：《{compact(left.get('title'), 180)}》和《{compact(right.get('title'), 180)}》。", f"第一篇记录的方法：{lm}；第二篇记录的方法：{rm}。这是字段层面的并列，不足以证明精度、成本或性能优劣；LLM只能协助检索和流程组织，不能替代DFT、MD或MLIP的数值计算。[P1][P2]", [left, right], ["title", "methods", "systems"], ["methods", "systems", "evidence"]))
    return sorted(rows, key=lambda x: x["id"])


def split(rows: list[dict[str, Any]], eval_mod: int | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
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
    # ``eval_mod`` remains accepted for callers of the previous two-way API;
    # three-way thresholding is now deliberately the only assignment rule.
    del eval_mod
    components: dict[str, list[dict[str, Any]]] = {}
    for item in rows:
        groups = sorted(item["provenance"].get("source_group_ids") or ["example:" + item["id"]])
        component = min(find(x) for x in groups)
        components.setdefault(component, []).append(item)
    # Hash the connected component, not an individual row.  The thresholds
    # make the expected distribution 80/10/10 while the repair pass keeps all
    # three files useful for small but non-trivial paper libraries.
    ordered = sorted(components.items(), key=lambda pair: hashlib.sha256(pair[0].encode()).hexdigest())
    buckets: dict[str, list[dict[str, Any]]] = {"train": [], "eval": [], "test": []}
    component_bucket: dict[str, str] = {}
    for component, items in ordered:
        bucket = int(hashlib.sha256(component.encode()).hexdigest()[:8], 16) % 100
        name = "train" if bucket < 80 else "eval" if bucket < 90 else "test"
        component_bucket[component] = name
        buckets[name].extend(items)
    if len(components) >= 3:
        # Deterministically move the smallest component(s) to empty buckets.
        for name in ("train", "eval", "test"):
            if buckets[name]:
                continue
            component_counts = {n: sum(1 for c in components if component_bucket[c] == n) for n in buckets}
            donor = max((n for n in buckets if component_counts[n] > 1), key=lambda n: component_counts[n])
            donor_components = [c for c in components if component_bucket[c] == donor]
            chosen = min(donor_components, key=lambda c: (len(components[c]), c))
            moved = components[chosen]
            buckets[donor] = [x for x in buckets[donor] if x not in moved]
            buckets[name].extend(moved)
            component_bucket[chosen] = name
    for name, items in buckets.items():
        for item in items:
            item["split"] = name
    return buckets["train"], buckets["eval"], buckets["test"]


def write(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for x in rows), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--papers", type=Path, default=ROOT / "data" / "papers.json")
    parser.add_argument("--expansion", type=Path, default=ROOT / "data" / "paper_expansion_20260920.json")
    parser.add_argument("--test-output", type=Path, default=ROOT / "training" / "expanded_test.jsonl")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    papers = merge_records(load_json(args.papers) + load_json(args.expansion))
    rows = build(papers)
    train, evaluation, test = split(rows)
    def relative_source(path: Path) -> str:
        try:
            return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
        except ValueError:
            return path.name
    counts = {"papers": len(papers), "rows": len(rows), "train": len(train), "eval": len(evaluation), "test": len(test), "seed": "sha256(source_group_id)", "sources": [relative_source(args.papers), relative_source(args.expansion)], "metadata_only": True}
    print(json.dumps(counts, ensure_ascii=False, indent=2))
    if args.dry_run:
        return
    write(ROOT / "training" / "expanded_train.jsonl", train)
    write(ROOT / "training" / "expanded_eval.jsonl", evaluation)
    write(args.test_output, test)
    write(ROOT / "finetune" / "data" / "train.jsonl", train)
    write(ROOT / "finetune" / "data" / "validation.jsonl", evaluation)
    write(ROOT / "finetune" / "data" / "test.jsonl", test)
    canonical = "".join(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for x in rows).encode("utf-8")
    manifest = {**counts, "policy": "metadata_only_no_fulltext_or_pdf_text", "split_rule": "sha256(connected_source_group) bucket thresholds 80/10/10", "model_status": "not a trained model", "format_version": 2, "dataset_sha256": hashlib.sha256(canonical).hexdigest(), "source_group_ids": sorted({g for x in rows for g in x["provenance"].get("source_group_ids", [])})}
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    (ROOT / "training" / "expanded_manifest.json").write_text(manifest_text, encoding="utf-8")
    (ROOT / "finetune" / "data" / "manifest.json").write_text(manifest_text, encoding="utf-8")


if __name__ == "__main__":
    main()
