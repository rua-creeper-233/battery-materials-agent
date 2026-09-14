from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from paper_tagging import classify_paper  # noqa: E402


class TaggingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.papers = json.loads((ROOT / "data" / "papers.json").read_text(encoding="utf-8"))
        cls.by_id = {paper["id"]: paper for paper in cls.papers}

    def test_all_papers_have_kind_tag(self) -> None:
        for paper in self.papers:
            row = classify_paper(paper)
            self.assertIn(row["paper_kind"], {"方法论文", "进展论文"})
            self.assertIn(row["paper_kind"], row["display_tags"])

    def test_aimd_paper_is_dft_and_md(self) -> None:
        row = classify_paper(self.by_id["leung2010_sei_aimd"])
        self.assertIn("DFT", row["method_tags"])
        self.assertIn("MD", row["method_tags"])

    def test_background_materials_studio_mention_is_not_method_use(self) -> None:
        rows = [classify_paper(paper) for paper in self.papers]
        ms_ids = {
            paper["id"]
            for paper, row in zip(self.papers, rows)
            if "MS" in row["method_tags"]
        }
        self.assertEqual(
            ms_ids,
            {
                "wu2023_edl_ms",
                "sheng2024_lipf6_hydrolysis_ms",
                "li2024_polymeric_asei_ms",
                "wu2025_spe_aimd_ms",
                "zhang2025_sei_phasefield_ms",
                "chen2025_heteroalkali_ms",
            },
        )
        self.assertIn("VASP", classify_paper(self.by_id["geng2025_vaspkit_protocol"])["method_tags"])


if __name__ == "__main__":
    unittest.main()
