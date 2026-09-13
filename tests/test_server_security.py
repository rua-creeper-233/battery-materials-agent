from __future__ import annotations

import unittest
from email.message import Message

from server import Handler


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


if __name__ == "__main__":
    unittest.main()
