#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_voice_worker.py — ویسِ کند نباید کلِ بات را بخواباند.

اندازه‌گیریِ زندهٔ ۲۰۲۶-۰۸-۰۱: ویسِ ۵ ثانیه‌ایِ مالک ۲۲.۶ ثانیه transcription
برد. `_capture_hook` داخلِ `_handle_message` است و آن داخلِ dispatch — یعنی در
تمامِ آن ۲۲ ثانیه مرکز به هیچ پیام و هیچ دکمه‌ای جواب نمی‌داد. با مدلِ `medium`
(رأیِ مالک، ~۳ برابر کندتر) یک ویسِ نیم‌دقیقه‌ای چند دقیقه بات را می‌خواباند، و
از بیرون باتِ خواب با باتِ مرده یک شکل است.

قواعدی که این‌جا قفل می‌شوند:
  · ویس **همان لحظه** برمی‌گردد و کارِ کند روی نخِ دیگری می‌رود.
  · مالک بی‌خبر نمی‌ماند: ackِ «دارم گوش می‌دم» فوری، و بعد **همان پیام** به
    نتیجه ویرایش می‌شود (نه پیامِ دوم — دو پیام برای یک ژست شلوغی است).
  · اگر کارگر در دسترس نباشد، مسیرِ همگامِ دیروز اجرا می‌شود. کندی قابلِ
    تحمل است؛ گم‌شدنِ ویسِ مالک نه.
  · متن/عکس همچنان همگام‌اند — تنها ورودیِ کند ویس است.
  · شکستِ خودِ capture در کارگر هم به مالک گفته می‌شود، نه سکوت.
"""
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("tg-voice-worker")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import capture  # noqa: E402
import center   # noqa: E402


class FakeClient:
    def __init__(self):
        self.sent = []
        self.edits = []
        self._mid = 900
        self.owner_chat_id = 777

    def wired(self):
        return True

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None,
             pin=False, stream=None):
        self._mid += 1
        self.sent.append({"mid": self._mid, "text": text, "chat_id": chat_id})
        return self._mid

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.edits.append({"mid": message_id, "text": text})
        return True


def _center(fc):
    return center.Center(client=fc, clock=lambda: 1000.0)


def _voice_msg(mid=7001):
    return {"message_id": mid, "chat": {"id": 777, "type": "private"},
            "voice": {"file_id": "VOICE-%d" % mid, "duration": 5}}


def _drain(timeout_s=8.0):
    """صبر کن تا کارگر واقعاً **تمام** کند.

    نسخهٔ اولِ این کمکی `q.empty()` را می‌سنجید و زود برمی‌گشت: صف به‌محضِ
    **برداشتنِ** کار خالی می‌شود، در حالی که کار تازه شروع شده. معیارِ درست
    `unfinished_tasks` است که فقط با `task_done` صفر می‌شود."""
    q = center._VOICE_Q
    if q is None:
        return
    end = time.time() + timeout_s
    while time.time() < end and getattr(q, "unfinished_tasks", 0) > 0:
        time.sleep(0.02)


def _with_capture_on(fn):
    os.environ["OCTOPUS_TG_CAPTURE"] = "1"
    try:
        return fn()
    finally:
        os.environ.pop("OCTOPUS_TG_CAPTURE", None)


def t_a_voice_returns_immediately_and_does_not_block_the_loop():
    """کارِ کند نباید در تماسِ hook اتفاق بیفتد.

    capture را عمداً «کند» می‌کنیم (۱.۵ ثانیه). اگر hook همگام باشد، خودش
    ۱.۵ ثانیه طول می‌کشد؛ اگر واقعاً صف شده باشد، میلی‌ثانیه."""
    fc = FakeClient()
    c = _center(fc)
    seen = []

    def slow_handle(msg, deps=None):
        time.sleep(1.5)
        seen.append(msg.get("message_id"))
        return {"handled": True, "kind": "note", "ack": "نوتِ ویس ثبت شد ✅"}

    orig = capture.handle
    capture.handle = slow_handle
    try:
        t0 = time.time()
        r = _with_capture_on(lambda: c._capture_hook(_voice_msg(7101)))
        elapsed = time.time() - t0
        assert elapsed < 0.5, "hook همگام ماند (%.2fs) — حلقه هنوز قفل می‌شود" % elapsed
        assert r and r.get("queued") is True, r
        assert not seen, "capture داخلِ حلقه اجرا شد"
        _drain()
        assert seen == [7101], "کارگر کار را انجام نداد: %r" % (seen,)
    finally:
        capture.handle = orig


def t_b_owner_gets_an_instant_ack_then_the_same_message_becomes_the_result():
    fc = FakeClient()
    c = _center(fc)

    def ok_handle(msg, deps=None):
        return {"handled": True, "kind": "task", "ack": "کار ساخته شد ✅"}

    orig = capture.handle
    capture.handle = ok_handle
    try:
        _with_capture_on(lambda: c._capture_hook(_voice_msg(7102)))
        assert fc.sent, "هیچ ackِ فوری‌ای نرفت — مالک مقابلِ سکوت می‌ماند"
        assert "گوش" in fc.sent[0]["text"], fc.sent[0]
        _drain()
        assert fc.edits, "نتیجه به‌جای ویرایش، هیچ نشد"
        assert "کار ساخته شد" in fc.edits[-1]["text"], fc.edits[-1]
        assert fc.edits[-1]["mid"] == fc.sent[0]["mid"], "پیامِ دیگری ویرایش شد"
        assert len(fc.sent) == 1, "پیامِ دومی فرستاده شد: %r" % (fc.sent,)
    finally:
        capture.handle = orig


def t_c_when_the_worker_is_unavailable_the_voice_is_still_captured():
    """کارگر نبود ⇒ همگام. ویسِ مالک تحتِ هیچ شرایطی گم نمی‌شود."""
    fc = FakeClient()
    c = _center(fc)
    done = []

    def ok_handle(msg, deps=None):
        done.append(msg.get("message_id"))
        return {"handled": True, "kind": "note", "ack": "ثبت شد ✅"}

    orig_h, orig_s = capture.handle, center._submit_voice_job
    capture.handle = ok_handle
    center._submit_voice_job = lambda job: False        # صف پر / نخ مرده
    try:
        r = _with_capture_on(lambda: c._capture_hook(_voice_msg(7103)))
        assert done == [7103], "ویس نه صف شد نه همگام اجرا شد — گم شد"
        assert r and r.get("kind") == "capture" and not r.get("queued"), r
    finally:
        capture.handle, center._submit_voice_job = orig_h, orig_s


def t_d_text_capture_stays_synchronous():
    """تنها ورودیِ کند ویس است؛ متن نباید بی‌دلیل به صف برود."""
    fc = FakeClient()
    c = _center(fc)
    done = []

    def ok_handle(msg, deps=None):
        done.append(msg.get("message_id"))
        return {"handled": True, "kind": "expense", "ack": "هزینه ثبت شد ✅"}

    orig = capture.handle
    capture.handle = ok_handle
    try:
        r = _with_capture_on(lambda: c._capture_hook(
            {"message_id": 7104, "chat": {"id": 777, "type": "private"},
             "text": "ثبت: خرید رنگ ۵۰ دلار"}))
        assert done == [7104], "متن به کارگر رفت — همگام بماند"
        assert r and not r.get("queued"), r
    finally:
        capture.handle = orig


def t_e_a_refusal_inside_the_worker_is_spoken_not_swallowed():
    fc = FakeClient()
    c = _center(fc)

    def refuse(msg, deps=None):
        return {"handled": False}

    orig = capture.handle
    capture.handle = refuse
    try:
        _with_capture_on(lambda: c._capture_hook(_voice_msg(7105)))
        _drain()
        said = (fc.edits[-1]["text"] if fc.edits
                else (fc.sent[-1]["text"] if fc.sent else ""))
        assert "ثبت نشد" in said, "ردِ capture در کارگر بی‌صدا ماند: %r" % (said,)
    finally:
        capture.handle = orig


def t_f_the_worker_survives_a_crashing_job():
    """یک کارِ منفجرشده نباید نخ را بکشد — ویسِ بعدی باید کار کند."""
    fc = FakeClient()
    c = _center(fc)
    done = []

    def boom(msg, deps=None):
        raise RuntimeError("transcription exploded")

    orig = capture.handle
    capture.handle = boom
    try:
        _with_capture_on(lambda: c._capture_hook(_voice_msg(7106)))
        _drain()
    finally:
        capture.handle = orig

    def ok_handle(msg, deps=None):
        done.append(msg.get("message_id"))
        return {"handled": True, "kind": "note", "ack": "ثبت شد ✅"}

    capture.handle = ok_handle
    try:
        _with_capture_on(lambda: c._capture_hook(_voice_msg(7107)))
        _drain()
        assert done == [7107], "کارگر بعد از یک انفجار مرد"
    finally:
        capture.handle = orig


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_voice_worker: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
