#!/usr/bin/env python3
"""Build small, local-only Q&A datasets from the library's structured metadata.

The generator intentionally never reads ``fulltext_chunks.jsonl`` or PDF files.
It is deterministic and safe to rerun; generated JSONL is suitable for review,
RAG regression, or a later LoRA/QLoRA experiment (not a substitute for RAG).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "training"
EVAL_EVERY = 7


def load(name: str) -> Any:
    with (DATA / name).open(encoding="utf-8") as f:
        return json.load(f)


def compact(value: Any, limit: int = 900) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def compact_value(value: Any, limit: int = 900) -> Any:
    """Keep structured metadata readable without ever loading full text."""
    if isinstance(value, list):
        return [compact_value(item, limit) for item in value[:8]]
    if isinstance(value, dict):
        return {str(key): compact_value(item, limit) for key, item in list(value.items())[:12]}
    return compact(value, limit)


def paper_context(papers: list[dict[str, Any]], fields: Iterable[str]) -> str:
    """Build the same small, citation-labelled packet shape used by RAG.

    This contains only curated metadata and short evidence claims. It never
    reads the PDF or page-aware full-text index.
    """
    packets = []
    field_list = list(fields)
    for index, paper in enumerate(papers, 1):
        packet: dict[str, Any] = {
            "source_id": f"P{index}",
            "paper_id": paper.get("id"),
            "title": paper.get("title"),
            "doi": paper.get("doi"),
        }
        for field in field_list:
            if field == "evidence":
                packet["curated_evidence"] = [
                    {
                        "claim": compact(e.get("claim"), 500),
                        "basis": compact(e.get("basis"), 300),
                        "strength": e.get("strength"),
                    }
                    for e in (paper.get("evidence") or [])[:8]
                    if e.get("claim")
                ]
            else:
                packet[field] = compact_value(paper.get(field), 800)
        packets.append(packet)
    return json.dumps({"papers": packets}, ensure_ascii=False, sort_keys=True)


def paper_ref(p: dict[str, Any], fields: Iterable[str]) -> dict[str, Any]:
    evidence = p.get("evidence") or []
    return {
        "source_paper_ids": [p["id"]],
        "source_group_ids": [f"paper:{p['id']}"],
        "source_fields": list(fields),
        "doi": p.get("doi"),
        "source_urls": [p.get("url")] if p.get("url") else [],
        "evidence_references": [
            {"claim": compact(e.get("claim"), 500), "basis": compact(e.get("basis"), 300), "strength": e.get("strength")}
            for e in evidence if e.get("claim")
        ],
    }


def example(eid: str, category: str, task: str, difficulty: str, question: str,
            answer: str, refs: dict[str, Any], *, requires_citation: bool = True,
            source: str = "structured_metadata", context: str | None = None) -> dict[str, Any]:
    user_content = question
    if context:
        user_content = f"证据包(JSON，仅允许使用其中信息)：\n{context}\n\n问题：{question}"
    return {
        "id": eid,
        "category": category,
        "task": task,
        "difficulty": difficulty,
        "split": "pending",
        "requires_citation": requires_citation,
        "messages": [
            {"role": "system", "content": "你是电池材料计算科研助理。只依据给定证据回答；不确定时明确说明并建议核验。"},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": answer},
        ],
        "provenance": {**refs, "generator_source": source, "copyright_note": "仅使用结构化元数据；未复制PDF或全文段落。"},
    }


def build_factual(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for p in papers:
        title = compact(p.get("title"), 300)
        systems = ", ".join(map(str, p.get("systems", []))) or "论文结构化记录未列出"
        methods = ", ".join(map(str, p.get("methods", []))) or "论文结构化记录未列出"
        out.append(example(
            f"fact-{p['id']}-scope", "factual", "paper_scope", p.get("difficulty", "普通"),
            f"论文《{title}》主要研究什么？",
            f"结构化记录将它定位为：{compact(p.get('role') or p.get('summary'))}。研究体系包括：{systems}。这只是元数据摘要；具体边界应回到论文正文核对。[P1]",
            paper_ref(p, ["title", "role", "systems", "summary"]),
            context=paper_context([p], ["role", "systems", "summary", "evidence"])))
        out.append(example(
            f"fact-{p['id']}-methods", "factual", "methods_and_systems", p.get("difficulty", "普通"),
            f"《{title}》用了哪些计算方法、考察哪些对象？",
            f"记录的方法为：{methods}；对象/体系为：{systems}。这些字段来自论文库的人工核验记录，不能据此推断未列出的参数或软件版本。[P1]",
            paper_ref(p, ["title", "methods", "systems"]),
            context=paper_context([p], ["methods", "systems", "evidence"])))
    return out


def build_workflow(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for p in papers:
        steps = p.get("protocol_steps") or []
        if steps:
            body = "\n".join(f"{i}. {compact(s, 500)}" for i, s in enumerate(steps, 1))
            fields = ["title", "protocol_steps", "methods", "scope_note"]
        else:
            methods = ", ".join(map(str, p.get("methods", []))) or "未列出"
            body = (f"论文记录的方法是：{methods}。先固定论文版本、软件/数据来源和单位；"
                    "再按正文与补充材料核对输入输出；最后用论文报告的指标和独立统计检查复现。"
                    "结构化记录没有给出更细的命令或参数，不能凭空补齐。")
            fields = ["title", "methods", "scope_note"]
        out.append(example(
            f"workflow-{p['id']}", "workflow", "reproduction_plan", p.get("difficulty", "普通"),
            f"我想跟练《{compact(p.get('title'), 240)}》，应如何开始？",
            f"建议先确认适用边界，再按记录的流程执行：\n{body}\n开始前应保存版本、输入、输出和单位，并将结果与原文指标逐项对照。[P1]",
            paper_ref(p, fields),
            context=paper_context([p], ["methods", "scope_note", "protocol_steps", "evidence"])))
    return out


def build_refusal(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for p in papers:
        title = compact(p.get("title"), 230)
        limitation = compact(p.get("scope_note") or "结构化记录没有提供足够信息", 700)
        variant = hashlib.sha256(p["id"].encode()).digest()[0] % 3
        role = compact(p.get("role") or "这项工作的研究目标", 260)
        systems = ", ".join(map(str, p.get("systems", []))) or "记录未列明体系"
        if variant == 0:
            question = f"《{title}》的结论能否直接外推到我的新体系？"
            answer = (f"不能直接外推。该记录关注的是：{role}；体系为：{systems}。"
                      f"适用边界还需核对：{limitation}。应先做小规模验证，再讨论推广。[P1]")
        elif variant == 1:
            question = f"只凭《{title}》的摘要记录，能否给我的体系指定同样的参数？"
            answer = (f"不能仅凭这条记录指定参数。现有信息只支持判断研究方向（{role}），"
                      f"并未证明新体系与原体系等价。请回到原文核对：{limitation}；缺失参数不能凭空补齐。[P1]")
        else:
            question = f"《{title}》是否足以证明我的材料也会得到同样的模拟结果？"
            answer = (f"不足以证明。论文记录的体系是：{systems}；边界说明为：{limitation}。"
                      "应复现原任务、检查单位与收敛，并用独立数据验证，不把相关性当作保证。[P1]")
        out.append(example(
            f"refusal-{p['id']}", "refusal", "unsupported_inference", "普通",
            question, answer, paper_ref(p, ["title", "role", "systems", "scope_note", "evidence"]),
            context=paper_context([p], ["role", "systems", "scope_note", "evidence"])))
    return out


def build_tool_traces(papers: list[dict[str, Any]], search: dict[str, Any],
                     guidance: list[dict[str, Any]], regression: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {p["id"]: p for p in papers}
    def resolve_source_ids(sources: list[dict[str, Any]]) -> list[str]:
        resolved: list[str] = []
        for source in sources:
            url = str(source.get("url") or "").lower().rstrip("/")
            for paper in papers:
                doi = str(paper.get("doi") or "").lower()
                paper_url = str(paper.get("url") or "").lower().rstrip("/")
                if (doi and doi in url) or (paper_url and paper_url == url):
                    if paper["id"] not in resolved:
                        resolved.append(paper["id"])
        return resolved

    # Include routing/regression supervision as tool plans too, then fill the
    # remainder with curated retrieval queries. This keeps all existing local
    # supervision sources represented without expanding the dataset endlessly.
    candidates = []
    guidance_by_id = {g.get("id"): g for g in guidance}
    for case in regression.get("cases", []):
        gid = case.get("guidance")
        g = guidance_by_id.get(gid)
        candidates.append({"query": case.get("question", ""), "relevant": [s.get("url") for s in (g or {}).get("sources", [])], "guidance": g})
    candidates.extend(search.get("training_examples", []))
    candidates.extend(search.get("held_out_examples", []))
    candidates = candidates[:25]
    out = []
    for i, item in enumerate(candidates, 1):
        guidance_item = item.get("guidance")
        guidance_sources = (guidance_item or {}).get("sources", [])
        ids = [x for x in item.get("relevant", []) if x in by_id]
        if guidance_item:
            ids = resolve_source_ids(guidance_sources)
        query = item.get("query", "")
        source_group_ids = [f"paper:{paper_id}" for paper_id in ids]
        if guidance_item:
            source_group_ids.insert(0, f"guidance:{guidance_item.get('id')}")
        refs = {
            "source_paper_ids": ids,
            "source_group_ids": source_group_ids,
            "source_fields": ["search_training.relevant"] if not guidance_item else ["answer_guidance", "answer_regression"],
            "doi": [by_id[x].get("doi") for x in ids if by_id[x].get("doi")],
            "source_urls": ([by_id[x].get("url") for x in ids if by_id[x].get("url")]
                            + [s.get("url") for s in guidance_sources if s.get("url")]),
            "evidence_references": [{"claim": compact(s.get("label"), 300), "basis": s.get("url"), "strength": "curated"} for s in guidance_sources],
        }
        if guidance_item:
            g = guidance_item
            answer = compact(g.get("answer"), 1200) + "\n建议工具流程：先检索并打开来源，再核对体系、单位和适用边界；若证据不足则保留不确定性。"
            context = (paper_context([by_id[x] for x in ids], ["role", "systems", "methods", "summary", "evidence"])
                       if ids else json.dumps({
                           "guidance_id": g.get("id"),
                           "curated_note": compact(g.get("answer"), 1400),
                           "recommended_checks": [compact(step, 500) for step in (g.get("steps") or [])[:8]],
                           "follow_up_question": compact(g.get("ask"), 400),
                           "sources": guidance_sources,
                       }, ensure_ascii=False, sort_keys=True))
            if ids:
                answer += " " + " ".join(f"[P{index}]" for index in range(1, len(ids) + 1))
        else:
            answer = (f"先检索关键词：{query}；再按标题、方法、体系和DOI去重。"
                      f"候选命中：{', '.join(ids) if ids else '无已标注命中'}。"
                      "下一步应打开出版社/数据仓库核验正文、版本和可复现材料，回答时只引用已核验来源。"
                      + (" " + " ".join(f"[P{index}]" for index in range(1, len(ids) + 1)) if ids else ""))
            context = (paper_context([by_id[x] for x in ids], ["title", "role", "systems", "methods", "summary", "evidence"])
                       if ids else json.dumps({"retrieval_query": query, "matched_paper_ids": ids}, ensure_ascii=False, sort_keys=True))
        out.append(example(f"trace-{i:03d}", "tool_trace", "retrieve_then_verify", "普通",
                           query, answer, refs, requires_citation=bool(ids),
                           source="answer_guidance" if guidance_item else "search_training.json",
                           context=context))
    return out


def split_groups(items: list[dict[str, Any]]) -> dict[str, str]:
    """Map each example ID to a leakage-control group.

    A multi-paper example connects all of its paper IDs into one component;
    this prevents a shared paper from appearing on opposite sides of the
    split even when a tool trace cites several papers.
    """
    parent: dict[str, str] = {}

    def find(value: str) -> str:
        parent.setdefault(value, value)
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left: str, right: str) -> None:
        root_left, root_right = find(left), find(right)
        if root_left == root_right:
            return
        # Lexicographic union keeps the result deterministic across runs.
        if root_right < root_left:
            root_left, root_right = root_right, root_left
        parent[root_right] = root_left

    def tokens(item: dict[str, Any]) -> list[str]:
        provenance = item.get("provenance", {})
        explicit = sorted(set(provenance.get("source_group_ids") or []))
        if explicit:
            return explicit
        return [f"paper:{paper_id}" for paper_id in sorted(set(provenance.get("source_paper_ids") or []))]

    for item in items:
        groups = tokens(item)
        for group in groups:
            find(group)
        for group in groups[1:]:
            union(groups[0], group)

    # Compress and canonicalize components after all unions are known.
    components: dict[str, list[str]] = {}
    for group_id in sorted(parent):
        components.setdefault(find(group_id), []).append(group_id)
    representative = {
        group_id: min(members)
        for members in components.values()
        for group_id in members
    }

    result: dict[str, str] = {}
    for item in items:
        groups = tokens(item)
        if groups:
            result[item["id"]] = representative[find(groups[0])]
        else:
            result[item["id"]] = "example:" + item["id"]
    return result


def stable_split(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    # Stable across machines and reruns; reserve about 1/7 for held-out evaluation.
    # The hash is over a paper group, not an individual question, to prevent
    # same-paper leakage between training and evaluation.
    groups = split_groups(items)
    train, evaluation = [], []
    for item in items:
        digest = hashlib.sha256(groups[item["id"]].encode()).digest()[0]
        target = evaluation if (digest % EVAL_EVERY == 0) else train
        item["split"] = "eval" if target is evaluation else "train"
        target.append(item)
    return train, evaluation


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> None:
    papers = load("papers.json")
    all_rows: list[dict[str, Any]] = []
    groups = {
        "qa_factual": build_factual(papers),
        "qa_workflow": build_workflow(papers),
        "qa_refusal": build_refusal(papers),
        "tool_traces": build_tool_traces(papers, load("search_training.json"), load("answer_guidance.json"), load("answer_regression.json")),
    }
    for rows in groups.values():
        all_rows.extend(rows)
    # IDs and ordering are deterministic, while category files remain easy to review.
    all_rows.sort(key=lambda x: x["id"])
    train, evaluation = stable_split(all_rows)
    for name, rows in groups.items():
        rows = [x for x in rows if x["split"] == "train"]
        rows.sort(key=lambda x: x["id"])
        write_jsonl(OUT / f"{name}.jsonl", rows)
    evaluation.sort(key=lambda x: x["id"])
    write_jsonl(OUT / "eval.jsonl", evaluation)
    manifest = {
        "schema_version": 1,
        "generated_by": "training/generate_dataset.py",
        "source_files": ["data/papers.json", "data/answer_guidance.json", "data/answer_regression.json", "data/search_training.json"],
        "policy": "metadata_only_no_fulltext_or_pdf_text",
        "split_rule": f"sha256(paper_group_or_example_id)[0] % {EVAL_EVERY} == 0 -> eval; paper groups stay together",
        "grouped_by_source_paper": True,
        "train_total": len(train),
        "counts": {name: sum(1 for x in all_rows if x["category"] == ("tool_trace" if name == "tool_traces" else name.removeprefix("qa_"))) for name in groups} | {"eval": len(evaluation), "total": len(all_rows)},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
