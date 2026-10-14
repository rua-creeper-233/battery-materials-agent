"""Build the static GitHub Pages bundle in ./docs."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
import publication_safety


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
GUIDE_NAMES = (
    "AGENT_IMPLEMENTATION_GUIDE.md", "BATTERY_RESEARCH_ROADMAP_20260918.md",
    "AGENT_STATUS_20260920.md", "BATTERY_COMPUTATION_FUTURE_DIRECTIONS.md",
    "AI_BATTERY_APPLICATIONS.md", "REPRODUCIBLE_BATTERY_AI_20261008.md",
    "PROJECT_STATUS.md", "RELEASE_20261008.md", "RELEASE_20261008_CONTINUATION.md",
    "RELEASE_20261008_FOUNDATIONS.md", "LEARNING_ROUTE_20261014.md",
    "BASELINE_DOWNLOAD_LIST_20261014.md", "RELEASE_20261014_LEARNING_ROUTE.md",
)


def copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def main() -> None:
    papers_path = ROOT / "data" / "papers.json"
    json.loads(papers_path.read_text(encoding="utf-8"))

    # Validate every sensitive source before the first docs mutation.
    publication_safety.validate_public_zotero_map(ROOT / "static" / "data" / "zotero-links.json")
    method_path = ROOT / "data" / "method_evidence.auto.json"
    method = json.loads(method_path.read_text(encoding="utf-8"))
    if method.get("visibility") != "public_sanitized" or method.get("papers") != {}:
        raise publication_safety.PublicationSafetyError("public method evidence must use an empty allowlist")
    public_method = method

    # Validate every planned source and render the route in memory before any
    # output write. This keeps a bad guide/catalog/route from partially mutating docs.
    from build_learning_route import ROUTE_PATH, PAPERS_PATH, build as render_route, validate as validate_route
    route = json.loads(ROUTE_PATH.read_text(encoding="utf-8"))
    route_papers = json.loads(PAPERS_PATH.read_text(encoding="utf-8"))
    route_catalog = validate_route(route, route_papers)
    route_html = render_route(route, route_catalog, stylesheet_text=(ROOT / "static" / "learning-route.css").read_text(encoding="utf-8"))
    publication_safety.assert_clean(publication_safety.scan_text(route_html, "static/learning-route.html"))
    planned = [
        ROOT / "static" / name for name in ("index.html", "future-directions.html", "ai-battery-applications.html", "foundations.html", "learning-route.css", "learning-route.js", "browser_agent.js", "tutorials.js", "tutorials.css", "dft_lessons.js", "beginner_lessons.js", "md_lessons.js")
    ] + [ROOT / "FINETUNE_INTEGRATION.md"]
    planned += [ROOT / "examples" / "ai_battery" / name for name in ("relax_mace.py", "msd_from_csv.py", "example_trajectory.csv")]
    planned += [ROOT / "guides" / name for name in GUIDE_NAMES]
    planned += [ROOT / "data" / name for name in ("papers.json", "paper_tags.json", "search_config.json", "project_status.json", "learning_route.json")]
    planned += [ROOT / "static" / "data" / "zotero-links.json", method_path]
    publication_safety.assert_clean(publication_safety.scan_files(planned, ROOT))

    copy(ROOT / "static" / "index.html", DOCS / "index.html")
    copy(ROOT / "static" / "future-directions.html", DOCS / "future-directions.html")
    copy(ROOT / "static" / "ai-battery-applications.html", DOCS / "ai-battery-applications.html")
    copy(ROOT / "static" / "foundations.html", DOCS / "foundations.html")
    (ROOT / "static" / "learning-route.html").write_text(route_html, encoding="utf-8")
    copy(ROOT / "static" / "learning-route.html", DOCS / "learning-route.html")
    copy(ROOT / "static" / "learning-route.css", DOCS / "learning-route.css")
    copy(ROOT / "static" / "learning-route.js", DOCS / "learning-route.js")
    copy(ROOT / "data" / "learning_route.json", DOCS / "data" / "learning_route.json")
    copy(ROOT / "FINETUNE_INTEGRATION.md", DOCS / "FINETUNE_INTEGRATION.md")
    copy(ROOT / "static" / "browser_agent.js", DOCS / "browser_agent.js")
    for example in ("relax_mace.py", "msd_from_csv.py", "example_trajectory.csv"):
        copy(ROOT / "examples" / "ai_battery" / example, DOCS / "examples" / "ai_battery" / example)
    for asset in ("tutorials.js", "tutorials.css", "dft_lessons.js", "beginner_lessons.js", "md_lessons.js"):
        copy(ROOT / "static" / asset, DOCS / asset)
    for guide in GUIDE_NAMES:
        copy(ROOT / "guides" / guide, DOCS / "guides" / guide)
    copy(papers_path, DOCS / "data" / "papers.json")
    copy(ROOT / "data" / "paper_tags.json", DOCS / "data" / "paper_tags.json")
    copy(ROOT / "data" / "search_config.json", DOCS / "data" / "search_config.json")
    copy(ROOT / "data" / "project_status.json", DOCS / "data" / "project_status.json")
    (DOCS / "data").mkdir(parents=True, exist_ok=True)
    (DOCS / "data" / "method_evidence.auto.json").write_text(json.dumps(public_method, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    copy(
        ROOT / "static" / "data" / "zotero-links.json",
        DOCS / "data" / "zotero-links.json",
    )
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"GitHub Pages bundle built at: {DOCS}")


if __name__ == "__main__":
    main()
