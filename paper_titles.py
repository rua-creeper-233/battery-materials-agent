"""Validate public reference translations without changing canonical titles."""
from __future__ import annotations

import json
import re
from pathlib import Path

from publication_safety import PublicationSafetyError

ROOT = Path(__file__).resolve().parent
TITLE_PATH = ROOT / "data" / "paper_titles_zh.json"


def validate_titles(payload: object, papers: list[dict]) -> dict:
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "as_of", "notice", "papers"}:
        raise PublicationSafetyError("public title map must use the exact metadata allowlist")
    if payload.get("schema_version") != 1 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(payload.get("as_of", ""))):
        raise PublicationSafetyError("title map needs a supported schema and update date")
    if not isinstance(payload.get("notice"), str) or not payload["notice"].strip():
        raise PublicationSafetyError("reference translations need a provenance notice")
    rows = payload.get("papers")
    catalog = {str(p["id"]): p for p in papers}
    if not isinstance(rows, dict) or set(rows) != set(catalog):
        raise PublicationSafetyError("title translations must cover the catalog exactly")
    for pid, entry in rows.items():
        if not isinstance(entry, dict) or set(entry) != {"title", "title_zh", "doi"}:
            raise PublicationSafetyError("title records must contain only English, Chinese and DOI")
        original = catalog[pid]
        if entry.get("title") != original.get("title") or entry.get("doi") != original.get("doi"):
            raise PublicationSafetyError("title map is stale or disagrees with the scientific catalog")
        zh = entry.get("title_zh")
        if not isinstance(zh, str) or not zh.strip() or len(zh) > 800 or not re.search(r"[\u3400-\u9fff]", zh):
            raise PublicationSafetyError("each title needs a nonempty Chinese reference translation")
    return payload


def load_titles(papers: list[dict], path: Path = TITLE_PATH) -> dict:
    return validate_titles(json.loads(path.read_text(encoding="utf-8")), papers)
