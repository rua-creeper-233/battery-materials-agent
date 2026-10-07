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
    copy(ROOT / "static" / "future-directions.html", DOCS / "future-directions.html")
    copy(ROOT / "static" / "ai-battery-applications.html", DOCS / "ai-battery-applications.html")
    copy(ROOT / "FINETUNE_INTEGRATION.md", DOCS / "FINETUNE_INTEGRATION.md")
    copy(ROOT / "static" / "browser_agent.js", DOCS / "browser_agent.js")
    for example in ("relax_mace.py", "msd_from_csv.py", "example_trajectory.csv"):
        copy(ROOT / "examples" / "ai_battery" / example, DOCS / "examples" / "ai_battery" / example)
    for asset in ("tutorials.js", "tutorials.css", "dft_lessons.js", "beginner_lessons.js", "md_lessons.js"):
        copy(ROOT / "static" / asset, DOCS / asset)
    for guide in (
        "AGENT_IMPLEMENTATION_GUIDE.md",
        "BATTERY_RESEARCH_ROADMAP_20260918.md",
        "AGENT_STATUS_20260920.md",
        "BATTERY_COMPUTATION_FUTURE_DIRECTIONS.md",
        "AI_BATTERY_APPLICATIONS.md",
        "REPRODUCIBLE_BATTERY_AI_20261008.md",
        "PROJECT_STATUS.md",
        "RELEASE_20261008.md",
        "RELEASE_20261008_CONTINUATION.md",
    ):
        copy(ROOT / "guides" / guide, DOCS / "guides" / guide)
    copy(papers_path, DOCS / "data" / "papers.json")
    copy(ROOT / "data" / "paper_tags.json", DOCS / "data" / "paper_tags.json")
    copy(ROOT / "data" / "search_config.json", DOCS / "data" / "search_config.json")
    copy(ROOT / "data" / "project_status.json", DOCS / "data" / "project_status.json")
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
