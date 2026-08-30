#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_mirror_menu_button.py — دکمهٔ منویِ mirror_room (مگاپرامپتِ تناقضات، ب-۹).

از درِ واقعی (center.handle_update) اثبات می‌کند:
  (الف) render_menu شاملِ دکمهٔ «🪞 حرف بزن» است.
  (ب)  mn:mr → edit با پرامپت + پرچمِ awaiting روشن می‌شود.
  (ج)  پیامِ بعدی (بدونِ تاپیکِ mirror) به mirror_room.ask می‌رود چون پرچم روشن است.
  (د)  پرچم فقط یک پیام مصرف می‌شود — پیامِ سوم دیگر به آینه نمی‌رود.
  (ه)  مسیرِ قدیمیِ تاپیک-محور دست‌نخورده می‌ماند (رگرسیون نه، افزونه).
صفر شبکه/تلگرام؛ FakeClient + fake mirror_room؛ owner=777.
"""
import os
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
harness.setup("mirror-menu-button")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import center  # noqa: E402
import render  # noqa: E402


class FakeClient:
    def __init__(self, owner_id=777):
        self.owner_id = owner_id
        self.calls = []
        self._mid = 100

    def wired(self):
        return True

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None, pin=False):
        self.calls.append(("send", {"text": text, "keyboard": keyboard}))
        self._mid += 1
        return self._mid

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.calls.append(("edit", {"message_id": message_id, "text": text, "keyboard": keyboard}))
        return True

    def answer_callback(self, callback_id, text=""):
        self.calls.append(("answer", {"text": text}))
        return True

    def is_owner(self, update):
        frm = ((update.get("message") or {}).get("from")
               or (update.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id

    def named(self, kind):
        return [c for k, c in self.calls if k == kind]


class FakeMirrorRoom:
    """جایگزینِ ماژولِ mirror_room — صفر مدل، صفر شبکه."""
    def __init__(self):
        self.asked = []

    def enabled(self):
        return True

    def observe(self, room, text, by=""):
        pass

    def ask(self, question, *, room="", ask_fn=None, now=None):
        self.asked.append(question)
        return {"ok": True, "text": "پاسخِ آزمایشی", "model": "fake", "recorded_correction": False}

    def card(self, text, model="", corrected=False):
        return (f"🪞 {text}", [[{"text": "🔙 منو", "callback_data": "mn:menu"}]])


def _center():
    fc = FakeClient()
    c = center.Center(client=fc, clock=lambda: 1000.0,
                      render_mod=types.SimpleNamespace(collect_feeds=lambda: {}, scrub=lambda t: t))
    return c, fc


def _msg(text, topic_id=None):
    m = {"from": {"id": 777}, "chat": {"id": 777}, "text": text, "message_id": 5}
    if topic_id is not None:
        m["message_thread_id"] = topic_id
    return {"message": m}


def _cb(data):
    return {"callback_query": {"id": "cb1", "from": {"id": 777},
                               "message": {"message_id": 100, "chat": {"id": 777}}, "data": data}}


def t_menu_button_present():
    txt, kb = render.render_menu(power=True, feeds={}, paused={})
    flat = [b for row in kb for b in row]
    hit = [b for b in flat if b.get("callback_data") == "mn:mr"]
    assert hit, "دکمهٔ mn:mr باید در منویِ اصلی باشد"
    assert "حرف بزن" in hit[0]["text"], hit[0]["text"]


def t_button_sets_prompt_and_flag():
    fake = FakeMirrorRoom()
    sys.modules["mirror_room"] = fake
    try:
        c, fc = _center()
        c.handle_update(_cb("mn:mr"))
        edits = fc.named("edit")
        assert edits, "mn:mr باید پیام را edit کند"
        assert "می‌شنوم" in edits[-1]["text"] or "بگو" in edits[-1]["text"], edits[-1]["text"]
        assert getattr(c, "_awaiting_mirror", False) is True, "پرچمِ awaiting باید روشن شود"
    finally:
        sys.modules.pop("mirror_room", None)


def t_next_message_routes_to_mirror_without_topic():
    # مستقیم رویِ _handle_ask (نه handle_update کامل) چون آنچه تست می‌شود
    # منطقِ دقیقِ همین تابع است؛ زنجیرهٔ بالادستِ handle_command پیش‌شرط‌های
    # خودش را دارد (chat_room/dispatch) که این‌جا موضوعِ تست نیست.
    fake = FakeMirrorRoom()
    sys.modules["mirror_room"] = fake
    try:
        c, fc = _center()
        c._defer_with_ack = lambda *a, **k: False  # اجبارِ مسیرِ همگام (بدونِ صف پس‌زمینه)
        c._awaiting_mirror = True  # شبیه‌سازیِ فشردنِ دکمه
        c._handle_ask(_msg("سوالِ من")["message"], "سوالِ من")
        assert fake.asked == ["سوالِ من"], fake.asked
        assert getattr(c, "_awaiting_mirror", None) is False, "پرچم باید بعدِ مصرف خاموش شود"
    finally:
        sys.modules.pop("mirror_room", None)


def t_flag_consumed_only_once():
    fake = FakeMirrorRoom()
    sys.modules["mirror_room"] = fake
    try:
        c, fc = _center()
        c._defer_with_ack = lambda *a, **k: False
        c._awaiting_mirror = True
        c._handle_ask(_msg("اول")["message"], "اول")
        c._handle_ask(_msg("دوم")["message"], "دوم")
        assert fake.asked == ["اول"], (
            "پیامِ دوم نباید به آینه برود — پرچم فقط یک‌بار مصرف است: " + str(fake.asked))
    finally:
        sys.modules.pop("mirror_room", None)


def t_topic_route_still_works_unchanged():
    """رگرسیون: مسیرِ قدیمیِ تاپیک-محور نباید بشکند."""
    fake = FakeMirrorRoom()
    sys.modules["mirror_room"] = fake
    try:
        c, fc = _center()
        c._defer_with_ack = lambda *a, **k: False
        c._topic_key = lambda msg: "mirror"  # شبیه‌سازیِ تاپیکِ آینه
        c._handle_ask(_msg("سوالِ تاپیکی")["message"], "سوالِ تاپیکی")
        assert fake.asked == ["سوالِ تاپیکی"], fake.asked
    finally:
        sys.modules.pop("mirror_room", None)


def t_disabled_flag_shows_dark_message_not_crash():
    class DarkMirror(FakeMirrorRoom):
        def enabled(self):
            return False
    sys.modules["mirror_room"] = DarkMirror()
    try:
        c, fc = _center()
        c.handle_update(_cb("mn:mr"))
        edits = fc.named("edit")
        assert edits, edits
        assert "خاموش" in edits[-1]["text"], edits[-1]["text"]
        assert getattr(c, "_awaiting_mirror", False) is False, "flag خاموش نباید awaiting را روشن کند"
    finally:
        sys.modules.pop("mirror_room", None)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_") and callable(v)]
    fails = []
    for t in tests:
        try:
            t()
            print("  ✅", t.__name__)
        except Exception as e:  # noqa: BLE001
            fails.append((t.__name__, e))
            print("  ❌", t.__name__, "-", e)
    print(("PASS" if not fails else "FAIL"), f"— test_mirror_menu_button — {len(fails)} failures")
    sys.exit(1 if fails else 0)
