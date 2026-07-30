#!/usr/bin/env python3
"""introspect_cmd — چهار فرمانِ فقط‌خواندنیِ خودنگری برای تلگرام.

چرا یک ماژولِ جدا و نه چند تابع داخلِ `center.py`
────────────────────────────────────────────────
`center.py` ۱۳۰ کیلوبایت است و همین حالا دستِ یک نشستِ همزمان. هر خطی که
آن‌جا اضافه شود ریسکِ تداخل دارد. پس کلِ منطق این‌جاست و `center.py` فقط
**چهار خط** می‌گیرد — کوچک‌ترین دیفِ ممکن روی داغ‌ترین فایل.

    /flags    مسلح در برابرِ بارگذاری‌شده (flag_drift)
    /trace    پیام‌ها واقعاً کجا نشستند (tg_trace)
    /scan     نقاطِ کورِ خودشناسی (self_scan)
    /insight  فرضیه‌های رتبه‌بندی‌شده + نمرهٔ اجرای قبل (self_insight)

ناوردی‌ها: هیچ‌کدام چیزی را عوض نمی‌کنند · هر خطا به یک جملهٔ فارسی تبدیل
می‌شود نه استثنا · خروجی برای تلگرام بریده می‌شود (سقفِ ۴۰۹۶ نویسه‌ای که
`sendMessage` دارد؛ ردشدن از آن یعنی تلگرام **کلِ** پیام را ۴۰۰ می‌کند و
مالک هیچ‌چیز نمی‌بیند — همان «فرستادم ولی نرسید»ی که این‌ها برای شکارش‌اند).
"""
from __future__ import annotations

import sys
from pathlib import Path

CARD_TITLE = "خودنگری"
TG_CAP = 3500          # حاشیهٔ امن زیرِ سقفِ ۴۰۹۶ تلگرام


def _ops_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _import(name):
    root = str(_ops_root())
    if root not in sys.path:
        sys.path.insert(0, root)
    return __import__(name)


def _clip(text: str, cap: int = TG_CAP) -> str:
    text = str(text or "")
    if len(text) <= cap:
        return text
    return text[:cap - 60].rstrip() + "\n…\n(بریده شد — نسخهٔ کامل با --json روی ماشین)"


def _guard(fn, label: str) -> str:
    try:
        return _clip(fn())
    except Exception as exc:  # noqa: BLE001 — یک ابزارِ خراب نباید بات را بکشد
        return f"🚩 {label} در دسترس نیست: {type(exc).__name__}: {exc}"


# ── چهار فرمان ─────────────────────────────────────────────────────────────

def flags_text() -> str:
    def _go():
        fd = _import("flag_drift")
        root = _ops_root()
        # per-process (۲۰۲۶-۰۷-۲۹): تک‌فایل یعنی «آخرین پروسه‌ای که بوت شد» به
        # نامِ همه گزارش می‌شد. probe_all اگر snapshotی نبود، خودش به مسیرِ
        # legacy برمی‌گردد — پس این تغییر بایت‌به‌بایت امن است.
        return fd.render_all(fd.probe_all(root / "OCTOPUS-flags.cmd",
                                          root / "state"))
    return _guard(_go, "پروبِ فلگ")


def trace_text(text: str = "") -> str:
    def _go():
        tg = _import("tg_trace")
        n = next((int(p) for p in str(text).split()[1:] if p.isdigit()), 15)
        rows, stats, topics, chat = tg.trace(limit=n)
        return tg.render(rows, stats, topics, chat, limit=n)
    return _guard(_go, "ردِ ارسال")


def scan_text() -> str:
    return _guard(lambda: _import("self_scan").card(_ops_root()), "اسکنِ خودشناسی")


def insight_text() -> str:
    return _guard(lambda: _import("self_insight").card(_ops_root()), "لایهٔ بینش")


def card() -> str:
    """کارتِ خلاصه — برای کشفِ خودکار توسطِ capability_registry."""
    return ("🔎 خودنگری\n"
            "  /flags    مسلح در برابرِ بارگذاری‌شده\n"
            "  /trace    پیام‌ها کجا نشستند\n"
            "  /scan     نقاطِ کور\n"
            "  /insight  فرضیه‌ها + نمرهٔ اجرای قبل")


if __name__ == "__main__":  # pragma: no cover — اجرای دستی
    which = sys.argv[1] if len(sys.argv) > 1 else "card"
    print({"flags": flags_text, "trace": lambda: trace_text(""),
           "scan": scan_text, "insight": insight_text,
           "card": card}.get(which, card)())
