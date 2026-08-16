"""Command-half lock on OFN: there is no command HTTP surface.

Unauthenticated /api/* falls through to the principal check and returns
401. That 401 is an auth trap — it must not be read as “a command API
exists and refused us” or rewritten as healthy. Public observation is
GET /healthz only.

These tests do not start a listener.
"""
from __future__ import annotations

import os
import unittest

from ofn.adapters.http_api import ApiApp, HostMap
from ofn.kernel.domain import PackSpec, TenantId
from ofn.kernel.tenancy import TenantRegistry

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTTP_API = os.path.join(ROOT, "ofn", "adapters", "http_api.py")

_ABSENT_ROUTES = (
    "/api/v1/command",
    "/api/v1/brain/ask",
)


def _app() -> ApiApp:
    registry = TenantRegistry({
        "ziman": PackSpec(tenant=TenantId("ziman"),
                          capacity_units_per_week=6, quota_share=1.0),
    })
    return ApiApp(
        registry,
        HostMap(tenants={"z.test": "ziman"}, owner_host="panel.test"),
        bot_tokens={},
        session_secret="s",
        owner_user_ids=(),
        partner_user_ids={},
        now=lambda: 1_785_000_000,
    )


class TestCommandSurfaceAbsent(unittest.TestCase):
    def setUp(self):
        with open(HTTP_API, encoding="utf-8") as fh:
            self.src = fh.read()
        self.app = _app()

    def test_source_has_no_command_routes(self):
        for route in _ABSENT_ROUTES:
            self.assertNotIn(f'path == "{route}"', self.src)
            self.assertNotIn(f"path == '{route}'", self.src)
            self.assertNotIn(f'path.startswith("{route}")', self.src)

    def test_unauthenticated_api_is_the_401_trap(self):
        """401 means not logged in, not ‘command endpoint ready’."""
        for route in _ABSENT_ROUTES:
            for method in ("GET", "POST"):
                resp = self.app.handle(
                    method, route, {"host": "z.test"}, b"")
                self.assertEqual(resp.status, 401, (method, route, resp.status))
                self.assertNotEqual(resp.status, 200)
                body = resp.body if isinstance(resp.body, dict) else {}
                self.assertEqual(body.get("error"), "unauthorised")

    def test_healthz_is_the_public_pin_not_api(self):
        resp = self.app.handle("GET", "/healthz", {"host": "z.test"}, b"")
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.body, {"ok": True})

    def test_healthz_is_content_free_on_every_leg_host(self):
        """G5: public liveness is 200 + {ok:true} only. No auth, no PII."""
        for host in (
            "ziman.master-painting.com",
            "lead.master-painting.com",
            "studio.master-painting.com",
            "panel.master-painting.com",
        ):
            resp = self.app.handle("GET", "/healthz", {"host": host}, b"")
            self.assertEqual(resp.status, 200, host)
            self.assertEqual(resp.body, {"ok": True}, host)
            self.assertEqual(set(resp.body), {"ok"}, host)


if __name__ == "__main__":
    unittest.main()
