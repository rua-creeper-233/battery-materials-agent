import json
import unittest
from pathlib import Path
from agent import BatteryResearchAgent

ROOT = Path(__file__).resolve().parents[1]

class AnswerGuidanceTests(unittest.TestCase):
    def test_shared_answer_regression(self):
        agent = BatteryResearchAgent(fulltext_path=None, extra_data_path=None)
        cases = json.loads((ROOT / 'data/answer_regression.json').read_text(encoding='utf-8'))['cases']
        for case in cases:
            with self.subTest(question=case['question']):
                result = agent.answer(case['question'], use_rag=False)
                self.assertEqual(result['guidance_id'], case['guidance'])
                if 'task' in case:
                    self.assertEqual(result['task'], case['task'])
                for word in case['contains']:
                    self.assertIn(word, result['answer_markdown'])
                for word in case.get('excludes', []):
                    self.assertNotIn(word, result['answer_markdown'])

    def test_new_papers_exact_doi_lookup(self):
        agent = BatteryResearchAgent(fulltext_path=None, extra_data_path=None)
        for doi, paper_id in [('10.1038/s41586-018-0337-2', 'butler2018_ml_materials_review'), ('10.1038/s41524-026-02271-y', 'takenaka2026_sei_mlff')]:
            self.assertEqual(agent.search(doi, limit=1)[0]['id'], paper_id)
