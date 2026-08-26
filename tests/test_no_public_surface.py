"""O9 — public surface: nothing is publicly reachable yet.

The safe default: no storefront, no public contact form, no anonymous
lead intake. These tests pin that the current HTTP surface exposes no
unauthenticated write routes other than the deliberate ones (auth/session,
shell/boot, webhooks — which are HMAC-gated).

If someone adds a public route, these tests force the decision into the
open instead of letting it ship silently.
"""

from __future__ import annotations

import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTTP_API = os.path.join(ROOT, "ofn", "adapters", "http_api.py")


class TestNoPublicSurface(unittest.TestCase):
    """The node must not answer anonymous business routes."""

    def setUp(self):
        with open(HTTP_API, encoding="utf-8") as fh:
            self.src = fh.read()

    def test_no_public_catalog_route(self):
        """No /store, /shop, /checkout, /order routes exist at all.
        The /public/catalog route exists but is flag-gated (404 unless
        enabled) — pinned by TestCatalogFlagGate."""
        for token in ("/store", "/shop", "/checkout", "/order"):
            self.assertNotIn(f'path == "/api/v1{token}"', self.src)
            self.assertNotIn(f'path.startswith("/api/v1{token}")', self.src)
        # The catalog route must be gated: 404 unless explicitly enabled.
        self.assertIn("_public_catalog_enabled", self.src)

    def test_no_anonymous_lead_intake(self):
        """Lead intake requires auth (partner routes)."""
        self.assertNotIn('"/api/v1/leads"', self.src)
        # Only the three deliberate anonymous POST routes may exist BEFORE
        # the principal check. Everything else must be inside the authed
        # owner/partner routers.
        pre_auth = self.src.split("principal = self._principal")[0]
        anon = re.findall(
            r'if method == "POST" and path (?:==|\.startswith\()'
            r'\s*"(/api/v1/[a-z0-9/_-]+)"', pre_auth)
        allowed_anon = {"/api/v1/auth/session", "/api/v1/shell/boot",
                        "/api/v1/webhooks/"}
        for route in anon:
            if route in allowed_anon:
                continue
            self.fail(f"unexpected anonymous POST route: {route}")

    def test_commerce_routes_are_authenticated_and_gated(self):
        """The audited-settlement route exists but is:

          - AFTER the principal check (authenticated, not anonymous), and
          - behind a default-off flag (404 until Ari enables it).

        No public payload can directly create a confirmed settlement; only a
        signed provider webhook or this authenticated audited path can.  The
        forbidden-token guard below still holds — the route uses 'settlement'
        terminology, never 'payment' or provider names.
        """
        # The route is registered and must reference the gate.
        self.assertIn('"/api/v1/owner/orders/settlements"', self.src)
        self.assertIn("_audited_settlements_enabled", self.src)
        # It must be AFTER the principal check — not in the anonymous prefix.
        pre_auth = self.src.split("principal = self._principal")[0]
        self.assertNotIn('"/api/v1/owner/orders/settlements"', pre_auth)

    def test_no_payment_symbols(self):
        for token in ("payment", "checkout", "stripe", "paypal"):
            self.assertNotIn(token, self.src.lower())


if __name__ == "__main__":
    unittest.main()


class TestCatalogPreparedNotServed(unittest.TestCase):
    """O9: the catalog payload builder exists; the route is flag-gated."""

    def test_route_is_flag_gated(self):
        with open(HTTP_API, encoding="utf-8") as fh:
            src = fh.read()
        # The route exists but only serves when _public_catalog_enabled.
        self.assertIn('path == "/api/v1/public/catalog"', src)
        self.assertIn("_public_catalog_enabled", src)

    def test_catalog_payload_matches_runtime_activation(self):
        from ofn.adapters.products import ProductStore
        from ofn.node import Node
        from ofn.adapters.ledger import Ledger
        from ofn.adapters.outbox import Outbox
        from ofn.adapters.facts import FactStore
        from ofn.kernel.domain import PackSpec, TenantId
        from ofn.kernel.quota import NodeQuota
        from ofn.kernel.tenancy import TenantRegistry
        from tests.tmpdir import temp_dir
        d = temp_dir(self)
        registry = TenantRegistry({
            "ziman": PackSpec(tenant=TenantId("ziman"),
                              capacity_units_per_week=6, quota_share=1.0)})
        node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0, shares={"ziman": 1.0}),
            ledger=Ledger(os.path.join(d, "l.sqlite")),
            facts=FactStore(os.path.join(d, "f.sqlite")),
            outbox=Outbox(os.path.join(d, "o.sqlite")),
            products=ProductStore(
                os.path.join(d, "p.sqlite"),
                cost_fields=["materials_cost_aud"],
                labour_hours_field="labour_hours",
                labour_rate_field="hourly_rate_aud"),
            now_epoch_s=lambda: 1_785_000_000,
            now_iso=lambda: "2026-08-10T12:00:00Z",
        )
        self.addCleanup(node.close)
        out = node.public_catalog()
        self.assertTrue(out["ok"])
        self.assertFalse(out["activated"])
        node.public_catalog_enabled = True
        self.assertTrue(node.public_catalog()["activated"])


class TestCatalogFlagGate(unittest.TestCase):
    """O9: the route exists but 404s until Ari enables the flag."""

    def _app(self, enabled: bool):
        from ofn.adapters.http_api import ApiApp, HostMap
        from ofn.kernel.domain import PackSpec, TenantId
        from ofn.kernel.tenancy import TenantRegistry
        registry = TenantRegistry({
            "ziman": PackSpec(tenant=TenantId("ziman"),
                              capacity_units_per_week=6, quota_share=1.0)})
        return ApiApp(
            registry,
            HostMap(tenants={"z.test": "ziman"}, owner_host="panel.test"),
            bot_tokens={},
            session_secret="s",
            owner_user_ids=(),
            partner_user_ids={},
            now=lambda: 1_785_000_000,
            public_catalog=lambda: {"ok": True, "items": [], "count": 0,
                                    "activated": True},
            public_catalog_enabled=enabled,
        )

    def test_off_by_default_404(self):
        resp = self._app(False).handle(
            "GET", "/api/v1/public/catalog",
            {"host": "z.test"}, b"")
        self.assertEqual(resp.status, 404)

    def test_on_serves(self):
        resp = self._app(True).handle(
            "GET", "/api/v1/public/catalog",
            {"host": "z.test"}, b"")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.body.get("ok"))
