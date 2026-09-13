"""Export the verified 16-paper seed set to a local Zotero-ready RIS file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "exports" / "battery_materials_16_verified.ris"


def clean(value: object) -> str:
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split())


def render(paper: dict) -> str:
    lines = ["TY  - JOUR"]
    for author in paper.get("authors", []):
        lines.append(f"AU  - {clean(author)}")
    lines.extend(
        [
            f"TI  - {clean(paper['title'])}",
            f"JO  - {clean(paper['journal'])}",
            f"PY  - {paper['year']}",
            f"DO  - {paper['doi']}",
            f"UR  - https://doi.org/{paper['doi']}",
        ]
    )
    if paper.get("wos_uid"):
        lines.append(f"AN  - {paper['wos_uid']}")
        lines.append(
            f"L2  - https://www.webofscience.com/wos/woscc/full-record/{paper['wos_uid']}"
        )
    for keyword in paper.get("keywords", []):
        lines.append(f"KW  - {clean(keyword)}")
    lines.extend(["N1  - Seed metadata verified in Web of Science on 2026-09-13", "ER  - "])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    library = json.loads((ROOT / "data" / "papers.json").read_text(encoding="utf-8"))
    papers = [paper for paper in library if paper.get("wos_uid")]
    if len(papers) != 16:
        raise SystemExit("expected 16 WOS-verified seed papers")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n\n".join(render(paper) for paper in papers) + "\n", encoding="utf-8")
    print(f"Exported {len(papers)} records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
