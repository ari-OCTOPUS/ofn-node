"""What the caller sees when a handler raises.

Before this, nothing caught an exception between `app.handle` and the socket.
`socketserver` printed a traceback and closed the connection without writing
a response, so the browser saw a network failure — and the shell, which maps
a network failure to "unreachable", told the partner the node was down.

It was not down. It was answering every other request. The one screen she
needed had a `sqlite3.OperationalError` behind it, and the message she got
sent her to check her internet.

A node that is broken must not be able to describe itself as absent.
"""

from __future__ import annotations

import json
import threading
import time
import unittest
import urllib.error
import urllib.request

from ofn.adapters.http_api import ApiApp, HostMap, Response, serve
from ofn.kernel.domain import TenantId
from ofn.kernel.tenancy import PackSpec, TenantRegistry


class Exploding(ApiApp):
    """An app whose routing raises the way a drifted schema did."""

    def handle(self, method, path, headers, body):      # noqa: D102
        if path == "/api/v1/boom":
            raise RuntimeError("no such column: price_primary_aud")
        return super().handle(method, path, headers, body)


class TestAHandlerThatRaisesStillAnswers(unittest.TestCase):
    # 8877 and 8879 are taken by the other two HTTP suites in this directory.
    PORT = 8881

    @classmethod
    def setUpClass(cls):
        packs = {"ziman": PackSpec(tenant=TenantId("ziman"),
                                   capacity_units_per_week=6, quota_share=1.0)}
        app = Exploding(TenantRegistry(packs),
                        HostMap(tenants={"z.test": "ziman"}),
                        bot_tokens={"ziman": "t"}, session_secret="s",
                        now=lambda: 1_785_000_000)
        cls.server = serve(app, cls.PORT, static={"/index.html": b"<html>"})
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def request(self, path, method="GET"):
        req = urllib.request.Request(f"http://127.0.0.1:{self.PORT}{path}",
                                     headers={"Host": "z.test"}, method=method,
                                     data=b"" if method == "POST" else None)
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()

    def test_the_connection_is_not_dropped(self):
        """The whole point. A closed socket is indistinguishable from a node
        that is not there."""
        status, _ = self.request("/api/v1/boom")
        self.assertEqual(status, 500)

    def test_the_body_says_nothing_about_the_failure(self):
        """The traceback goes to the journal, where the operator is. Column
        names and file paths do not belong on a phone."""
        _, body = self.request("/api/v1/boom")
        payload = json.loads(body)
        self.assertEqual(payload, {"error": "internal error"})
        self.assertNotIn(b"price_primary_aud", body)
        self.assertNotIn(b"sqlite", body.lower())
        self.assertNotIn(b"Traceback", body)

    def test_post_is_covered_too(self):
        status, _ = self.request("/api/v1/boom", method="POST")
        self.assertEqual(status, 500)

    def test_the_server_keeps_serving_afterwards(self):
        """One failed request must not take the other two legs with it."""
        self.request("/api/v1/boom")
        status, body = self.request("/")
        self.assertEqual(status, 200)
        self.assertEqual(body, b"<html>")

    def test_a_normal_route_is_unaffected(self):
        status, _ = self.request("/healthz")
        self.assertEqual(status, 200)


class TestResponseShape(unittest.TestCase):
    def test_the_error_response_is_json(self):
        r = Response(500, {"error": "internal error"})
        self.assertEqual(r.status, 500)
        self.assertEqual(r.body["error"], "internal error")


if __name__ == "__main__":
    unittest.main()
