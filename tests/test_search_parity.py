"""Cross-runtime retrieval regressions for the Python and browser agents."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent import BatteryResearchAgent


ROOT = Path(__file__).resolve().parents[1]
NODE = os.environ.get("BATTERY_NODE") or shutil.which("node")
RUNNER = ROOT / "tests" / "search_parity_runner.mjs"


class SearchParityTests(unittest.TestCase):
    QUERIES = [
        "文献", "开路电压", "聚合物电解质", "纳秒到秒",
        "AI for Science", "ai for science", "AI FOR SCIENCE",
        "10.1038/S41524-020-00406-3",
        "DOI: https://doi.org/10.1038/S41524-020-00406-3.",
        "10.1038/s41524-020-00406-30", "文献 10.1038/S41524-020-00406-3",
        "10.1038/S41524-020-00406-3 10.1038/s43588-022-00349-3",
    ]

    @classmethod
    def setUpClass(cls) -> None:
        if not NODE:
            raise unittest.SkipTest("Node.js is required; install node or set BATTERY_NODE")
        cls.py_agent = BatteryResearchAgent(fulltext_path=None, extra_data_path=None)

    def browser_results(self, queries: list[str], data_path: Path | None = None, answer: str | None = None) -> dict:
        command = [str(NODE), str(RUNNER), str(data_path or (ROOT / "data" / "papers.json")), json.dumps(queries, ensure_ascii=False)]
        if answer is not None:
            command.append(answer)
        env = dict(os.environ)
        completed = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8", env=env)
        return json.loads(completed.stdout)

    def test_top_ids_and_doi_modes_match_across_runtimes(self) -> None:
        browser = self.browser_results(self.QUERIES)
        for query in self.QUERIES:
            py = self.py_agent.search_detailed(query, limit=8)
            self.assertEqual([x["id"] for x in py["results"]], browser[query]["ids"], query)
            self.assertEqual(py["query"]["dois"], browser[query]["dois"], query)
            self.assertEqual(py["query"]["mode"], browser[query]["mode"], query)
            self.assertEqual(py["query"]["expanded_terms"], browser[query]["expanded_terms"], query)

    def test_metadata_only_pdf_fixture_has_honest_claim_and_generic_doi_label(self) -> None:
        fixture = [{
            "id": "fixture_metadata_pdf", "title": "Fixture metadata paper",
            "doi": "10.9999/fixture.2026", "year": 2026,
            "role": "fixture metadata record", "summary": "structured metadata only",
            "methods": ["DFT"], "systems": ["fixture"], "properties": [],
            "scope_note": "结构化元数据；本地已有PDF入口，具体内容仍待核验。",
            "local_pdf": "literature/papers/fixture.pdf",
            "evidence": [], "collection": "core",
        }]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "papers.json"
            path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
            py_agent = BatteryResearchAgent(data_path=path, fulltext_path=None, extra_data_path=None)
            question = "fixture metadata paper"
            py_answer = py_agent.answer(question)["answer_markdown"]
            browser_answer = self.browser_results([], path, question)["answer"]
            for answer in (py_answer, browser_answer):
                self.assertNotIn("本地未保存全文", answer)
                self.assertIn("DOI/出版社记录", answer)
                self.assertIn("10.9999/fixture.2026", answer)
                self.assertIn("元数据入口", answer)


if __name__ == "__main__":
    unittest.main()
