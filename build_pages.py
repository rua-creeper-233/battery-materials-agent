"""Build the static GitHub Pages bundle in ./docs."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"


def copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def main() -> None:
    papers_path = ROOT / "data" / "papers.json"
    json.loads(papers_path.read_text(encoding="utf-8"))

    copy(ROOT / "static" / "index.html", DOCS / "index.html")
    copy(ROOT / "static" / "browser_agent.js", DOCS / "browser_agent.js")
    for asset in ("tutorials.js", "tutorials.css"):
        copy(ROOT / "static" / asset, DOCS / asset)
    copy(papers_path, DOCS / "data" / "papers.json")
    copy(ROOT / "data" / "paper_tags.json", DOCS / "data" / "paper_tags.json")
    copy(ROOT / "data" / "search_config.json", DOCS / "data" / "search_config.json")
    method_path = ROOT / "data" / "method_evidence.auto.json"
    json.loads(method_path.read_text(encoding="utf-8"))
    copy(method_path, DOCS / "data" / "method_evidence.auto.json")
    copy(
        ROOT / "static" / "data" / "zotero-links.json",
        DOCS / "data" / "zotero-links.json",
    )
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"GitHub Pages bundle built at: {DOCS}")


if __name__ == "__main__":
    main()
