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
