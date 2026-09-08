#!/usr/bin/env python3
"""three_role.py — MP-CAPABILITY-GAP-01 G-1: مأموریت‌یابِ سه‌نقشیِ واقعی.

Director (مغز: انتخاب) → Executor (کد: اجرای قطعی) → Evaluator (کد: بازخوانی + مغز: تفسیر)
→ Director (مغز: حکم نهایی yes/no/unclear).

اصل طراحی (ADR-050 / ACD-01..07): مغزِ ضعیف هرگز کارِ ساختاری نمی‌گیرد.
هر خروجیِ مغز ساختاراً اعتبارسنجی می‌شود؛ نامعتبر = fallback قطعی (fail-closed).
هیچ инфrastructure جدیدی ساخته نمی‌شود: event_spine برای رویدادها، local_llm برای مغز،
capability_router برای مسیریابی — همهٔ موجود.

Usage:
  python three_role.py --json            # run one full cycle
  python three_role.py --mission shelf_check_zm_gallery_0013 --json
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
STATE = _HERE / "state"   # MP-CONNECT-ALL-01: state/store-watch.json (از چشمِ ۱۳۸)
for _p in (str(_HERE), str(_HERE / "cortex"), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import event_spine          # noqa: E402 — UNIFY spine (رویدادها)
import local_llm            # noqa: E402 — مغزِ محلی $0 (qwen2.5:1.5b)
from tools.capability_router import route  # noqa: E402 — ADR-050 مسیریاب

RECEIPTS = Path(r"F:\backup\09-LANES\MP-CAPABILITY-GAP-01-20260907\evidence\three-role-receipts.jsonl")

SHELF_URL = ("https://ziman-gift.com/products/"
             "kitty-bubble-balloon-gift-box-with-pink-roses-and-chocolates")
SHOP_DOMAIN = "ziman-gift.myshopify.com"
# expectation source: 07-HANDOFF/CHECKOUT1-READY-20260906.md (repo level-2 evidence)
EXPECT = {
    "title_tokens": ["Kitty", "Bubble"],
    "price_text": "$45.00",
    "cart_text": "Add to cart",
    "shipping_tokens": ["$20"],
    "desc_tokens": ["chocolates"],
}
OUT_OF_STOCK_MARKERS = ("Sold out", "sold out", "Unavailable")


# ── Executor ابزارها (کدِ قطعی، هرگز مغز) ─────────────────────────────────

def _fetch(url: str, headers: dict | None = None, timeout: int = 25) -> dict:
    req = urllib.request.Request(url, headers={
        "User-Agent": "OCTOPUS-three-role/1.0 (receipt-backed mission runner)"})
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", errors="replace")
            return {"ok": True, "status": r.status, "ms": int((time.time() - t0) * 1000),
                    "body": body, "sha256": hashlib.sha256(body.encode()).hexdigest()[:16],
                    "bytes": len(body)}
    except Exception as e:  # noqa: BLE001 — fail-soft، ابزار هرگز می‌کشد
        return {"ok": False, "err": f"{type(e).__name__}: {e}"[:200],
                "ms": int((time.time() - t0) * 1000)}


def _shopify_token() -> str:
    import os
    tok = os.environ.get("OFN_SHOPIFY_ADMIN_TOKEN", "").strip()
    if tok:
        return tok
    p = Path.home() / ".config" / "ofn" / "secrets.env"
    try:
        for ln in p.read_text(encoding="utf-8").splitlines():
            if ln.startswith("OFN_SHOPIFY_ADMIN_TOKEN="):
                return ln.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""


# ── مأموریت‌ها (هر سه واقعی، فقط‌خواندن، بدون ارسال بیرونی) ───────────────

def m_shelf_check() -> dict:
    """G-3: زیمان ZM-GALLERY-0013 روی قفسه است و قیمتش درست است؟
    منبعِ مرجع: products.json (API عمومی Shopify)؛ به‌علاوه چکِ دسترسیِ دامنهٔ مشتری."""
    # 1) دامنهٔ سفارشیِ مشتری باید resolve شود (وگرنه هیچ مشتری‌ای صفحه را باز نمی‌کند)
    import socket
    try:
        socket.getaddrinfo("ziman-gift.com", 443)
        dom_ok = True
    except OSError:
        dom_ok = False
    # 2) دادهٔ مرجعِ محصول از API عمومی (redirect نمی‌خورد)
    f = _fetch("https://ziman-gift.myshopify.com/products.json?limit=250")
    if not f.get("ok"):
        return {"fetch": f, "checks": [
            {"check": "customer_domain_resolves", "pass": dom_ok,
             "expectation": "ziman-gift.com در DNS باشد"}],
            "note": "products.json unreachable — product checks ABSTAIN"}
    prods = json.loads(f["body"]).get("products", [])
    hit = [p for p in prods if any(
        (v.get("sku") == "ZM-GALLERY-0013") for v in p.get("variants", []))]
    p = hit[0] if hit else {}
    v = (p.get("variants") or [{}])[0]
    checks = [
        ("customer_domain_resolves", dom_ok, "ziman-gift.com در DNS باشد (صفحهٔ مشتری)"),
        ("api_200", f.get("status") == 200, "products.json پاسخ ۲۰۰"),
        ("product_on_shelf", bool(hit), "SKU ZM-GALLERY-0013 در کاتالوگ"),
        ("price_45_aud", str(v.get("price")) == "45.00", "قیمت 45.00 AUD"),
        ("variant_available", v.get("available") is True, "قابل‌خرید (available)"),
        ("images_present", len(p.get("images", [])) >= 1, "حداقل یک تصویر"),
        ("title_matches", "Kitty" in str(p.get("title", "")), "عنوان Kitty"),
    ]
    return {"fetch": {"status": f.get("status"), "catalog_size": len(prods),
                      "sha256": f.get("sha256")},
            "product": {"id": p.get("id"), "title": p.get("title"),
                        "sku": v.get("sku"), "price": v.get("price"),
                        "available": v.get("available"),
                        "updated_at": p.get("updated_at")},
            "checks": [{"check": c, "pass": bool(p_) if p_ is not None else None,
                        "expectation": e} for c, p_, e in checks],
            "observed_url": "https://ziman-gift.myshopify.com/products.json"}


def m_checkout1_order_check() -> dict:
    """CHECKOUT-1: آیا سفارشِ تستِ مالک در Shopify افتاده؟ فقط‌خواندن."""
    tok = _shopify_token()
    if not tok:
        return {"fetch": {"ok": False, "err": "NO_TOKEN"},
                "checks": [{"check": "orders_readable", "pass": None,
                            "expectation": "توکن ادمین Shopify موجود باشد"}],
                "note": "ABSTAIN — بدون توکن ادعا نمی‌شود"}
    f = _fetch(f"https://{SHOP_DOMAIN}/admin/api/2026-04/orders.json?limit=10&status=any",
               headers={"X-Shopify-Access-Token": tok})
    if not f.get("ok"):
        return {"fetch": {"ok": False, "err": f.get("err", "")},
                "checks": [{"check": "orders_readable", "pass": None,
                            "expectation": "API پاسخ ۲۰۰ بدهد"}]}
    orders = json.loads(f["body"]).get("orders", [])
    hit = [o for o in orders if any(
        ln.get("sku", "").startswith("ZM-GALLERY") for ln in o.get("line_items", []))]
    checks = [
        ("api_ok", True, "orders.json خوانده شد"),
        ("any_order", bool(orders), "حداقل یک سفارش درStore"),
        ("zm_gallery_order", bool(hit), "سفارش با SKU ZM-GALLERY"),
    ]
    return {"fetch": {"status": f.get("status"), "order_count": len(orders)},
            "checks": [{"check": c, "pass": bool(p), "expectation": e} for c, p, e in checks],
            "matching_orders": [{"id": o.get("id"), "created_at": o.get("created_at"),
                                 "total": o.get("total_price")} for o in hit[:3]]}


def m_organism_liveness() -> dict:
    """beat زنده و تازه است؟ (کد، صفر مغز)"""
    p = _HERE / "state" / "ORGANISM-STATE.json"
    try:
        st = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"fetch": {"ok": False, "err": str(e)[:100]},
                "checks": [{"check": "state_readable", "pass": False,
                            "expectation": "ORGANISM-STATE.json قابل خواندن"}]}
    beat, ts = st.get("beat"), str(st.get("ts", ""))
    fresh = False
    try:
        from datetime import datetime
        tsep = datetime.fromisoformat(ts).timestamp()
        fresh = (time.time() - tsep) < 900
    except ValueError:
        pass
    checks = [
        ("beat_int", isinstance(beat, int), "beat عدد صحیح"),
        ("ts_fresh_900s", fresh, "نوشته‌شده در ۱۵ دقیقهٔ اخیر"),
    ]
    return {"fetch": {"ok": True}, "beat": beat, "ts": ts,
            "checks": [{"check": c, "pass": bool(p), "expectation": e} for c, p, e in checks]}


def m_store_order_check() -> dict:
    """MP-CONNECT-ALL-01 فاز C: وضعیت فروشگاه از چشمِ ۱۳۸ (state محلی، بدون شبکه)."""
    w = json.loads((STATE / "store-watch.json").read_text(encoding="utf-8")) \
        if (STATE / "store-watch.json").exists() else {}
    dom = w.get("domain") or {}
    orders = w.get("orders") or {}
    def _age_s(ts):
        try:  # ts یو‌تی‌سی است — با timegm نه mktime (باگ منطقه‌زمانی)
            import calendar
            return time.time() - calendar.timegm(
                time.strptime(str(ts)[:19], "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            return float("inf")
    checks = [
        ("watch_fresh_6h", bool(w.get("ts_utc")) and _age_s(w.get("ts_utc")) < 21600,
         "state/store-watch.json تازه"),
        ("orders_api_ok", orders.get("ok") is True, "چشمِ ۱۳۸ به API وصل است"),
        ("domain_page_200", dom.get("page_ok") is True,
         "صفحهٔ محصول برای مشتری باز است"),
        ("first_real_order", orders.get("first_real_order") is True,
         "اولین سفارش واقعی رسیده"),
    ]
    return {"fetch": {"ok": bool(w)}, "watch": {"ts": w.get("ts_utc"),
            "paid_since_sep1": orders.get("paid_since_sep1"),
            "last_order_id": orders.get("last_order_id")},
            "checks": [{"check": c, "pass": bool(p) if p is not None else None,
                        "expectation": e} for c, p, e in checks],
            "observed_url": "state/store-watch.json (از board138 store_watch)"}


MISSIONS = {
    "shelf_check_zm_gallery_0013": {
        "title": "زیمان: ZM-GALLERY-0013 روی قفسه است و قیمت A$45 درست است (سطح فروش پول‌ساز)",
        "fn": m_shelf_check, "priority": 1,
        "executor_task_type": "presence_check"},
    "store_order_check": {
        "title": "فروشگاه: سفارش/دامنه از چشمِ ۱۳۸ — اولین VERIFIED_CASH رسیده؟ (درایو: ترسِ پولِ صفر)",
        "fn": m_store_order_check, "priority": 2,
        "executor_task_type": "timestamp_freshness"},
    "checkout1_order_check": {
        "title": "CHECKOUT-1: سفارش تستی مالک در Shopify افتاده یا نه (ریل پول)",
        "fn": m_checkout1_order_check, "priority": 3,
        "executor_task_type": "field_extraction"},
    "organism_liveness_check": {
        "title": "عملیاتی: ارگانیسم زنده است و beat تازه دارد",
        "fn": m_organism_liveness, "priority": 4,
        "executor_task_type": "timestamp_freshness"},
}


# ── OQD-H9: resume-from-archive (QD-BRIDGE-REALTESTS-20260908، GO مالک 2026-09-08) ──
# آزمون زندهٔ درسِ آزمایشگاه QD (H8): مصرف حافظهٔ مهارتِ بالغ، انتخاب والد/زمینهٔ
# بهتر می‌سازد. بازوی T = بذرِ نخبگانِ حافظهٔ معنایی در زمینهٔ مدیر؛ بازوی R = وضع موجود.
# پیش‌ثبت و آستانه‌ها: 09-LANES/QD-BRIDGE-REALTESTS-20260908/h9/study_h9.json
# قواعد MP-CONNECT-ALL-01 §0 حفظ شده: بدون فلگ، بدون دیمن، فقط همین فایل، fail-closed.

SEMANTIC_MEMORY = _HERE / "state" / "semantic_memory.jsonl"


def archive_seed(context: str, k: int = 3) -> dict:
    """نخبگانِ حافظهٔ معنایی مرتبط با زمینه: مرتب‌سازی = هم‌پوشانی توکن × salience.
    fail-closed: نبودن/خرابی فایل = بذرِ خالی، هرگز کرش، هرگز fabrication."""
    out = {"n_store": 0, "seeded": [], "digest": "", "digest_chars": 0}
    try:
        rows = [json.loads(ln) for ln in
                open(SEMANTIC_MEMORY, encoding="utf-8") if ln.strip()]
    except OSError as e:
        out["seed_error"] = f"{type(e).__name__}"
        return out
    out["n_store"] = len(rows)
    toks = __import__("re").findall(r"[a-zA-Z\u0600-\u06FF]{3,}", context.lower())
    ctx_tokens = set(toks)

    def rank(r: dict):
        g = str(r.get("gist", ""))
        rt = set(__import__("re").findall(r"[a-zA-Z\u0600-\u06FF]{3,}", g.lower()))
        overlap = len(ctx_tokens & rt)
        return (overlap > 0, overlap * 10 + float(r.get("salience") or 0.0))

    for r in sorted(rows, key=rank, reverse=True)[:k]:
        out["seeded"].append({"ts": r.get("ts"), "salience": r.get("salience"),
                              "gist": str(r.get("gist", ""))[:120],
                              "next_action": r.get("next_action")})
    out["digest"] = " | ".join(
        f"[{s['ts'][:10]} sal={s['salience']}] {s['gist']} → {s['next_action']}"
        for s in out["seeded"])
    out["digest_chars"] = len(out["digest"])
    return out


def _h9_arm(coin_key: str) -> str:
    """سکهٔ قطعی از هشِ کلید (مأموریت+ساعت) — بدون فلگ، بدون تصادفِ ذخیره‌نشده."""
    return "T" if int(hashlib.sha256(coin_key.encode()).hexdigest()[:8], 16) % 2 == 0 else "R"


# ── نقش‌ها ─────────────────────────────────────────────────────────────────

def _brain(prompt: str, system: str = "", max_tokens: int = 200) -> dict:
    """تماسِ کنترل‌شده با مغزِ محلی. خروجی همیشه ساختار دارد؛ None = مغز نبود.
    rate-limiter مغز (10s) با یک بازگشتِ صبور محترم شمرده می‌شود، نه دور زدن."""
    r = local_llm.ask(prompt, system=system, max_tokens=max_tokens)
    if (not r or not r.get("text")) and "rate" not in str(r).lower():
        time.sleep(12)  # بازگشتِ واحدِ صبور برای rate-limiter
        r = local_llm.ask(prompt, system=system, max_tokens=max_tokens)
    if not r or not r.get("text"):
        return {"ok": False, "raw": None, "err": "brain unavailable (local fail-soft)"}
    return {"ok": True, "raw": r["text"], "model": r.get("model"), "ms": r.get("ms")}


def director_pick(candidates: list[dict], context: str) -> dict:
    """نقش ۱ — مغز: انتخابِ مأموریت. اعتبارسنجی: id در رجیستری، وگرنه fallback قطعی."""
    listing = "\n".join(f"- {c['id']}: {c['title']}" for c in candidates)
    b = _brain(
        f"Context: {context}\n\nAvailable missions (pick exactly ONE id):\n{listing}\n\n"
        "Which single mission most advances revenue now? Reply with ONLY the mission id.",
        system="You are the Director of an autonomous organism. Answer with the exact id only.",
        max_tokens=40)
    pick = (b.get("raw") or "").strip().strip('`"\' .')
    valid = pick in MISSIONS and pick in {c["id"] for c in candidates}
    fallback = sorted(candidates, key=lambda c: c["priority"])[0]["id"]
    return {"role": "director_pick", "brain": b, "picked": pick if valid else fallback,
            "pick_valid": valid, "fallback_used": not valid,
            "routing": {"task": "choice_between_options",
                        "route": route("choice_between_options")}}


def executor_run(mission_id: str) -> dict:
    """نقش ۲ — کد: اجرای قطعیِ مأموریت. routing طبق ADR-050 ثبت می‌شود."""
    spec = MISSIONS[mission_id]
    t0 = time.time()
    out = spec["fn"]()
    return {"role": "executor", "mission": mission_id,
            "routing": {"task": spec["executor_task_type"],
                        "route": route(spec["executor_task_type"])},
            "duration_ms": int((time.time() - t0) * 1000), "output": out}


def evaluator_run(exec_out: dict) -> dict:
    """نقش ۳ — کد: حکمِ قطعی هر چک؛ مغز: یک جمله تفسیر. قاعدهٔ حکم fail-closed."""
    checks = exec_out["output"].get("checks", [])
    table = []
    for c in checks:
        v = "PASS" if c["pass"] is True else "FAIL" if c["pass"] is False else "ABSTAIN"
        table.append({"check": c["check"], "verdict": v})
    if any(t["verdict"] == "FAIL" for t in table):
        overall = "FAIL"
    elif any(t["verdict"] == "ABSTAIN" for t in table) or not table:
        overall = "UNKNOWN"
    else:
        overall = "PASS"
    b = _brain(
        f"Mission: {exec_out['mission']}\nCheck table: {json.dumps(table)}\n"
        f"Overall: {overall}\nOne short sentence (Persian): what does this mean for revenue?",
        system="You are the Evaluator. One sentence, max 20 words.",
        max_tokens=80)
    interp = (b.get("raw") or "").strip()
    interp_valid = bool(interp) and len(interp) <= 300
    return {"role": "evaluator",
            "routing": {"read_back": "code", "interpretation": "summarization→model"},
            "table": table, "overall": overall,
            "checks_passed": sum(1 for t in table if t["verdict"] == "PASS"),
            "checks_total": len(table),
            "brain": b, "interpretation": interp if interp_valid else None,
            "interpretation_valid": interp_valid}


def director_final(mission_id: str, ev: dict) -> dict:
    """نقش ۴ — مغز: حکم نهایی. اعتبارسنجی: enum {yes,no,unclear} وگرنه unclear."""
    b = _brain(
        f"Mission: {mission_id}\nOverall: {ev['overall']}\n"
        f"Checks passed: {ev['checks_passed']}/{ev['checks_total']}\n"
        "Is the mission goal achieved? Reply with exactly one word: yes, no, or unclear.",
        system="You are the Director. One word answer only.", max_tokens=10)
    ans = (b.get("raw") or "").strip().lower()
    valid = ans in ("yes", "no", "unclear")
    return {"role": "director_final", "brain": b,
            "final_call": ans if valid else "unclear", "call_valid": valid}


def _receipt(rec: dict) -> None:
    RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
    with open(RECEIPTS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run(mission_id: str | None = None, context: str = "") -> dict:
    """یک چرخهٔ کامل سه‌نقشی با رسید در هر مرزِ نقش."""
    run_id = event_spine.begin_run(source="three-role-g1",
                                   description=mission_id or "director auto-pick")
    t0 = time.time()
    candidates = [{"id": k, "title": v["title"], "priority": v["priority"]}
                  for k, v in MISSIONS.items()]
    # DRIVE (رأی مالک 2026-09-07): مدیر باید درایوها را حس کند — ترس/دوپامینِ رسیددار
    drive_ctx = ""
    try:
        import drive_loops
        drive_ctx = drive_loops.context_for_director()
    except Exception:  # noqa: BLE001 — درایو نباید مأموریت را بکشد
        pass
    ctx = context or (drive_ctx or
                      "VERIFIED_CASH=0; CHECKOUT-1 awaiting owner test buy; shelf must stay sellable")
    # OQD-H9 (پیش‌ثبت: QD-BRIDGE-REALTESTS-20260908/h9/study_h9.json):
    coin_key = f"{mission_id or 'auto'}:{time.strftime('%Y-%m-%dT%H')}"
    h9_arm = _h9_arm(coin_key)
    h9 = {"arm": h9_arm, "coin_key": coin_key}
    if h9_arm == "T":
        h9.update(archive_seed(ctx))
        if h9.get("digest"):
            ctx = (ctx + "\nELITE MEMORY (top-salience relevant notes from your own past):\n"
                   + h9["digest"])
    d1 = director_pick(candidates, ctx)
    chosen = mission_id or d1["picked"]
    event_spine.emit("task.started", source="three-role-g1",
                     payload={"mission": chosen, "director_pick": d1["picked"],
                              "pick_valid": d1["pick_valid"], "h9_arm": h9_arm},
                     run_id=run_id)
    ex = executor_run(chosen)
    ev = evaluator_run(ex)
    d2 = director_final(chosen, ev)
    rec = {"schema": "three-role-run.v1", "run_id": run_id, "ts_utc":
           time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "duration_ms": int((time.time() - t0) * 1000),
           "h9": h9,
           "director_pick": d1, "executor": {k: v for k, v in ex.items() if k != "output"},
           "executor_output": ex["output"], "evaluator": {k: v for k, v in ev.items()
                                                          if k != "brain"},
           "director_final": d2}
    _receipt(rec)
    event_spine.emit("task.completed", source="three-role-g1",
                     payload={"mission": chosen, "verdict": ev["overall"],
                              "checks_passed": ev["checks_passed"],
                              "checks_total": ev["checks_total"],
                              "final_call": d2["final_call"]},
                     evidence_ref=str(RECEIPTS), run_id=run_id,
                     idempotency_key=f"{run_id}:task.completed")
    event_spine.end_run(source="three-role-g1",
                        summary=f"{chosen} → {ev['overall']} → {d2['final_call']}")
    return rec


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mission", default=None, choices=list(MISSIONS))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = run(a.mission)
    print(json.dumps(r, ensure_ascii=False, indent=1 if not a.json else None))
