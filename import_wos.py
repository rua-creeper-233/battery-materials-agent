"""Import a Web of Science plain-text export into the local paper store.

Recommended WoS export fields: Full Record and Cited References.
The importer never overwrites the curated seed library unless --merge is supplied.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


FIELD_MAP = {
    "TI": "title",
    "SO": "journal",
    "PY": "year",
    "DI": "doi",
    "UT": "wos_ut",
    "AB": "abstract",
    "DE": "author_keywords",
    "ID": "keywords_plus",
}


def parse_wos_text(text: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current: dict[str, list[str]] = {}
    active_field: str | None = None

    for raw_line in text.replace("\r\n", "\n").split("\n"):
        if raw_line == "ER":
            if current:
                records.append(_normalize(current))
            current = {}
            active_field = None
            continue
        match = re.match(r"^([A-Z0-9]{2}) (.*)$", raw_line)
        if match:
            active_field = match.group(1)
            current.setdefault(active_field, []).append(match.group(2).strip())
        elif raw_line.startswith("   ") and active_field:
            current.setdefault(active_field, []).append(raw_line.strip())

    if current:
        records.append(_normalize(current))
    return [record for record in records if record.get("title")]


def _normalize(fields: dict[str, list[str]]) -> dict[str, Any]:
    title = " ".join(fields.get("TI", [])).strip()
    doi = " ".join(fields.get("DI", [])).strip()
    raw_id = doi or " ".join(fields.get("UT", [])) or title
    safe_id = re.sub(r"[^a-z0-9]+", "_", raw_id.lower()).strip("_")[:80]
    record: dict[str, Any] = {
        "id": f"wos_{safe_id}",
        "title": title,
        "authors": fields.get("AF") or fields.get("AU") or [],
        "year": _year(fields.get("PY", [""])[0]),
        "journal": " ".join(fields.get("SO", [])).strip(),
        "document_type": " ".join(fields.get("DT", ["Article"])).strip(),
        "doi": doi,
        "url": f"https://doi.org/{doi}" if doi else "",
        "role": "WOS导入记录（待人工标注用途）",
        "systems": _split_keywords(fields.get("DE", [])),
        "methods": [],
        "properties": [],
        "tags_zh": [],
        "summary": " ".join(fields.get("AB", [])).strip(),
        "evidence": [],
        "relations": [],
        "verification": {
            "publisher": "not_checked",
            "doi": "present" if doi else "missing",
            "wos": "exported_from_wos",
            "wos_ut": " ".join(fields.get("UT", [])).strip(),
        },
        "wos_raw": {
            "author_keywords": _split_keywords(fields.get("DE", [])),
            "keywords_plus": _split_keywords(fields.get("ID", [])),
            "times_cited": " ".join(fields.get("TC", [])).strip(),
        },
    }
    return record


def _year(value: str) -> int | str:
    match = re.search(r"\d{4}", value)
    return int(match.group(0)) if match else value


def _split_keywords(values: list[str]) -> list[str]:
    joined = " ".join(values)
    return [item.strip() for item in joined.split(";") if item.strip()]


def merge_records(seed: list[dict[str, Any]], imported: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = list(seed)
    seen_doi = {str(item.get("doi", "")).lower() for item in result if item.get("doi")}
    seen_ut = {
        str(item.get("verification", {}).get("wos_ut", "")).lower()
        for item in result
        if item.get("verification", {}).get("wos_ut")
    }
    for record in imported:
        doi = str(record.get("doi", "")).lower()
        ut = str(record.get("verification", {}).get("wos_ut", "")).lower()
        if (doi and doi in seen_doi) or (ut and ut in seen_ut):
            continue
        result.append(record)
        if doi:
            seen_doi.add(doi)
        if ut:
            seen_ut.add(ut)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a WoS plain-text export")
    parser.add_argument("input", help="WoS savedrecs.txt")
    parser.add_argument("--output", default="data/papers.wos.json")
    parser.add_argument("--merge", help="Optional existing JSON library to merge into the output")
    args = parser.parse_args()

    source = Path(args.input)
    imported = parse_wos_text(source.read_text(encoding="utf-8-sig", errors="replace"))
    output = Path(args.output)
    if not output.is_absolute():
        output = Path(__file__).resolve().parent / output
    records = imported
    if args.merge:
        seed_path = Path(args.merge)
        records = merge_records(json.loads(seed_path.read_text(encoding="utf-8")), imported)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Imported {len(imported)} WoS records; wrote {len(records)} records to {output}")


if __name__ == "__main__":
    main()
