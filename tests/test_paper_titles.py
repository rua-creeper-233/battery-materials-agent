"""Regression coverage for the public bilingual paper-title allowlist."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from paper_titles import load_titles, validate_titles
from publication_safety import PublicationSafetyError


ROOT = Path(__file__).parents[1]
PAPERS = json.loads((ROOT / "data" / "papers.json").read_text(encoding="utf-8"))
PAYLOAD = json.loads((ROOT / "data" / "paper_titles_zh.json").read_text(encoding="utf-8"))


class PaperTitleTests(unittest.TestCase):
    def test_title_map_covers_exactly_the_176_canonical_papers(self):
        self.assertEqual(len(PAPERS), 176)
        checked = validate_titles(PAYLOAD, PAPERS)
        self.assertEqual(set(checked["papers"]), {str(p["id"]) for p in PAPERS})
        self.assertTrue(all(row["title_zh"].strip() for row in checked["papers"].values()))

    def test_missing_and_extra_ids_are_rejected(self):
        missing = copy.deepcopy(PAYLOAD)
        missing["papers"].pop(next(iter(missing["papers"])))
        with self.assertRaises(PublicationSafetyError):
            validate_titles(missing, PAPERS)

        extra = copy.deepcopy(PAYLOAD)
        extra["papers"]["fixture-extra"] = {"title": "x", "title_zh": "测试", "doi": "10.1/x"}
        with self.assertRaises(PublicationSafetyError):
            validate_titles(extra, PAPERS)

    def test_stale_english_title_or_doi_and_private_fields_are_rejected(self):
        stale = copy.deepcopy(PAYLOAD)
        first = next(iter(stale["papers"]))
        stale["papers"][first]["title"] += " (stale)"
        with self.assertRaises(PublicationSafetyError):
            validate_titles(stale, PAPERS)

        stale = copy.deepcopy(PAYLOAD)
        stale["papers"][first]["doi"] = "10.9999/stale"
        with self.assertRaises(PublicationSafetyError):
            validate_titles(stale, PAPERS)

        private = copy.deepcopy(PAYLOAD)
        private["papers"][first]["local_pdf_url"] = "/private/paper.pdf"
        with self.assertRaises(PublicationSafetyError):
            validate_titles(private, PAPERS)

    def test_load_titles_uses_the_same_exact_schema(self):
        self.assertEqual(load_titles(PAPERS)["papers"].keys(), PAYLOAD["papers"].keys())


if __name__ == "__main__":
    unittest.main()
