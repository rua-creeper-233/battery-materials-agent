"""Extract reviewable method-setting signals from the local full-text index.

This is intentionally a conservative locator, not a scientific parser.  Every
result keeps its PDF page and is marked for human review before reuse in an
input file, manuscript, or comparison table.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PAPERS_PATH = ROOT / "data" / "papers.json"
FULLTEXT_PATH = ROOT / "data" / "fulltext_chunks.jsonl"
OUTPUT_PATH = ROOT / "data" / "method_evidence.auto.json"
REPORT_PATH = ROOT / "METHOD_EVIDENCE_AUDIT.md"
REVIEW_STATUS = "auto_extracted_needs_human_review"


# Patterns are deliberately tied to recognizable software/method names or to
# values with units.  Broad words such as "calculation" are not evidence.
RULES: list[dict[str, Any]] = [
    {
        "category": "software",
        "label_zh": "计算软件",
        "pattern": r"\b(?:VASP|LAMMPS|CASTEP|CP2K|ABINIT|GULP|pymatgen)\b|Quantum\s+ESPRESSO|Vienna\s+Ab[- ]initio\s+Simulation\s+Package",
        "confidence": "high",
    },
    {
        "category": "electronic_structure",
        "label_zh": "泛函与电子结构近似",
        "pattern": r"\b(?:PBE|PBEsol|LDA|GGA|SCAN|r2SCAN|HSE|HSE06)\b|DFT\s*\+\s*U|Hubbard\s+(?:parameter\s+)?U|projector[- ]augmented[- ]wave|\bPAW\b|generalized\s+gradient\s+approximation|local\s+density\s+approximation",
        "confidence": "medium",
    },
    {
        "category": "basis_cutoff",
        "label_zh": "平面波截断能",
        "pattern": r"(?:(?:plane[- ]wave\s+)?(?:energy\s+)?cutoff|cut[- ]off\s+energy)[^.;\n]{0,55}?\b\d+(?:\.\d+)?\s*(?:eV|Ry)\b|\b\d+(?:\.\d+)?\s*(?:eV|Ry)\b[^.;\n]{0,35}?(?:cutoff|cut[- ]off)",
        "confidence": "high",
    },
    {
        "category": "k_points",
        "label_zh": "k 点采样",
        "pattern": r"(?:\b\d+\s*[×xX]\s*\d+\s*[×xX]\s*\d+\b[^.;\n]{0,55}?k[- ]?points?|k[- ]?points?[^.;\n]{0,55}?\b\d+\s*[×xX]\s*\d+\s*[×xX]\s*\d+\b)|Monkhorst[- ]Pack|Brillouin[- ]zone\s+(?:sampling|integration)",
        "confidence": "medium",
    },
    {
        "category": "convergence",
        "label_zh": "收敛判据",
        "pattern": r"(?:force|energy|electronic|ionic)[^.;\n]{0,65}?(?:converg\w*|tolerance|threshold)[^.;\n]{0,35}?\b\d+(?:\.\d+)?(?:\s*[×xX]\s*10\s*[−-]?\s*\d+|[Ee][−+-]?\d+)?\s*(?:eV(?:\s*[ÅA]/?\s*atom|\s*/\s*[ÅA])?|Ha|Ry)?",
        "confidence": "medium",
    },
    {
        "category": "cell_model",
        "label_zh": "超胞与模型规模",
        "pattern": r"\b\d+\s*[×xX]\s*\d+\s*[×xX]\s*\d+\s+(?:simulation\s+)?supercells?\b|\bsupercells?\b[^.;\n]{0,55}?\b\d+\s+atoms?\b|\b\d+\s+atoms?\b[^.;\n]{0,45}?\bsupercells?\b",
        "confidence": "high",
    },
    {
        "category": "molecular_dynamics",
        "label_zh": "分子动力学条件",
        "pattern": r"(?:time\s*step|timestep)[^.;\n]{0,40}?\b\d+(?:\.\d+)?\s*fs\b|\b\d+(?:\.\d+)?\s*fs\b[^.;\n]{0,35}?(?:time\s*step|timestep)|\b(?:NVT|NPT|NVE)\b|Nos[eé][- ]Hoover|\b\d{2,4}\s*K\b[^.;\n]{0,55}?(?:molecular\s+dynamics|\bMD\b|simulation)|(?:molecular\s+dynamics|\bMD\b|simulation)[^.;\n]{0,55}?\b\d{2,4}\s*K\b|\b\d+(?:\.\d+)?\s*(?:ps|ns)\b[^.;\n]{0,45}?(?:trajectory|simulation|production|equilibration)",
        "confidence": "medium",
    },
    {
        "category": "ion_transport",
        "label_zh": "扩散与迁移势垒方法",
        "pattern": r"climbing[- ]image\s+(?:nudged\s+elastic\s+band|NEB)|nudged\s+elastic\s+band|\bCI[- ]?NEB\b|\bNEB\b|mean[- ]squared?\s+displacement|\bMSD\b|Arrhenius\s+(?:fit|plot|relation|equation)|migration\s+(?:barrier|pathway)",
        "confidence": "medium",
    },
    {
        "category": "ml_training",
        "label_zh": "机器学习训练设置",
        "pattern": r"(?:train(?:ing)?|validation|test)\s+(?:set|split|data(?:set)?)|\b(?:MAE|RMSE)\b|mean\s+absolute\s+error|root\s+mean\s+squared?\s+error|cutoff\s+radius|(?:energy|force|stress)\s+(?:loss|error|weight)|machine[- ]learn(?:ed|ing)\s+(?:interatomic\s+)?potential",
        "confidence": "medium",
    },
]


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _signal(match: re.Match[str]) -> str:
    value = _normalise(match.group(0))
    return value if len(value) <= 120 else value[:117].rstrip() + "..."


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def extract(
    papers_path: Path = PAPERS_PATH,
    fulltext_path: Path = FULLTEXT_PATH,
) -> dict[str, Any]:
    # Keep this versioned/public artifact restricted to the curated seed set.
    # User-uploaded papers stay in private/user-papers.local.json and are never
    # copied into the GitHub Pages bundle.
    papers = json.loads(papers_path.read_text(encoding="utf-8"))
    curated_ids = {paper["id"] for paper in papers}
    chunks = load_jsonl(fulltext_path)
    chunks_by_paper: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks:
        if chunk.get("section") == "body" and chunk.get("paper_id") in curated_ids:
            chunks_by_paper[chunk["paper_id"]].append(chunk)
    fulltext_paper_ids = sorted(chunks_by_paper)

    output: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "review_status": REVIEW_STATUS,
        "notice_zh": "自动结果只用于定位原文；用于计算输入、论文或汇报前，必须打开对应 PDF 页人工核对。",
        "rules_version": 1,
        "fulltext_paper_count": len(fulltext_paper_ids),
        "fulltext_paper_ids": fulltext_paper_ids,
        "papers": {},
    }

    for paper in papers:
        paper_id = paper["id"]
        found: list[dict[str, Any]] = []
        per_category: dict[str, int] = defaultdict(int)
        seen: set[tuple[str, int, str]] = set()
        for rule in RULES:
            pattern = re.compile(rule["pattern"], re.IGNORECASE)
            for chunk in chunks_by_paper.get(paper_id, []):
                if per_category[rule["category"]] >= 3:
                    break
                for match in pattern.finditer(chunk.get("text", "")):
                    if per_category[rule["category"]] >= 3:
                        break
                    signal = _signal(match)
                    key = (rule["category"], int(chunk["page"]), signal.casefold())
                    if key in seen:
                        continue
                    seen.add(key)
                    per_category[rule["category"]] += 1
                    found.append(
                        {
                            "category": rule["category"],
                            "label_zh": rule["label_zh"],
                            "page": int(chunk["page"]),
                            "section": "body",
                            "signal": signal,
                            "confidence": rule["confidence"],
                            "review_status": REVIEW_STATUS,
                            "local_pdf_url": f"/local-pdf/{paper_id}.pdf#page={int(chunk['page'])}",
                        }
                    )
        found.sort(key=lambda item: (item["page"], item["category"], item["signal"].casefold()))
        output["papers"][paper_id] = {
            "title": paper["title"],
            "doi": paper.get("doi"),
            "wos_uid": paper.get("wos_uid"),
            "review_status": REVIEW_STATUS,
            "evidence_count": len(found),
            "evidence": found,
        }
    return output


def write_report(payload: dict[str, Any], report_path: Path = REPORT_PATH) -> None:
    papers = payload["papers"]
    with_evidence = sum(bool(row["evidence"]) for row in papers.values())
    total = sum(row["evidence_count"] for row in papers.values())
    lines = [
        "# 计算方法证据自动抽取审计",
        "",
        "> 所有条目均为“自动抽取、待人工核对”。它们是原文定位器，不是可直接复制到 VASP/MD 输入文件的最终参数。",
        "",
        f"- 本地有正文的论文：{payload['fulltext_paper_count']}",
        f"- 抽取到至少一条方法信号的论文：{with_evidence}",
        f"- 方法信号总数：{total}",
        "- 参考文献区：已排除",
        "- 每篇每类上限：3 条",
        "- 公开数据只保存短方法信号与页码，不保存连续正文上下文",
        "",
        "## 分论文结果",
        "",
    ]
    for paper_id, row in papers.items():
        lines.append(f"### {row['title']}")
        lines.append("")
        if not row["evidence"]:
            lines.append("- 未抽取到方法设置；可能无本地正文或正文未给出可识别参数。")
            lines.append("")
            continue
        by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in row["evidence"]:
            by_category[item["label_zh"]].append(item)
        for label, items in by_category.items():
            locators = "；".join(
                f"p.{item['page']} `{item['signal']}`" for item in items
            )
            lines.append(f"- {label}：{locators}")
        lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract reviewable method evidence")
    parser.add_argument("--papers", type=Path, default=PAPERS_PATH)
    parser.add_argument("--fulltext", type=Path, default=FULLTEXT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    args = parser.parse_args()

    payload = extract(args.papers, args.fulltext)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_report(payload, args.report)
    with_evidence = sum(bool(row["evidence"]) for row in payload["papers"].values())
    total = sum(row["evidence_count"] for row in payload["papers"].values())
    print(f"Method evidence: {total} signals across {with_evidence} papers")
    print(args.output)
    print(args.report)


if __name__ == "__main__":
    main()
