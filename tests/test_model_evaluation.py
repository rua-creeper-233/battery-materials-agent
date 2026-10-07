import unittest

from training.evaluate_model import score


class ModelEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.expected = [{"id": key, "requires_citation": True, "task": "evidence_insufficient",
                          "messages": [{"role": "system", "content": ""},
                                       {"role": "user", "content": '{"papers":[{"source_id":"P1"}]}'},
                                       {"role": "assistant", "content": "参考"}]} for key in ("a", "b")]

    def test_incomplete_predictions_show_coverage_and_invalid_citation(self):
        result = score(self.expected, [{"id": "a", "response": "证据不足 [P99]"}])
        self.assertEqual(result["coverage"], 0.5)
        self.assertEqual(result["citation_rate"], 1)
        self.assertEqual(result["valid_citation_format_rate"], 0)
        self.assertEqual(result["invalid_citation_rows"], ["a"])

    def test_duplicate_predictions_rejected(self):
        with self.assertRaises(ValueError):
            score(self.expected, [{"id": "a", "response": "[P1]"}] * 2)


if __name__ == "__main__":
    unittest.main()
