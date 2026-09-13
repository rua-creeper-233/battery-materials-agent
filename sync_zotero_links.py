"""Create DOI-to-Zotero deep-link mappings from Zotero's local read API.

Zotero must be running. In Zotero Settings > Advanced, enable:
"Allow other applications on this computer to communicate with Zotero".
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
API_ROOT = "http://127.0.0.1:23119/api/users/0"


def normalize_doi(value: str) -> str:
    doi = (value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix) :].strip()
    return doi


def fetch_json(path: str):
    request = urllib.request.Request(
        f"{API_ROOT}{path}", headers={"Zotero-API-Version": "3"}
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        return json.load(response)


def collect_links(fetcher=fetch_json) -> dict[str, dict]:
    result: dict[str, dict] = {}
    start = 0
    limit = 100

    while True:
        items = fetcher(f"/items/top?format=json&limit={limit}&start={start}")
        if not items:
            break
        for item in items:
            data = item.get("data", {})
            doi = normalize_doi(data.get("DOI", ""))
            if not doi:
                continue
            item_key = item.get("key") or data.get("key")
            attachment_key = None
            if item_key:
                children = fetcher(
                    f"/items/{urllib.parse.quote(item_key)}/children?format=json&limit=100"
                )
                for child in children:
                    child_data = child.get("data", {})
                    filename = child_data.get("filename", "").lower()
                    if (
                        child_data.get("itemType") == "attachment"
                        and (
                            child_data.get("contentType") == "application/pdf"
                            or filename.endswith(".pdf")
                        )
                    ):
                        attachment_key = child.get("key") or child_data.get("key")
                        break
            result[doi] = {
                "title": data.get("title", ""),
                "item_key": item_key,
                "attachment_key": attachment_key,
                "has_pdf": bool(attachment_key),
            }
        if len(items) < limit:
            break
        start += limit

    return result


def write_mapping(mapping: dict[str, dict], paths: list[Path]) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": mapping,
    }
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "static" / "data" / "zotero-links.json",
    )
    parser.add_argument(
        "--pages-output",
        type=Path,
        default=ROOT / "docs" / "data" / "zotero-links.json",
    )
    args = parser.parse_args()

    try:
        mapping = collect_links()
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        print(
            "无法读取 Zotero。本机需启动 Zotero，并在 设置 → 高级 中允许其他应用与 Zotero 通信。\n"
            f"具体错误：{error}",
            file=sys.stderr,
        )
        return 1

    write_mapping(mapping, [args.output, args.pages_output])
    with_pdf = sum(1 for item in mapping.values() if item["has_pdf"])
    print(f"已同步 {len(mapping)} 个 DOI 条目，其中 {with_pdf} 个包含 PDF。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
