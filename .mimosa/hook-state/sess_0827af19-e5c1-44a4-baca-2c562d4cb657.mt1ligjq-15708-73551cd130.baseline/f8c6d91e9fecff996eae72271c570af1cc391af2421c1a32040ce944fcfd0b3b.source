#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lead_card_buttons_live.py — دکمه‌های کارتِ لید باید **اجرا** شوند.

VQ-DEAD-LEAD-BUTTONS-001 (۲۰۲۶-۰۸-۰۴). `lead_card.keyboard` دو دکمه می‌سازد —
«📞 زنگ بزن» (`lcall`) و «📤 پیش‌نویس» (`ldraft`) — و **هیچ‌کدام روت نداشتند**.
مالک کلیک می‌کرد و هیچ اتفاقی نمی‌افتاد؛ حتی spinner ِ تلگرام هم بی‌جواب
می‌ماند. دقیقاً همان شکایتِ «هرکاری می‌کنم دیده نمی‌شود».

⚠️ **چرا این فایل لازم است در حالی که `test_callback_routing` از قبل وجود
دارد:** آن تست سورس را با regex می‌خواند و «روت شده» را از وجودِ یک
`verb == "..."` نتیجه می‌گیرد. حین همین رفع، نسخهٔ اولِ سیم‌کشیِ من متغیرِ
`parts` را استفاده کرد که در آن متد **وجود ندارد** ⇒ هر کلیک
`UnboundLocalError` می‌داد — و `test_callback_routing` همان لحظه **۶/۶ سبز**
بود. سبزیِ یک تستِ متنی دربارهٔ اجرا هیچ نمی‌گوید.

پس این تست **رفتاری** است: کلیک را واقعاً dispatch می‌کند و می‌سنجد که پاسخی
تولید شد.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("lead-card-buttons")
sys.path.insert(0, str(harness.REAL_VAULT / "_ops" / "legs"))

import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "center_lb", harness.REAL_VAULT / "_ops" / "telegram_center" / "center.py")
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
import lead_sense  # noqa: E402


def _center():
    c = mod.Center.__new__(mod.Center)
    sent = []

    class _C:
        owner_chat_id = 555

        def send(self, text, **kw):
            sent.append((kw.get("stream"), str(text)))
            return 1

    c._client = _C()
    c._answer = lambda *a, **k: None
    c._reply_thread = lambda msg: None
    c._power_mod = lambda: None
    return c, sent


def _click(c, data):
    return c._handle_callback({"data": data,
                               "message": {"chat": {"id": 555}},
                               "from": {"id": 555}})


def _seed():
    inbox = lead_sense._inbox()
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / "lead_t1.json").write_text(json.dumps({
        "lead_id": "lead_t1",
        "contact": {"phone": "0412345678", "email": "a@b.com"},
        "first_reply": {"subject": "نقاشیِ بیرونی", "body": "سلام، در دسترسم."},
    }, ensure_ascii=False), encoding="utf-8")


def t_a_a_click_never_dies_silently():
    """قلبِ گارد. هر کلیک باید **هم** روت شود **هم** پاسخی تولید کند —
    حتی وقتی لید پیدا نمی‌شود. دکمهٔ بی‌جواب همان باگ است."""
    _seed()
    for data in ("lcall:lead_t1", "ldraft:lead_t1", "lcall:lead_absent"):
        c, sent = _center()
        r = _click(c, data)
        assert isinstance(r, dict) and r.get("kind") == "lead-card", (data, r)
        assert sent, (data, "کلیک شد ولی هیچ پاسخی تولید نشد")


def t_b_the_contact_button_renders_a_tappable_number():
    _seed()
    c, sent = _center()
    _click(c, "lcall:lead_t1")
    body = "\n".join(t for _, t in sent)
    assert "tel:+61412345678" in body, ("شمارهٔ E.164 ِ قابلِ لمس نیست", body[:200])
    assert "lead_t1" in body


def t_c_the_draft_button_renders_the_draft_and_says_it_sends_nothing():
    _seed()
    c, sent = _center()
    _click(c, "ldraft:lead_t1")
    body = "\n".join(t for _, t in sent)
    assert "سلام، در دسترسم." in body, ("متنِ پیش‌نویس نیامد", body[:200])
    assert "نمی‌فرستد" in body, (
        "برچسبِ «چیزی نمی‌فرستد» گم شد — مالک باید بداند این فقط مرور است")


def t_d_neither_button_can_send_anything_outbound():
    """ناوردیِ ایمنی. `lead_card.SAFE_VERBS` تضمینِ ماژول است؛ این‌جا تضمینِ
    مسیر: پاسخ فقط به همان چتِ مالک می‌رود، با stream ِ نام‌دار، و هیچ
    transport ِ لید صدا زده نمی‌شود."""
    import lead_card as lc
    assert lc.SAFE_VERBS == frozenset({"lcall", "ldraft"}), lc.SAFE_VERBS
    _seed()
    for data in ("lcall:lead_t1", "ldraft:lead_t1"):
        c, sent = _center()
        _click(c, data)
        for stream, _t in sent:
            assert str(stream).startswith("lead-l"), (data, stream)


def t_e_an_unknown_lead_is_answered_not_swallowed():
    c, sent = _center()
    r = _click(c, "lcall:no_such_lead")
    assert r.get("kind") == "lead-card"
    assert sent and "پیدا نشد" in sent[0][1], sent


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t(); passed += 1; print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__); print(f"  FAIL {t.__name__}: {e}")
    print(f"\ntest_lead_card_buttons_live: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
