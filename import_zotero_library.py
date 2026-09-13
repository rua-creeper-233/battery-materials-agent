"""Idempotently import the verified seed library into a running Zotero client.

The default mode is a read-only plan.  Pass ``--apply`` to create only DOI
records that are not already present.  For newly created records, audited local
PDFs are attached through Zotero's own Connector HTTP server.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
PAPERS_PATH = ROOT / "data" / "papers.json"
MANIFEST_PATH = ROOT / "literature" / "manifest.json"
REPORT_PATH = ROOT / "ZOTERO_IMPORT_AUDIT.md"
BASE = "http://127.0.0.1:23119"
COMMON_TAG = "battery-materials-agent"


def normalize_doi(value: str | None) -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", text)
    return text.rstrip(". ")


def _split_author(name: str) -> dict[str, str]:
    clean = re.sub(r"\s+", " ", name).strip()
    if not clean:
        return {"creatorType": "author", "name": "Unknown"}
    if "," in clean:
        last, first = [part.strip() for part in clean.split(",", 1)]
        return {"creatorType": "author", "firstName": first, "lastName": last}
    parts = clean.split(" ")
    if len(parts) == 1:
        return {"creatorType": "author", "name": clean}
    return {
        "creatorType": "author",
        "firstName": " ".join(parts[:-1]),
        "lastName": parts[-1],
    }


def build_zotero_item(paper: dict[str, Any], connector_id: str) -> dict[str, Any]:
    verification_tag = "WOS-verified" if paper.get("wos_uid") else "DOI-publisher-verified"
    tags = [COMMON_TAG, verification_tag] + list(paper.get("tags_zh", []))
    seen: set[str] = set()
    unique_tags = []
    for tag in tags:
        if tag and tag.casefold() not in seen:
            seen.add(tag.casefold())
            unique_tags.append({"tag": tag})
    return {
        "id": connector_id,
        "itemType": "journalArticle",
        "title": paper["title"],
        "creators": [_split_author(name) for name in paper.get("authors", [])],
        "abstractNote": paper.get("summary", ""),
        "publicationTitle": paper.get("journal", ""),
        "date": str(paper.get("year", "")),
        "DOI": paper.get("doi", ""),
        "url": paper.get("url") or f"https://doi.org/{paper.get('doi', '')}",
        "language": "en",
        "extra": (
            f"WOS: {paper['wos_uid']}\nEvidence status: WOS verified 2026-09-13"
            if paper.get("wos_uid")
            else "Evidence status: DOI and publisher record verified 2026-09-13; WOS not checked"
        ),
        "tags": unique_tags,
    }


def _request(
    path: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> tuple[int, bytes, dict[str, str]]:
    base_headers = {
        "Zotero-Allowed-Request": "true",
        "X-Zotero-Connector-API-Version": "3",
        "User-Agent": "BatteryMaterialsAgent/1.0",
    }
    base_headers.update(headers or {})
    request = Request(BASE + path, data=data, headers=base_headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.read(), dict(response.headers.items())
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Zotero HTTP {exc.code} for {path}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(
            "无法连接 Zotero。请启动 Zotero，并在设置→高级中允许本机其他应用通信。"
        ) from exc


def ping() -> str:
    status, body, _ = _request("/connector/ping", timeout=5)
    if status != 200:
        raise RuntimeError(f"Zotero connector ping returned HTTP {status}")
    return body.decode("utf-8", errors="replace")


def list_top_items() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    start = 0
    while True:
        query = urlencode({"format": "json", "limit": 100, "start": start})
        status, body, _ = _request(f"/api/users/0/items/top?{query}", timeout=30)
        if status != 200:
            raise RuntimeError(f"Zotero local API returned HTTP {status}")
        page = json.loads(body.decode("utf-8"))
        rows.extend(page)
        if len(page) < 100:
            return rows
        start += len(page)


def list_children(item_key: str) -> list[dict[str, Any]]:
    query = urlencode({"format": "json", "limit": 100})
    status, body, _ = _request(
        f"/api/users/0/items/{item_key}/children?{query}", timeout=30
    )
    if status != 200:
        return []
    return json.loads(body.decode("utf-8"))


def _item_doi(item: dict[str, Any]) -> str:
    data = item.get("data", item)
    doi = normalize_doi(data.get("DOI"))
    if doi:
        return doi
    extra = str(data.get("extra", ""))
    match = re.search(r"\b10\.\d{4,9}/\S+", extra, flags=re.IGNORECASE)
    return normalize_doi(match.group(0)) if match else ""


def save_new_item_with_optional_pdf(
    paper: dict[str, Any], pdf_path: Path | None
) -> dict[str, Any]:
    session_id = "battery-agent-" + uuid.uuid4().hex
    connector_id = "paper-" + uuid.uuid4().hex
    payload = {
        "sessionID": session_id,
        "uri": paper.get("url") or f"https://doi.org/{paper['doi']}",
        "items": [build_zotero_item(paper, connector_id)],
    }
    status, _, _ = _request(
        "/connector/saveItems",
        method="POST",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    if status not in (200, 201):
        raise RuntimeError(f"saveItems returned HTTP {status}")

    attachment_status = "not_available"
    if pdf_path and pdf_path.is_file():
        body = pdf_path.read_bytes()
        if not body.startswith(b"%PDF-"):
            raise RuntimeError(f"本地文件不是 PDF: {pdf_path}")
        metadata = {
            "sessionID": session_id,
            "parentItemID": connector_id,
            "title": f"{paper['title']} - Full Text PDF",
            "url": paper.get("url") or f"https://doi.org/{paper['doi']}",
        }
        attach_status, _, _ = _request(
            "/connector/saveAttachment",
            method="POST",
            data=body,
            headers={
                "Content-Type": "application/pdf",
                "Content-Length": str(len(body)),
                "X-Metadata": json.dumps(metadata, ensure_ascii=True, separators=(",", ":")),
            },
            timeout=120,
        )
        if attach_status not in (200, 201):
            raise RuntimeError(f"saveAttachment returned HTTP {attach_status}")
        attachment_status = "submitted"
    return {"item": "created", "attachment": attachment_status}


def _pdf_for(paper_id: str, manifest: dict[str, Any]) -> Path | None:
    row = manifest.get("papers", {}).get(paper_id, {})
    if row.get("status") != "downloaded":
        return None
    relative = row.get("local_pdf")
    if not relative:
        return None
    path = ROOT / relative
    return path if path.is_file() else None


def verify_import(papers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    wanted = {normalize_doi(paper["doi"]): paper for paper in papers}
    top_items = list_top_items()
    result: dict[str, dict[str, Any]] = {}
    for item in top_items:
        doi = _item_doi(item)
        if doi not in wanted:
            continue
        data = item.get("data", item)
        key = item.get("key") or data.get("key")
        children = list_children(key) if key else []
        pdfs = [
            child
            for child in children
            if (child.get("data", child).get("contentType") == "application/pdf")
        ]
        result[doi] = {
            "item_key": key,
            "pdf_attachment_keys": [
                child.get("key") or child.get("data", child).get("key") for child in pdfs
            ],
        }
    return result


def write_report(
    papers: list[dict[str, Any]],
    actions: dict[str, dict[str, Any]],
    verified: dict[str, dict[str, Any]],
) -> None:
    lines = [
        "# Zotero 导入审计",
        "",
        f"- 核验时间：{datetime.now(timezone.utc).isoformat()}",
        f"- 目标记录：{len(papers)}",
        f"- Zotero 中核验到的目标 DOI：{len(verified)}",
        f"- 带 PDF 附件的目标记录：{sum(bool(row['pdf_attachment_keys']) for row in verified.values())}",
        f"- 统一标签：`{COMMON_TAG}`",
        "- 写入策略：按 DOI 幂等；已存在条目不重复创建；只附加本地审计通过的主文 PDF。",
        "",
        "## 逐篇状态",
        "",
    ]
    for paper in papers:
        doi = normalize_doi(paper["doi"])
        action = actions.get(doi, {})
        check = verified.get(doi)
        if check:
            attachment = "有 PDF" if check["pdf_attachment_keys"] else "无 PDF"
            state = f"已核验，{attachment}"
        else:
            state = "未在 Zotero 中核验到"
        lines.append(f"- {paper['title']} — `{doi}` — {action.get('item', '未处理')}；{state}")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import verified papers into Zotero")
    parser.add_argument("--apply", action="store_true", help="write missing records to Zotero")
    parser.add_argument("--paper-id", action="append", help="limit to one or more paper IDs")
    args = parser.parse_args()

    papers = json.loads(PAPERS_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if args.paper_id:
        selected = set(args.paper_id)
        papers = [paper for paper in papers if paper["id"] in selected]
        unknown = selected - {paper["id"] for paper in papers}
        if unknown:
            raise SystemExit(f"Unknown paper IDs: {', '.join(sorted(unknown))}")

    print(f"Zotero: {ping()}")
    existing = {_item_doi(item): item for item in list_top_items() if _item_doi(item)}
    actions: dict[str, dict[str, Any]] = {}
    for index, paper in enumerate(papers, 1):
        doi = normalize_doi(paper["doi"])
        if doi in existing:
            actions[doi] = {"item": "skipped_existing", "attachment": "unchanged"}
            print(f"[{index}/{len(papers)}] SKIP existing {doi}")
            continue
        pdf_path = _pdf_for(paper["id"], manifest)
        if not args.apply:
            actions[doi] = {
                "item": "would_create",
                "attachment": "would_attach" if pdf_path else "not_available",
            }
            print(f"[{index}/{len(papers)}] PLAN create {doi}; PDF={bool(pdf_path)}")
            continue
        print(f"[{index}/{len(papers)}] CREATE {doi}; PDF={bool(pdf_path)}")
        try:
            actions[doi] = save_new_item_with_optional_pdf(paper, pdf_path)
        except Exception as exc:  # keep later verified records progressing
            actions[doi] = {"item": "failed", "error": str(exc)}
            print(f"  ERROR: {exc}", file=sys.stderr)
        time.sleep(0.05)

    verified = verify_import(papers)
    write_report(papers, actions, verified)
    print(
        f"Verified {len(verified)}/{len(papers)} DOI records; "
        f"{sum(bool(row['pdf_attachment_keys']) for row in verified.values())} with PDFs"
    )
    print(REPORT_PATH)
    return 0 if not args.apply or len(verified) == len(papers) else 1


if __name__ == "__main__":
    raise SystemExit(main())
