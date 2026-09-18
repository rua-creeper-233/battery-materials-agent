from __future__ import annotations

import unittest

from pull_zotero_fulltexts import is_matching_main_article


class ZoteroFulltextIdentityTests(unittest.TestCase):
    def test_accepts_matching_readable_main_article(self) -> None:
        self.assertTrue(is_matching_main_article({
            "valid_pdf": True,
            "document_kind": "article",
            "first_pages_text_chars": 5000,
            "title_token_match": 0.75,
        }))

    def test_rejects_unrelated_readable_attachment(self) -> None:
        self.assertFalse(is_matching_main_article({
            "valid_pdf": True,
            "document_kind": "article",
            "first_pages_text_chars": 5000,
            "title_token_match": 0.0,
        }))

    def test_rejects_supplement_or_nearly_empty_text(self) -> None:
        self.assertFalse(is_matching_main_article({
            "valid_pdf": True,
            "document_kind": "supplementary",
            "first_pages_text_chars": 5000,
            "title_token_match": 1.0,
        }))
        self.assertFalse(is_matching_main_article({
            "valid_pdf": True,
            "document_kind": "article",
            "first_pages_text_chars": 100,
            "title_token_match": 1.0,
        }))


if __name__ == "__main__":
    unittest.main()
