"""funnel_cmd — مالک واقعیتِ بازار را به ارگانیسم می‌گوید (D3b).

چرا این مهم‌ترین حلقهٔ گمشده بود
────────────────────────────────
`outcomes/funnel_store.py` کاملاً نوشته شده — SQLite، append-only، fold، متریک —
و در سربرگِ خودش نوشته: «دستوراتِ مالک (`/sent /replied /meeting /won /lost
/dead`) در D3b. این store صرفاً داده‌خور/خواننده است، **صفر caller** تا wiring
بعداً.» آن wiring هرگز ساخته نشد. اسکنِ ۲۰۲۶-۰۷-۲۷ ماژول را به‌عنوان یتیم پیدا
کرد و شش ایجنتِ مستقل تأیید کردند که «نتیجهٔ بازار» نه‌تنها از تلگرام، بلکه از
**کلِ ارگانیسم** غایب است.

نتیجه‌اش این بود: ارگانیسمی که مأموریتش پول است، هیچ‌وقت نمی‌فهمید کدام لید
**برنده** شد. لید می‌ساخت، امتیاز می‌داد، پیشنهاد می‌نوشت — و بعد سکوت. هیچ
سیگنالی از واقعیت برنمی‌گشت، پس هیچ چیزی هم قابلِ یادگیری نبود.

این ماژول همان یک سیم است: مالک می‌گوید چه شد، و گفته‌اش می‌ماند.

مرزها
─────
· **صفر پول جابه‌جا نمی‌شود.** `invoice.paid` این‌جا یک **گزارش** است نه یک
  تراکنش؛ به هیچ ledger و هیچ درآمدِ تأییدشده‌ای وصل نیست.
· **صفر ارسالِ بیرونی.** هیچ‌کدام از این افعال به مشتری چیزی نمی‌فرستند.
· append-only. اشتباه با یک رویدادِ تازه اصلاح می‌شود، نه با پاک‌کردن.
· فلگ‌دار و پیش‌فرض خاموش.
"""
from __future__ import annotations

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "outcomes"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_WIRE_FUNNEL_CMD"
CARD_TITLE = "📈 قیفِ لید"

# فعلِ فارسی/انگلیسیِ مالک → رویدادِ قراردادیِ store. عمداً کوچک: هر فعلی که
# معنایش مبهم باشد، دادهٔ مبهم می‌سازد و بعد نمی‌شود از دادهٔ واقعی جدایش کرد.
VERBS = {
    "sent":     ("communication.sent", "پیام برایش رفت"),
    "replied":  ("customer.replied", "جواب داد"),
    "meeting":  ("inspection.booked", "قرارِ بازدید گذاشته شد"),
    "quote":    ("quote.sent", "قیمت فرستاده شد"),
    "won":      ("quote.won", "🎉 برنده شدیم"),
    "lost":     ("quote.lost", "از دست رفت"),
    "paid":     ("invoice.paid", "💰 پول رسید (گزارش، نه تراکنش)"),
}


def enabled() -> bool:
    import os
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _store():
    import funnel_store
    return funnel_store.FunnelStore()


def record(verb: str, lead_id: str, note: str = "") -> dict:
    """ثبتِ یک نتیجهٔ بازار. خروجی: {ok, msg}."""
    v = str(verb or "").strip().lower().lstrip("/")
    if v not in VERBS:
        return {"ok": False, "msg": f"«{v}» فعلِ شناخته‌شده‌ای نیست"}
    lid = str(lead_id or "").strip()[:64]
    if not lid:
        return {"ok": False, "msg": "شناسهٔ لید لازم است"}
    if not enabled():
        return {"ok": False, "msg": "flag-off"}
    et, label = VERBS[v]
    try:
        st = _store()
        try:
            fresh = st.record({"event_type": et, "lead_id": lid,
                               "source": "owner-telegram",
                               "payload": {"note": str(note or "")[:200]}})
        finally:
            try:
                st.close()
            except Exception:  # noqa: BLE001
                pass
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "msg": f"ثبت نشد: {type(e).__name__}"}
    return {"ok": True, "fresh": bool(fresh), "event": et,
            "msg": label + ("" if fresh else " (از قبل ثبت شده بود)")}


def handle(text: str) -> str:
    """`/won lead-123 توضیح` → کارتِ جواب. هیچ ارسالی، هیچ پولی."""
    import html
    parts = str(text or "").split()
    if not parts:
        return card()
    verb = parts[0].lstrip("/").lower()
    if verb not in VERBS:
        return card()
    if len(parts) < 2:
        return (f"📈 <b>{html.escape(VERBS[verb][1])}</b>\n"
                f"▸ شناسهٔ لید را هم بنویس: <code>/{verb} lead-123</code>\n"
                "▸ نکنی: چیزی ثبت نمی‌شود.")
    r = record(verb, parts[1], " ".join(parts[2:]))
    if not r["ok"] and r["msg"] == "flag-off":
        return ("📈 <b>قیفِ لید خاموش است</b>\n"
                "▸ چیزی ثبت نمی‌شود.\n"
                f"🔑 برای روشن‌کردنش: <code>OWNER_AUTH: ARM FLAG {FLAG}</code>")
    head = "✅" if r["ok"] else "⚠️"
    return (f"📈 {head} <b>{html.escape(r['msg'])}</b>\n"
            f"▸ لید: <code>{html.escape(parts[1][:40])}</code>\n"
            "▸ این فقط ثبتِ واقعیت است — نه پولی جابه‌جا شد نه پیامی رفت.\n"
            "▸ نکنی: هیچ.")


def card() -> str:
    """کارتِ قیف: چه می‌دانیم و چه نمی‌دانیم."""
    if not enabled():
        return ("📈 <b>قیفِ لید: خاموش</b>\n"
                "▸ نتیجهٔ بازار هیچ‌جا ثبت نمی‌شود — یعنی ارگانیسم هرگز "
                "نمی‌فهمد کدام لید برنده شد.\n"
                "▸ نکنی: همین‌طور می‌ماند.")
    try:
        st = _store()
        try:
            m = st.metrics() or {}
        finally:
            st.close()
    except Exception as e:  # noqa: BLE001
        return f"📈 قیف در دسترس نیست: {type(e).__name__}"
    counts = m.get("by_event") or m.get("counts") or {}
    won = int(counts.get("quote.won", 0) or 0)
    lost = int(counts.get("quote.lost", 0) or 0)
    paid = int(counts.get("invoice.paid", 0) or 0)
    lines = ["📈 <b>قیفِ لید</b>",
             f"▸ برده: {won} · باخته: {lost} · پول رسیده: {paid}"]
    if won + lost == 0:
        lines.append("▸ هنوز هیچ نتیجه‌ای نگفته‌ای — پس هیچ چیزی هم "
                     "قابلِ یادگیری نیست.")
    lines += ["",
              "<b>افعال:</b> " + " · ".join(f"/{v}" for v in VERBS),
              "مثال: <code>/won lead-123</code>",
              "",
              "▸ نکنی: هیچ — ثبتِ نتیجه اختیاری است، ولی بدونش قیف کور است."]
    return "\n".join(lines)


if __name__ == "__main__":   # pragma: no cover
    print(card())
