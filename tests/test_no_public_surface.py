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
        """No /public, /store, /catalog, /shop route exists at all."""
        for token in ("/public", "/store", "/catalog", "/shop",
                      "/checkout", "/order"):
            self.assertNotIn(f'path == "/api/v1{token}"', self.src)
            self.assertNotIn(f'path.startswith("/api/v1{token}")', self.src)

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

    def test_no_payment_symbols(self):
        for token in ("payment", "checkout", "stripe", "paypal"):
            self.assertNotIn(token, self.src.lower())


if __name__ == "__main__":
    unittest.main()


class TestCatalogPreparedNotServed(unittest.TestCase):
    """O9: the catalog payload builder exists but nothing serves it."""

    def test_no_public_route_serves_catalog(self):
        with open(HTTP_API, encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn('"/api/v1/public/catalog"', src)
        self.assertNotIn('public_catalog', src)

    def test_catalog_payload_says_not_activated(self):
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
