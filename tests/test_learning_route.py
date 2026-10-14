"""Focused invariants for the evidence-first learning route artifact."""

from __future__ import annotations

import copy
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

import build_learning_route as route_builder


ROOT = Path(__file__).parents[1]
ROUTE = json.loads((ROOT / "data" / "learning_route.json").read_text(encoding="utf-8"))
CATALOG = {
    str(p["id"]): p
    for p in json.loads((ROOT / "data" / "papers.json").read_text(encoding="utf-8"))
}


class _IdsAndLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.hrefs = []
        self.paper_ids = []
        self.reference_ids = []
        self.candidate_cards = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.hrefs.append(attrs["href"])
        classes = attrs.get("class", "").split()
        if "paper-card" in classes:
            self.paper_ids.append(attrs.get("data-paper-id"))
        if "reference-paper-card" in classes:
            self.reference_ids.append(attrs.get("data-paper-id"))
        if "candidate-card" in classes:
            self.candidate_cards += 1


class LearningRouteTests(unittest.TestCase):
  def test_baseline_reference_groups_and_public_route_has_no_pending_candidates(self):
    baseline = next(s for s in ROUTE["stages"] if s["id"] == "baseline")
    self.assertTrue(baseline["label"].lower().startswith("baseline"))
    groups = baseline.get("reference_groups", [])
    self.assertEqual(len(groups), 5)
    self.assertTrue(all(g.get("id") and g.get("label") and g.get("paper_ids") for g in groups))
    self.assertEqual(len({g["id"] for g in groups}), 5)
    self.assertEqual(sum(len(g["paper_ids"]) for g in groups), 51)
    self.assertEqual(len({str(pid) for g in groups for pid in g["paper_ids"]}), 48)
    for group in groups:
      self.assertTrue(set(str(pid) for pid in group["paper_ids"]) <= set(CATALOG))
    self.assertEqual(ROUTE.get("candidates", []), [])

  def test_catalog_stage_and_primary_frontier_counts_are_exact(self):
    assert len(CATALOG) == 176
    assert [len(next(s for s in ROUTE["stages"] if s["id"] == sid)["paper_ids"]) for sid in
            ("baseline", "beginner", "intermediate", "frontier")] == [15, 34, 55, 72]
    assert len(ROUTE["frontiers"]) == 8
    assert all(len(f["paper_ids"]) > 0 for f in ROUTE["frontiers"])


  def test_stage_ids_and_mappings_are_unique_and_consistent(self):
    stage_ids = [s["id"] for s in ROUTE["stages"]]
    assert len(stage_ids) == len(set(stage_ids)) == 4
    listed = [str(pid) for s in ROUTE["stages"] for pid in s["paper_ids"]]
    assert len(listed) == len(set(listed)) == len(CATALOG)
    assert set(listed) == set(ROUTE["papers"]) == set(CATALOG)
    frontier_ids = [f["id"] for f in ROUTE["frontiers"]]
    assert len(frontier_ids) == len(set(frontier_ids)) == 8
    for pid, mapping in ROUTE["papers"].items():
        assert pid in {str(x) for s in ROUTE["stages"] if s["id"] == mapping["stage"] for x in s["paper_ids"]}
        assert set(mapping.get("frontiers", [])) <= set(frontier_ids)
        if mapping["stage"] == "frontier":
            assert mapping.get("frontiers")
    for frontier in ROUTE["frontiers"]:
        for pid in frontier["paper_ids"]:
            assert frontier["id"] in ROUTE["papers"][str(pid)].get("frontiers", [])
            assert any(topic in ROUTE["papers"][str(pid)].get("frontiers", []) for topic in frontier_ids)


  def test_every_stage_and_frontier_has_readable_pedagogy_blocks(self):
    required = ("prerequisites", "reading", "experiments", "paper_sections", "simulation", "deliverables")
    for block in [*ROUTE["stages"], *ROUTE["frontiers"]]:
        for key in required:
            values = block.get(key)
            assert isinstance(values, list) and values
            assert all(str(item).strip() for item in values)
        assert all(item.get("title") and item.get("url") for item in block["reading"])
        assert all(item.get("name") and item.get("note") for item in block["experiments"])
        assert all(item.get("name") and item.get("content") for item in block["paper_sections"])
        if block in ROUTE["stages"]:
            assert block.get("glossary")


  def test_built_html_has_unique_primary_bibliography_and_safe_links(self):
    title_records = {next(iter(CATALOG)): {"title_zh": '<img src=x onerror="alert(1)">'}}
    html_text = route_builder.build(ROUTE, CATALOG, title_records=title_records)
    parsed = _IdsAndLinks()
    parsed.feed(html_text)
    assert len(parsed.ids) == len(set(parsed.ids))
    assert len(set(parsed.paper_ids)) == 176
    expected_refs = sum(len(f["paper_ids"]) for f in ROUTE["frontiers"]) + sum(
        len(g["paper_ids"]) for g in next(s for s in ROUTE["stages"] if s["id"] == "baseline").get("reference_groups", [])
    )
    assert len(parsed.paper_ids) == 176 + sum(len(f["paper_ids"]) for f in ROUTE["frontiers"]) == 283
    assert len(parsed.reference_ids) == expected_refs - sum(len(f["paper_ids"]) for f in ROUTE["frontiers"]) == 51
    assert len(set(parsed.paper_ids)) == 176
    assert parsed.candidate_cards == len(ROUTE.get("candidates", [])) == 0
    assert "paper-title-zh" in html_text
    assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;" in html_text
    assert all(pid in CATALOG for pid in parsed.paper_ids)
    assert all(f"?paper={pid}" in html_text for pid in CATALOG)
    assert all(f"https://doi.org/{quote(str(p['doi']).strip(), safe='/')}" in html_text for p in CATALOG.values() if p.get("doi"))
    assert all(
        (href.startswith("https://") and "@" not in href.split("//", 1)[1].split("/", 1)[0])
        or href.startswith(("./", "../", "/", "#"))
        for href in parsed.hrefs
    )
    self.assertNotIn("/private/", html_text.lower())
    self.assertNotIn("zotero://", html_text.lower())
    assert "<script src=\"./learning-route.js\"" in html_text
    assert "<details" in html_text
    assert all(marker in html_text for marker in ("阅读与书籍", "实验验证分类", "典型论文段落 / 图表", "通关清单"))


  def test_escape_and_url_safety_cover_malformed_scheme_relative_and_credentials(self):
    self.assertEqual(route_builder.esc('<script a="x">&'), "&lt;script a=&quot;x&quot;&gt;&amp;")
    for value in ("javascript:alert(1)", "//evil.example/x", "https://user:pass@evil.example/x", "https://evil.example/x\n"):
        self.assertEqual(route_builder.safe_url(value), "#")
    self.assertEqual(route_builder.safe_url("./index.html?paper=x"), "./index.html?paper=x")
    self.assertEqual(route_builder.safe_url("/public/file"), "/public/file")


  def test_validation_rejects_unknown_or_repeated_ids_and_mapping_disagreement(self):
    bad = copy.deepcopy(ROUTE)
    bad["stages"][0]["paper_ids"].append(bad["stages"][0]["paper_ids"][0])
    with self.assertRaises(ValueError):
        route_builder.validate(bad, list(CATALOG.values()))

  def test_validation_rejects_optional_reference_and_candidate_schema_corruption(self):
    baseline = next(s for s in ROUTE["stages"] if s["id"] == "baseline")
    cases = []
    bad = copy.deepcopy(ROUTE)
    bad["stages"][0]["reference_groups"][0]["paper_ids"].append("unknown-paper")
    cases.append(bad)
    bad = copy.deepcopy(ROUTE)
    bad["stages"][0]["reference_groups"].append(copy.deepcopy(bad["stages"][0]["reference_groups"][0]))
    cases.append(bad)
    bad = copy.deepcopy(ROUTE)
    bad["candidates"] = [{"id": "pending", "title": "Pending"}]
    cases.append(bad)
    for corrupted in cases:
      with self.assertRaises(ValueError):
        route_builder.validate(corrupted, list(CATALOG.values()))
    bad = copy.deepcopy(ROUTE)
    bad["frontiers"][0]["paper_ids"].append("does-not-exist")
    with self.assertRaises(ValueError):
        route_builder.validate(bad, list(CATALOG.values()))
    bad = copy.deepcopy(ROUTE)
    pid = bad["stages"][0]["paper_ids"][0]
    bad["papers"][str(pid)]["stage"] = "frontier"
    with self.assertRaises(ValueError):
        route_builder.validate(bad, list(CATALOG.values()))


if __name__ == "__main__":
    unittest.main()
