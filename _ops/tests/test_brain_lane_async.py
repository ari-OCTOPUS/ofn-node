#!/usr/bin/env python3
"""test_brain_lane_async.py — لِینِ مغز: حلقهٔ poll دیگر پشتِ مدل نمی‌ماند.

اندازه‌گیریِ ممیزیِ ۲۰۲۶-۰۸-۰۳: یک پیامِ آزادِ مالک تا **۲۳۵ ثانیه** مرکز را کر
می‌کرد. `center.run_forever` تک‌رشته است؛ `_handle_message` → `ask_brain.ask` →
Fugu روی همان رشته می‌نشست و در تمامِ آن مدت هیچ `answerCallbackQuery` برای هیچ
دکمه‌ای در هیچ تاپیکی نمی‌رفت — یعنی هر کارتِ سیستم می‌چرخید.

سنجهٔ این فایل عمداً **زمانِ سپری‌شده** است، نه «تابع برگشت». یک تستِ صرفاً
ساختاری («صف صدا زده شد؟») همان سبزِ دروغینی است که این ریپو بارها خورده:
می‌شود صف را صدا زد و همچنان همگام منتظر ماند.

قرارداد:
  · کارِ کند به لِین می‌رود ⇒ صداکننده **فوراً** برمی‌گردد.
  · نتیجه بعداً همان پیامِ ack را **ویرایش** می‌کند (نه پیامِ دوم).
  · صفِ پر / نخِ مرده ⇒ `False` ⇒ صداکننده همگام ادامه می‌دهد (کندی بهتر از سکوت).
  · لِینِ ویس و لِینِ مغز **جدا** اند: یک مدلِ کندِ ۲۷۰ثانیه‌ای نباید ویسِ مالک
    را پشتِ خودش حبس کند.
"""
import sys
import threading
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("brain-lane-async")
_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "telegram_center"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import center  # noqa: E402

SLOW_S = 1.5          # «مدلِ کند» — کوچک نگه داشته تا سوییت سریع بماند
FAST_MAX_S = 0.4      # صداکننده باید خیلی زودتر از SLOW_S برگردد


class _FakeClient:
    """کلاینتِ تلگرامِ ثبت‌کننده — صفر شبکه."""

    def __init__(self):
        self.sent, self.edited = [], []
        self._next = 100
        self._lk = threading.Lock()

    def send(self, text, chat_id=None, keyboard=None, topic_id=None):
        with self._lk:
            self._next += 1
            self.sent.append({"text": text, "kb": keyboard, "mid": self._next})
            return self._next

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        with self._lk:
            self.edited.append({"mid": message_id, "text": text, "kb": keyboard})
        return True


class _Host:
    """کمینه‌ترین میزبانِ متدِ واقعی — importِ کاملِ Center یک poller می‌سازد."""

    _defer_with_ack = center.Center._defer_with_ack

    def __init__(self):
        self._client = _FakeClient()


def _reset_lanes():
    """هر تست با لِینِ تازه شروع شود (نخِ daemon از تستِ قبلی زنده می‌ماند)."""
    center._BG_LANES.clear()


def t_a_the_caller_returns_immediately_not_after_the_slow_work():
    """قلبِ رگرسیون: زمانِ سپری‌شدهٔ صداکننده، نه صرفِ برگشتنش."""
    _reset_lanes()
    h = _Host()
    done = threading.Event()

    def _slow():
        time.sleep(SLOW_S)
        done.set()
        return "جوابِ مدل"

    t0 = time.time()
    queued = h._defer_with_ack(1, "🧠 دارم فکر می‌کنم…", _slow)
    elapsed = time.time() - t0

    assert queued is True, "کار به لِین نرفت"
    assert elapsed < FAST_MAX_S, (
        f"صداکننده {elapsed:.2f}s بلاک شد — حلقهٔ poll هنوز پشتِ مدل می‌ماند")
    assert done.wait(SLOW_S * 4), "کارگر هرگز کار را اجرا نکرد"


def t_b_the_ack_goes_out_before_the_work_runs():
    _reset_lanes()
    h = _Host()
    seen = {}

    def _slow():
        seen["acks_at_work_time"] = len(h._client.sent)
        return "تمام"

    h._defer_with_ack(1, "🧠 دارم فکر می‌کنم…", _slow)
    time.sleep(0.5)
    assert h._client.sent, "هیچ ack ی نرفت"
    assert "دارم فکر" in h._client.sent[0]["text"]
    assert seen.get("acks_at_work_time") == 1, seen


def t_c_the_result_edits_the_same_message_not_a_second_one():
    _reset_lanes()
    h = _Host()
    h._defer_with_ack(1, "🧠 دارم فکر می‌کنم…", lambda: "جوابِ نهایی")
    time.sleep(0.5)
    assert len(h._client.sent) == 1, ("پیامِ دوم فرستاده شد", h._client.sent)
    assert len(h._client.edited) == 1, h._client.edited
    assert h._client.edited[0]["mid"] == h._client.sent[0]["mid"]
    assert "جوابِ نهایی" in h._client.edited[0]["text"]


def t_d_a_tuple_result_carries_its_keyboard():
    """`ask_brain.card` یک tuple برمی‌گرداند — کیبورد نباید گم شود."""
    _reset_lanes()
    h = _Host()
    kb = {"inline_keyboard": [[{"text": "x", "callback_data": "y"}]]}
    h._defer_with_ack(1, "…", lambda: ("متن", kb))
    time.sleep(0.5)
    assert h._client.edited and h._client.edited[0]["kb"] == kb, h._client.edited


def t_e_a_crashing_job_still_answers_the_owner():
    """کارگر هرگز نمی‌میرد و مالک بی‌جواب نمی‌ماند."""
    _reset_lanes()
    h = _Host()

    def _boom():
        raise RuntimeError("simulated model failure")

    h._defer_with_ack(1, "…", _boom)
    time.sleep(0.5)
    assert h._client.edited, "استثنا مالک را بی‌جواب گذاشت"
    assert "RuntimeError" in h._client.edited[0]["text"]


def t_f_a_full_queue_falls_back_to_sync_never_blocks():
    """صفِ پر ⇒ False ⇒ صداکننده همگام ادامه می‌دهد (کندی بهتر از سکوت)."""
    _reset_lanes()
    import queue as _q
    # لِین را با صفِ پُرِ بی‌کارگر جا بینداز تا put_nowait قطعاً بشکند
    full = _q.Queue(maxsize=1)
    full.put(lambda: None)
    center._BG_LANES["brain"] = (full, threading.current_thread())
    t0 = time.time()
    ok = center._submit_bg_job("brain", lambda: None, center.BRAIN_QUEUE_MAX)
    assert ok is False, "صفِ پر باید False بدهد نه بلاک"
    assert time.time() - t0 < FAST_MAX_S, "صفِ پر صداکننده را بلاک کرد"


def t_g_voice_and_brain_are_separate_lanes():
    """یک مدلِ کند نباید ویسِ مالک را پشتِ خودش حبس کند."""
    _reset_lanes()
    center._bg_queue("voice", center.VOICE_QUEUE_MAX)
    center._bg_queue("brain", center.BRAIN_QUEUE_MAX)
    vq, vt = center._BG_LANES["voice"]
    bq, bt = center._BG_LANES["brain"]
    assert vq is not bq, "ویس و مغز یک صف را share می‌کنند"
    assert vt is not bt, "ویس و مغز یک نخ را share می‌کنند"
    assert vt.name == "tg-voice-worker", vt.name      # نامِ قبلی حفظ شده
    assert bt.name == "tg-brain-worker", bt.name


def t_h_voice_helpers_still_work_backward_compatible():
    """`_submit_voice_job` قراردادِ قبلی‌اش را نگه می‌دارد."""
    _reset_lanes()
    done = threading.Event()
    assert center._submit_voice_job(lambda: done.set()) is True
    assert done.wait(3.0), "کارگرِ ویس اجرا نکرد"


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__)
            print(f"  FAIL {t.__name__}: {e!r}")
    print(f"\ntest_brain_lane_async: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
