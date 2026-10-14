import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from publication_safety import (
    PublicationSafetyError,
    assert_clean,
    sanitize_method_evidence,
    scan_text,
    validate_public_zotero_map,
)


class PublicationSafetyTests(unittest.TestCase):
    def test_zotero_allowlist_is_empty(self):
        self.assertEqual(validate_public_zotero_map({"visibility": "public_sanitized", "items": {}})["items"], {})
        for value in (
            {"visibility": "public_sanitized", "items": {"paper": {"item_key": "abc"}}},
            {"visibility": "public", "items": {}},
            {"visibility": "public_sanitized", "items": {}, "extra": 1},
        ):
            with self.assertRaises(PublicationSafetyError):
                validate_public_zotero_map(value)

    def test_method_payload_is_empty_and_has_no_local_fields(self):
        public = sanitize_method_evidence({"generated_at": "2026-01-01T00:00:00Z", "papers": {"p": {
            "title": "Public author name", "doi": "10.1/x", "evidence": [{"signal": "MAE", "local_pdf_url": "/local-pdf/p.pdf", "page": 1}]
        }}})
        self.assertEqual(public["papers"], {})
        self.assertNotIn("generated_at", json.dumps(public))
        self.assertNotIn("local_pdf_url", json.dumps(public))

    def test_scanner_has_no_secret_snippets_and_accepts_placeholders(self):
        self.assertEqual(scan_text("Author: Jane Doe\npath=<project-root>\\data"), [])
        findings = scan_text("token=" + "AKIA" + "1234567890123456", "fixture.md")
        self.assertEqual([(x.path, x.line, x.type) for x in findings], [("fixture.md", 1, "credential_format")])
        with self.assertRaises(PublicationSafetyError) as raised:
            assert_clean(findings)
        self.assertNotIn("AKIA", str(raised.exception))

    def test_public_catalog_rejects_per_paper_fulltext_holdings(self):
        safe = '{"id":"paper-1","title":"Battery method","verification":{"publisher":"verified"}}'
        self.assertEqual(scan_text(safe, "data/papers.json"), [])
        private = json.dumps({"id": "paper-1", "verification": {"fulltext": "verified_local_pdf" + "_2026-10-14"}})
        findings = scan_text(private, "data/papers.json")
        self.assertTrue(any(item.type == "fulltext_verification" for item in findings))
        self.assertTrue(any(item.type == "private_evidence_value" for item in findings))

    def test_empty_fulltext_fields_are_allowed_only_as_empty_values(self):
        empty = '{"verification":{"fulltext":""}}'
        self.assertFalse(any(item.type == "private_evidence_value" for item in scan_text(empty, "data/papers.json")))

    def test_institution_session_marker_is_private_access_trace(self):
        marker = "verified_institution_session" + "_2026-09-13"
        findings = scan_text(json.dumps({"verification": {"wos": marker}}), "data/papers.json")
        self.assertTrue(any(item.type == "personal_access_trace" for item in findings))

    def test_empty_structured_fields_are_not_private_values(self):
        for value in (None, "", {}, []):
            content = json.dumps({"item_key": value}, indent=2)
            self.assertEqual(scan_text(content, "fixture.json"), [])
        self.assertTrue(scan_text(json.dumps({"item_key": "fixture-only"}), "fixture.json"))
        self.assertTrue(scan_text(json.dumps({"indexed_chunks": 1}), "fixture.json"))

    def test_private_paths_and_credential_shapes_are_redacted(self):
        from publication_safety import FORBIDDEN_PATH
        for path in ("data/fulltext_chunks.jsonl", "literature/manifest.json", "private/result.json", "model.gguf", ".env.backup", "data/zotero-links.local.json"):
            self.assertTrue(FORBIDDEN_PATH.search(path), path)
        for text in ("ghp_" + "a" * 36, "sk-proj-" + "a" * 24, "zotero://open-pdf/library/items/" + "ABC" + "12345", "C:/" + "Users/" + "example-user/file"):
            self.assertTrue(scan_text(text, "fixture.md"))

    def test_build_rejects_bad_sources_before_any_docs_mutation(self):
        import shutil
        import build_pages
        import build_learning_route

        root = Path(__file__).resolve().parents[1]
        assets = ("index.html", "future-directions.html", "ai-battery-applications.html", "foundations.html", "learning-route.css", "learning-route.js", "lab-ui.css", "lab-ui.js", "browser_agent.js", "tutorials.js", "tutorials.css", "dft_lessons.js", "beginner_lessons.js", "md_lessons.js")
        sources = [root / "static" / name for name in assets]
        sources += [root / "guides" / name for name in build_pages.GUIDE_NAMES]
        sources += [root / "FINETUNE_INTEGRATION.md", root / "static/data/zotero-links.json"]
        sources += [root / "examples/ai_battery" / name for name in ("relax_mace.py", "msd_from_csv.py", "example_trajectory.csv")]
        sources += [root / "data" / name for name in ("papers.json", "learning_route.json", "paper_tags.json", "search_config.json", "project_status.json", "paper_titles_zh.json", "method_evidence.auto.json")]
        for kind in ("zotero", "method", "catalog", "titles", "shared_asset", "route", "guide"):
            with self.subTest(source=kind), tempfile.TemporaryDirectory() as folder:
                target_root = Path(folder)
                for source in sources:
                    target = target_root / source.relative_to(root)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                target_docs = target_root / "docs"
                target_docs.mkdir()
                sentinel = target_docs / "sentinel.txt"
                sentinel.write_text("preserve existing publication", encoding="utf-8")
                if kind == "zotero":
                    target = target_root / "static/data/zotero-links.json"
                    value = {"visibility": "public_sanitized", "items": {"fixture": {}}}
                elif kind == "method":
                    target = target_root / "data/method_evidence.auto.json"
                    value = {"visibility": "public_sanitized", "papers": {"fixture": {}}}
                elif kind == "catalog":
                    target = target_root / "data/papers.json"
                    value = json.loads(target.read_text(encoding="utf-8"))
                    value[0]["title"] += " C:/" + "Users/" + "fixture-person/file"
                elif kind == "route":
                    target = target_root / "data/learning_route.json"
                    value = json.loads(target.read_text(encoding="utf-8"))
                    value["stages"][0]["summary"] += " sk-proj-" + "a" * 24
                elif kind == "titles":
                    target = target_root / "data/paper_titles_zh.json"
                    value = json.loads(target.read_text(encoding="utf-8"))
                    first = next(iter(value["papers"]))
                    value["papers"][first]["title"] += " C:/" + "Users/" + "fixture-person/file"
                elif kind == "shared_asset":
                    target = target_root / "static/lab-ui.js"
                    target.write_text("const leaked = 'sk-proj-" + "a" * 24 + "';", encoding="utf-8")
                    value = None
                else:
                    target = target_root / "guides" / build_pages.GUIDE_NAMES[0]
                    target.write_text("contact=" + "fixture" + "@" + "example.invalid", encoding="utf-8")
                    value = None
                if value is not None:
                    target.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
                with patch.object(build_pages, "ROOT", target_root), patch.object(build_pages, "DOCS", target_docs), patch.object(build_learning_route, "ROUTE_PATH", target_root / "data/learning_route.json"), patch.object(build_learning_route, "PAPERS_PATH", target_root / "data/papers.json"):
                    with self.assertRaises(PublicationSafetyError):
                        build_pages.main()
                self.assertEqual(list(target_docs.iterdir()), [sentinel])
                self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve existing publication")
                self.assertFalse((target_root / "static/learning-route.html").exists())


if __name__ == "__main__":
    unittest.main()
