#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_center_notif_inbox — قلابِ دایجستِ سلامت (center.py:beat) به صندوقِ
اعلانِ مینی‌اپ (notif_inbox، ۲۰۲۶-۰۸-۰۷).

ادعاها:
  ۱) فلگ خاموش → beat() دقیقاً مثلِ قبل self._route_send را صدا می‌زند و روی
     موفقیت mark_digest_flushed پیش می‌رود.
  ۲) فلگ روشن → دایجست در صندوق می‌نشیند، self._route_send هرگز صدا زده
     نمی‌شود، و mark_digest_flushed هنوز درست پیش می‌رود (چون push موفق است).
  ۳) فلگ روشن + شکستِ نوشتنِ صندوق (push→None) → mark_digest_flushed صدا زده
     نمی‌شود — دقیقاً همان ناوردیِ «ارسالِ شکست‌خورده هرگز گم نشود» که کامنتِ
     خودِ center.py برایش نوشته شده.

mutation-gate: اگر push() به رشتهٔ خالی برگردد (نه None)، ادعای ۳ قرمز می‌شود
(چون "" is not None == True و mark_digest_flushed اشتباهاً صدا زده می‌شود).
"""
import os
import sys
from pathlib import Path
from unittest import mock

import harness

ENV = harness.setup("center-notif-inbox")

_OPS_SELF = Path(__file__).resolve().parent.parent
if str(_OPS_SELF / "telegram_center") not in sys.path:
    sys.path.insert(0, str(_OPS_SELF / "telegram_center"))

import center  # noqa: E402
import hold_policy as hp  # noqa: E402
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


class _FakeClient:
    def wired(self):
        return True

    def edit(self, *a, **k):
        return False


def _reset_inbox():
    try:
        ni._STORE_PATH.unlink()
    except OSError:
        pass
    try:
        ni._STORE_PATH.with_suffix(".json.lock").unlink()
    except OSError:
        pass


def _make_center():
    return center.Center(client=_FakeClient(), clock=lambda: 1000.0, render_mod=None)


def _force_digest_due(digest_text="متنِ دایجست"):
    """hold_policy را طوری patch کن که digest_due=True و flush_digest متنِ
    معلوم بدهد — بدونِ لمسِ فایل‌های واقعیِ digest-buffer."""
    return (
        mock.patch.object(hp, "digest_due", return_value=True),
        mock.patch.object(hp, "flush_digest", return_value=digest_text),
        mock.patch.object(hp, "mark_digest_flushed"),
        mock.patch.object(hp, "urgent_pending", return_value=[]),
    )


# ════════════════════════════════════════════════════════════════════════════
# (۱) فلگ خاموش = رفتارِ امروز
# ════════════════════════════════════════════════════════════════════════════
def t_flag_off_calls_route_send_and_marks_flushed_on_success():
    _reset_inbox()
    c = _make_center()
    p_due, p_flush, p_mark, p_urg = _force_digest_due()
    with _Flag(ni.FLAG, None), p_due, p_flush, p_mark as mock_mark, p_urg, \
         mock.patch.object(center.Center, "_route_send", return_value="msg-id-123") as mock_rs:
        c.beat()
    assert mock_rs.called, "فلگ خاموش باید _route_send را صدا بزند"
    assert mock_rs.call_args[0][0] == "center-health-digest", mock_rs.call_args
    mock_mark.assert_called_once()
    assert ni.unread_count() == 0, "فلگ خاموش نباید چیزی به صندوق بنویسد"


# ════════════════════════════════════════════════════════════════════════════
# (۲) فلگ روشن + موفق = صندوق، صفر _route_send، mark_digest_flushed هنوز پیش می‌رود
# ════════════════════════════════════════════════════════════════════════════
def t_flag_on_pushes_to_inbox_never_calls_route_send_still_marks_flushed():
    _reset_inbox()
    c = _make_center()
    p_due, p_flush, p_mark, p_urg = _force_digest_due("محتوایِ دایجستِ سلامت")
    with _Flag(ni.FLAG, "1"), p_due, p_flush, p_mark as mock_mark, p_urg, \
         mock.patch.object(center.Center, "_route_send") as mock_rs:
        c.beat()
    assert not mock_rs.called, f"فلگ روشن نباید _route_send را صدا بزند: {mock_rs.call_args_list}"
    mock_mark.assert_called_once()
    assert ni.unread_count() == 1, ni.unread_count()
    items = ni.list_items()
    assert items[0]["category"] == "health_digest", items[0]
    assert items[0]["body"] == "محتوایِ دایجستِ سلامت", items[0]


# ════════════════════════════════════════════════════════════════════════════
# (۳) فلگ روشن + شکستِ نوشتن = mark_digest_flushed صدا زده نمی‌شود
# ════════════════════════════════════════════════════════════════════════════
def t_flag_on_inbox_write_failure_never_marks_flushed():
    """رگرسیونِ باربر: اگر push() شکست بخورد (None)، دایجست نباید «رسیده»
    علامت بخورد — همان ناوردیِ ارسالِ شکست‌خورده که کامنتِ center.py دربارهٔ آن
    هشدار می‌دهد."""
    _reset_inbox()
    c = _make_center()
    p_due, p_flush, p_mark, p_urg = _force_digest_due()
    with _Flag(ni.FLAG, "1"), p_due, p_flush, p_mark as mock_mark, p_urg, \
         mock.patch.object(center.Center, "_route_send") as mock_rs, \
         mock.patch.object(ni, "push", return_value=None):
        c.beat()
    assert not mock_rs.called
    mock_mark.assert_not_called(), \
        "push شکست خورد (None) — mark_digest_flushed نباید صدا زده شود"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_center_notif_inbox: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
