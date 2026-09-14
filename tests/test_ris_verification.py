import unittest
from export_ris import render

class RisVerificationTests(unittest.TestCase):
    def test_doi_only_paper_is_not_claimed_wos_verified(self):
        paper = dict(title='Example', journal='Journal', year=2025, doi='10.1234/example', tags_zh=['MACE'])
        text = render(paper)
        self.assertIn('Web of Science record not checked', text)
        self.assertNotIn('AN  - WOS:', text)
        self.assertIn('KW  - MACE', text)

    def test_wos_record_keeps_accession(self):
        paper = dict(title='Example', journal='Journal', year=2025, doi='10.1234/example', wos_uid='WOS:EXAMPLE')
        text = render(paper)
        self.assertIn('AN  - WOS:EXAMPLE', text)
        self.assertNotIn('record not checked', text)
