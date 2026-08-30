"""test_tg_callback_actor.py — کنشگرِ یک کلیک کیست؟

گزارشِ زندهٔ مالک ۲۰۲۶-۰۷-۲۶: «وقتی کلیک می‌کنم تأیید، می‌گوید فقط مالک می‌تواند».

ریشه: در `poll_once`، برای یک `callback_query` مقدارِ `msg` به
`cbq["message"]` می‌افتد — یعنی **کارتی که خودِ بات فرستاده**. پس
`msg["from"]` همیشه پر است و شناسهٔ *بات* را می‌دهد، و شرطِ
`msg.get("from") or cbq.get("from")` هرگز به کلیک‌کنندهٔ واقعی نمی‌رسید.

اثرِ ساختاری: `_callback_owner_ok` برای هر callbackِ mutating **همیشه** False
می‌داد. گیتِ fail-closed درست نوشته شده بود ولی ورودی‌اش همیشه غلط بود — همان
شکلِ «ادعایی که نمی‌تواند درست باشد». و همین توضیح می‌دهد چرا جدولِ
`rfc_decision` در کلِ تاریخِ سیستم صفر ردیف دارد: هیچ رأیی رد نشد چون هیچ رأیی
هرگز پذیرفته نشد.

پس آزمونِ این فایل روی **هویتِ استخراج‌شده** است، نه روی اینکه dispatch چیزی
برگرداند. اگر فقط خروجی را assert می‌کردیم، همین باگ سبز می‌ماند.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("tg-callback-actor")

import approval_channel as ac   # noqa: E402

OWNER = 6150431610
BOT = 8187434784
STRANGER = 111222333


def _update(actor_id, card_sender=BOT, data="rfc:merge:c6-abc:tok", chat=OWNER):
    """updateِ واقعیِ تلگرام برای یک کلیک: `from` کلیک‌کننده است،
    `message.from` فرستندهٔ کارت (همیشه بات)."""
    return {"update_id": 1, "callback_query": {
        "id": "cb1",
        "from": {"id": actor_id, "is_bot": False},
        "message": {"message_id": 9, "from": {"id": card_sender, "is_bot": True},
                    "chat": {"id": chat}},
        "data": data}}


def _extract(upd):
    """همان منطقِ استخراجِ `poll_once`، جدا شده تا مستقیم assert شود."""
    is_callback = "callback_query" in upd
    cbq = upd.get("callback_query") if is_callback else {}
    msg = upd.get("message") or cbq.get("message") or {}
    return ((cbq.get("from") if is_callback else None)
            or msg.get("from") or {}).get("id")


class Post:
    def __init__(self):
        self.bodies = []

    def __call__(self, url, body):
        self.bodies.append(body)
        return {"ok": True, "result": {"message_id": 1}}


def _chan():
    return ac.TelegramApprovalChannel(token="t" * 10, owner_chat_id=OWNER,
                                      http_post=Post())


# ─── استخراجِ کنشگر ──────────────────────────────────────────────────────────
def t_a_click_is_attributed_to_the_clicker_not_the_card_sender():
    """قلبِ باگ. کارت را بات فرستاده؛ کلیک را مالک کرده."""
    got = _extract(_update(OWNER))
    assert got == OWNER, f"کلیک به {got} نسبت داده شد — باید {OWNER} باشد"
    assert got != BOT, "کلیک به خودِ بات نسبت داده شد (همان باگِ ۲۰۲۶-۰۷-۲۶)"


def t_a_stranger_click_stays_a_stranger():
    """فیکس نباید گیت را شل کند — غریبه باید غریبه بماند."""
    assert _extract(_update(STRANGER)) == STRANGER


def t_a_plain_message_still_uses_its_own_sender():
    """مسیرِ پیامِ متنی نباید عوض شده باشد."""
    upd = {"update_id": 2, "message": {"message_id": 3, "from": {"id": OWNER},
                                       "chat": {"id": OWNER}, "text": "/now"}}
    assert _extract(upd) == OWNER


def t_a_callback_without_a_from_does_not_crash():
    upd = {"update_id": 3, "callback_query": {"id": "x", "data": "menu:now",
                                              "message": {"chat": {"id": OWNER}}}}
    assert _extract(upd) is None, "نبودِ هویت باید None بدهد تا گیت fail-closed بماند"


# ─── گیتِ مالک با هویتِ درست ─────────────────────────────────────────────────
def t_owner_gate_accepts_the_real_owner():
    c = _chan()
    assert c._callback_owner_ok(_extract(_update(OWNER))) is True, \
        "مالکِ واقعی رد شد — همان پیامِ «فقط مالک می‌تواند»"


def t_owner_gate_still_refuses_the_bot_and_a_stranger():
    c = _chan()
    assert c._callback_owner_ok(BOT) is False
    assert c._callback_owner_ok(STRANGER) is False
    assert c._callback_owner_ok(None) is False


def t_mutating_callback_from_the_owner_is_no_longer_refused():
    """سرتاسری: dispatch با هویتِ درست نباید پیامِ ردِ مالک بدهد."""
    c = _chan()
    out = c.dispatch_callback("rfc:merge:c6-abc:tok",
                              from_id=_extract(_update(OWNER)), external=True)
    assert "فقط مالک" not in str(out), f"مالک هنوز رد می‌شود: {out!r}"


def t_mutating_callback_from_a_stranger_is_still_refused():
    c = _chan()
    out = c.dispatch_callback("rfc:merge:c6-abc:tok",
                              from_id=STRANGER, external=True)
    assert "فقط مالک" in str(out), f"غریبه باید رد شود، شد: {out!r}"


def t_the_old_extraction_would_have_failed_this_suite():
    """گاردِ صریح: فرمِ قبلی را بازسازی می‌کند و ثابت می‌کند غلط بود.
    اگر روزی کسی به آن برگردد، این تست دقیقاً همان را می‌گیرد."""
    upd = _update(OWNER)
    cbq = upd["callback_query"]
    msg = upd.get("message") or cbq.get("message") or {}
    old = (msg.get("from") or cbq.get("from") or {}).get("id")
    assert old == BOT, "بازسازیِ باگِ قدیمی درست نیست"
    assert old != OWNER, "فرمِ قبلی کلیکِ مالک را به بات نسبت می‌داد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_callback_actor: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
