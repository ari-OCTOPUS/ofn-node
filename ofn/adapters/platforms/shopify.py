"""Shopify adapter — commerce storefront (Ziman lane).

Default dry_run. Real Admin API product create when OFN_SHOPIFY_WIRE=1 and
OFN_SHOPIFY_ADMIN_TOKEN is set. Secrets from env at call time — never logged.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from ofn.adapters.platforms.base import (
    PublishRequest,
    PublishResult,
    RULE_DRY_RUN,
    RULE_WIRE_CLOSED,
)

API_VERSION = "2024-10"


class ShopifyAdapter:
    """Dry-run by default; live create when OFN_SHOPIFY_WIRE=1."""

    platform = "shopify"

    def __init__(self, shop_domain: str = ""):
        self.shop_domain = (shop_domain or os.environ.get("OFN_SHOPIFY_SHOP_DOMAIN") or "").strip()

    def publish(self, req: PublishRequest) -> PublishResult:
        if req.dry_run:
            return PublishResult(
                True, self.platform, req.idempotency_key, rule=RULE_DRY_RUN
            )
        if os.environ.get("OFN_SHOPIFY_WIRE", "").strip() != "1":
            return PublishResult(
                False, self.platform, req.idempotency_key, rule=RULE_WIRE_CLOSED
            )
        token = (os.environ.get("OFN_SHOPIFY_ADMIN_TOKEN") or "").strip()
        shop = self.shop_domain or (os.environ.get("OFN_SHOPIFY_SHOP_DOMAIN") or "").strip()
        if not token or not shop:
            return PublishResult(
                False, self.platform, req.idempotency_key, rule="shopify:no-credentials"
            )
        # Caption carries JSON product payload from caller when live-publishing pieces.
        try:
            payload = json.loads(req.caption) if req.caption.startswith("{") else {
                "title": req.caption or "Untitled",
                "body_html": "",
                "variants": [{"price": "0.00", "sku": req.idempotency_key}],
            }
        except json.JSONDecodeError:
            payload = {
                "title": req.caption or "Untitled",
                "body_html": "",
                "variants": [{"price": "0.00"}],
            }
        body = json.dumps({"product": payload}).encode("utf-8")
        url = f"https://{shop}/admin/api/{API_VERSION}/products.json"
        http_req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Shopify-Access-Token": token,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return PublishResult(
                False, self.platform, req.idempotency_key,
                rule=f"shopify:http-{exc.code}",
            )
        except Exception:
            return PublishResult(
                False, self.platform, req.idempotency_key, rule="shopify:network"
            )
        product = data.get("product") or {}
        external_id = str(product.get("id") or "")
        if not external_id:
            return PublishResult(
                False, self.platform, req.idempotency_key, rule="shopify:no-id"
            )
        return PublishResult(
            True, self.platform, req.idempotency_key, external_id=external_id
        )
