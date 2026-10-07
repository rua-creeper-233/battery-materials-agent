"""Merge the DOI-verified 2026-09-20 catalog into the public seed library.

The catalog contains metadata only.  It never downloads PDFs or marks a paper as
WOS/full-text verified.  Running it is deterministic and DOI-idempotent.
"""

from __future__ import annotations

import json
import html
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PAPERS = ROOT / "data" / "papers.json"
CATALOG = ROOT / "data" / "paper_expansion_20260920.json"
RECENT_CATALOG = ROOT / "data" / "paper_expansion_20261008.json"


def normalize_doi(value: str) -> str:
    return str(value or "").strip().lower().removeprefix("https://doi.org/").removeprefix("doi:").rstrip(".,;)")

def clean_title(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", "", str(value or "")))
    value = re.sub(r"\s+", " ", value).strip()
    return value.replace("Li 6 PS 5 Cl", "Li6PS5Cl")


def build_record(row: dict[str, Any]) -> dict[str, Any]:
    doi = normalize_doi(row["doi"])
    tags = list(dict.fromkeys(str(tag) for tag in row.get("tags", []) if str(tag).strip()))
    title_lower = row["title"].lower()
    is_review = "综述" in tags or "review" in title_lower or row.get("id", "").endswith("_review")
    starter = row.get("collection") == "starter"
    methods = tags[:]
    if "DFT" in tags and "第一性原理" not in methods:
        methods.append("第一性原理")
    if "AIMD" in tags and "molecular dynamics" not in methods:
        methods.append("molecular dynamics")
    if "MD" in tags and "molecular dynamics" not in methods:
        methods.append("molecular dynamics")
    record = {
        "id": row["id"],
        "title": clean_title(row["title"]),
        "authors": row.get("authors", ["待补充"]),
        "year": int(row["year"]),
        "journal": row.get("journal", ""),
        "document_type": "Review" if is_review else "Paper",
        "doi": doi,
        "url": f"https://doi.org/{doi}",
        "role": row.get("role", "电池材料计算论文的结构化入口。"),
        "systems": row.get("systems", []),
        "methods": methods,
        "properties": [],
        "tags_zh": tags,
        "summary": row.get("summary", ""),
        "scope_note": "本条为 DOI/出版社记录核验的结构化元数据；本地尚未保存全文，具体参数、页码和适用边界必须回到出版社正文或补充材料核对。",
        "publication_status": "published",
        "collection": row.get("collection", "core"),
        "difficulty": row.get("difficulty", "进阶"),
        "protocol_steps": [
            "先从 DOI 页面确认版本、正文和补充材料是否可访问。",
            "记录论文使用的体系、软件、泛函/力场和边界条件；本条元数据不补猜具体参数。",
            "准备结构和输入文件，保存来源、版本、单位与随机种子。",
            "先做小体系或短轨迹冒烟测试，再进行收敛、有限尺寸和采样检查。",
            "把能量、力、扩散/势垒或稳定性等指标与原文图表逐项对照。",
            "报告无法核验的参数和外推风险，不把元数据摘要当作全文证据。",
        ] if starter else [],
        "evidence": [{
            "claim": "DOI 与出版社记录已核验；当前库中保留结构化元数据入口。",
            "basis": f"出版社/DOI：https://doi.org/{doi}",
            "strength": "moderate",
        }],
        "relations": [],
        "resources": [{"label": "DOI / 出版社记录", "url": f"https://doi.org/{doi}"}],
        "wos_uid": "",
        "verification": {
            "doi": "verified_publisher_2026-09-20",
            "publisher": "verified_2026-09-20",
            "wos": "not_checked",
            "fulltext": "not_downloaded",
            "sources": [f"https://doi.org/{doi}"],
        },
    }
    # Preserve structured, DOI-verified fields emitted by the recent catalog.
    for key in ("role", "systems", "methods", "properties", "tags_zh", "summary", "scope_note",
                "publication_date", "publication_date_precision", "online_date", "online_date_precision",
                "verification", "resources", "evidence", "document_type"):
        if key in row:
            record[key] = row[key]
    return record


def main() -> None:
    papers: list[dict[str, Any]] = json.loads(PAPERS.read_text(encoding="utf-8"))
    additions: list[dict[str, Any]] = json.loads(CATALOG.read_text(encoding="utf-8"))
    if RECENT_CATALOG.exists():
        additions.extend(json.loads(RECENT_CATALOG.read_text(encoding="utf-8")))
    seen = {normalize_doi(paper.get("doi", "")) for paper in papers}
    added: list[dict[str, Any]] = []
    for row in additions:
        doi = normalize_doi(row.get("doi", ""))
        if not doi:
            continue
        if doi in seen:
            # Refresh only records owned by this expansion; never overwrite
            # older hand-curated records that happen to share a DOI.
            for index, current in enumerate(papers):
                if (normalize_doi(current.get("doi", "")) == doi
                        and row.get("collection") == "recent_verified_20261008"
                        and current.get("collection") == "recent_verified_20261008"
                        and current.get("id", "").startswith("recent_")):
                    refreshed = build_record(row)
                    refreshed["id"] = current["id"]
                    refreshed["wos_uid"] = current.get("wos_uid", "")
                    old_verification = current.get("verification", {})
                    refreshed["verification"]["fulltext"] = old_verification.get("fulltext", refreshed["verification"].get("fulltext", "not_downloaded"))
                    papers[index] = refreshed
            continue
        record = build_record(row)
        papers.append(record)
        seen.add(doi)
        added.append(record)
    for paper in papers:
        if paper.get("collection") == "recent_verified_20261008":
            paper["title"] = clean_title(paper.get("title", ""))
    if len({normalize_doi(paper.get("doi", "")) for paper in papers}) != len(papers):
        raise SystemExit("duplicate DOI after merge")
    PAPERS.write_text(json.dumps(papers, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"added {len(added)} metadata records; library now has {len(papers)} papers")
    print("new DOIs:")
    for paper in added:
        print(f"- {paper['id']} {paper['doi']}")


if __name__ == "__main__":
    main()
