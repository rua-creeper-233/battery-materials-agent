from __future__ import annotations

import json
import unittest

from agent import BatteryResearchAgent
from rag import EvidenceRAG


class FakeProvider:
    name = "fake-provider"
    model = "fake-model"

    def __init__(self, answer: str):
        self.answer = answer
        self.system = ""
        self.user = ""

    def complete(self, system: str, user: str) -> str:
        self.system = system
        self.user = user
        return self.answer


class RagTests(unittest.TestCase):
    def test_valid_cited_answer_is_used(self) -> None:
        provider = FakeProvider("建议先核对原文方法，再复现实验。[P1]")
        rag = EvidenceRAG(provider)
        result = rag.generate(
            "如何入门？",
            [{"id": "paper-a", "title": "Paper A", "doi": "10.1/a"}],
            [],
        )
        self.assertTrue(result["used"])
        self.assertEqual(result["source_map"], {"P1": "paper-a"})
        self.assertEqual(result["source_provenance"]["P1"]["evidence_type"], "curated_metadata")

    def test_page_aware_provenance_is_exposed(self) -> None:
        provider = FakeProvider("原文摘录支持该判断。[P1]")
        result = EvidenceRAG(provider).generate(
            "问题", [{"id": "paper-a", "title": "Paper A", "scope_note": "仅研究体相"}],
            [{"paper_id": "paper-a", "page": 7, "excerpt": "原文摘录"}],
        )
        self.assertTrue(result["used"])
        self.assertEqual(result["source_provenance"]["P1"]["evidence_type"], "fulltext_excerpt")
        self.assertEqual(result["source_provenance"]["P1"]["pages"], [7])

    def test_unsupported_parameter_claim_falls_back(self) -> None:
        result = EvidenceRAG(FakeProvider("使用 900 K 运行。[P1]")).generate(
            "问题", [{"id": "paper-a", "title": "Paper A"}], [],
        )
        self.assertFalse(result["used"])
        self.assertEqual(result["reason"], "unsupported_numeric_claim")
        self.assertEqual(result["unsupported_claims"], ["900 K"])

    def test_question_parameter_does_not_count_as_evidence(self) -> None:
        result = EvidenceRAG(FakeProvider("使用 900 K 运行。[P1]")).generate(
            "问题：900 K 是否合适？", [{"id": "paper-a", "title": "Paper A"}], [],
        )
        self.assertFalse(result["used"])
        self.assertEqual(result["reason"], "unsupported_numeric_claim")

    def test_parameter_substrings_do_not_count_as_evidence(self) -> None:
        result = EvidenceRAG(FakeProvider("使用 300 K 运行。[P1]")).generate(
            "问题", [{"id": "paper-a", "title": "Paper A"}],
            [{"paper_id": "paper-a", "page": 2, "excerpt": "模拟温度为 1300 K。"}],
        )
        self.assertFalse(result["used"])
        self.assertEqual(result["reason"], "unsupported_numeric_claim")

    def test_supported_parameter_claim_is_allowed(self) -> None:
        result = EvidenceRAG(FakeProvider("在 300 K 下计算。[P1]")).generate(
            "问题", [{"id": "paper-a", "title": "Paper A"}],
            [{"paper_id": "paper-a", "page": 2, "excerpt": "模拟温度为 300 K。"}],
        )
        self.assertTrue(result["used"])

    def test_missing_or_invalid_citation_falls_back(self) -> None:
        for answer in ("没有引用。", "错误来源。[P99]"):
            result = EvidenceRAG(FakeProvider(answer)).generate(
                "问题",
                [{"id": "paper-a", "title": "Paper A"}],
                [],
            )
            self.assertFalse(result["used"])
            self.assertEqual(result["reason"], "citation_validation_failed")

    def test_only_selected_fulltext_reaches_prompt(self) -> None:
        provider = FakeProvider("证据结论。[P1]")
        rag = EvidenceRAG(provider)
        result = rag.generate(
            "问题",
            [{"id": "paper-a", "title": "Paper A"}],
            [
                {"paper_id": "paper-a", "page": 2, "excerpt": "allowed excerpt"},
                {"paper_id": "paper-b", "page": 3, "excerpt": "secret unrelated excerpt"},
            ],
        )
        self.assertTrue(result["used"])
        self.assertIn("allowed excerpt", provider.user)
        self.assertNotIn("secret unrelated excerpt", provider.user)
        packet = provider.user.split("证据包(JSON)：\n", 1)[1]
        json.loads(packet)

    def test_agent_inserts_valid_rag_answer(self) -> None:
        provider = FakeProvider("使用所列入门论文建立最小基线。[P1]")
        agent = BatteryResearchAgent(fulltext_path=None, rag=EvidenceRAG(provider))
        result = agent.answer("VASP 入门", limit=2)
        self.assertTrue(result["rag"]["used"])
        self.assertIn("RAG 综合回答", result["answer_markdown"])


if __name__ == "__main__":
    unittest.main()
