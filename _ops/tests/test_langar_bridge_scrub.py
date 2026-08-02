#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_langar_bridge_scrub.py — گاردِ حریمِ Project-F روی مسیرِ پلِ تلگرام.

یافتهٔ ممیزیِ ۲۰۲۶-۰۸-۰۳ (CONFIRMED، متخاصمانه راستی‌آزمایی شد): ‏docstring ِ
`langar_bridge` ادعا می‌کرد «OpsecGuard ِ langar روی هر خروجی فعال است» ولی
`dispatch` فقط `bot.handle()` را صدا می‌زد که خودش می‌گوید پاسخ را **قبل از
guard** برمی‌گرداند؛ تنها صداکنندهٔ `guard.clean` تابعِ `langar_bot.send` است که
در این مسیر هرگز اجرا نمی‌شود. یعنی خروجیِ langar بدونِ scrub به تلگرام می‌رفت،
درست همان‌جا که قواعدِ قفل‌شدهٔ #۶/#۷ (بدونِ نامِ شهر/هویت بیرون از پوشهٔ پروژه)
به آن تکیه دارند.

این تست دو چیز را قفل می‌کند:
  ۱) خروجیِ پل واقعاً از گاردِ **خودِ** langar می‌گذرد (نه یک گاردِ موازیِ دوم).
  ۲) fail-closed: اگر گارد نبود یا خطا داد، متنِ خام **بیرون نمی‌رود**.

هرمتیک: هیچ باتِ واقعی/شبکه‌ای؛ فقط دو stub.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import langar_bridge as LB  # noqa: E402

CITY = "Sydney"
SECRET_ISH = f"وضعیت: خوب — {CITY} · مسیر C:\\backup\\private"


class _Guard:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = 0

    def clean(self, text):
        self.calls += 1
        if self.fail:
            raise RuntimeError("guard exploded")
        return str(text).replace(CITY, "⟦geo⟧")


class _Bot:
    def __init__(self, guard=None, reply=SECRET_ISH):
        self.guard = guard
        self._reply = reply

    def handle(self, chat_id, text):     # امضای واقعیِ langar_bot.handle
        return self._reply


class TestBridgeScrub(unittest.TestCase):

    def _dispatch_with(self, bot, cmd="/pf_status"):
        orig = LB._get_langar_bot
        try:
            LB._get_langar_bot = lambda owner=None: bot
            return LB.dispatch(cmd, chat_id=111, owner=111)
        finally:
            LB._get_langar_bot = orig

    def test_output_passes_through_langar_guard(self):
        g = _Guard()
        out = self._dispatch_with(_Bot(guard=g))
        self.assertEqual(g.calls, 1, "گاردِ langar روی مسیرِ پل صدا زده نشد")
        self.assertNotIn(CITY, out, "نامِ شهر از مرزِ پروژه بیرون رفت (نقضِ قاعدهٔ #۶)")
        self.assertIn("⟦geo⟧", out)

    def test_missing_guard_is_fail_closed(self):
        out = self._dispatch_with(_Bot(guard=None))
        self.assertNotIn(CITY, out, "بدونِ گارد نباید متنِ خام بیرون برود")
        self.assertIn("fail-closed", out)

    def test_broken_guard_is_fail_closed(self):
        out = self._dispatch_with(_Bot(guard=_Guard(fail=True)))
        self.assertNotIn(CITY, out)
        self.assertIn("fail-closed", out)

    def test_non_langar_command_is_untouched(self):
        """پل نباید فرمانِ غیرِ langar را بدزدد (رفتارِ قبلی حفظ شود)."""
        self.assertIsNone(self._dispatch_with(_Bot(guard=_Guard()), cmd="/panel"))

    def test_empty_reply_is_passed_through(self):
        g = _Guard()
        out = self._dispatch_with(_Bot(guard=g, reply=""))
        self.assertEqual(out, "")
        self.assertEqual(g.calls, 0, "روی پاسخِ خالی نباید گارد صدا زده شود")

    def test_docstring_no_longer_claims_automatic_guard(self):
        """درسِ «قانون هم از کدش عقب می‌افتد»: سند نباید دوباره ادعای غلط کند."""
        doc = LB.dispatch.__doc__ or ""
        self.assertIn("_scrub_via_langar", doc,
                      "docstring باید به مکانیزمِ واقعیِ scrub اشاره کند")


if __name__ == "__main__":
    unittest.main(verbosity=2)
