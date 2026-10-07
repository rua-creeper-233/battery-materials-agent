import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import expand_library as library
from expand_recent_library import enrich_record


class RecentMetadataTests(unittest.TestCase):
    def test_date_precision_does_not_invent_month_or_day(self):
        row = enrich_record({"doi": "10.x/one", "publication_date": "2026-1-1",
                             "publication_date_precision": "year", "online_date": "2025-3-1",
                             "online_date_precision": "month"})
        self.assertEqual(row["publication_date"], "2026")
        self.assertEqual(row["online_date"], "2025-03")

    def test_primary_method_description_is_specific(self):
        row = enrich_record({"doi": "10.1038/s41524-026-02023-y"})
        self.assertIn("NEP", row["methods"])
        self.assertIn("LGPS", row["systems"])
        self.assertIn("迁移势垒", row["properties"])

    def test_merge_preserves_legacy_and_owned_stable_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [root / name for name in ("papers.json", "old.json", "recent.json")]
            papers = [{"id": "legacy", "doi": "10.x/old", "collection": "core", "custom": "keep"},
                      {"id": "recent_owned", "doi": "10.x/recent", "collection": "recent_verified_20261008",
                       "wos_uid": "WOS:test", "verification": {"fulltext": "verified_local_pdf_test"}}]
            rows = [{"id": "recent_rekeyed", "doi": doi, "year": 2026, "title": "Verified title",
                     "collection": "recent_verified_20261008", "document_type": "Perspective",
                     "systems": ["SSE"], "properties": ["barrier"], "publication_date": "2026-09",
                     "publication_date_precision": "month", "verification": {"doi": "verified_crossref"}}
                    for doi in ("10.x/old", "10.x/recent")]
            for path, value in zip(paths, (papers, [], rows)):
                path.write_text(json.dumps(value), encoding="utf-8")
            with patch.object(library, "PAPERS", paths[0]), patch.object(library, "CATALOG", paths[1]), \
                 patch.object(library, "RECENT_CATALOG", paths[2]), patch("builtins.print"):
                library.main()
                first = paths[0].read_bytes()
                library.main()
                self.assertEqual(first, paths[0].read_bytes())
            merged = json.loads(first)
            self.assertEqual(merged[0], papers[0])
            self.assertEqual(merged[1]["id"], "recent_owned")
            self.assertEqual(merged[1]["document_type"], "Perspective")
            self.assertEqual(merged[1]["properties"], ["barrier"])
            self.assertEqual(merged[1]["publication_date_precision"], "month")
            self.assertEqual(merged[1]["verification"]["fulltext"], "verified_local_pdf_test")


if __name__ == "__main__":
    unittest.main()
