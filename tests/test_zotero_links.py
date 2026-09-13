import unittest

from sync_zotero_links import collect_links, normalize_doi


class ZoteroLinkTests(unittest.TestCase):
    def test_normalize_doi(self) -> None:
        self.assertEqual(normalize_doi("https://doi.org/10.1000/ABC "), "10.1000/abc")
        self.assertEqual(normalize_doi("doi:10.1000/xyz"), "10.1000/xyz")

    def test_collects_parent_and_pdf_attachment(self) -> None:
        def fake_fetch(path):
            if path.startswith("/items/top"):
                return [
                    {
                        "key": "PARENT01",
                        "data": {"title": "Example", "DOI": "10.1000/EXAMPLE"},
                    }
                ]
            self.assertTrue(path.startswith("/items/PARENT01/children"))
            return [
                {
                    "key": "PDF00001",
                    "data": {
                        "itemType": "attachment",
                        "contentType": "application/pdf",
                        "filename": "paper.pdf",
                    },
                }
            ]

        mapping = collect_links(fake_fetch)
        self.assertEqual(mapping["10.1000/example"]["item_key"], "PARENT01")
        self.assertEqual(mapping["10.1000/example"]["attachment_key"], "PDF00001")
        self.assertTrue(mapping["10.1000/example"]["has_pdf"])


if __name__ == "__main__":
    unittest.main()
