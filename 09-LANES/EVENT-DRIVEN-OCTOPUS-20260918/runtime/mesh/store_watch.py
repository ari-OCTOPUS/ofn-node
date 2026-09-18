#!/usr/bin/env python3
"""store_watch.py v2 — چشمِ فروشگاه زیمان روی ۱۳۸ (EVENT-DRIVEN-OCTOPUS 2026-09-18).

هر اجرا: DNS/HTTP دامنه + سفارش‌ها + اسنپ‌شات موجودی محصولات → state/ziman/store-watch.json
+ رسید فشرده. اولین سفارشِ واقعیِ پرداخت‌شده ⇒ FIRST-ORDER-MARKER.json (قرارداد لپ‌تاپ).

v2 (additive): همین تابع‌ها حالا رویداد دامنه هم emit می‌کنند —
  order_seen (سفارش جدید) · payment_seen (financial_status=paid/partially_paid) ·
  stock_changed (تغییر موجودی هر محصول نسبت به اسنپ‌شات قبلی).
اسنپ‌شات سفارش‌ها در state/ziman/seen-orders.json نگه داشته می‌شود (idempotent).
هیچ PII مشتری روی باس نمی‌رود: فقط order_id/total/status/تعداد آیتم.

fail-closed: خطا در JSON ثبت می‌شود، نه سکوت. stdlib فقط.
"""
import json
import pathlib
import socket
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

MESH = pathlib.Path.home() / "octopus-mesh"
STATE = MESH / "state" / "ziman"
RECEIPTS = MESH / "receipts"
MARKER = STATE / "FIRST-ORDER-MARKER.json"
OUT = STATE / "store-watch.json"
SEEN_ORDERS = STATE / "seen-orders.json"
STOCK_SNAP = STATE / "stock-snapshot.json"
PRODUCT_URL = ("https://ziman-gift.myshopify.com/products/"
               "kitty-bubble-balloon-gift-box-with-pink-roses-and-chocolates")
DOMAIN = "ziman-gift.com.au"
API = "https://ziman-gift.myshopify.com/admin/api/2026-04"

sys.path.insert(0, "/home/ari/ofn/tools")
try:
    import octopus_events as _oe
except Exception:  # noqa: BLE001 — bus missing must not stop the store sensor
    _oe = None

EMITTED = []


def _emit(kind, item_id, payload):
    if _oe is None:
        return
    try:
        ev = _oe.emit(kind, item_id, payload)
        EMITTED.append({"kind": kind, "item_id": item_id, "event_id": ev["event_id"]})
    except Exception as exc:  # noqa: BLE001
        EMITTED.append({"kind": kind, "item_id": item_id, "error": type(exc).__name__})


def token():
    for ln in (pathlib.Path.home() / ".config/ofn/secrets.env").read_text().splitlines():
        if ln.startswith("OFN_SHOPIFY_ADMIN_TOKEN="):
            return ln.split("=", 1)[1].strip().strip('"')
    return ""


def _get(path, tok):
    req = urllib.request.Request(API + path, headers={"X-Shopify-Access-Token": tok})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())


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


def _load_json(p, default):
    try:
        return json.loads(p.read_text())
    except Exception:  # noqa: BLE001
        return default


def orders_check():
    tok = token()
    if not tok:
        return {"ok": False, "err": "NO_TOKEN"}
    try:
        orders = _get("/orders.json?limit=25&status=any", tok).get("orders", [])
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
    # ---- v2: new-order events (idempotent via seen-orders.json) -------------
    seen = _load_json(SEEN_ORDERS, {"ids": []})
    if not isinstance(seen, dict):
        seen = {"ids": []}
    known = set(str(i) for i in seen.get("ids", []))
    new_paid, new_any = [], []
    for o in paid:
        oid = str(o.get("id"))
        if oid not in known:
            new_paid.append(o)
    for o in orders:
        oid = str(o.get("id"))
        if oid not in known:
            new_any.append(o)
    for o in new_any:
        _emit("order_seen", str(o.get("id")),
              {"total": o.get("total_price"), "financial_status": o.get("financial_status"),
               "created_at": o.get("created_at"), "line_items": len(o.get("line_items") or []),
               "src": "store_watch"})
    for o in new_paid:
        _emit("payment_seen", str(o.get("id")),
              {"total": o.get("total_price"), "currency": o.get("currency"),
               "financial_status": o.get("financial_status"), "src": "store_watch"})
    if new_any:
        ids = list(known | {str(o.get("id")) for o in orders})[-500:]
        SEEN_ORDERS.write_text(json.dumps({"ids": ids,
                                           "at": datetime.now(timezone.utc).isoformat()}, indent=1))
    out["new_orders"] = len(new_any)
    out["new_paid"] = len(new_paid)
    return out


def stock_check():
    """v2: product inventory snapshot -> stock_changed per changed product (no PII)."""
    tok = token()
    if not tok:
        return {"ok": False, "err": "NO_TOKEN"}
    try:
        prods = _get("/products.json?limit=250&fields=id,title,status,variants", tok).get("products", [])
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "err": type(e).__name__}
    now_snap = {}
    for p in prods:
        vs = p.get("variants") or []
        qty = sum(int(v.get("inventory_quantity") or 0) for v in vs)
        now_snap[str(p.get("id"))] = {"title": (p.get("title") or "")[:80],
                                      "status": p.get("status"), "qty": qty,
                                      "available": any(v.get("inventory_quantity", 0) > 0 for v in vs)}
    prev = _load_json(STOCK_SNAP, {})
    if not isinstance(prev, dict):
        prev = {}
    changed = []
    for pid, cur in now_snap.items():
        old = prev.get(pid)
        if old is None:
            continue  # first snapshot: baseline only, no event
        if old.get("qty") != cur.get("qty") or old.get("available") != cur.get("available"):
            changed.append({"id": pid, "title": cur["title"], "qty_from": old.get("qty"),
                            "qty_to": cur.get("qty"), "available": cur["available"]})
    for c in changed:
        _emit("stock_changed", c["id"], {"title": c["title"], "qty_from": c["qty_from"],
                                         "qty_to": c["qty_to"], "available": c["available"],
                                         "src": "store_watch"})
    STOCK_SNAP.write_text(json.dumps(now_snap, ensure_ascii=False, indent=1))
    return {"ok": True, "products": len(now_snap), "changed": len(changed),
            "for_sale": sum(1 for v in now_snap.values() if v.get("available"))}


def main():
    STATE.mkdir(parents=True, exist_ok=True)
    rec = {"schema": "store-watch.v2",
           "ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "domain": domain_check(), "orders": orders_check(), "stock": stock_check(),
           "events": EMITTED}
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
    with open(RECEIPTS / "store-watch.jsonl", "a") as fh:
        fh.write(json.dumps({"ts": rec["ts_utc"],
                             "d": rec["domain"].get("page_ok"),
                             "o": rec["orders"].get("paid_since_sep1"),
                             "first": rec["orders"].get("first_real_order"),
                             "new_o": rec["orders"].get("new_orders"),
                             "new_p": rec["orders"].get("new_paid"),
                             "stock_chg": rec["stock"].get("changed"),
                             "ev": len(EMITTED)}) + "\n")
    print(json.dumps(rec)[:400])


if __name__ == "__main__":
    main()
