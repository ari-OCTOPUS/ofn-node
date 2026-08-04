"""Each shell must actually be served, on its own port, with the right file.

This exists because the API was correct for a whole phase while nothing was
visible to any partner — the HTML was never wired to a listener. An API that
answers and a screen that renders are two separate claims, and only the second
one is what a partner experiences.
"""

from __future__ import annotations

import json
import os
import threading
import time
import unittest
import urllib.request

from ofn import config
from ofn.adapters.http_api import ApiApp, HostMap, serve
from ofn.kernel.domain import PackSpec, TenantId
from ofn.kernel.tenancy import TenantRegistry

WEB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")


class TestWebAssets(unittest.TestCase):
    def test_all_four_shells_exist(self):
        for name in ("ziman.html", "lead.html", "studio.html", "panel.html"):
            with self.subTest(shell=name):
                path = os.path.join(WEB_DIR, name)
                self.assertTrue(os.path.exists(path), f"{name} is missing")
                self.assertGreater(os.path.getsize(path), 5000)

    def test_every_shell_is_rtl_and_utf8(self):
        """A Persian page without an explicit charset renders as mojibake —
        this happened once already on the real device."""
        for name in ("ziman.html", "lead.html", "studio.html", "panel.html"):
            with self.subTest(shell=name):
                src = open(os.path.join(WEB_DIR, name), encoding="utf-8").read()
                self.assertIn('charset="utf-8"', src)
                self.assertIn('dir="rtl"', src)
                self.assertIn('lang="fa"', src)

    def test_partner_shells_carry_the_api_connector(self):
        for name in ("ziman.html", "lead.html", "studio.html"):
            with self.subTest(shell=name):
                src = open(os.path.join(WEB_DIR, name), encoding="utf-8").read()
                self.assertIn("OFN.connect", src)
                self.assertIn("telegram-web-app.js", src)

    def test_shells_do_not_keep_business_state_in_the_browser(self):
        """State lives in the ledger, not in a browser. A partner switching
        phones must see the same thing.

        One narrow exception, added deliberately 2026-08-04: the half-typed
        new-piece form autosaves to `localStorage` under a single key. That is
        not business state — it is an unfinished sentence. It has never been
        sent anywhere, no ledger entry describes it, and losing it by picking
        up a different phone is the correct outcome rather than a bug.

        The rule the exception must not weaken: anything that HAS been saved
        is read back from the node, so two phones always agree. Hence the
        allowance is one key, in one shell, and the session token is still
        never written anywhere a page reload could find it.
        """
        allowed = {"ziman.html": {"ziman.draft.v1"}}
        for name in ("ziman.html", "lead.html", "studio.html", "panel.html"):
            with self.subTest(shell=name):
                src = open(os.path.join(WEB_DIR, name), encoding="utf-8").read()
                self.assertNotIn("sessionStorage", src)
                keys = allowed.get(name, set())
                if not keys:
                    self.assertNotIn("localStorage", src)
                    continue
                for key in keys:
                    self.assertIn(key, src)
                # Whatever is stored, it is not the session and not a record.
                for forbidden in ("session", "token", "authorization",
                                  "products", "sku"):
                    self.assertNotIn(f"localStorage.setItem('{forbidden}",
                                     src.lower())


class TestServedOverHttp(unittest.TestCase):
    PORT = 8877

    @classmethod
    def setUpClass(cls):
        packs = {"ziman": PackSpec(tenant=TenantId("ziman"),
                                   capacity_units_per_week=6, quota_share=1.0)}
        app = ApiApp(TenantRegistry(packs),
                     HostMap(tenants={"z.test": "ziman"}),
                     bot_tokens={"ziman": "t"}, session_secret="s",
                     now=lambda: 1_785_000_000)
        html = open(os.path.join(WEB_DIR, "ziman.html"), "rb").read()
        cls.server = serve(app, cls.PORT, static={"/index.html": html})
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def get(self, path):
        req = urllib.request.Request(f"http://127.0.0.1:{self.PORT}{path}",
                                     headers={"Host": "z.test"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.read(), dict(r.headers)

    def test_root_serves_the_shell(self):
        code, body, headers = self.get("/")
        self.assertEqual(code, 200)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn("charset=utf-8", headers["Content-Type"])
        self.assertIn("ملیحه".encode(), body)

    def test_persian_survives_the_wire(self):
        """Bytes in, bytes out — no re-encoding anywhere in the path."""
        _, body, _ = self.get("/")
        self.assertIn("چند تا".encode("utf-8"), body)

    def test_api_still_works_alongside_static(self):
        code, body, _ = self.get("/healthz")
        self.assertEqual(code, 200)
        self.assertTrue(json.loads(body)["ok"])

    def test_nosniff_header_is_set(self):
        _, _, headers = self.get("/")
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")


class TestPortMapping(unittest.TestCase):
    def test_each_shell_has_its_own_port(self):
        cfg = config.load()
        ports = [cfg.ports[k] for k in ("ziman", "lead", "studio", "owner")]
        self.assertEqual(len(set(ports)), 4, "shells must not share a port")

    def test_ports_avoid_the_reserved_range(self):
        """8770 and 8780 belong to services already on this board."""
        cfg = config.load()
        for name, port in cfg.ports.items():
            with self.subTest(shell=name):
                self.assertNotIn(port, (8770, 8780))


if __name__ == "__main__":
    unittest.main()
