from __future__ import annotations

import json
import unittest
from pathlib import Path

from extract_method_evidence import REVIEW_STATUS


ROOT = Path(__file__).resolve().parents[1]


class MethodEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(
            (ROOT / "data" / "method_evidence.auto.json").read_text(encoding="utf-8")
        )

    def test_scope_and_review_boundary(self) -> None:
        self.assertEqual(self.payload["review_status"], REVIEW_STATUS)
        self.assertEqual(self.payload["fulltext_paper_count"], 16)
        self.assertEqual(len(self.payload["fulltext_paper_ids"]), 16)
        self.assertEqual(len(self.payload["papers"]), 16)
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
