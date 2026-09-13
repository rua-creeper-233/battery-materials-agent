"""Dependency-light local web server for Battery Evidence Lab.

The default mode is loopback-only. ``--public-api`` is intended for an HTTPS
tunnel and requires a bearer access key plus an explicit browser origin.
"""

from __future__ import annotations

import argparse
import hmac
import json
import mimetypes
import os
import re
from email.parser import BytesParser
from email.policy import default as email_policy
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from agent import BatteryResearchAgent
from library_store import KEYWORDS, MAX_PDF_BYTES, ingest_pdf


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
LITERATURE = ROOT / "literature"
PDF_DIR = LITERATURE / "pdfs"
MANIFEST = LITERATURE / "manifest.json"
METHOD_EVIDENCE = ROOT / "data" / "method_evidence.auto.json"
ZOTERO_LINKS = ROOT / "private" / "zotero-links.local.json"
DEFAULT_ALLOWED_ORIGIN = "https://rua-creeper-233.github.io"
AGENT = BatteryResearchAgent()


def _load_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _load_method_evidence() -> dict[str, object]:
    return _load_json(METHOD_EVIDENCE, {"review_status": "not_generated", "papers": {}})


def _load_zotero_links() -> dict[str, object]:
    payload = _load_json(ZOTERO_LINKS, {"items": {}})
    payload["visibility"] = "local_private"
    return payload


class BatteryHTTPServer(ThreadingHTTPServer):
    public_api: bool = False
    access_token: str = ""
    allowed_origins: set[str]


class Handler(BaseHTTPRequestHandler):
    server_version = "BatteryEvidenceLab/0.2"

    @property
    def config(self) -> BatteryHTTPServer:
        return self.server  # type: ignore[return-value]

    def _origin(self) -> str:
        return self.headers.get("Origin", "").rstrip("/")

    def _host_is_local(self) -> bool:
        host = self.headers.get("Host", "").split(":", 1)[0].strip("[]").lower()
        return host in {"127.0.0.1", "localhost", "::1"}

    def _is_local_request(self) -> bool:
        origin = self._origin()
        local_origin = not origin or origin.startswith("http://127.0.0.1:") or origin.startswith("http://localhost:")
        return self.client_address[0] in {"127.0.0.1", "::1"} and self._host_is_local() and local_origin

    def _origin_allowed(self) -> bool:
        origin = self._origin()
        return not origin or origin in self.config.allowed_origins or origin.startswith("http://127.0.0.1:") or origin.startswith("http://localhost:")

    def _send_cors(self) -> None:
        origin = self._origin()
        if origin and self._origin_allowed():
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

    def _authorized(self) -> bool:
        if self._is_local_request():
            return True
        if not self.config.public_api or not self._origin_allowed():
            return False
        supplied = self.headers.get("Authorization", "")
        expected = f"Bearer {self.config.access_token}"
        return bool(self.config.access_token) and hmac.compare_digest(supplied, expected)

    def _json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self._send_cors()
        self.end_headers()
        self.wfile.write(body)

    def _deny(self, message: str = "需要本地访问或正确的访问密钥。") -> None:
        self._json({"error": message}, HTTPStatus.UNAUTHORIZED)

    def do_OPTIONS(self) -> None:  # noqa: N802
        if not urlparse(self.path).path.startswith("/api/") or not self._origin_allowed():
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            manifest = _load_json(MANIFEST, {"papers": {}})
            downloaded = sum(row.get("status") == "downloaded" for row in manifest.get("papers", {}).values())
            methods = _load_method_evidence().get("papers", {})
            self._json(
                {
                    "ok": True,
                    "service": "Battery Evidence Lab local API",
                    "api_version": "v1",
                    "papers": len(AGENT.papers),
                    "downloaded_pdfs": downloaded,
                    "fulltext_papers": len({row["paper_id"] for row in AGENT.fulltext_chunks}),
                    "fulltext_chunks": len(AGENT.fulltext_chunks),
                    "method_evidence_signals": sum(int(row.get("evidence_count", 0)) for row in methods.values()) if isinstance(methods, dict) else 0,
                    "public_api": self.config.public_api,
                }
            )
            return
        if path == "/api/capabilities":
            self._json(
                {
                    "api_version": "v1",
                    "upload": {"endpoint": "/api/upload", "max_pdf_bytes": MAX_PDF_BYTES, "auth": "bearer-when-tunneled"},
                    "keywords": {"endpoint": "/api/keywords", "version": KEYWORDS.api_version, "provider": KEYWORDS.provider},
                    "privacy": {"zotero_links": "loopback-only", "pdf_download": "loopback-only"},
                }
            )
            return

        if path.startswith("/api/") and not self._authorized():
            self._deny()
            return
        if path == "/api/papers":
            self._json({"papers": AGENT.papers})
            return
        if path == "/api/literature":
            raw = _load_json(MANIFEST, {"papers": {}})
            payload: dict[str, object] = {
                "updated_at": raw.get("updated_at"),
                "fulltext_index": raw.get("fulltext_index", {}),
                "papers": {
                    paper_id: {
                        "status": row.get("status"),
                        "local_pdf": row.get("local_pdf") if self._is_local_request() else None,
                        "pages": (row.get("validation") or {}).get("pages"),
                        "text_chunks": (row.get("text_extraction") or {}).get("chunks"),
                    }
                    for paper_id, row in raw.get("papers", {}).items()
                },
            }
            self._json(payload)
            return
        if path == "/api/zotero-links":
            # A tunnel also reaches this process from loopback. Host and Origin
            # checks ensure personal Zotero keys never cross the tunnel.
            self._json(_load_zotero_links() if self._is_local_request() else {"visibility": "private", "items": {}})
            return
        if path == "/api/methods":
            self._json(_load_method_evidence())
            return
        if path.startswith("/api/papers/"):
            paper_id = unquote(path.removeprefix("/api/papers/"))
            paper = next((item for item in AGENT.papers if item["id"] == paper_id), None)
            self._json(paper or {"error": "paper not found"}, 200 if paper else 404)
            return
        if path.startswith("/api/methods/"):
            paper_id = unquote(path.removeprefix("/api/methods/"))
            papers = _load_method_evidence().get("papers", {})
            row = papers.get(paper_id) if isinstance(papers, dict) else None
            self._json(row or {"error": "method evidence not found"}, 200 if row else 404)
            return
        if path.startswith("/local-pdf/"):
            if not self._is_local_request():
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            paper_id = unquote(path.removeprefix("/local-pdf/")).removesuffix(".pdf")
            known = {paper["id"] for paper in AGENT.papers}
            pdf = PDF_DIR / f"{paper_id}.pdf"
            if paper_id not in known or not pdf.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            body = pdf.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", f'inline; filename="{paper_id}.pdf"')
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)
            return
        self._serve_static(path)

    def _read_json_body(self, limit: int = 200_000) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length < 0 or length > limit:
            raise ValueError("request too large")
        payload = json.loads(self.rfile.read(length) or b"{}")
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def _read_upload(self) -> tuple[bytes, str, dict[str, str]]:
        content_type = self.headers.get("Content-Type", "")
        if not content_type.lower().startswith("multipart/form-data"):
            raise ValueError("上传接口需要 multipart/form-data。")
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_PDF_BYTES + 512_000:
            raise ValueError("上传内容为空或超过 50 MiB 上限。")
        raw = self.rfile.read(length)
        envelope = b"Content-Type: " + content_type.encode("ascii", "ignore") + b"\r\nMIME-Version: 1.0\r\n\r\n" + raw
        message = BytesParser(policy=email_policy).parsebytes(envelope)
        pdf_bytes = b""
        filename = "uploaded.pdf"
        fields: dict[str, str] = {}
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition") or ""
            part_filename = part.get_filename()
            value = part.get_payload(decode=True) or b""
            if name == "file" and part_filename:
                pdf_bytes = value
                filename = Path(part_filename).name
            elif name:
                fields[name] = value.decode(part.get_content_charset() or "utf-8", errors="replace").strip()
        if not pdf_bytes:
            raise ValueError("没有收到 PDF 文件。")
        return pdf_bytes, filename, fields

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path not in {"/api/chat", "/api/keywords", "/api/upload"}:
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        if not self._authorized():
            self._deny()
            return
        try:
            if path == "/api/chat":
                payload = self._read_json_body(100_000)
                question = str(payload.get("question", "")).strip()
                limit = min(max(int(payload.get("limit", 5)), 1), 10)
                result = AGENT.answer(question, limit=limit)
                if not self._is_local_request():
                    result["fulltext_hits"] = []
                    result["answer_markdown"] = re.sub(
                        r"\n### 本地全文命中.*?(?=\n### 边界与下一步)",
                        "",
                        result["answer_markdown"],
                        flags=re.S,
                    )
                self._json(result)
                return
            if path == "/api/keywords":
                payload = self._read_json_body(300_000)
                text = str(payload.get("text", ""))
                paper_id = str(payload.get("paper_id", "")).strip()
                if paper_id:
                    paper = next((row for row in AGENT.papers if row["id"] == paper_id), None)
                    chunks = [row.get("text", "") for row in AGENT.fulltext_chunks if row.get("paper_id") == paper_id]
                    if not paper:
                        raise ValueError("paper_id 不存在。")
                    text = " ".join([paper.get("title", ""), paper.get("summary", ""), *chunks])[:250_000]
                if not text.strip():
                    raise ValueError("请提供 text 或 paper_id。")
                limit = min(max(int(payload.get("limit", 12)), 1), 30)
                self._json({"api_version": KEYWORDS.api_version, "provider": KEYWORDS.provider, "keywords": KEYWORDS.extract(text, limit)})
                return

            pdf_bytes, filename, fields = self._read_upload()
            result = ingest_pdf(pdf_bytes, filename, fields)
            AGENT.reload()
            self._json(result, HTTPStatus.CREATED if result.get("created") else HTTPStatus.OK)
        except (ValueError, TypeError, json.JSONDecodeError, RuntimeError) as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def _serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in ("", "/") else unquote(request_path.lstrip("/"))
        target = (STATIC / relative).resolve()
        if STATIC.resolve() not in target.parents and target != STATIC.resolve():
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = target.read_bytes()
        mime, _ = mimetypes.guess_type(target.name)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", (mime or "application/octet-stream") + ("; charset=utf-8" if mime and mime.startswith("text/") else ""))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Battery Evidence Lab")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--public-api", action="store_true", help="allow authenticated access through an HTTPS tunnel")
    parser.add_argument("--allowed-origin", action="append", default=[], help="browser origin allowed to call the API")
    args = parser.parse_args()

    token = os.environ.get("BATTERY_AGENT_ACCESS_TOKEN", "").strip()
    if args.public_api and len(token) < 16:
        parser.error("--public-api requires BATTERY_AGENT_ACCESS_TOKEN with at least 16 characters")

    server = BatteryHTTPServer((args.host, args.port), Handler)
    server.public_api = args.public_api
    server.access_token = token
    server.allowed_origins = set(args.allowed_origin or [DEFAULT_ALLOWED_ORIGIN])
    print(f"Battery Evidence Lab: http://{args.host}:{args.port}")
    if args.public_api:
        print("Tunnel API mode: enabled; PDF viewing and Zotero links remain loopback-only.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
