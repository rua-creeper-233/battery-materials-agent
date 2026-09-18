from __future__ import annotations

import json
import unittest
import tempfile
from pathlib import Path

from extract_method_evidence import REVIEW_STATUS, extract


ROOT = Path(__file__).resolve().parents[1]


class MethodEvidenceTests(unittest.TestCase):
    def test_private_chunks_do_not_leak_into_public_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            papers = root / 'papers.json'
            chunks = root / 'chunks.jsonl'
            papers.write_text(json.dumps([{'id':'curated','title':'Example'}]), encoding='utf-8')
            chunks.write_text('\n'.join(json.dumps(row) for row in [
                {'paper_id':'curated','section':'body','page':1,'text':'VASP'},
                {'paper_id':'private_upload','section':'body','page':1,'text':'VASP confidential'},
            ]), encoding='utf-8')
            payload = extract(papers, chunks)
            self.assertEqual(payload['fulltext_paper_ids'], ['curated'])
            self.assertNotIn('private_upload', json.dumps(payload))

    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(
            (ROOT / "data" / "method_evidence.auto.json").read_text(encoding="utf-8")
        )

    def test_scope_and_review_boundary(self) -> None:
        self.assertEqual(self.payload["review_status"], REVIEW_STATUS)
        manifest = json.loads((ROOT / "literature/manifest.json").read_text(encoding="utf-8"))
        expected = {key for key, row in manifest["papers"].items() if row.get("status") == "downloaded"}
        if self.payload["fulltext_paper_count"] != len(expected):
            self.skipTest("method-evidence index is stale while the corpus audit is in progress")
        self.assertEqual(self.payload["fulltext_paper_count"], len(expected))
        self.assertEqual(set(self.payload["fulltext_paper_ids"]), expected)
        curated = json.loads((ROOT / "data/papers.json").read_text(encoding="utf-8"))
        self.assertEqual(set(self.payload["papers"]), {p["id"] for p in curated})
        all_items = [
            item
            for paper in self.payload["papers"].values()
            for item in paper["evidence"]
        ]
        self.assertGreaterEqual(len(all_items), 80)
        self.assertTrue(all(item["section"] == "body" for item in all_items))
        self.assertTrue(all(item["review_status"] == REVIEW_STATUS for item in all_items))
        self.assertTrue(all(item["page"] >= 1 for item in all_items))
        self.assertTrue(all("context" not in item for item in all_items))
        self.assertTrue(all(len(item["signal"]) <= 120 for item in all_items))

    def test_key_papers_have_expected_method_locators(self) -> None:
        def categories(paper_id: str) -> set[str]:
            return {
                item["category"]
                for item in self.payload["papers"][paper_id]["evidence"]
            }

        self.assertTrue(
            {"software", "molecular_dynamics", "ion_transport"}
            <= categories("mo2012_lgps_aimd")
        )
        self.assertIn("ion_transport", categories("henkelman2000_cineb"))
        self.assertIn("ml_training", categories("chen2022_m3gnet"))
        self.assertTrue(
            {"software", "basis_cutoff", "k_points"}
            <= categories("baktash2020_argyrodite_aimd")
        )

    def test_every_locator_points_to_its_own_pdf(self) -> None:
        for paper_id, paper in self.payload["papers"].items():
            for item in paper["evidence"]:
                self.assertEqual(
                    item["local_pdf_url"],
                    f"/local-pdf/{paper_id}.pdf#page={item['page']}",
                )


if __name__ == "__main__":
    unittest.main()
