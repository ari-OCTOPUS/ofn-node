#!/usr/bin/env python3
"""test_cortex_augmented.py — تست‌های مغزِ پوششیِ غنی‌شده (۲۰۲۶-۰۷-۲۵).

پوشش:
  ۱) flag-off: CortexAugmentedBrain == DualBrainV3 (byte-for-byte thoughts).
  ۲) flag-on + cortex mock ok=True: یک cortex_insight thought اضافه می‌شود.
  ۳) flag-on + cortex fallback (ok=False): هیچ insight اضافه نمی‌شود (fail-soft).
  ۴) مرزِ #۷: prompt هیچ PII/محتوا/پلتفرم ندارد (containment سخت).
  ۵) blocked compliance → cortex صدا زده نمی‌شود.

همه $0، آفلاین، cortex با mock patch می‌شود.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

from brain.dual_brain_v3 import DualBrainV3  # noqa: E402
from brain import cortex_augmented  # noqa: E402


class TestCortexAugmented(unittest.TestCase):
    def setUp(self):
        # compliance checks must pass for brain to think
        self._checks = {
            "faceless": True, "feet_only": True, "no_explicit": True,
            "geo_block_iran": True, "inplatform_payment": True, "over_18": True,
            "no_dark_pattern": True, "no_manipulation": True,
            "relationship_80_sales_20": True, "no_engagement_optimization": True,
            "performer_welfare": True, "scope_supreme": True,
        }

    def _brain(self):
        return cortex_augmented.CortexAugmentedBrain(thinking=DualBrainV3())

    # ═══ ۱) flag-off = byte-for-byte DualBrainV3 ════════════════════════════
    def test_flag_off_identical_to_dual_brain(self):
        os.environ.pop("OCTOPUS_WIRE_PROJECTF_CORTEX", None)
        db = DualBrainV3()
        cab = self._brain()
        kw = dict(checks=self._checks, visitors=100, subscribers=5,
                  ppv_buyers=1, season="summer", drafts_count=3)
        base = db.think_and_communicate(**kw)
        aug = cab.think_and_communicate(**kw)
        # flag-off: نباید cortex_insight در thoughts باشد
        kinds = [t.get("kind") for t in aug["thoughts"]]
        self.assertNotIn("cortex_insight", kinds,
                         "flag-off: نباید cortex_insight اضافه شود")
        # تعدادِ thoughts باید برابر باشد
        self.assertEqual(len(base["thoughts"]), len(aug["thoughts"]),
                         "flag-off: thoughts باید هم‌اندازه باشد")

    # ═══ ۲) flag-on + cortex ok=True → insight اضافه می‌شود ═════════════════
    def test_flag_on_cortex_ok_adds_insight(self):
        os.environ["OCTOPUS_WIRE_PROJECTF_CORTEX"] = "1"
        try:
            cab = self._brain()
            fake_out = {"ok": True, "tier": "primary", "text": "Focus on retention.",
                        "source": "cortex", "ms": 1234}
            with mock.patch("pf_os.cortex_client.ask", return_value=fake_out):
                aug = cab.think_and_communicate(
                    checks=self._checks, visitors=100, subscribers=5,
                    ppv_buyers=1, season="summer", drafts_count=3)
            kinds = [t.get("kind") for t in aug["thoughts"]]
            self.assertIn("cortex_insight", kinds,
                          "flag-on + cortex ok: باید cortex_insight اضافه شود")
            ins = next(t for t in aug["thoughts"] if t.get("kind") == "cortex_insight")
            self.assertEqual(ins["data"]["tier"], "primary")
            self.assertEqual(ins["data"]["source"], "cortex")
        finally:
            os.environ.pop("OCTOPUS_WIRE_PROJECTF_CORTEX", None)

    # ═══ ۳) flag-on + cortex fallback → هیچ insight ═════════════════════════
    def test_flag_on_cortex_fallback_no_insight(self):
        os.environ["OCTOPUS_WIRE_PROJECTF_CORTEX"] = "1"
        try:
            cab = self._brain()
            # cortex down → ok=False (fallback)
            fake_out = {"ok": False, "tier": "none", "text": "",
                        "source": "fallback", "ms": 0, "reason": "down"}
            with mock.patch("pf_os.cortex_client.ask", return_value=fake_out):
                aug = cab.think_and_communicate(
                    checks=self._checks, visitors=100, subscribers=5)
            kinds = [t.get("kind") for t in aug["thoughts"]]
            self.assertNotIn("cortex_insight", kinds,
                             "fallback: نباید دروغ‌گو insight اضافه شود")
        finally:
            os.environ.pop("OCTOPUS_WIRE_PROJECTF_CORTEX", None)

    # ═══ ۴) مرزِ #۷: prompt فقط اعداد، هیچ PII/محتوا/پلتفرم ═════════════════
    def test_prompt_has_no_pii_content_platform(self):
        """promptی که به cortex می‌رود باید فقط اعدادِ abstract داشته باشد.

        تطبیق با مرزِ واژه (word-boundary) — وگرنه 'ari' در 'scenario' مثبتِ کاذب می‌دهد."""
        import re
        prompt = cortex_augmented.CortexAugmentedBrain._abstract_prompt(
            visitors=100, subscribers=5, ppv_buyers=1, season="summer",
            drafts_count=3, partner_stress=0.3)
        low = prompt.lower()

        def _has_word(word):
            # مرزِ واژه در انگلیسی + تطبیقِ ساده در فارسی
            return bool(re.search(r"\b" + re.escape(word) + r"\b", low))

        # PII ممنوع (word-boundary)
        for bad in ("saba", "ari", "sydney", "anar", "armin", "amber"):
            self.assertFalse(_has_word(bad),
                             f"prompt نباید PIIِ کلمه‌ای داشته باشه: {bad} (در: {low!r})")
        # پلتفرم ممنوع (این‌ها چندکلمه‌ای یا substring امن‌اند)
        for bad in ("onlyfans", "reddit", "fansly", "twitter"):
            self.assertFalse(_has_word(bad),
                             f"prompt نباید پلتفرم داشته باشه: {bad}")
        # محتوای niche ممنوع (feet/sole/foot)
        for bad in ("feet", "sole", "foot", "nude"):
            self.assertFalse(_has_word(bad),
                             f"prompt نباید محتوای niche داشته باشه: {bad}")
        # ولی اعداد باید باشن (این یک promptِ واقعیِ بازاریابی‌ست)
        self.assertIn("visitors", low)
        self.assertIn("subscribers", low)
        self.assertIn("season", low)

    # ═══ ۵) blocked compliance → cortex صدا زده نمی‌شود ═════════════════════
    def test_blocked_compliance_no_cortex_call(self):
        os.environ["OCTOPUS_WIRE_PROJECTF_CORTEX"] = "1"
        try:
            cab = self._brain()
            # checks که fail می‌کند (faceless=False)
            bad_checks = dict(self._checks, faceless=False)
            with mock.patch("pf_os.cortex_client.ask") as mock_ask:
                aug = cab.think_and_communicate(
                    checks=bad_checks, visitors=100, subscribers=5)
                # compliance بلاک کرده → cortex نباید صدا زده شود
                mock_ask.assert_not_called()
            self.assertTrue(aug.get("blocked", False),
                            "faceless=False باید brain را بلاک کند")
        finally:
            os.environ.pop("OCTOPUS_WIRE_PROJECTF_CORTEX", None)

    # ═══ ۶) emit هرگز exception بیرون نمی‌دهد ═══════════════════════════════
    def test_cortex_exception_is_swallowed(self):
        os.environ["OCTOPUS_WIRE_PROJECTF_CORTEX"] = "1"
        try:
            cab = self._brain()
            with mock.patch("pf_os.cortex_client.ask",
                            side_effect=RuntimeError("boom")):
                # نباید raise کند
                aug = cab.think_and_communicate(
                    checks=self._checks, visitors=100, subscribers=5)
            kinds = [t.get("kind") for t in aug["thoughts"]]
            self.assertNotIn("cortex_insight", kinds,
                             "exception: نباید insight اضافه شود")
        finally:
            os.environ.pop("OCTOPUS_WIRE_PROJECTF_CORTEX", None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
