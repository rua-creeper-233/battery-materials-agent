"""Build the static GitHub Pages bundle in ./docs."""

from __future__ import annotations

import html
import json
import re
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
    "RELEASE_20261014_LEARNING_ROUTE.md",
    "RELEASE_20261014_FRONTEND.md",
)
PAGE_NAMES = ("index.html", "future-directions.html", "ai-battery-applications.html", "foundations.html")
ASSET_NAMES = ("learning-route.css", "learning-route.js", "lab-ui.css", "lab-ui.js", "browser_agent.js", "tutorials.js", "tutorials.css", "dft_lessons.js", "beginner_lessons.js", "md_lessons.js")
DATA_NAMES = ("papers.json", "paper_tags.json", "search_config.json", "project_status.json", "learning_route.json", "paper_titles_zh.json")


def progress_text(status: dict) -> str:
    """Only display public aggregate statistics, never private access records."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(status.get("as_of", ""))):
        raise publication_safety.PublicationSafetyError("public progress needs an update date")
    for key in ("papers", "dataset_rows"):
        if type(status.get(key)) is not int or status[key] < 0:
            raise publication_safety.PublicationSafetyError("public progress counts must be nonnegative integers")
    return (f"项目更新 {status['as_of']} · {status['papers']} 篇论文 · "
            f"{status['dataset_rows']} 条问答数据 · 本版未重新训练模型")


def prepare_page(source: str, status_text: str, shared_css: str = "") -> str:
    """Pre-render progress and shared styles; keep authored scripts unchanged."""
    source = re.sub(
        r"(<p\b[^>]*\bdata-project-progress[^>]*>).*?(</p>)",
        lambda match: match[1] + html.escape(status_text) + match[2],
        source, flags=re.S,
    )
    if shared_css:
        css = re.sub(r"</style", lambda _: r"<\/style", shared_css, flags=re.I)
        source = source.replace("</head>", f'<style data-lab-ui-inline>{css}</style></head>', 1)
    return source


def copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def main() -> None:
    papers_path = ROOT / "data" / "papers.json"
    papers = json.loads(papers_path.read_text(encoding="utf-8"))

    # Validate every sensitive source before the first docs mutation.
    publication_safety.validate_public_zotero_map(ROOT / "static" / "data" / "zotero-links.json")
    method_path = ROOT / "data" / "method_evidence.auto.json"
    method = json.loads(method_path.read_text(encoding="utf-8"))
    if method.get("visibility") != "public_sanitized" or method.get("papers") != {}:
        raise publication_safety.PublicationSafetyError("public method evidence must use an empty allowlist")
    public_method = method

    # Validate every planned source and render the route in memory before any
    # output write. This keeps a bad guide/catalog/route from partially mutating docs.
    from build_learning_route import build as render_route, validate as validate_route
    from paper_titles import load_titles
    route = json.loads((ROOT / "data" / "learning_route.json").read_text(encoding="utf-8"))
    route_catalog = validate_route(route, papers)
    titles = load_titles(papers, ROOT / "data" / "paper_titles_zh.json")
    status = json.loads((ROOT / "data" / "project_status.json").read_text(encoding="utf-8"))
    status_text = progress_text(status)
    if status["papers"] != len(papers):
        raise publication_safety.PublicationSafetyError("public progress is stale relative to the catalog")
    shared_css = (ROOT / "static" / "lab-ui.css").read_text(encoding="utf-8")
    route_html = prepare_page(render_route(
        route, route_catalog,
        stylesheet_text=(ROOT / "static" / "learning-route.css").read_text(encoding="utf-8") + "\n" + shared_css,
        title_records=titles["papers"],
    ), status_text)
    rendered = {name: prepare_page((ROOT / "static" / name).read_text(encoding="utf-8"), status_text, shared_css) for name in PAGE_NAMES}
    rendered["learning-route.html"] = route_html
    for name, content in rendered.items():
        publication_safety.assert_clean(publication_safety.scan_text(content, f"docs/{name}"))
    planned = [
        ROOT / "static" / name for name in (*PAGE_NAMES, *ASSET_NAMES)
    ] + [ROOT / "FINETUNE_INTEGRATION.md"]
    planned += [ROOT / "examples" / "ai_battery" / name for name in ("relax_mace.py", "msd_from_csv.py", "example_trajectory.csv")]
    planned += [ROOT / "guides" / name for name in GUIDE_NAMES]
    planned += [ROOT / "data" / name for name in DATA_NAMES]
    planned += [ROOT / "static" / "data" / "zotero-links.json", method_path]
    missing = [path.relative_to(ROOT).as_posix() for path in planned if not path.is_file()]
    if missing:
        raise publication_safety.PublicationSafetyError("missing public build inputs: " + ", ".join(missing))
    publication_safety.assert_clean(publication_safety.scan_files(planned, ROOT))

    DOCS.mkdir(parents=True, exist_ok=True)
    for name, content in rendered.items():
        (DOCS / name).write_text(content, encoding="utf-8")
    (ROOT / "static" / "learning-route.html").write_text(route_html, encoding="utf-8")
    for asset in ASSET_NAMES:
        copy(ROOT / "static" / asset, DOCS / asset)
    copy(ROOT / "FINETUNE_INTEGRATION.md", DOCS / "FINETUNE_INTEGRATION.md")
    for example in ("relax_mace.py", "msd_from_csv.py", "example_trajectory.csv"):
        copy(ROOT / "examples" / "ai_battery" / example, DOCS / "examples" / "ai_battery" / example)
    for guide in GUIDE_NAMES:
        copy(ROOT / "guides" / guide, DOCS / "guides" / guide)
    for name in DATA_NAMES:
        copy(ROOT / "data" / name, DOCS / "data" / name)
    for name in ("project_status.json", "paper_titles_zh.json"):
        copy(ROOT / "data" / name, ROOT / "static" / "data" / name)
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
