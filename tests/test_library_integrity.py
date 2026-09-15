from __future__ import annotations

import json
import unittest
from pathlib import Path

from agent import BatteryResearchAgent


ROOT = Path(__file__).resolve().parents[1]


class LibraryIntegrityTests(unittest.TestCase):
    def test_library_has_verified_core_and_starter_sets(self) -> None:
        papers = json.loads((ROOT / "data" / "papers.json").read_text(encoding="utf-8"))
        self.assertEqual(len(papers), 55)
        dois = [paper["doi"].lower() for paper in papers]
        wos_papers = [paper for paper in papers if paper.get("wos_uid")]
        starter_papers = [paper for paper in papers if paper.get("collection") == "starter"]
        uids = [paper["wos_uid"] for paper in wos_papers]
        self.assertEqual(len(set(dois)), 55)
        self.assertEqual(len(wos_papers), 16)
        self.assertEqual(len(starter_papers), 27)
        self.assertTrue(all(uid.startswith("WOS:") for uid in uids))
        self.assertEqual(len(set(uids)), 16)
        self.assertTrue(
            all(
                paper.get("verification", {}).get("wos")
                == "verified_institution_session_2026-09-13"
                for paper in wos_papers
            )
        )
        self.assertTrue(
            all(len(paper.get("protocol_steps", [])) >= 5 for paper in starter_papers)
        )
        self.assertTrue(
            {
                "10.1016/j.cpc.2018.03.016",
                "10.1016/j.cpc.2020.107206",
                "10.1038/s41467-022-29939-5",
                "10.1103/physrevb.82.125416",
                "10.21105/joss.05941",
            }.issubset(set(dois))
        )
        self.assertTrue(
            all(
                paper.get("verification", {}).get("doi", "").startswith("verified")
                for paper in papers
            )
        )

    def test_local_main_text_library_is_audited_and_searchable(self) -> None:
        manifest = json.loads(
            (ROOT / "literature" / "manifest.json").read_text(encoding="utf-8")
        )
        audit = manifest["integrity_audit"]
        self.assertEqual(audit["library_papers"], 55)
        self.assertEqual(audit["doi_verified"], 55)
        self.assertGreaterEqual(audit["downloaded_main_texts"], 16)
        self.assertEqual(audit["wos_uid_verified"], 16)
        self.assertEqual(audit["duplicate_pdf_hashes"], 0)
        downloaded = [
            row for row in manifest["papers"].values() if row.get("status") == "downloaded"
        ]
        self.assertEqual(len(downloaded), audit["downloaded_main_texts"])
        self.assertTrue(
            all(
                (row.get("validation") or {}).get("document_kind") == "article"
                for row in downloaded
            )
        )
        self.assertTrue(all((ROOT / row["local_pdf"]).is_file() for row in downloaded))

        agent = BatteryResearchAgent()
        self.assertEqual(
            len({row["paper_id"] for row in agent.fulltext_chunks}),
            audit["downloaded_main_texts"],
        )
        hits = agent.search_fulltext("锂离子扩散 势垒", limit=6)
        self.assertTrue(hits)
        self.assertTrue(
            all(
                hit["page"] >= 1 and hit["local_pdf_url"].startswith("/local-pdf/")
                for hit in hits
            )
        )

    def test_m3gnet_main_text_and_supplement_are_separated(self) -> None:
        manifest = json.loads(
            (ROOT / "literature" / "manifest.json").read_text(encoding="utf-8")
        )
        entry = manifest["papers"]["chen2022_m3gnet"]
        self.assertEqual(entry["validation"]["document_kind"], "article")
        self.assertEqual(entry["validation"]["pages"], 58)
        self.assertTrue((ROOT / entry["supplementary_pdf"]).is_file())
        indexed_ids = {
            json.loads(line)["paper_id"]
            for line in (ROOT / "data" / "fulltext_chunks.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        }
        self.assertIn("chen2022_m3gnet", indexed_ids)

    def test_ris_has_16_complete_records(self) -> None:
        ris = (ROOT / "exports" / "battery_materials_16_verified.ris").read_text(
            encoding="utf-8"
        )
        self.assertEqual(ris.count("TY  - JOUR"), 16)
        self.assertEqual(ris.count("ER  - "), 16)
        self.assertEqual(ris.count("AN  - WOS:"), 16)


if __name__ == "__main__":
    unittest.main()
