#!/usr/bin/env python3
"""checkout1_poll.py — after the owner's test purchase: fetch order + txn receipts.

Read-only Shopify admin API. Token from the existing store (~/.config/ofn/secrets.env
or env). Idempotent: one receipt, then ALREADY_DONE. Stdlib only.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

SECRETS = Path.home() / ".config" / "ofn" / "secrets.env"
# MP-CAPABILITY-GAP-01 G-2: رسید باید cross-platform باشد (قبلاً Linux path هاردکد بود)
if sys.platform == "win32":
    RECEIPT = Path(r"F:\backup\_ops\state\receipts\CHECKOUT1-RECEIPT.json")
else:
    RECEIPT = Path("/home/ari/ops-ign1/ops/receipts/CHECKOUT1-RECEIPT.json")
DOMAIN = "ziman-gift.myshopify.com"


def _token() -> str:
    try:
        for ln in SECRETS.read_text(encoding="utf-8").splitlines():
            if ln.startswith("OFN_SHOPIFY_ADMIN_TOKEN="):
                return ln.split("=", 1)[1].strip()
    except OSError:
        pass
    return os.environ.get("OFN_SHOPIFY_ADMIN_TOKEN", "").strip()


def _api(path: str) -> dict:
    req = urllib.request.Request(
        f"https://{DOMAIN}/admin/api/2026-04/{path}",
        headers={"X-Shopify-Access-Token": _token()})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    if RECEIPT.exists():
        print("CHECKOUT1 ALREADY_DONE")
        return 1
    if not _token():
        print("CHECKOUT1 NO_TOKEN")
        return 2
    try:
        d = _api("orders.json?limit=10&status=any")
    except Exception as e:  # noqa: BLE001
        print(f"CHECKOUT1 API_ERR {type(e).__name__}")
        return 3
    orders = sorted(d.get("orders", []),
                    key=lambda x: str(x.get("created_at") or ""), reverse=True)
    if not orders:
        print("CHECKOUT1 NO_ORDERS")
        return 3
    o = orders[0]
    txns: list[dict] = []
    try:
        t = _api(f"orders/{o['id']}/transactions.json")
        txns = [{"id": x.get("id"), "kind": x.get("kind"),
                 "status": x.get("status"), "amount": x.get("amount"),
                 "gateway": x.get("gateway")}
                for x in t.get("transactions", [])]
    except Exception as e:  # noqa: BLE001
        txns = [{"error": type(e).__name__}]
    payouts: list[dict] | str = []
    try:
        p = _api("shopify_payments/payouts.json?limit=1")
        payouts = p.get("payouts", [])
    except Exception as e:  # noqa: BLE001
        payouts = f"unavailable:{type(e).__name__}"
    rec = {
        "schema": "checkout1.receipt.v1",
        "kind": "REPORTED_NOT_VERIFIED",
        "note": "buyer=owner by design — money-path test only; not revenue",
        "order_id": o.get("id"),
        "order_number": o.get("name"),
        "total_aud": o.get("total_price"),
        "financial_status": o.get("financial_status"),
        "created_at": o.get("created_at"),
        "transactions": txns,
        "payouts": payouts,
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
    print(json.dumps(rec, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
