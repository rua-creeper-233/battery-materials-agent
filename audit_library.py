"""Offline integrity audit for the local seed-paper library.

No network request is made.  The command revalidates PDFs, refreshes hashes and
the page-level text index, and writes a concise Markdown report.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from fetch_literature import (
    MANIFEST_PATH,
    PAPERS_PATH,
    ROOT,
    load_json,
    rebuild_fulltext_index,
    save_json,
    utc_now,
    validate_pdf,
)


REPORT_PATH = ROOT / "FULLTEXT_AUDIT.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    papers = load_json(PAPERS_PATH, [])
    manifest = load_json(MANIFEST_PATH, {"schema_version": 1, "papers": {}})
    entries = manifest.setdefault("papers", {})
    seen_dois: set[str] = set()
    seen_uids: set[str] = set()
    duplicate_hashes: dict[str, list[str]] = {}

    for paper in papers:
        doi = paper["doi"].lower()
        uid = paper.get("wos_uid")
        if doi in seen_dois:
            raise SystemExit(f"duplicate DOI: {doi}")
        if not uid or uid in seen_uids:
            raise SystemExit(f"missing/duplicate WOS UID: {paper['id']} {uid}")
        seen_dois.add(doi)
        seen_uids.add(uid)

        entry = entries.setdefault(paper["id"], {})
        entry.update({"title": paper["title"], "doi": paper["doi"], "wos_uid": uid})
        relative = entry.get("local_pdf")
        path = ROOT / relative if relative else None
        if not path or not path.is_file():
            entry.pop("local_pdf", None)
            entry["status"] = "not_downloaded"
            continue
        validation = validate_pdf(path, paper["title"])
        if not validation.get("valid_pdf"):
            raise SystemExit(f"invalid PDF: {path}")
        if validation.get("document_kind") != "article":
            raise SystemExit(f"non-article in main library: {path}")
        digest = sha256(path)
        duplicate_hashes.setdefault(digest, []).append(paper["id"])
        entry.update(
            {
                "status": "downloaded",
                "bytes": path.stat().st_size,
                "sha256": digest,
                "validation": validation,
                "audited_at": utc_now(),
            }
        )

    duplicates = {key: value for key, value in duplicate_hashes.items() if len(value) > 1}
    if duplicates:
        raise SystemExit(f"duplicate PDF content: {duplicates}")

    rebuild_fulltext_index(papers, manifest)
    manifest["integrity_audit"] = {
        "audited_at": utc_now(),
        "seed_papers": len(papers),
        "wos_uid_verified": len(seen_uids),
        "downloaded_main_texts": sum(
            entry.get("status") == "downloaded" for entry in entries.values()
        ),
        "duplicate_pdf_hashes": 0,
        "checks": [
            "PDF magic/parse",
            "title token match",
            "main text vs supplementary",
            "SHA-256",
            "unique DOI",
            "unique WOS UID",
            "page-level text extraction",
        ],
    }
    manifest["updated_at"] = utc_now()
    save_json(MANIFEST_PATH, manifest)

    rows: list[str] = []
    for index, paper in enumerate(papers, 1):
        entry = entries[paper["id"]]
        validation = entry.get("validation") or {}
        extraction = entry.get("text_extraction") or {}
        if entry.get("status") == "downloaded":
            availability = "已下载正文"
            source = entry.get("access_basis", "已核验来源")
            pages = validation.get("pages", "")
            chunks = extraction.get("chunks", "")
            match = validation.get("title_token_match", "")
        else:
            availability = "未保存本地全文"
            source = "WOS/DOI 回退"
            pages = chunks = match = "—"
        rows.append(
            f"| {index} | {paper['year']} | {paper['title']} | {availability} | {pages} | {chunks} | {match} | {source} |"
        )

    downloaded = manifest["integrity_audit"]["downloaded_main_texts"]
    chunks = manifest.get("fulltext_index", {}).get("chunks", 0)
    missing = [paper for paper in papers if entries[paper["id"]].get("status") != "downloaded"]
    missing_lines = (
        [f"- {paper['title']}，DOI `{paper['doi']}`：本地未保存正文，使用 WOS/DOI 回退。" for paper in missing]
        if missing
        else ["当前 16 篇种子论文均已有经校验的本地正文。"]
    )
    report = "\n".join(
        [
            "# 本地全文与证据索引审计",
            "",
            f"审计时间：{manifest['integrity_audit']['audited_at']}",
            "",
            f"结论：16 篇种子论文和 WOS UT 均已核验；本地可检索正文 {downloaded}/16 篇，共 {chunks} 个页级文本块。未下载项不会伪装成全文，会回退到精确 WOS 记录和 DOI 页面。",
            "",
            "所有保留文件均通过 PDF 解析、标题匹配、正文/补充材料区分、SHA-256 和重复文件检查。M3GNet 的补充材料单独放在 `literature/supplementary/`，不进入正文索引。",
            "",
            "| # | 年份 | 论文 | 本地状态 | 页数 | 文本块 | 标题匹配 | 获取依据 |",
            "|---:|---:|---|---|---:|---:|---:|---|",
            *rows,
            "",
            "## 尚未保存的正文",
            "",
            *missing_lines,
            "",
            "## 使用边界",
            "",
            "本地全文命中是定位原文页码的入口，不自动等于经过人工复核的科学结论。涉及具体计算参数、数值或因果判断时，仍应回到对应页、图、表与补充材料核对。",
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Audited {downloaded}/16 local main-text PDFs; {chunks} chunks")
    print(REPORT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
