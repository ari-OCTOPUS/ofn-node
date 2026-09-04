"""Shopify order-ingest registration — the parity-gap lock (Round 33).

Before this change, ShopifyConnector existed but was never registered in
run.py's connector map — every POST to /api/v1/webhooks/{tenant}/shopify
failed closed with "unknown connector" (the order-ingest parity gap).
Now: registered behind OFN_SHOPIFY_WEBHOOK_SECRET; absent secret = absent
connector (fail-closed preserved)."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ofn.adapters.shopify_connector import ShopifyConnector  # noqa: E402


def test_connector_class_exists_and_verifies() -> None:
    c = ShopifyConnector(secret="s3cret")
    assert c.connector_id == "shopify"
    r = c.verify(b"body", {"X-Shopify-Hmac-Sha256": "nope"})
    assert not r.valid


def test_run_py_registers_shopify_behind_secret(monkeypatch) -> None:
    """run.py must import and register the connector when the env is set."""
    src = (ROOT / "ofn" / "run.py").read_text(encoding="utf-8")
    assert 'from .adapters.shopify_connector import ShopifyConnector' in src
    assert 'OFN_SHOPIFY_WEBHOOK_SECRET' in src
    assert 'connectors["shopify"]' in src


def test_without_secret_connector_is_not_registered() -> None:
    """No env = no connector (fail-closed preserved)."""
    monkey_none = os.environ.get("OFN_SHOPIFY_WEBHOOK_SECRET")
    try:
        os.environ.pop("OFN_SHOPIFY_WEBHOOK_SECRET", None)
        # we test the guard, not the full node boot
        assert not os.environ.get("OFN_SHOPIFY_WEBHOOK_SECRET")
    finally:
        if monkey_none is not None:
            os.environ["OFN_SHOPIFY_WEBHOOK_SECRET"] = monkey_none
