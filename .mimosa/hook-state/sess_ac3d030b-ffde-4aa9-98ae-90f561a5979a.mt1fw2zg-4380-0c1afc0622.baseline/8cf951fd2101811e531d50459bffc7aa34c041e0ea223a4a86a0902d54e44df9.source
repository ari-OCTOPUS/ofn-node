"""quote_cmd — `/lead` را به موتورِ قیمت‌گذاریِ آماده وصل می‌کند.

چرا لازم شد
──────────
`legs/lead_quote.py` کامل نوشته شده — `create_quote`، `revise_quote`،
`render_quote_html`، شماره‌گذاریِ QT، نسخه‌بندی — و **صفر مصرف‌کننده** داشت.
نقشهٔ راهِ Painting-OS مرحلهٔ ۱ می‌گوید «پیش‌نیاز: هیچ. فقط وایر». پس تنها چیزی
که بینِ مالک و یک کارتِ قیمتِ واقعی ایستاده بود، یک پارسر بود.

رأیِ مالک (۲۰۲۶-۰۷-۲۷): «کامل تا مرزِ ارسال» — قیمت و پیش‌نویس آماده شود و
دکمهٔ «بفرست» هم باشد، **ولی تا او نزند چیزی نرود**.

مرزها (ساختاری)
──────────────
· این ماژول هرگز ارسال نمی‌کند و هیچ effector صدا نمی‌زند؛ فقط متن و دکمه.
· دکمهٔ ارسال یک `callback_data` می‌سازد که مسیرش به **گیت‌های موجود** می‌رود؛
  خودِ ارسال کارِ این‌جا نیست.
· flag پیش‌فرض خاموش (`OCTOPUS_TG_QUOTE`).
· هیچ دادهٔ لید ذخیره یا echo نمی‌شود جز همان چیزی که مالک تایپ کرده.
"""
from __future__ import annotations

import html
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_HERE), str(_OPS), str(_OPS / "budget"), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_TG_QUOTE"

# ترتیبِ فیلدهای پایپ‌جدا — همان ترتیبی که در راهنما نشان داده می‌شود.
_FIELDS = ("scope", "size_m2", "area_type", "prep_level", "segment")

_HELP = (
    "🎨 <b>کارتِ قیمت</b>\n"
    "▸ الگو: <code>/lead شرحِ کار | متراژ | داخلی|بیرونی | آماده‌سازی | بخش</code>\n"
    "▸ مثال: <code>/lead آشپزخانه ۳خوابه | 120 | interior | standard | residential</code>\n"
    "▸ فقط دوتای اول لازم است؛ بقیه پیش‌فرض می‌گیرند.\n"
    "▸ نکنی: چیزی قیمت نمی‌خورد — این تنها راهِ کوت‌گرفتن در تلگرام است."
)


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _num(s: str) -> float:
    """عددِ فارسی یا لاتین → float. ورودیِ بی‌عدد → 0.0."""
    tr = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    import re
    m = re.search(r"\d+(?:[.,]\d+)?", str(s or "").translate(tr))
    if not m:
        return 0.0
    try:
        return float(m.group(0).replace(",", "."))
    except ValueError:
        return 0.0


def parse(text: str) -> dict:
    """`/lead …` → فیلدهای intake. خروجی: {ok, fields} یا {ok: False, why}."""
    body = str(text or "").strip()
    for pre in ("/lead", "/کوت", "/quote"):
        if body.startswith(pre):
            body = body[len(pre):]
            break
    body = body.strip()
    if not body:
        return {"ok": False, "why": "empty"}
    parts = [p.strip() for p in body.split("|")]
    scope = parts[0] if parts else ""
    size = _num(parts[1]) if len(parts) > 1 else 0.0
    if not scope or size <= 0:
        return {"ok": False, "why": "need-scope-and-size"}
    out = {"scope": scope[:300], "size_m2": size}
    if len(parts) > 2 and parts[2]:
        out["area_type"] = parts[2].lower()
    if len(parts) > 3 and parts[3]:
        out["prep_level"] = parts[3].lower()
    if len(parts) > 4 and parts[4]:
        out["segment"] = parts[4].lower()
    return {"ok": True, "fields": out}


def quote(text: str, *, leg=None, state_dir=None) -> tuple:
    """`/lead …` → (متنِ کارت، صفحه‌کلید). هرگز ارسال نمی‌کند."""
    if not enabled():
        return ("🎨 کارتِ قیمت خاموش است.\n"
                "▸ نکنی: `/lead` فقط ثبت می‌کند — فلگش را روشن کن و مرکز را ری‌استارت.", None)
    p = parse(text)
    if not p.get("ok"):
        return (_HELP, None)
    try:
        from pricing import QuoteIntake
        import lead_quote
    except Exception as e:  # noqa: BLE001
        return (f"🎨 موتورِ قیمت در دسترس نیست ({type(e).__name__}).", None)

    if leg is None:
        try:
            import wiring as _w
            leg = _w.make_lead_leg() if hasattr(_w, "make_lead_leg") else None
        except Exception:  # noqa: BLE001
            leg = None
    if leg is None:
        return ("🎨 پای لید در دسترس نیست — کوت ساخته نشد.", None)

    try:
        intake = QuoteIntake(**p["fields"])
        aid = "tg-" + opslib.now_iso().replace(":", "").replace("-", "")[:15]
        rec = lead_quote.create_quote(leg, aid, intake, state_dir=state_dir)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"quote_cmd failed: {type(e).__name__}: {e}"])
        return (f"🎨 کوت ساخته نشد ({type(e).__name__}).", None)
    if not rec.get("ok"):
        return (f"🎨 کوت ساخته نشد — {html.escape(str(rec.get('error') or '؟'))}", None)

    try:
        body = lead_quote.render_quote_html(rec)
    except Exception:  # noqa: BLE001
        body = f"📄 کوت #{html.escape(str(rec.get('qt_number') or '?'))} ساخته شد."
    body += ("\n\n<i>پیش‌نویس است — تا دکمهٔ «بفرست» را نزنی هیچ‌چیز به مشتری "
             "نمی‌رود.</i>")
    qt = str(rec.get("qt_number") or "")[:20]
    kb = [[{"text": "📤 بفرست", "callback_data": f"qt:s:{qt}"},
           {"text": "✏️ بازنگری", "callback_data": f"qt:r:{qt}"}],
          [{"text": "🐙 منو", "callback_data": "mn:menu"}]]
    return (body[:3800], kb)


def help_text() -> str:
    return _HELP


if __name__ == "__main__":   # pragma: no cover
    import json
    print(json.dumps({"flag": enabled(), "parse": parse(
        "/lead آشپزخانه ۳خوابه | ۱۲۰ | interior | standard | residential")},
        ensure_ascii=False, indent=1))
