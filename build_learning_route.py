"""Build the static, evidence-linked learning route page.

The route is deliberately a build-time artifact: the browser receives all route
copy and paper citations in the HTML, while learning-route.js only improves
search, filtering, and navigation.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import quote, urlsplit


ROOT = Path(__file__).resolve().parent
ROUTE_PATH = ROOT / "data" / "learning_route.json"
PAPERS_PATH = ROOT / "data" / "papers.json"
OUT_PATH = ROOT / "static" / "learning-route.html"
REQUIRED_STAGES = {"baseline", "beginner", "intermediate", "frontier"}
SAFE_INTERNAL = re.compile(r"^(?:\./|\.\./|/(?!/))[^\s<>'\"]*$")


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def safe_url(value: object, *, fallback: str = "#") -> str:
    """Allow only https URLs or relative internal links in public data."""
    candidate = str(value or "")
    if "\n" in candidate or "\r" in candidate:
        return fallback
    raw = candidate.strip()
    if raw.startswith("https://"):
        parsed = urlsplit(raw)
        if parsed.hostname and not parsed.username and not parsed.password:
            return raw
    if SAFE_INTERNAL.fullmatch(raw):
        return raw
    return fallback


def text_list(values: object) -> str:
    if not isinstance(values, list):
        return ""
    return "".join(f"<li>{esc(item)}</li>" for item in values if str(item).strip())


def validate(route: dict, papers: list[dict]) -> dict[str, dict]:
    if route.get("schema_version") != 1:
        raise ValueError("learning_route.json must use schema_version 1")
    stages = route.get("stages")
    if not isinstance(stages, list) or len(stages) != 4 or {s.get("id") for s in stages} != REQUIRED_STAGES:
        raise ValueError("route must contain baseline, beginner, intermediate, and frontier stages")
    catalog = {str(p.get("id")): p for p in papers if p.get("id")}
    listed: list[str] = []
    for stage in stages:
        ids = stage.get("paper_ids", [])
        if not isinstance(ids, list) or len(ids) != len(set(ids)):
            raise ValueError(f"stage {stage.get('id')} has duplicate/non-list paper_ids")
        listed.extend(str(pid) for pid in ids)
        for pid in ids:
            if str(pid) not in catalog:
                raise ValueError(f"unknown catalog paper id: {pid}")
    if len(listed) != len(set(listed)) or set(listed) != set(catalog):
        missing = sorted(set(catalog) - set(listed))
        extra = sorted(set(listed) - set(catalog))
        raise ValueError(f"stage paper_ids must cover catalog exactly (missing={missing[:3]}, extra={extra[:3]})")
    frontier_ids = {f.get("id") for f in route.get("frontiers", [])}
    if len(frontier_ids) != len(route.get("frontiers", [])):
        raise ValueError("frontier ids must be unique")
    for frontier in route.get("frontiers", []):
        frontier_ids_list = frontier.get("paper_ids", [])
        if not isinstance(frontier_ids_list, list) or not frontier_ids_list:
            raise ValueError(f"frontier {frontier.get('id')} must have paper_ids")
        if len(frontier_ids_list) != len(set(frontier_ids_list)):
            raise ValueError(f"frontier {frontier.get('id')} has duplicate paper_ids")
        for pid in frontier_ids_list:
            if str(pid) not in catalog:
                raise ValueError(f"unknown frontier paper id: {pid}")
            if frontier.get("id") not in route.get("papers", {}).get(str(pid), {}).get("frontiers", []):
                raise ValueError(f"frontier {frontier.get('id')} and paper {pid} mappings disagree")
    mappings = route.get("papers", {})
    if set(mappings) != set(catalog):
        raise ValueError("papers mapping must contain exactly every catalog paper id")
    for pid, mapping in mappings.items():
        if mapping.get("stage") not in REQUIRED_STAGES:
            raise ValueError(f"paper {pid} has invalid learning stage")
        stage_ids = next(s.get("paper_ids", []) for s in stages if s.get("id") == mapping.get("stage"))
        if pid not in [str(item) for item in stage_ids]:
            raise ValueError(f"paper {pid} mapping stage disagrees with stage.paper_ids")
        if any(fid not in frontier_ids for fid in mapping.get("frontiers", [])):
            raise ValueError(f"paper {pid} references an unknown frontier")
        if mapping.get("stage") == "frontier" and not mapping.get("frontiers"):
            raise ValueError(f"frontier-stage paper {pid} must reference a frontier")
    # Cross-stage baseline references are reusable citations, not extra papers.
    # Reject broken source data instead of silently dropping unknown references.
    baseline = next(s for s in stages if s.get("id") == "baseline")
    groups = baseline.get("reference_groups", [])
    if not isinstance(groups, list):
        raise ValueError("baseline reference_groups must be a list")
    group_ids = []
    for group in groups:
        group_id = str(group.get("id", ""))
        if not re.fullmatch(r"[A-Za-z0-9_-]+", group_id):
            raise ValueError("baseline reference group needs a safe id")
        group_ids.append(group_id)
        ids = group.get("paper_ids", [])
        if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)):
            raise ValueError(f"baseline reference group {group_id} needs unique paper_ids")
        if any(str(pid) not in catalog for pid in ids):
            raise ValueError(f"baseline reference group {group_id} contains unknown papers")
    if len(group_ids) != len(set(group_ids)):
        raise ValueError("baseline reference group ids must be unique")
    candidates = route.get("candidates", [])
    if not isinstance(candidates, list):
        raise ValueError("candidates must be a list")
    candidate_ids, candidate_dois = set(), set()
    catalog_dois = {str(p.get("doi", "")).strip().casefold() for p in papers}
    for candidate in candidates:
        cid = str(candidate.get("id", ""))
        doi = str(candidate.get("doi", "")).strip().casefold()
        if not re.fullmatch(r"[A-Za-z0-9_-]+", cid) or cid in candidate_ids or cid in catalog:
            raise ValueError("candidate ids must be unique and outside the catalog")
        if not doi.startswith("10.") or "/" not in doi or doi in candidate_dois or doi in catalog_dois:
            raise ValueError("candidate DOIs must be unique and outside the catalog")
        if not candidate.get("title") or not candidate.get("pending_note"):
            raise ValueError("candidate needs a title and an explicit not-in-library notice")
        source = candidate.get("source_url")
        if source and safe_url(source) == "#":
            raise ValueError("candidate source URL is not safe")
        candidate_ids.add(cid)
        candidate_dois.add(doi)
    return catalog


def link(url: object, label: str, *, external: bool = False) -> str:
    target = safe_url(url)
    attrs = ' target="_blank" rel="noreferrer noopener"' if external else ""
    return f'<a href="{esc(target)}"{attrs}>{esc(label)}</a>'


def glossary(items: object) -> str:
    if not isinstance(items, list) or not items:
        return ""
    rows = "".join(f"<dt>{esc(item.get('term'))}</dt><dd>{esc(item.get('definition'))}</dd>" for item in items)
    return f'<dl class="glossary">{rows}</dl>'


def readings(items: object) -> str:
    if not isinstance(items, list) or not items:
        return ""
    cards = []
    for item in items:
        title = esc(item.get("title"))
        authors = esc(item.get("authors"))
        focus = esc(item.get("focus"))
        url = safe_url(item.get("url"))
        cards.append(f'<li><a href="{esc(url)}" target="_blank" rel="noreferrer noopener">{title}</a><span>{authors} · {focus}</span></li>')
    return '<section class="subsection"><h4>阅读与书籍</h4><ul class="reading">' + "".join(cards) + "</ul></section>"


def experiments(items: object) -> str:
    if not isinstance(items, list) or not items:
        return ""
    cards = "".join(f'<li><strong>{esc(item.get("name"))}</strong><span class="tag">{esc(item.get("role"))}</span><p>{esc(item.get("note"))}</p></li>' for item in items)
    return '<section class="subsection"><h4>实验验证分类</h4><ul class="experiment-list">' + cards + "</ul></section>"


def paper_sections(items: object) -> str:
    if not isinstance(items, list) or not items:
        return ""
    cards = "".join(f'<li><strong>{esc(item.get("name"))}</strong><p>{esc(item.get("content"))}</p></li>' for item in items)
    return '<section class="subsection"><h4>典型论文段落 / 图表</h4><ul class="section-list">' + cards + "</ul></section>"


def paper_card(pid: str, paper: dict, mapping: dict, anchor_prefix: str = "paper", card_class: str = "paper-card") -> str:
    doi = f"https://doi.org/{quote(str(paper['doi']).strip(), safe='/') }" if paper.get("doi") else paper.get("url")
    title = paper.get("title") or pid
    authors = paper.get("authors", [])
    authors_text = ", ".join(authors) if isinstance(authors, list) else authors
    route_href = f"./index.html?paper={quote(pid, safe='')}"
    route_labels = " ".join([str(mapping.get("stage_label", mapping.get("stage", ""))), *[str(label) for label in mapping.get("frontier_labels", mapping.get("frontiers", []))]])
    searchable = " ".join([str(title), str(authors_text), str(paper.get("journal", "")), str(paper.get("doi", "")), str(mapping.get('rationale', '')), str(mapping.get('evidence_basis', '')), route_labels, " ".join(str(x) for x in paper.get("methods", []))])
    return f'''<article class="{esc(card_class)}" id="{esc(anchor_prefix)}-{esc(pid)}" data-paper-id="{esc(pid)}" data-search="{esc(searchable)}">
      <h4>{esc(title)}</h4><p class="paper-meta">{esc(authors_text)}{(' · ' + esc(paper.get('year'))) if paper.get('year') else ''}</p>
      <p>{esc(mapping.get('rationale'))}</p><p class="evidence"><strong>证据基础：</strong>{esc(mapping.get('evidence_basis'))}</p>
      <div class="paper-links">{link(doi, 'DOI / 出版社', external=True)} {link(route_href, '在证据库打开')}</div>
    </article>'''


def reference_groups(stage: dict, catalog: dict[str, dict], mappings: dict) -> str:
    groups = stage.get("reference_groups", [])
    if stage.get("id") != "baseline" or not isinstance(groups, list) or not groups:
        return ""
    rendered = []
    for group in groups:
        ids = [str(pid) for pid in group.get("paper_ids", []) if str(pid) in catalog]
        papers = "".join(paper_card(pid, catalog[pid], mappings[pid], f"ref-baseline-{group.get('id')}", "reference-paper-card") for pid in ids)
        rendered.append(f'''<details class="reference-group" id="reference-group-{esc(group.get('id'))}"><summary><strong>{esc(group.get('label'))}</strong><span>{len(ids)} 篇常备参考</span></summary><p>{esc(group.get('summary'))}</p><div class="paper-grid">{papers}</div></details>''')
    return '<section class="subsection reference-groups"><h3>常备参考组 <span>允许引用其他主阶段论文</span></h3>' + "".join(rendered) + "</section>"


def candidates_appendix(candidates: object) -> str:
    if not isinstance(candidates, list) or not candidates:
        return ""
    cards = []
    for item in candidates:
        doi = f"https://doi.org/{quote(str(item.get('doi')).strip(), safe='/')}" if item.get("doi") else item.get("source_url")
        cards.append(f'''<article class="candidate-card" data-search="{esc(' '.join(str(item.get(key, '')) for key in ('id', 'title', 'doi', 'purpose', 'priority', 'pending_note')))}"><h3>{esc(item.get('title') or item.get('id'))}</h3><p class="paper-meta">{esc(item.get('year'))} · 优先级 {esc(item.get('priority'))}</p><p>{esc(item.get('purpose'))}</p><p class="candidate-note">{esc(item.get('pending_note'))}</p><div class="paper-links">{link(doi, 'DOI / 来源', external=True)}</div></article>''')
    return '<section class="candidates subsection" aria-labelledby="candidate-title"><h2 id="candidate-title">补充论文下载清单 · 尚未入库</h2><p>以下书目已按官方来源核验，但尚未完成本地全文核验与入库，不计入现有精选论文库。可按 DOI 自行下载，再核验论文版本、题名与完整性。</p><div class="paper-grid">' + "".join(cards) + '</div></section>'


def stage_body(stage: dict, catalog: dict[str, dict], mappings: dict, nested_frontiers: str = "") -> str:
    ids = [str(pid) for pid in stage.get("paper_ids", [])]
    papers = "".join(paper_card(pid, catalog[pid], mappings[pid]) for pid in ids)
    return f'''<div class="stage-body"><div class="route-grid"><section><h3>先备知识</h3><ul>{text_list(stage.get('prerequisites'))}</ul>{glossary(stage.get('glossary'))}</section>
      <section><h3>练习与交付</h3><h4>模拟步骤</h4><ol>{text_list(stage.get('simulation'))}</ol><h4>通关清单</h4><ul class="checklist">{text_list(stage.get('deliverables'))}</ul></section></div>
      {readings(stage.get('reading'))}{experiments(stage.get('experiments'))}{paper_sections(stage.get('paper_sections'))}{reference_groups(stage, catalog, mappings)}{nested_frontiers}
      <section class="subsection citations"><h3>路线论文 <span>{len(ids)} 篇，来自精选论文库</span></h3><div class="paper-grid">{papers}</div></section></div>'''


def frontier_body(frontier: dict, catalog: dict[str, dict], mappings: dict) -> str:
    ids = [str(pid) for pid in frontier.get("paper_ids", [])]
    papers = "".join(paper_card(pid, catalog[pid], mappings[pid], f"frontier-{frontier.get('id')}" ) for pid in ids)
    return f'''<div class="frontier-body"><p class="question"><strong>开放问题：</strong>{esc(frontier.get('question'))}</p>
      <div class="route-grid"><section><h3>进入条件</h3><ul>{text_list(frontier.get('prerequisites'))}</ul>{glossary(frontier.get('glossary'))}</section><section><h3>练习与交付</h3><h4>模拟步骤</h4><ol>{text_list(frontier.get('simulation'))}</ol><h4>限制 / 不外推</h4><ul class="limits">{text_list(frontier.get('limits'))}</ul><h4>通关清单</h4><ul class="checklist">{text_list(frontier.get('deliverables'))}</ul></section></div>
      {readings(frontier.get('reading'))}{experiments(frontier.get('experiments'))}{paper_sections(frontier.get('paper_sections'))}<section class="subsection citations"><h3>前沿路线论文 <span>{len(ids)} 篇，可与多个阶段交叉</span></h3><div class="paper-grid">{papers}</div></section></div>'''


def build(route: dict, catalog: dict[str, dict], *, stylesheet_text: str | None = None) -> str:
    # Keep the published page self-contained so a delayed stylesheet request
    # cannot leave the research reference map unreadable or unstyled.
    if stylesheet_text is None:
        stylesheet_tag = '<link rel="stylesheet" href="./learning-route.css">'
    else:
        inline_css = re.sub(r"</style", lambda _: r"<\/style", stylesheet_text, flags=re.I)
        stylesheet_tag = f"<style>{inline_css}</style>"
    stage_order = {s["id"]: s for s in route["stages"]}
    frontier_order = {f["id"]: f for f in route.get("frontiers", [])}
    mappings = {pid: {**mapping, "stage_label": "baseline" if mapping.get("stage") == "baseline" else stage_order.get(mapping.get("stage"), {}).get("label", mapping.get("stage", "")), "frontier_labels": [frontier_order[fid].get("label", fid) for fid in mapping.get("frontiers", []) if fid in frontier_order]} for pid, mapping in route["papers"].items()}
    frontier_refs = sum(len(mapping.get("frontiers", [])) for mapping in mappings.values())
    baseline_refs = sum(len(group.get("paper_ids", [])) for group in stage_order["baseline"].get("reference_groups", []))
    frontiers = "".join(f'''<details class="frontier-card" id="frontier-{esc(item['id'])}" data-frontier="{esc(item['id'])}"><summary><span class="stage-kicker">FRONTIER</span><h3>{esc(item.get('label'))}</h3><p>{esc(item.get('summary'))}</p></summary>{frontier_body(item, catalog, mappings)}</details>''' for item in route.get("frontiers", []))
    stages = "".join(f'''<details class="stage-card" id="stage-{esc(stage['id'])}" data-stage="{esc(stage['id'])}"{' open' if stage['id'] == 'baseline' else ''}><summary><span class="stage-kicker">{esc(stage['id'])}</span><h2>{esc('baseline' if stage['id'] == 'baseline' else stage.get('label'))}</h2><p>{esc(stage.get('summary'))}</p></summary>{stage_body(stage, catalog, mappings, frontiers if stage['id'] == 'frontier' else '')}</details>''' for stage in [stage_order[k] for k in ("baseline", "beginner", "intermediate", "frontier")])
    candidates = candidates_appendix(route.get("candidates"))
    source_links = " ".join(link(s.get("url"), s.get("title", "来源"), external=True) for s in route.get("sources", []))
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Battery Evidence Lab 的可展开学习路线与论文证据地图"><title>学习路线 · Battery Evidence Lab</title>{stylesheet_tag}</head><body><div class="shell">
      <nav class="site-nav" aria-label="页面导航"><a class="brand" href="./index.html#top">Battery Evidence Lab</a><div class="site-nav-links"><a href="./index.html#research-question">证据问答</a><a href="./foundations.html">基础地图</a><a href="./future-directions.html">未来方向</a><a href="./ai-battery-applications.html">AI 应用</a><a href="./learning-route.html" aria-current="page">学习路线</a></div></nav>
      <header><div class="eyebrow">LEARNING ROUTE · EVIDENCE FIRST</div><h1>从科研常备到前沿：电池材料研究与查阅路线</h1><p class="lede">baseline 用于科研中反复查验；入门、进阶与前沿用于选择练习和研究问题。每个部分都包含术语、参考、验证、论文结构和可检查的交付。论文可跨专题引用，但不重复计入精选目录。</p><div class="meta"><span>{esc(route.get('as_of', ''))} 更新</span><span>{len(catalog)} 篇精选论文</span><span>{frontier_refs} 个前沿交叉引用</span><span>{baseline_refs} 个常备交叉引用</span><span>默认展开 baseline · 键盘可操作</span></div><div class="notice">{esc(route.get('policy'))}</div></header>
      <main><div class="controls"><label for="route-search">搜索路线与论文</label><input id="route-search" type="search" placeholder="搜索：NEB / diffusion / 电解液…" autocomplete="off"><label for="stage-filter">阶段筛选</label><select id="stage-filter"><option value="all">全部阶段</option><option value="baseline">baseline</option><option value="beginner">入门</option><option value="intermediate">进阶</option><option value="frontier">前沿</option></select><button id="expand-visible" type="button">展开可见</button><button id="collapse-visible" type="button">折叠可见</button><span class="count" id="route-count" role="status" aria-live="polite"></span></div><p class="empty" id="route-empty" hidden>没有匹配内容。试试更短的关键词，或清除阶段筛选。</p><section class="stages" aria-label="学习阶段">{stages}</section>{candidates}</main><footer><p>数据政策：{esc(route.get('policy'))}</p><p>公开来源：{source_links}</p></footer></div><script src="./learning-route.js" defer></script></body></html>'''


def main() -> None:
    route = json.loads(ROUTE_PATH.read_text(encoding="utf-8"))
    papers = json.loads(PAPERS_PATH.read_text(encoding="utf-8"))
    catalog = validate(route, papers)
    css = (ROOT / "static" / "learning-route.css").read_text(encoding="utf-8")
    OUT_PATH.write_text(build(route, catalog, stylesheet_text=css), encoding="utf-8")
    print(f"Built {OUT_PATH} with {len(catalog)} catalog papers")


if __name__ == "__main__":
    main()
