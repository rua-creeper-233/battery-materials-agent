"""Reject invalid lengths before reading or tokenizing a request body."""
import unittest

from finetune.serve_adapter import Handler


class NeverRead:
    def read(self, size):
        raise AssertionError(f"invalid request reached body read: {size}")


class FakeHandler:
    path = "/v1/chat/completions"
    rfile = NeverRead()

    def __init__(self, length):
        self.headers = {} if length is None else {"Content-Length": length}
        self.result = None

    def _json(self, payload, status=200):
        self.result = payload, status


class AdapterRequestLimitTests(unittest.TestCase):
    def test_invalid_lengths_do_not_read_body(self):
        for length in (None, "0", "-1", str(2 * 1024 * 1024 + 1), "invalid"):
            with self.subTest(length=length):
                handler = FakeHandler(length)
                Handler.do_POST(handler)
                payload, status = handler.result
                self.assertEqual(status, 400)
                self.assertEqual(payload["error"]["type"], "ValueError")


if __name__ == "__main__":
    unittest.main()
