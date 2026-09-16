#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""store_reply.py — پیامِ مشتریِ فروشگاه: مغز پیش‌نویس می‌دهد، هرگز سکوت، هرگز ارسالِ خودکار.

اتصالِ ۱ از CORTEX-CONNECT-ALL (بالاترین ارزشِ پول). seamِ واقعی:
  trigger  → drive_loops.sync_store_watch() (پولِ state/store-watch.json از ۱۳۸؛
             فیلدهای orders.last_order_id / first_real_order / paid_since_sep1).
             store-watch امروز فقط **سفارش** دارد، نه پیامِ متنیِ مشتری — پس event
             از نوع "order" است؛ "message" برای وقتی که مسیرِ پیامِ Shopify وصل شود.
  consumer → مالک (کارتِ متنی از باتِ درونی) + ledgerِ replies.jsonl. ارسال به مشتری
             کلاسِ Z است: فقط پس از رأیِ مالک و از مسیرِ رسیددار. این ماژول **هیچ**
             transportی به مشتری ندارد و هیچ رسیدِ تحویلی جعل نمی‌کند (sent=False).
  storage  → STATE_DIR/store/replies.jsonl (append-only، idempotent روی event_id).

قواعد: فقط از cortex/brain_link (→ model_router) · اسکرابر پیش از مغز · پاسخِ None /
بریده / خطا ⇒ قالبِ محافظه‌کارانهٔ ثابت (FALLBACK) · فیلترِ واژگانِ ممنوعه پیش از
پیشنهاد · تکرارِ رویداد ⇒ همان پیش‌نویسِ قبلی، بدونِ تماسِ دوباره.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent            # _ops/legs
for _p in (_HERE.parent, _HERE.parent / "budget", _HERE.parent / "cortex"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import opslib      # noqa: E402
import brain_link  # noqa: E402

TASK = "customer_reply"
MAX_TOKENS = 600                       # مگاپرامپت: >= 600
SCHEMA = "store_reply.v1"
SCHEMA_PROPOSED = "store_reply.v1.proposed"   # رسیدِ «کارت به مالک رفت» (نه تحویل به مشتری)
FLAG = "OCTOPUS_CONNECT_STORE_REPLY"   # پیش‌فرض خاموش؛ روشن‌کردن = تصمیمِ مالک (نه OCTOPUS_WIRE_*)


def enabled() -> bool:
    """فلگ خاموش (پیش‌فرض) = صداکننده‌های production هیچ کاری نمی‌کنند."""
    return str(os.environ.get(FLAG, "") or "").strip().lower() in ("1", "true", "yes", "on")
FALLBACK = ("Thanks for your order and your message — we've received it and will "
            "reply within a few hours (Australian time).")
# واژگانِ ممنوعه: هیچ وعدهٔ مالی/فوریت/کانالِ پرداختِ خارج از فروشگاه. override با env (CSV).
_DEFAULT_FORBIDDEN = ("guarantee", "refund now", "free money", "wire transfer", "crypto",
                      "urgent", "act now", "password", "bank details", "gift card")
_SYSTEM = ("You draft short, warm, honest customer-service replies for a small Australian "
           "gift store (Ziman). Never promise refunds, discounts, delivery dates or anything "
           "you cannot verify. Never ask for payment details. Plain English, max 120 words. "
           "If unsure, say a human will follow up.")


def forbidden_words() -> tuple[str, ...]:
    raw = os.environ.get("OCTOPUS_STORE_REPLY_FORBIDDEN", "")
    extra = tuple(w.strip().lower() for w in raw.split(",") if w.strip())
    return _DEFAULT_FORBIDDEN + extra


def _ledger_path() -> Path:
    return opslib.STATE_DIR / "store" / "replies.jsonl"


def _sha(s) -> str:
    return hashlib.sha256(str(s or "").encode("utf-8")).hexdigest()[:16]


def _rows() -> list[dict]:
    p = _ledger_path()
    if not p.exists():
        return []
    out = []
    for ln in p.read_text("utf-8", errors="replace").splitlines():
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if isinstance(d, dict):
            out.append(d)
    return out


def _existing(event_id: str) -> dict | None:
    last = None
    for d in _rows():
        if d.get("schema") == SCHEMA and d.get("event_id") == event_id:
            last = d
    return last


def _prompt(event: dict) -> str:
    kind = str(event.get("kind") or "order")
    lines = [f"Event kind: {kind}.",
             f"Order id: {event.get('order_id') or 'n/a'}."]
    items = event.get("items")
    if isinstance(items, list) and items:
        lines.append("Items: " + ", ".join(str(i)[:60] for i in items[:6]) + ".")
    if event.get("customer_name"):
        lines.append(f"Customer first name: {str(event['customer_name'])[:40]}.")
    txt = str(event.get("customer_text") or "").strip()
    if txt:
        lines.append("Customer wrote:\n" + txt[:1500])
    else:
        lines.append("No customer text; write a brief order acknowledgement.")
    lines.append("Write the reply only, no subject line, no placeholders.")
    return "\n".join(lines)


def check_forbidden(text: str) -> list[str]:
    low = str(text or "").lower()
    return [w for w in forbidden_words() if w in low]


def draft_reply(event: dict, *, ask_fn=None, now=None) -> dict:
    """پیش‌نویسِ پاسخ برای یک رویدادِ فروشگاه. همیشه dict، همیشه یک reply_text (مغز یا قالب).
    خروجی ذخیره می‌شود؛ sent همیشه False است — ارسال کارِ این ماژول نیست."""
    event = dict(event or {})
    event_id = str(event.get("event_id") or "").strip()
    if not event_id:
        return {"ok": False, "reason": "missing-event_id", "schema": SCHEMA}
    prev = _existing(event_id)
    if prev is not None:
        return {**prev, "replayed": True}

    r = brain_link.ask_brain(TASK, _prompt(event), system=_SYSTEM,
                             max_tokens=MAX_TOKENS, ask_fn=ask_fn, now=now)
    fallback, reason = False, ""
    text = str(r.get("text") or "").strip() if r.get("ok") else ""
    if not text:
        fallback, reason, text = True, str(r.get("reason") or "no-text"), FALLBACK
    else:
        bad = check_forbidden(text)
        if bad:
            fallback, reason, text = True, "forbidden-word:" + ",".join(bad)[:60], FALLBACK
    row = {"ts": opslib.now_iso(), "schema": SCHEMA, "event_id": event_id,
           "kind": str(event.get("kind") or "order")[:16],
           "order_id": str(event.get("order_id") or "")[:40],
           "customer_text_sha": _sha(event.get("customer_text")),   # متنِ مشتری ذخیره نمی‌شود
           "task": TASK, "ok": bool(r.get("ok")), "fallback": fallback, "reason": reason,
           "model": str(r.get("model") or "")[:40] if r.get("ok") else "",
           "reply_text": text, "reply_sha": _sha(text),
           "sent": False, "delivery": None,        # هرگز از این ماژول True نمی‌شود
           "production_authorized": False}
    try:
        opslib.append_jsonl(_ledger_path(), row)
    except Exception:  # noqa: BLE001 — لجر هرگز پاسخ را نمی‌کشد
        pass
    return row


def owner_card(row: dict) -> str:
    """کارتِ متنیِ مالک (بدونِ دکمهٔ callback: هر verbِ تازه بدونِ handler روی روترِ
    باتِ درونی = دکمهٔ مرده — درسِ mr:know). تصمیمِ ارسال: کارتِ یک‌تصمیمیِ مالک."""
    import html as _h
    src = "قالبِ ثابت (مغز جواب نداد: " + _h.escape(str(row.get("reason") or "")) + ")" \
        if row.get("fallback") else "مغز (" + _h.escape(str(row.get("model") or "?")) + ")"
    return ("🛍 <b>پیش‌نویسِ پاسخ به مشتری</b>\n"
            f"▸ رویداد: {_h.escape(str(row.get('kind')))} · سفارش {_h.escape(str(row.get('order_id') or '—'))}\n"
            f"▸ منبع: {src}\n\n"
            f"{_h.escape(str(row.get('reply_text') or ''))}\n\n"
            "<i>ارسال به مشتری فقط با رأیِ تو (کلاس Z). هنوز چیزی فرستاده نشده.</i>")


def propose(row: dict, channel) -> bool:
    """کارت را به مالک می‌دهد — از کانالی که خودش رسید می‌نویسد (send_text).
    خروجی = آیا کانال پذیرفت. هیچ فیلدِ sent/delivery در لجر تغییر نمی‌کند."""
    if channel is None or not getattr(channel, "wired", False):
        return False
    try:
        return bool(channel.send_text(owner_card(row), stream="store"))
    except Exception:  # noqa: BLE001
        return False


def pending_for_owner() -> list[dict]:
    """پیش‌نویس‌هایی که هنوز کارتشان به مالک نرفته (ردیفِ SCHEMA بدونِ ردیفِ proposed)."""
    proposed = {d.get("event_id") for d in _rows() if d.get("schema") == SCHEMA_PROPOSED}
    seen, out = set(), []
    for d in _rows():
        if d.get("schema") != SCHEMA:
            continue
        eid = d.get("event_id")
        if eid in proposed or eid in seen:
            continue
        seen.add(eid)
        out.append(d)
    return out


def propose_pending(channel, *, limit: int = 3) -> dict:
    """consumerِ واقعیِ کارتِ مالک — از حلقهٔ epoch ِ organism (جایی که _chan هست) صدا زده
    می‌شود، پشتِ enabled(). هر پیش‌نویس فقط یک‌بار کارت می‌گیرد (رسیدِ proposed، append-only).
    کارتِ رفته به مالک ≠ تحویل به مشتری؛ sent همچنان False می‌ماند."""
    out = {"proposed": 0, "skipped": 0, "enabled": enabled()}
    if not enabled():
        return out
    for row in pending_for_owner()[:max(0, int(limit))]:
        if propose(row, channel):
            try:
                opslib.append_jsonl(_ledger_path(), {
                    "ts": opslib.now_iso(), "schema": SCHEMA_PROPOSED,
                    "event_id": row.get("event_id"), "task": TASK,
                    "reply_sha": row.get("reply_sha"), "channel": "inner"})
                out["proposed"] += 1
            except Exception:  # noqa: BLE001 — بدونِ رسید، دفعهٔ بعد دوباره پیشنهاد می‌شود (تکرار > گم‌شدن)
                out["skipped"] += 1
        else:
            out["skipped"] += 1
    return out


def event_from_store_watch(prev: dict | None, cur: dict) -> dict | None:
    """از دو snapshotِ store-watch.json یک رویدادِ سفارشِ جدید می‌سازد (یا None).
    این همان seamِ drive_loops.sync_store_watch است؛ این‌جا فقط تابعِ خالص."""
    try:
        o_prev = ((prev or {}).get("orders") or {}) if isinstance(prev, dict) else {}
        o_cur = (cur or {}).get("orders") or {}
        oid = o_cur.get("last_order_id")
        if not oid or oid == o_prev.get("last_order_id"):
            return None
        return {"event_id": f"order:{oid}", "kind": "order", "order_id": str(oid),
                "customer_text": None, "created": o_cur.get("last_created")}
    except Exception:  # noqa: BLE001
        return None
