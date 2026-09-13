"""Tiny dependency-free local web server for the battery research agent."""

from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from agent import BatteryResearchAgent


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
LITERATURE = ROOT / "literature"
PDF_DIR = LITERATURE / "pdfs"
MANIFEST = LITERATURE / "manifest.json"
METHOD_EVIDENCE = ROOT / "data" / "method_evidence.auto.json"
AGENT = BatteryResearchAgent()


def _load_method_evidence() -> dict[str, object]:
    if not METHOD_EVIDENCE.exists():
        return {"review_status": "not_generated", "papers": {}}
    try:
        return json.loads(METHOD_EVIDENCE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"review_status": "invalid", "papers": {}}


class Handler(BaseHTTPRequestHandler):
    server_version = "BatteryEvidenceLab/0.1"

    def _json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            downloaded = 0
            if MANIFEST.exists():
                try:
                    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
                    downloaded = sum(
                        row.get("status") == "downloaded"
                        for row in manifest.get("papers", {}).values()
                    )
                except (OSError, json.JSONDecodeError):
                    pass
            methods = _load_method_evidence()
            method_rows = methods.get("papers", {})
            self._json(
                {
                    "ok": True,
                    "papers": len(AGENT.papers),
                    "downloaded_pdfs": downloaded,
                    "fulltext_papers": len({row["paper_id"] for row in AGENT.fulltext_chunks}),
                    "fulltext_chunks": len(AGENT.fulltext_chunks),
                    "method_evidence_signals": sum(
                        int(row.get("evidence_count", 0))
                        for row in method_rows.values()
                    ) if isinstance(method_rows, dict) else 0,
                }
            )
            return
        if path == "/api/papers":
            self._json({"papers": AGENT.papers})
            return
        if path == "/api/literature":
            payload: dict[str, object] = {"papers": {}}
            if MANIFEST.exists():
                try:
                    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
                    payload["updated_at"] = raw.get("updated_at")
                    payload["fulltext_index"] = raw.get("fulltext_index", {})
                    payload["papers"] = {
                        paper_id: {
                            "status": row.get("status"),
                            "local_pdf": row.get("local_pdf"),
                            "pages": (row.get("validation") or {}).get("pages"),
                            "text_chunks": (row.get("text_extraction") or {}).get("chunks"),
                        }
                        for paper_id, row in raw.get("papers", {}).items()
                    }
                except (OSError, json.JSONDecodeError):
                    pass
            self._json(payload)
            return
        if path.startswith("/api/papers/"):
            paper_id = unquote(path.removeprefix("/api/papers/"))
            paper = next((item for item in AGENT.papers if item["id"] == paper_id), None)
            self._json(paper or {"error": "paper not found"}, 200 if paper else 404)
            return
        if path == "/api/methods":
            self._json(_load_method_evidence())
            return
        if path.startswith("/api/methods/"):
            paper_id = unquote(path.removeprefix("/api/methods/"))
            payload = _load_method_evidence()
            papers = payload.get("papers", {})
            row = papers.get(paper_id) if isinstance(papers, dict) else None
            self._json(row or {"error": "method evidence not found"}, 200 if row else 404)
            return
        if path.startswith("/local-pdf/"):
            paper_id = unquote(path.removeprefix("/local-pdf/")).removesuffix(".pdf")
            known = {paper["id"] for paper in AGENT.papers}
            if paper_id not in known:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            pdf = PDF_DIR / f"{paper_id}.pdf"
            if not pdf.is_file():
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

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/chat":
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 100_000:
                raise ValueError("request too large")
            payload = json.loads(self.rfile.read(length) or b"{}")
            question = str(payload.get("question", "")).strip()
            limit = min(max(int(payload.get("limit", 5)), 1), 10)
            self._json(AGENT.answer(question, limit=limit))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
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
    import argparse

    parser = argparse.ArgumentParser(description="Run Battery Evidence Lab")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Battery Evidence Lab: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
