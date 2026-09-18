"""Attach audited PDFs to existing Zotero 10 items through the local API.

The local API key is requested interactively from Zotero, kept in memory only,
and never printed or written to disk. Existing DOI records are never replaced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

import import_zotero_library as zotero


ROOT = Path(__file__).resolve().parent
BASE = "http://127.0.0.1:23119"
APP_NAME = "Battery Evidence Lab"


class LocalZoteroWriter:
    def __init__(self) -> None:
        self.server_id = self._server_id()
        self.key: str | None = None

    @staticmethod
    def _headers(extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "Zotero-Allowed-Request": "true",
            "Zotero-API-Version": "3",
            "User-Agent": "BatteryMaterialsAgent/1.0",
        }
        headers.update(extra or {})
        return headers

    def _server_id(self) -> str:
        request = Request(BASE + "/api/", headers=self._headers())
        try:
            with urlopen(request, timeout=10) as response:
                server_id = response.headers.get("Zotero-Server-ID", "")
                version = response.headers.get("X-Zotero-Version", "")
        except URLError as exc:
            raise RuntimeError("无法连接 Zotero 本地 API；请启动 Zotero 10。") from exc
        if not server_id or not version.startswith("10."):
            raise RuntimeError("需要 Zotero 10 本地 API 写入支持。")
        return server_id

    def authorize(self) -> None:
        payload = json.dumps({"appName": APP_NAME}).encode("utf-8")
        request = Request(
            BASE + "/api/local/authorize",
            data=payload,
            method="POST",
            headers=self._headers({
                "Content-Type": "application/json",
                "Zotero-Server-ID": self.server_id,
            }),
        )
        try:
            with urlopen(request, timeout=180) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 403:
                raise RuntimeError("Zotero 写入授权被拒绝。") from exc
            raise
        key = result.get("key") if isinstance(result, dict) else None
        if not isinstance(key, str) or len(key) < 16:
            raise RuntimeError("Zotero 未返回有效的本地授权。")
        self.key = key

    def write(
        self,
        path: str,
        *,
        data: bytes,
        content_type: str,
        headers: dict[str, str] | None = None,
        timeout: int = 180,
    ) -> tuple[int, bytes, dict[str, str]]:
        for attempt in range(2):
            if not self.key:
                self.authorize()
            request_headers = self._headers({
                "Content-Type": content_type,
                "Zotero-Server-ID": self.server_id,
                "Zotero-API-Key": self.key or "",
                **(headers or {}),
            })
            request = Request(urljoin(BASE + "/", path.lstrip("/")), data=data,
                              method="POST", headers=request_headers)
            try:
                with urlopen(request, timeout=timeout) as response:
                    return response.status, response.read(), dict(response.headers.items())
            except HTTPError as exc:
                if exc.code == 401 and attempt == 0:
                    self.key = None
                    continue
                detail = exc.read().decode("utf-8", errors="replace")[:500]
                raise RuntimeError(f"Zotero 写入失败 HTTP {exc.code}: {detail}") from exc
        raise RuntimeError("Zotero 本地授权已失效。")

    def _upload_attachment_bytes(self, attachment_key: str, pdf_path: Path,
                                 file_bytes: bytes) -> None:
        md5 = hashlib.md5(file_bytes).hexdigest()  # noqa: S324 - required by Zotero upload protocol
        form = urlencode({
            "md5": md5,
            "filename": pdf_path.name,
            "filesize": len(file_bytes),
            "mtime": int(pdf_path.stat().st_mtime * 1000),
            "contentType": mimetypes.guess_type(pdf_path.name)[0] or "application/pdf",
        }).encode("ascii")
        _, body, _ = self.write(
            f"/api/users/0/items/{attachment_key}/file",
            data=form,
            content_type="application/x-www-form-urlencoded",
            headers={"If-None-Match": "*"},
        )
        upload = json.loads(body.decode("utf-8"))
        if upload.get("exists") == 1:
            return
        upload_url = upload.get("url")
        upload_key = upload.get("uploadKey")
        if not upload_url or not upload_key:
            raise RuntimeError("Zotero 未返回文件上传地址。")
        request = Request(urljoin(BASE + "/", upload_url), data=file_bytes, method="POST",
                          headers=self._headers({"Content-Type": "application/pdf"}))
        with urlopen(request, timeout=180) as response:
            if response.status not in (200, 201, 204):
                raise RuntimeError(f"Zotero 文件接收失败 HTTP {response.status}")
        self.write(
            f"/api/users/0/items/{attachment_key}/file",
            data=urlencode({"upload": upload_key}).encode("ascii"),
            content_type="application/x-www-form-urlencoded",
            headers={"If-None-Match": "*"},
        )

    def upload_stored_file(self, attachment_key: str, pdf_path: Path) -> None:
        file_bytes = pdf_path.read_bytes()
        if not file_bytes.startswith(b"%PDF-"):
            raise RuntimeError(f"本地文件不是 PDF: {pdf_path}")
        self._upload_attachment_bytes(attachment_key, pdf_path, file_bytes)

    def create_stored_attachment(self, parent_key: str, title: str, source_url: str,
                                 pdf_path: Path) -> str:
        # Read and validate before the metadata write. A local I/O failure must
        # not leave an empty child attachment behind.
        file_bytes = pdf_path.read_bytes()
        if not file_bytes.startswith(b"%PDF-"):
            raise RuntimeError(f"本地文件不是 PDF: {pdf_path}")
        payload = [{
            "itemType": "attachment",
            "parentItem": parent_key,
            "linkMode": "imported_file",
            "title": f"{title} - Full Text PDF",
            "accessDate": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "url": source_url,
            "note": "",
            "tags": [{"tag": "battery-materials-agent"}],
            "relations": {},
            "contentType": "application/pdf",
            "charset": "",
            "filename": pdf_path.name,
        }]
        _, body, _ = self.write(
            "/api/users/0/items",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            content_type="application/json; charset=utf-8",
            headers={"Zotero-Write-Token": uuid.uuid4().hex},
        )
        result = json.loads(body.decode("utf-8"))
        created = (result.get("successful") or {}).get("0")
        attachment_key = created.get("key") if isinstance(created, dict) else None
        if not attachment_key:
            raise RuntimeError(f"Zotero 未创建附件条目: {str(result)[:500]}")
        self._upload_attachment_bytes(attachment_key, pdf_path, file_bytes)
        return attachment_key


def pdf_attachment_state(children: list[dict[str, Any]]) -> tuple[str, str | None]:
    """Return complete, resumable, or absent for PDF child attachments."""
    resumable = None
    for child in children:
        data = child.get("data", child)
        if data.get("contentType") != "application/pdf":
            continue
        key = child.get("key") or data.get("key")
        enclosure = child.get("links", {}).get("enclosure", {})
        if enclosure.get("href") and int(enclosure.get("length") or 0) > 0:
            return "complete", key
        tags = {str(tag.get("tag", "")) for tag in data.get("tags", []) if isinstance(tag, dict)}
        if "battery-materials-agent" in tags and key:
            resumable = key
    return ("resumable", resumable) if resumable else ("absent", None)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-id", action="append", required=True)
    args = parser.parse_args()
    selected = set(args.paper_id)
    papers = json.loads(zotero.PAPERS_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(zotero.MANIFEST_PATH.read_text(encoding="utf-8"))
    papers = [paper for paper in papers if paper["id"] in selected]
    if selected - {paper["id"] for paper in papers}:
        raise SystemExit("Unknown selected paper IDs")
    existing = {zotero._item_doi(item): item for item in zotero.list_top_items() if zotero._item_doi(item)}
    writer: LocalZoteroWriter | None = None
    for paper in papers:
        parent = existing.get(zotero.normalize_doi(paper["doi"]))
        if not parent:
            print(paper["id"], "DOI_not_found")
            continue
        parent_key = parent.get("key") or parent.get("data", {}).get("key")
        children = zotero.list_children(parent_key)
        attachment_state, attachment_key = pdf_attachment_state(children)
        if attachment_state == "complete":
            print(paper["id"], "PDF_already_attached")
            continue
        pdf_path = zotero._pdf_for(paper["id"], manifest)
        if not pdf_path:
            print(paper["id"], "no_audited_local_PDF")
            continue
        writer = writer or LocalZoteroWriter()
        if attachment_state == "resumable" and attachment_key:
            writer.upload_stored_file(attachment_key, pdf_path)
            print(paper["id"], "resumed", attachment_key)
            continue
        attachment_key = writer.create_stored_attachment(
            parent_key, paper["title"], paper.get("url") or f"https://doi.org/{paper['doi']}", pdf_path
        )
        print(paper["id"], "attached", attachment_key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
