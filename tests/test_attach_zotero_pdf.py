from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from attach_zotero_pdf import LocalZoteroWriter, pdf_attachment_state


class ZoteroAttachmentRecoveryTests(unittest.TestCase):
    def test_detects_complete_and_own_resumable_attachment(self) -> None:
        incomplete = {"key": "EMPTY1", "links": {}, "data": {
            "contentType": "application/pdf", "tags": [{"tag": "battery-materials-agent"}],
        }}
        self.assertEqual(pdf_attachment_state([incomplete]), ("resumable", "EMPTY1"))
        complete = {"key": "DONE1", "links": {"enclosure": {
            "href": "file:///tmp/paper.pdf", "length": 100,
        }}, "data": {"contentType": "application/pdf", "tags": []}}
        self.assertEqual(pdf_attachment_state([incomplete, complete]), ("complete", "DONE1"))

    def test_unrelated_incomplete_pdf_is_not_claimed_for_resume(self) -> None:
        child = {"key": "OTHER", "links": {}, "data": {
            "contentType": "application/pdf", "tags": [],
        }}
        self.assertEqual(pdf_attachment_state([child]), ("absent", None))

    def test_bad_local_file_fails_before_metadata_write(self) -> None:
        writer = object.__new__(LocalZoteroWriter)
        writer.write = Mock()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "not.pdf"
            path.write_bytes(b"not a PDF")
            with self.assertRaises(RuntimeError):
                writer.create_stored_attachment("PARENT", "Title", "https://example.test", path)
        writer.write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
