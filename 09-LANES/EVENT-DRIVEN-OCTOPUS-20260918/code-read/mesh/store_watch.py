#!/usr/bin/env python3
"""store_watch.py — MP-CONNECT-ALL-01 فاز A: چشمِ فروشگاه زیمان روی ۱۳۸.
هر تیک: DNS/HTTP دامنه + سفارش‌ها (توکن فقط همین ماشین) → state/ziman/store-watch.json
+ رسید فشرده. اولین سفارشِ واقعیِ پرداخت‌شده ⇒ FIRST-ORDER-MARKER.json (قرارداد لپ‌تاپ).
fail-closed: خطا در JSON ثبت می‌شود، نه سکوت. stdlib فقط."""
import json, socket, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

MESH = Path.home() / "octopus-mesh"
STATE = MESH / "state" / "ziman"
RECEIPTS = MESH / "receipts"
MARKER = STATE / "FIRST-ORDER-MARKER.json"
OUT = STATE / "store-watch.json"
PRODUCT_URL = ("https://ziman-gift.myshopify.com/products/"
               "kitty-bubble-balloon-gift-box-with-pink-roses-and-chocolates")
DOMAIN = "ziman-gift.com.au"


def token():
    for ln in (Path.home() / ".config/ofn/secrets.env").read_text().splitlines():
        if ln.startswith("OFN_SHOPIFY_ADMIN_TOKEN="):
            return ln.split("=", 1)[1].strip().strip('"')
    return ""


def domain_check():
    try:
        socket.getaddrinfo(DOMAIN, 443)
        dns = True
    except OSError as e:
        return {"dns_ok": False, "page_ok": False, "err": type(e).__name__}
    try:
        req = urllib.request.Request(PRODUCT_URL, method="GET",
                                     headers={"User-Agent": "OCTOPUS-store-watch/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return {"dns_ok": dns, "page_ok": r.status == 200}
    except urllib.error.HTTPError as e:
        return {"dns_ok": dns, "page_ok": False, "err": "HTTP%d" % e.code}
    except Exception as e:  # noqa: BLE001
        return {"dns_ok": dns, "page_ok": False, "err": type(e).__name__}


def orders_check():
    tok = token()
    if not tok:
        return {"ok": False, "err": "NO_TOKEN"}
    try:
        req = urllib.request.Request(
            "https://ziman-gift.myshopify.com/admin/api/2026-04/orders.json?limit=25&status=any",
            headers={"X-Shopify-Access-Token": tok})
        with urllib.request.urlopen(req, timeout=25) as r:
            orders = json.loads(r.read().decode()).get("orders", [])
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "err": type(e).__name__}
    paid = [o for o in orders if (o.get("financial_status") in ("paid", "partially_paid")
            and str(o.get("created_at", "")) >= "2026-09-01")]
    out = {"ok": True, "total_fetched": len(orders), "paid_since_sep1": len(paid),
           "last_order_id": orders[0].get("id") if orders else None,
           "last_created": orders[0].get("created_at") if orders else None}
    if paid and not MARKER.exists():
        o = paid[-1]
        MARKER.write_text(json.dumps({
            "order_id": o.get("id"), "created_at": o.get("created_at"),
            "total": o.get("total_price"), "financial_status": o.get("financial_status"),
            "ts_utc": datetime.now(timezone.utc).isoformat()}, indent=1))
    out["first_real_order"] = MARKER.exists()
    return out


def main():
    STATE.mkdir(parents=True, exist_ok=True)
    rec = {"schema": "store-watch.v1",
           "ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "domain": domain_check(), "orders": orders_check()}
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
    with open(RECEIPTS / "store-watch.jsonl", "a") as fh:
        fh.write(json.dumps({"ts": rec["ts_utc"],
                             "d": rec["domain"].get("page_ok"),
                             "o": rec["orders"].get("paid_since_sep1"),
                             "first": rec["orders"].get("first_real_order")}) + "\n")
    print(json.dumps(rec)[:300])


if __name__ == "__main__":
    main()
