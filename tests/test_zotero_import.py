from __future__ import annotations

import unittest

from import_zotero_library import COMMON_TAG, build_zotero_item, normalize_doi


class ZoteroImportTests(unittest.TestCase):
    def test_normalize_doi(self) -> None:
        self.assertEqual(
            normalize_doi("https://doi.org/10.1038/S43588-022-00349-3."),
            "10.1038/s43588-022-00349-3",
        )

    def test_build_item_keeps_wos_and_project_tag(self) -> None:
        paper = {
            "title": "A paper",
            "authors": ["M. K. Aydinol", "Ceder, Gerbrand"],
            "summary": "Summary",
            "journal": "Journal",
            "year": 2024,
            "doi": "10.1000/test",
            "url": "https://doi.org/10.1000/test",
            "wos_uid": "WOS:123",
            "tags_zh": ["电池"],
        }
        item = build_zotero_item(paper, "connector-id")
        self.assertEqual(item["itemType"], "journalArticle")
        self.assertEqual(item["creators"][0]["lastName"], "Aydinol")
        self.assertEqual(item["creators"][1]["lastName"], "Ceder")
        self.assertIn("WOS:123", item["extra"])
        self.assertIn(COMMON_TAG, {tag["tag"] for tag in item["tags"]})

    def test_non_wos_paper_is_not_mislabeled(self) -> None:
        paper = {
            "title": "A DOI-verified starter paper",
            "authors": ["Alex Example"],
            "summary": "Summary",
            "journal": "Journal",
            "year": 2025,
            "doi": "10.1000/starter",
            "url": "https://doi.org/10.1000/starter",
            "tags_zh": ["入门"],
        }
        item = build_zotero_item(paper, "connector-id")
        tags = {tag["tag"] for tag in item["tags"]}
        self.assertIn("DOI-publisher-verified", tags)
        self.assertNotIn("WOS-verified", tags)
        self.assertIn("WOS not checked", item["extra"])


if __name__ == "__main__":
    unittest.main()
