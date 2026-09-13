from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent import BatteryResearchAgent  # noqa: E402
from import_wos import merge_records, parse_wos_text  # noqa: E402


class AgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.agent = BatteryResearchAgent()

    def test_library_has_battery_not_osc_seed(self) -> None:
        self.assertGreaterEqual(len(self.agent.papers), 12)
        text = json.dumps(self.agent.papers, ensure_ascii=False).lower()
        self.assertIn("lgps", text)
        self.assertIn("chgnet", text)
        self.assertNotIn("organic solar", text)

    def test_diffusion_query_ranks_relevant_paper(self) -> None:
        result = self.agent.search("如何计算锂离子扩散势垒和扩散系数", limit=5)
        joined = " ".join(item["id"] for item in result)
        self.assertTrue(any(key in joined for key in ("diffusion", "cineb", "aimd", "lgps")))

    def test_mlp_workflow_contains_domain_and_validation(self) -> None:
        result = self.agent.answer("给我一个LGPS机器学习势的落地流程")
        self.assertEqual(result["task"], "mlp")
        answer = result["answer_markdown"]
        self.assertIn("适用域", answer)
        self.assertIn("DFT", answer)
        self.assertIn("DOI", answer)

    def test_answer_has_provenance_and_graph(self) -> None:
        result = self.agent.answer("怎么判断固态电解质界面稳定？")
        self.assertGreater(len(result["papers"]), 0)
        self.assertGreater(len(result["graph"]["edges"]), 0)
        self.assertIn("wos_note", result["provenance"])


class WosImportTests(unittest.TestCase):
    def test_parse_and_merge(self) -> None:
        raw = """FN Clarivate Web of Science\nVR 1.0\nPT J\nAU Doe, J\nAF Doe, Jane\nTI A Battery Materials Calculation Paper\nSO TEST JOURNAL\nPY 2025\nDI 10.1234/test.1\nUT WOS:000000001\nDE battery; DFT; diffusion\nAB First line\n   continued abstract\nER\nEF\n"""
        parsed = parse_wos_text(raw)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["doi"], "10.1234/test.1")
        self.assertEqual(parsed[0]["verification"]["wos_ut"], "WOS:000000001")
        self.assertIn("continued abstract", parsed[0]["summary"])
        self.assertEqual(len(merge_records(parsed, parsed)), 1)


if __name__ == "__main__":
    unittest.main()
