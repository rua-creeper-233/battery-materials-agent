"""Repair Zotero records whose DOI/title metadata was corrected in the library.

Only records created from the 2026-09-20 expansion batch are considered.  If a
correct DOI already exists, an attachment-free erroneous duplicate is removed;
records with children are never deleted automatically.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import import_zotero_library as zotero
from repair_library_metadata import REPAIRS


ROOT = Path(__file__).resolve().parent
PAPERS = ROOT / "data" / "papers.json"
REPORT = ROOT / "ZOTERO_METADATA_REPAIR_20260920.md"

OLD_TO_NEW = {
    "10.1016/0010-4655(96)00008-0": "10.1016/0927-0256(96)00008-0",
    "10.1080/01418619808243130": "10.1103/PhysRevB.57.1505",
    "10.1002/jcc.20495": "10.1063/1.3382344",
    "10.1063/1.132322": "10.1063/1.1323224",
    "10.1063/1.1649964": "10.1016/j.commatsci.2005.04.010",
    "10.1063/1.4935867": "10.1016/j.jcp.2014.12.018",
    "10.1016/j.cpc.2017.07.018": "10.1016/j.commatsci.2017.08.031",
    "10.1038/s41524-020-0312-8": "10.1038/s41524-020-0283-z",
    "10.1038/ncomms15172": "10.1039/C6EE02697D",
    "10.1039/c5ee00664d": "10.1016/j.isci.2019.05.036",
    "10.1039/c6cs00586h": "10.1149/2.1441707jes",
    "10.1016/j.commatsci.2014.10.002": "10.1002/cpe.3505",
    "10.1038/npjcompumats.2016.28": "10.1016/j.commatsci.2018.05.018",
}


def _paper_by_doi() -> dict[str, dict[str, Any]]:
    rows = json.loads(PAPERS.read_text(encoding="utf-8"))
    return {zotero.normalize_doi(row.get("doi")): row for row in rows}


def _updated_data(item: dict[str, Any], paper: dict[str, Any]) -> dict[str, Any]:
    data = dict(item.get("data", item))
    data.update(
        {
            "title": paper["title"],
            "creators": [zotero._split_author(name) for name in paper.get("authors", [])],
            "abstractNote": paper.get("summary", ""),
            "publicationTitle": paper.get("journal", ""),
            "date": str(paper.get("year", "")),
            "DOI": paper["doi"],
            "url": paper.get("url") or f"https://doi.org/{paper['doi']}",
        }
    )
    tags = list(data.get("tags", []))
    if not any(str(tag.get("tag", "")).casefold() == "metadata-repaired-20260920" for tag in tags):
        tags.append({"tag": "metadata-repaired-20260920"})
    data["tags"] = tags
    return data


def _put_item(key: str, data: dict[str, Any], server_id: str, api_key: str) -> None:
    status, _, _ = zotero._request(
        f"/api/users/0/items/{key}",
        method="PUT",
        data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Zotero-Server-ID": server_id,
            "Zotero-API-Key": api_key,
        },
        timeout=30,
    )
    if status not in (200, 204):
        raise RuntimeError(f"Zotero PUT returned HTTP {status} for {key}")


def _delete_item(key: str, version: int, server_id: str, api_key: str) -> None:
    status, _, _ = zotero._request(
        f"/api/users/0/items/{key}?version={version}",
        method="DELETE",
        headers={
            "Zotero-Server-ID": server_id,
            "Zotero-API-Key": api_key,
            "If-Unmodified-Since-Version": str(version),
        },
        timeout=30,
    )
    if status not in (200, 204):
        raise RuntimeError(f"Zotero DELETE returned HTTP {status} for {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair DOI metadata in the local Zotero client.")
    parser.add_argument("--apply", action="store_true", help="write changes; default is a read-only plan")
    args = parser.parse_args()
    zotero.ping()
    _, _, server_headers = zotero._request("/api/users/0/items/top?limit=1")
    server_id = server_headers.get("Zotero-Server-ID", "")
    if not server_id:
        raise RuntimeError("Zotero local API did not return Zotero-Server-ID")
    api_key = ""
    if args.apply:
        status, body, _ = zotero._request(
            "/api/local/authorize",
            method="POST",
            data=json.dumps({"appName": "Battery Materials Agent metadata repair"}).encode(),
            headers={"Content-Type": "application/json", "Zotero-Server-ID": server_id},
            timeout=120,
        )
        auth = json.loads(body.decode("utf-8"))
        api_key = str(auth.get("key", ""))
        if status != 200 or not api_key:
            raise RuntimeError("Zotero did not grant local write authorization")
    papers = _paper_by_doi()
    rows = zotero.list_top_items()
    current_by_doi = {zotero.normalize_doi(item.get("data", item).get("DOI")): item for item in rows}
    actions: list[str] = []
    for old_doi, new_doi in OLD_TO_NEW.items():
        item = current_by_doi.get(old_doi)
        if not item:
            continue
        key = item.get("key") or item.get("data", {}).get("key")
        existing = current_by_doi.get(zotero.normalize_doi(new_doi))
        if existing and (existing.get("key") or existing.get("data", {}).get("key")) != key:
            children = zotero.list_children(key)
            if children:
                actions.append(f"保留错误条目 {key}（有 {len(children)} 个附件），需人工合并到 {existing.get('key')}")
                continue
            actions.append(f"删除重复错误条目 {key}: {old_doi}（正确条目 {existing.get('key')} 已存在）")
            if args.apply:
                _delete_item(key, int(item.get("version") or item.get("data", {}).get("version") or 0), server_id, api_key)
            continue
        paper = papers.get(zotero.normalize_doi(new_doi))
        if not paper:
            raise RuntimeError(f"corrected DOI missing from local library: {new_doi}")
        actions.append(f"修正 {key}: {old_doi} -> {new_doi}")
        if args.apply:
            _put_item(key, _updated_data(item, paper), server_id, api_key)

    # The author-only repairs retain their DOI, so they are not in the old-to-
    # new mapping above.  Update an existing current record in place.
    mapped_ids = {paper_id for paper_id, repair in REPAIRS.items() if "doi" in repair}
    for paper_id, repair in REPAIRS.items():
        if paper_id in mapped_ids:
            continue
        paper = next((row for row in json.loads(PAPERS.read_text(encoding="utf-8"))
                      if row.get("id") == paper_id), None)
        if not paper:
            continue
        item = current_by_doi.get(zotero.normalize_doi(paper.get("doi")))
        if not item:
            continue
        key = item.get("key") or item.get("data", {}).get("key")
        actions.append(f"规范作者 {key}: {paper.get('doi')}")
        if args.apply:
            _put_item(key, _updated_data(item, paper), server_id, api_key)
    mode = "已执行" if args.apply else "计划"
    REPORT.write_text(
        "# Zotero 元数据修复\n\n"
        f"- 模式：{mode}\n"
        f"- 目标映射：{len(OLD_TO_NEW)} 条\n\n"
        + "\n".join(f"- {action}" for action in actions)
        + "\n",
        encoding="utf-8",
    )
    print(f"{mode}：{len(actions)} 个 Zotero 条目动作；报告：{REPORT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
