from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfWriter

import library_store


class KeywordApiTests(unittest.TestCase):
    def test_domain_keywords_rank_ahead_of_generic_words(self) -> None:
        rows = library_store.KEYWORDS.extract(
            "VASP density functional theory and AIMD molecular dynamics for lithium diffusion in a solid electrolyte",
            limit=8,
        )
        terms = [row["term"] for row in rows]
        self.assertIn("VASP", terms)
        self.assertIn("density functional theory", terms)
        self.assertIn("molecular dynamics", terms)
        self.assertIn("lithium diffusion", terms)

    def test_keyword_api_contract_is_versioned(self) -> None:
        self.assertEqual(library_store.KEYWORDS.api_version, "v1")
        self.assertTrue(library_store.KEYWORDS.provider)


class UploadIngestionTests(unittest.TestCase):
    @staticmethod
    def _pdf_bytes() -> bytes:
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.add_metadata({"/Title": "A Test Battery Materials Paper"})
        stream = io.BytesIO()
        writer.write(stream)
        return stream.getvalue()

    def test_new_upload_is_private_and_indexed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            seed = root / "data" / "papers.json"
            user = root / "private" / "user-papers.local.json"
            manifest = root / "literature" / "manifest.json"
            pdf_dir = root / "literature" / "pdfs"
            seed.parent.mkdir(parents=True)
            seed.write_text("[]", encoding="utf-8")

            def fake_load(seed_path=seed, user_path=user):
                seeds = json.loads(seed_path.read_text(encoding="utf-8")) if seed_path.exists() else []
                users = json.loads(user_path.read_text(encoding="utf-8")) if user_path and user_path.exists() else []
                return seeds + users

            with (
                patch.object(library_store, "ROOT", root),
                patch.object(library_store, "SEED_PAPERS", seed),
                patch.object(library_store, "USER_PAPERS", user),
                patch.object(library_store, "MANIFEST", manifest),
                patch.object(library_store, "PDF_DIR", pdf_dir),
                patch.object(library_store, "load_library_papers", side_effect=fake_load),
                patch.object(library_store, "rebuild_fulltext_index") as rebuild,
            ):
                result = library_store.ingest_pdf(
                    self._pdf_bytes(),
                    "paper.pdf",
                    {
                        "title": "A Test Battery Materials Paper",
                        "doi": "10.1234/test-battery",
                        "year": "2025",
                        "journal": "Test Journal",
                        "authors": "Alice Example; Bob Example",
                    },
                )

            self.assertTrue(result["ok"])
            self.assertTrue(result["created"])
            self.assertTrue(user.is_file())
            self.assertEqual(len(json.loads(user.read_text(encoding="utf-8"))), 1)
            self.assertEqual(len(list(pdf_dir.glob("*.pdf"))), 1)
            rebuild.assert_called_once()


if __name__ == "__main__":
    unittest.main()
