from __future__ import annotations

import unittest
import threading
from email.message import Message
from urllib.request import urlopen
from unittest.mock import patch

from server import BatteryHTTPServer, Handler


class _Config:
    public_api = True
    access_token = "test-access-token-123456"
    allowed_origins = {"https://rua-creeper-233.github.io"}


def make_handler(host: str, origin: str = "", authorization: str = "") -> Handler:
    handler = object.__new__(Handler)
    handler.server = _Config()
    handler.client_address = ("127.0.0.1", 50000)
    headers = Message()
    headers["Host"] = host
    if origin:
        headers["Origin"] = origin
    if authorization:
        headers["Authorization"] = authorization
    handler.headers = headers
    return handler


class ServerSecurityTests(unittest.TestCase):
    def test_direct_loopback_is_local_without_token(self) -> None:
        handler = make_handler("127.0.0.1:8765")
        self.assertTrue(handler._is_local_request())
        self.assertTrue(handler._authorized())

    def test_tunnel_request_is_not_mistaken_for_localhost(self) -> None:
        handler = make_handler(
            "demo.trycloudflare.com",
            "https://rua-creeper-233.github.io",
        )
        self.assertFalse(handler._is_local_request())
        self.assertFalse(handler._authorized())

    def test_tunnel_requires_exact_origin_and_bearer_token(self) -> None:
        handler = make_handler(
            "demo.trycloudflare.com",
            "https://rua-creeper-233.github.io",
            "Bearer test-access-token-123456",
        )
        self.assertTrue(handler._origin_allowed())
        self.assertTrue(handler._authorized())

        wrong_origin = make_handler(
            "demo.trycloudflare.com",
            "https://evil.example",
            "Bearer test-access-token-123456",
        )
        self.assertFalse(wrong_origin._origin_allowed())
        self.assertFalse(wrong_origin._authorized())

    def test_agent_rejects_remote_request_before_provider(self) -> None:
        handler = make_handler(
            "demo.trycloudflare.com",
            "https://rua-creeper-233.github.io",
            "Bearer test-access-token-123456",
        )
        handler.client_address = ("10.0.0.8", 50000)
        handler.path = "/api/agent"
        handler.requestline = "POST /api/agent HTTP/1.1"
        handler._json = lambda payload, status=200: setattr(handler, "response", (payload, status))
        with patch("server.run_tool_agent", side_effect=AssertionError("provider must not run")):
            handler.do_POST()
        self.assertEqual(handler.response[1], 403)
        self.assertIn("回环", handler.response[0]["error"])

    def test_public_guides_are_served_locally_from_allowlist(self) -> None:
        httpd = BatteryHTTPServer(("127.0.0.1", 0), Handler)
        httpd.public_api = False
        httpd.access_token = ""
        httpd.allowed_origins = set()
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            port = httpd.server_address[1]
            for name in ("AGENT_IMPLEMENTATION_GUIDE.md", "BATTERY_RESEARCH_ROADMAP_20260918.md"):
                with urlopen(f"http://127.0.0.1:{port}/guides/{name}", timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertGreater(len(response.read()), 100)
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
