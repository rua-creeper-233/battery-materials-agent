"""Auditable method and paper-kind tags for the curated library."""

from __future__ import annotations

import re
from typing import Any


METHOD_RULES: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = (
    (
        "DFT",
        (
            re.compile(r"\bdft(?:\+u)?\b", re.I),
            re.compile(r"density functional", re.I),
            re.compile(r"first[- ]principles?", re.I),
            re.compile(r"\bab initio\b", re.I),
        ),
    ),
    (
        "MD",
        (
            re.compile(r"molecular dynamics", re.I),
            re.compile(r"\baimd\b", re.I),
            re.compile(r"\bmlmd\b", re.I),
            re.compile(r"\blammps\b", re.I),
        ),
    ),
    ("VASP", (re.compile(r"\bvasp(?:kit)?\b", re.I),)),
    # MS means BIOVIA Materials Studio.  It is deliberately restricted to the
    # curated methods/tags fields: a background citation is not evidence that
    # the paper used Materials Studio in its workflow.
    ("MS", (re.compile(r"materials studio", re.I),)),
)


def _as_text(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(_as_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_as_text(item) for item in value.values())
    return str(value or "")


def classify_paper(paper: dict[str, Any]) -> dict[str, Any]:
    broad_fields = {
        "title": paper.get("title"),
        "role": paper.get("role"),
        "methods": paper.get("methods", []),
        "tags_zh": paper.get("tags_zh", []),
        "summary": paper.get("summary"),
        "protocol_steps": paper.get("protocol_steps", []),
    }
    broad_text = _as_text(broad_fields)
    strict_ms_text = _as_text(
        {"methods": paper.get("methods", []), "tags_zh": paper.get("tags_zh", [])}
    )
    method_tags: list[str] = []
    basis: dict[str, list[str]] = {}
    for tag, patterns in METHOD_RULES:
        source = strict_ms_text if tag == "MS" else broad_text
        matches = sorted(
            {match.group(0) for pattern in patterns for match in pattern.finditer(source)},
            key=str.casefold,
        )
        if matches:
            method_tags.append(tag)
            basis[tag] = matches[:6]

    paper_kind = "方法论文" if paper.get("collection") == "starter" else "进展论文"
    review_tag = "综述" if "review" in str(paper.get("document_type", "")).lower() else None
    display_tags = [paper_kind, *method_tags]
    if review_tag:
        display_tags.insert(1, review_tag)
    return {
        "paper_kind": paper_kind,
        "method_tags": method_tags,
        "display_tags": display_tags,
        "tag_basis": basis,
        "tag_policy": "curated_metadata_v1",
    }


def attach_tags(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**paper, **classify_paper(paper)} for paper in papers]
