#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_wiring_notif_inbox — قلابِ ۵ جریانِ دایجست (wiring.py:_send_stream) به
صندوقِ اعلانِ مینی‌اپ (notif_inbox، ۲۰۲۶-۰۸-۰۷).

ادعاها:
  ۱) فلگِ notif_inbox خاموش → _send_stream دقیقاً مثلِ قبل channel.send_text
     را صدا می‌زند (برای هر پنج stream، صرف‌نظر از دسته).
  ۲) فلگ روشن + streamِ شناخته‌شده (needs/discovery/doctor/brain/heart) → پوش
     به صندوق، channel.send_text هرگز صدا زده نمی‌شود.
  ۳) فلگ روشن + streamِ ناشناخته (مثلِ کارتِ per-leg گروه: mining/crypto/...) →
     دست‌نخورده — channel.send_text مثلِ همیشه صدا زده می‌شود (leg_rooms_beat
     نباید از این تغییر متأثر شود).

mutation-gate: اگر _NOTIF_STREAM_CATEGORY حذف/نادیده گرفته شود و همه‌ی
streamها بی‌قیدوشرط route شوند، تستِ ادعای ۳ قرمز می‌شود.
"""
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("wiring-notif-inbox")

_OPS_SELF = Path(__file__).resolve().parent.parent
if str(_OPS_SELF / "telegram_center") not in sys.path:
    sys.path.insert(0, str(_OPS_SELF / "telegram_center"))

import wiring  # noqa: E402
import notif_inbox as ni  # noqa: E402


class _Flag:
    def __init__(self, name, val):
        self.name, self.val = name, val

    def __enter__(self):
        self.old = os.environ.get(self.name)
        if self.val is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.val
        return self

    def __exit__(self, *exc):
        if self.old is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.old


class _FakeChannel:
    def __init__(self):
        self.calls = []

    def send_text(self, text, kb=None, stream=None):
        self.calls.append({"text": text, "kb": kb, "stream": stream})
        return True


def _reset_inbox():
    try:
        ni._STORE_PATH.unlink()
    except OSError:
        pass
    try:
        ni._STORE_PATH.with_suffix(".json.lock").unlink()
    except OSError:
        pass


# ════════════════════════════════════════════════════════════════════════════
# (۱) فلگ خاموش = رفتارِ امروز، برای هر پنج stream
# ════════════════════════════════════════════════════════════════════════════
def t_flag_off_all_five_streams_reach_channel_unchanged():
    _reset_inbox()
    with _Flag(ni.FLAG, None):
        for stream in ("needs", "discovery", "doctor", "brain", "heart"):
            ch = _FakeChannel()
            out = wiring._send_stream(ch, f"متنِ {stream}", stream=stream)
            assert out is True, (stream, out)
            assert len(ch.calls) == 1, (stream, ch.calls)
            assert ch.calls[0]["stream"] == stream, ch.calls
    assert ni.unread_count() == 0, "فلگ خاموش نباید چیزی به صندوق بنویسد"


# ════════════════════════════════════════════════════════════════════════════
# (۲) فلگ روشن + streamِ شناخته‌شده = صندوق، صفر send_text
# ════════════════════════════════════════════════════════════════════════════
def t_flag_on_known_streams_route_to_inbox_never_touch_channel():
    _reset_inbox()
    expect = {"needs": "needs", "discovery": "discovery", "doctor": "doctor_digest",
              "brain": "brain_digest", "heart": "heart_digest"}
    with _Flag(ni.FLAG, "1"):
        for stream, category in expect.items():
            ch = _FakeChannel()
            out = wiring._send_stream(ch, f"متنِ {stream}", stream=stream)
            assert out, (stream, out)
            assert ch.calls == [], f"{stream}: send_text نباید صدا زده شود: {ch.calls}"
    items = ni.list_items(limit=100)
    assert len(items) == 5, items
    cats = {it["category"] for it in items}
    assert cats == set(expect.values()), cats


# ════════════════════════════════════════════════════════════════════════════
# (۳) فلگ روشن + streamِ ناشناخته (کارتِ per-leg گروه) = دست‌نخورده
# ════════════════════════════════════════════════════════════════════════════
def t_flag_on_unknown_stream_still_reaches_channel():
    """leg_rooms_beat با stream=نامِ پا (مثلِ mining) صدا می‌زند — این خارج از
    محدودهٔ notif_inbox است و نباید تحتِ تأثیر قرار بگیرد."""
    _reset_inbox()
    with _Flag(ni.FLAG, "1"):
        for leg_stream in ("mining", "crypto", "accounting", "studio_pf"):
            ch = _FakeChannel()
            out = wiring._send_stream(ch, "کارتِ پا", stream=leg_stream)
            assert out is True, (leg_stream, out)
            assert len(ch.calls) == 1, \
                f"{leg_stream}: کارتِ per-leg گروه باید مثلِ همیشه به تلگرام برود: {ch.calls}"
    assert ni.unread_count() == 0, \
        "streamِ ناشناخته نباید چیزی به صندوق اضافه کند"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_wiring_notif_inbox: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
