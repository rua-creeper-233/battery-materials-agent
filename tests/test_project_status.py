import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import update_project_status as status


class ProjectStatusTests(unittest.TestCase):
    def test_curated_counts_and_public_privacy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for folder in ("data", "literature", "finetune/data"):
                (root / folder).mkdir(parents=True)
            papers = [{"id": "p1", "doi": "10.x/one", "year": 2026, "document_type": "Perspective"},
                      {"id": "p2", "doi": "10.x/two", "year": 2018}]
            (root / "data/papers.json").write_text(json.dumps(papers), encoding="utf-8")
            (root / "literature/one.pdf").write_bytes(b"%PDF-test-fixture")
            manifest = {"papers": {
                "p1": {"status": "downloaded", "local_pdf": "literature/one.pdf",
                       "validation": {"valid_pdf": True}, "private_key": "never_publish"},
                "p2": {"status": "downloaded", "local_pdf": "../outside.pdf", "validation": {"valid_pdf": True}},
                "not_curated": {"status": "downloaded", "local_pdf": "literature/one.pdf", "validation": {"valid_pdf": True}}}}
            (root / "literature/manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (root / "data/fulltext_chunks.jsonl").write_text('\n'.join(json.dumps(x) for x in
                [{"paper_id": "p1"}, {"paper_id": "p1"}, {"paper_id": "not_curated"}]), encoding="utf-8")
            for name in ("train", "validation", "test"):
                (root / f"finetune/data/{name}.jsonl").write_text('{"category":"fact"}\n', encoding="utf-8")
            with patch.object(status, "ROOT", root):
                value = status.build_status("2026-10-08")
            self.assertEqual(value["papers"], 2)
            self.assertEqual(value["local_fulltext_papers"], 1)
            self.assertEqual(value["indexed_chunks"], 2)
            self.assertEqual(value["dataset_rows"], 3)
            self.assertNotIn("never_publish", json.dumps(value))
            self.assertNotIn(str(root), json.dumps(value))

    def test_duplicate_doi_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "data").mkdir()
            (root / "data/papers.json").write_text(json.dumps([
                {"id": "one", "doi": "10.x/same"}, {"id": "two", "doi": "10.X/SAME"}]), encoding="utf-8")
            with patch.object(status, "ROOT", root), self.assertRaises(ValueError):
                status.build_status("2026-10-08")


if __name__ == "__main__":
    unittest.main()
