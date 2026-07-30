#!/usr/bin/env python3
"""tradequote_bridge.py — پلِ پیشنهادیِ lead_leg → اپ TradeQuote Local (flag-off).

دستور مالک 2026-07-20: «TradeQuote را به پای لید نقاشی اضافه کن.»
اپ (Flutter/Drift، آفلاین، روی گوشی مالک) در
`03 - Projects/Lead-نقاشی/tradequote_local/` زندگی می‌کند و در MVP هیچ API
واردکردنی ندارد (فقط backup/restore). پس «الحاق» صادقانه در این سطح یعنی:
هر draft کوتیشنِ lead_quote، وقتی فلگ روشن است، به یک بستهٔ handoff داخلی
ترجمه شود که (الف) JSONِ ماشین‌خوان با قرارداد پولیِ خود اپ (سنت صحیح، R3)
برای import آینده و (ب) متن انسان‌خوان برای تایپِ سریع مالک در اپ.

E1 خالص (نوشتن فایل داخلی در state). صفر شبکه، صفر ارسال، صفر LLM.
flag: OCTOPUS_WIRE_TRADEQUOTE (پیش‌فرض خاموش؛ خواندن strip-safe — درسِ
فاصله‌های انتهایی flags.cmd در دلتا-اسکن 2026-07-20).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_FLAG = "OCTOPUS_WIRE_TRADEQUOTE"
SCHEMA = "tradequote-handoff.v1"


def _flag_on() -> bool:
    return os.environ.get(_FLAG, "0").strip() == "1"


def _outbox_dir(state_dir=None) -> Path:
    if state_dir:
        base = Path(state_dir)
    else:
        import opslib  # lazy: تست‌ها می‌توانند state_dir صریح بدهند
        base = Path(opslib.STATE_DIR)
    return base / "legs" / "tradequote-outbox"


def _cents(aud) -> int:
    """AUD → سنتِ صحیح (قرارداد R3 اپ: پول فقط integer cents، بدون float)."""
    try:
        return int(round(float(aud) * 100))
    except (TypeError, ValueError):
        return 0


def _range_cents(v) -> dict:
    """مقادیر lead_quote بازه‌ای‌اند ([lo, hi])؛ هر دو کران حفظ می‌شود."""
    if isinstance(v, (list, tuple)) and len(v) == 2:
        return {"lo_cents": _cents(v[0]), "hi_cents": _cents(v[1])}
    return {"lo_cents": _cents(v), "hi_cents": _cents(v)}


def to_tradequote(rec: dict) -> dict:
    """نگاشتِ خالصِ recordِ `lead-quote.v1` → بستهٔ handoff سازگار با دامنهٔ اپ.

    ورودی: rec همان چیزی که create_quote persist می‌کند (qt_number، intake،
    breakdown با بازه‌ها، proposal). خروجی: dict قطعی، بدون I/O.
    """
    rec = rec if isinstance(rec, dict) else {}
    bd = rec.get("breakdown")
    bd = bd if isinstance(bd, dict) else {}
    intake = rec.get("intake")
    intake = intake if isinstance(intake, dict) else {}
    items = []
    for li in (bd.get("line_items") or []):
        if not isinstance(li, dict):
            continue
        items.append({
            "description": str(li.get("description") or li.get("label") or "item")[:200],
            "qty_milli": int(round(float(li.get("qty", 1) or 1) * 1000)) if _num(li.get("qty", 1)) else 1000,
            "unit": str(li.get("unit") or "")[:16],
            "rate": _range_cents(li.get("rate_aud")),
            "amount": _range_cents(li.get("subtotal_aud") or li.get("aud") or li.get("amount_aud")),
        })
    return {
        "schema": SCHEMA,
        "source": "octopus/lead_quote",
        "ts": rec.get("ts"),
        "qt_number": rec.get("qt_number"),
        "attribution_id": rec.get("attribution_id"),
        "customer_hint": str(rec.get("attribution_id") or "")[:64],  # اپ نامِ مشتری را خودش می‌گیرد
        "site_scope": str((intake.get("scope") or ""))[:300],
        "gst_mode": "exclusive_10pct_added",  # قرارداد lead_quote: subtotal_excl + gst
        "line_items": items,
        "totals": {
            "subtotal_excl_gst": _range_cents(bd.get("subtotal_excl_gst")),
            "gst": _range_cents(bd.get("gst")),
            "total_incl_gst": _range_cents(bd.get("total_incl_gst")),
            "max_deposit_nsw": _range_cents(bd.get("max_deposit_nsw")),
        },
        "draft_only": True,
    }


def _num(v) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def _txt(pkg: dict) -> str:
    """متن انسان‌خوان برای تایپ در اپ (فقط ارقام دلاری، بدون PII اضافه)."""
    t = pkg.get("totals") or {}

    def _rng(k):
        r = t.get(k) or {}
        lo, hi = r.get("lo_cents", 0) / 100, r.get("hi_cents", 0) / 100
        return f"${lo:,.2f}" if lo == hi else f"${lo:,.2f} – ${hi:,.2f}"

    lines = [
        f"TradeQuote handoff — {pkg.get('qt_number')}",
        f"scope: {pkg.get('site_scope') or '-'}",
        "line items:",
    ]
    for li in pkg.get("line_items") or []:
        a = li.get("amount") or {}
        lo, hi = a.get("lo_cents", 0) / 100, a.get("hi_cents", 0) / 100
        amt = f"${lo:,.2f}" if lo == hi else f"${lo:,.2f} – ${hi:,.2f}"
        lines.append(f"  - {li.get('description')}: {amt}")
    lines += [
        f"subtotal (excl GST): {_rng('subtotal_excl_gst')}",
        f"GST 10%: {_rng('gst')}",
        f"TOTAL (incl GST): {_rng('total_incl_gst')}",
        f"max NSW deposit: {_rng('max_deposit_nsw')}",
        "(draft-only handoff — در اپ وارد و نهایی کن؛ ارسال فقط دستِ مالک)",
    ]
    return "\n".join(lines)


def maybe_export(rec: dict, state_dir=None):
    """اگر فلگ روشن بود، بستهٔ handoff را atomic بنویس؛ وگرنه هیچ.

    خروجی: مسیر JSON یا None. هرگز raise نمی‌کند (fail-soft) — مسیر
    کوتیشنِ اصلی نباید هرگز به‌خاطر پل بشکند.
    """
    try:
        if not _flag_on() or not isinstance(rec, dict) or not rec.get("qt_number"):
            return None
        pkg = to_tradequote(rec)
        out = _outbox_dir(state_dir)
        out.mkdir(parents=True, exist_ok=True)
        stem = str(pkg["qt_number"]).replace("/", "-")
        try:
            import os as _og_os, sys as _og_sys
            from pathlib import Path as _OGPath
            if _og_os.environ.get("OCTOPUS_WIRE_OUTPUT_GUARD") == "1":
                _ogd = str(_OGPath(__file__).resolve().parents[1])
                if _ogd not in _og_sys.path:
                    _og_sys.path.insert(0, _ogd)
                import output_guard as _og
                _og_json = json.dumps(pkg, ensure_ascii=False, indent=1)
                for _og_nm, _og_ct in ((stem + ".tq.json", _og_json), (stem + ".txt", _txt(pkg))):
                    _og_v = _og.check_output("state/legs/tradequote-outbox/" + _og_nm, _og_ct, allow_prefixes=("state/legs/",))
                    if not _og_v.allowed:
                        return None
        except Exception:
            pass
        jpath = out / f"{stem}.tq.json"
        tmp = out / f"{stem}.tq.json.tmp"
        tmp.write_text(json.dumps(pkg, ensure_ascii=False, indent=1), "utf-8")
        os.replace(tmp, jpath)  # atomic روی ویندوز
        (out / f"{stem}.txt").write_text(_txt(pkg), "utf-8")
        return jpath
    except Exception:  # noqa: BLE001
        return None
