#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_leg_registry_parity.py — «قاعده را ببند نه شکاف را».

کلاسِ باگ (کشف‌شده در ممیزیِ ۲۰۲۶-۰۸-۰۳): رجیستریِ پاها **یک جا نیست، چند جاست**
و هیچ‌کدام از هم مشتق نمی‌شوند:

  · `_ops/wiring.py::_BUSINESS_LEGS_SPEC`            ← منبعِ ORGANISM-STATE.business_legs
  · `_ops/budget/approval_channel.py::TelegramApprovalChannel.ORGANS` ← منویِ ارگان (هاردکد)
  · `_ops/telegram_center/weekly_review.py::BUSINESS_LEGS` ← گزارشِ هفتگی (هاردکد)

هر بار پایی به اولی اضافه شد و به بقیه نه، آن پا در همان سطح **نامرئی** ماند و
هیچ تستی نگرفت. امروز هم `sync_agent` (از ۰۸-۰۲) و هم `studio_pf` قربانیِ همین
بودند. این تست به‌جای وصله‌زدنِ یک نمونه، **ناوردی** را قفل می‌کند: هر پایی که در
رجیستریِ اصلی هست باید در سطح‌های مالک‌رو هم باشد.

اگر روزی عمداً پایی نباید در یک سطح دیده شود، به `_INTENTIONALLY_HIDDEN` اضافه‌اش
کن — با دلیل. سکوتِ بی‌دلیل ممنوع.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "telegram_center"), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# پاهایی که عمداً در یک سطح پنهان‌اند (کلید → دلیل). خالی = هیچ استثنایی.
_INTENTIONALLY_HIDDEN: dict = {}


def _spec_names() -> set:
    import wiring  # noqa: WPS433
    return {n for n, _m, _f in wiring._BUSINESS_LEGS_SPEC}


class TestLegRegistryParity(unittest.TestCase):

    def test_spec_is_not_empty(self):
        """گاردِ ضدِ سبزِ توخالی: اگر spec خالی شود بقیهٔ assertها بی‌معنا سبز می‌شوند."""
        self.assertGreaterEqual(len(_spec_names()), 5)

    def test_every_leg_appears_in_telegram_organ_menu(self):
        from approval_channel import TelegramApprovalChannel as _AC  # noqa: WPS433
        organs = {k for k, *_rest in _AC.ORGANS}
        missing = _spec_names() - organs - set(_INTENTIONALLY_HIDDEN)
        self.assertFalse(missing,
                         f"این پاها در منویِ ارگانِ تلگرام نامرئی‌اند: {sorted(missing)} — "
                         "یا به ORGANS اضافه کن یا با دلیل در _INTENTIONALLY_HIDDEN")

    def test_every_leg_appears_in_weekly_review(self):
        import weekly_review  # noqa: WPS433
        missing = _spec_names() - set(weekly_review.BUSINESS_LEGS) - set(_INTENTIONALLY_HIDDEN)
        self.assertFalse(missing,
                         f"سکوتِ این پاها در گزارشِ هفتگی دیده نمی‌شود: {sorted(missing)}")

    def test_weekly_review_display_labels_exist(self):
        """هر پایی که در گزارش هست باید برچسب داشته باشد وگرنه کلیدِ خام رندر می‌شود."""
        import weekly_review  # noqa: WPS433
        for leg in weekly_review.BUSINESS_LEGS:
            self.assertIn(leg, weekly_review.DISPLAY, f"برچسبِ نمایشیِ «{leg}» نیست")

    def test_project_f_label_is_content_free_everywhere(self):
        """قاعدهٔ قفل‌شدهٔ #۷: بیرون از پوشهٔ پروژه فقط کدِ «Project-F»."""
        import weekly_review  # noqa: WPS433
        from approval_channel import TelegramApprovalChannel as _AC  # noqa: WPS433
        labels = [weekly_review.DISPLAY.get("studio_pf", "")]
        labels += [lbl for k, lbl, *_r in _AC.ORGANS if k == "studio_pf"]
        for lbl in labels:
            self.assertTrue(lbl, "برچسبِ studio_pf خالی است")
            for banned in ("اونلی", "onlyfans", "OnlyFans", "استودیو"):
                self.assertNotIn(banned, lbl,
                                 f"برچسبِ «{lbl}» نامِ پروژه/پلتفرم را بیرون می‌برد")

    def test_every_leg_module_is_importable(self):
        """رجیستری نباید به ماژولی اشاره کند که وجود ندارد (fail-soft پنهانش می‌کند)."""
        import importlib
        import wiring  # noqa: WPS433
        broken = []
        for name, mod_name, fn_name in wiring._BUSINESS_LEGS_SPEC:
            try:
                mod = importlib.import_module(mod_name)
                if not callable(getattr(mod, fn_name, None)):
                    broken.append(f"{name}: {mod_name}.{fn_name} صدازدنی نیست")
            except Exception as exc:  # noqa: BLE001
                broken.append(f"{name}: import {mod_name} → {type(exc).__name__}")
        self.assertFalse(broken, "رجیستری به ماژول/تابعِ ناموجود اشاره می‌کند: " + str(broken))


if __name__ == "__main__":
    unittest.main(verbosity=2)
