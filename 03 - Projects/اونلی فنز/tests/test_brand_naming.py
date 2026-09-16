#!/usr/bin/env python3
"""test_brand_naming.py — تست‌های سیستمِ انتخابِ پویای نامِ برند (۲۰۲۶-۰۷-۲۵).

پوشش:
  ۱) flag-off: propose_next نامِ اولیه (seed) را برمی‌گرداند — نه Thompson.
  ۲) flag-on: propose_next یک نام از candidates پیشنهاد می‌دهد + شفافیت.
  ۳) record_feedback: reward ثبت می‌شود و بر رتبه‌بندی اثر می‌گذارد.
  ۴) add_candidate: نامِ جدید اضافه می‌شود (propose-only، idempotent).
  ۵) metric نامعتبر رد می‌شود.
  ۶) هرگز PII/محتوا به cortex نمی‌رود (این ماژول cortex را صدا نمی‌زند).
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

_PROJ = Path(__file__).resolve().parent.parent
for _p in (str(_PROJ), str(_PROJ / "brain")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from brain import brand_naming  # noqa: E402


class TestBrandNaming(unittest.TestCase):
    def setUp(self):
        os.environ.pop(brand_naming.FLAG, None)
        self._tmp = tempfile.mkdtemp(prefix="brand-test-")

    def tearDown(self):
        os.environ.pop(brand_naming.FLAG, None)
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _bn(self, candidates=None):
        return brand_naming.BrandNaming(data_dir=self._tmp, candidates=candidates)

    # ═══ ۱) flag-off = seed ════════════════════════════════════════════════
    def test_flag_off_returns_seed(self):
        bn = self._bn(candidates=["Name A", "Name B"])
        out = bn.propose_next()
        self.assertEqual(out["name"], "Name A",
                         "flag-off: نامِ اولیه (seed) باید پیشنهاد شود")
        self.assertIn("flag-off", out["reason"])

    # ═══ ۲) flag-on = Thompson + explain ═══════════════════════════════════
    def test_flag_on_proposes_with_explain(self):
        os.environ[brand_naming.FLAG] = "1"
        bn = self._bn(candidates=["Name A", "Name B"])
        out = bn.propose_next()
        self.assertIn(out["name"], ("Name A", "Name B"),
                      "flag-on: نام باید یکی از candidates باشد")
        self.assertIn("explain", out)
        self.assertIsInstance(out["explain"], dict)

    # ═══ ۳) record_feedback اثر می‌گذارد ═══════════════════════════════════
    def test_feedback_affects_ranking(self):
        os.environ[brand_naming.FLAG] = "1"
        bn = self._bn(candidates=["Strong", "Weak"])
        # Strong را با reward بالا، Weak را با reward پایین ثبت کن
        for _ in range(20):
            bn.record_feedback("Strong", "manual_rating", 0.9, approved=True)
        for _ in range(20):
            bn.record_feedback("Weak", "manual_rating", 0.1, approved=True)
        out = bn.propose_next()
        explain = out["explain"].get("arms", {})
        # meanِ Strong باید بالاتر از Weak باشد (با دادهٔ کافی)
        self.assertGreater(explain.get("Strong", {}).get("mean", 0),
                           explain.get("Weak", {}).get("mean", 1),
                           "Strong با reward بالا باید mean بالاتر داشته باشه")

    # ═══ ۴) add_candidate idempotent ═══════════════════════════════════════
    def test_add_candidate_idempotent(self):
        bn = self._bn(candidates=["Existing"])
        self.assertTrue(bn.add_candidate("New Name"),
                        "نامِ جدید باید اضافه شود")
        self.assertFalse(bn.add_candidate("New Name"),
                         "نامِ تکراری نباید دوباره اضافه شود")
        self.assertIn("New Name", bn.candidates())

    # ═══ ۵) metric نامعتبر رد ══════════════════════════════════════════════
    def test_invalid_metric_rejected(self):
        bn = self._bn(candidates=["X"])
        self.assertFalse(bn.record_feedback("X", "bogus_metric", 0.5),
                         "metric نامعتبر باید رد شود")
        # metric معتبر باید پذیرفته شود
        self.assertTrue(bn.record_feedback("X", "ctr", 0.3),
                        "metric معتبر باید پذیرفته شود")

    # ═══ ۶) status structure ═══════════════════════════════════════════════
    def test_status_structure(self):
        bn = self._bn(candidates=["A", "B"])
        s = bn.status()
        self.assertIn("candidates", s)
        self.assertIn("flag_on", s)
        self.assertEqual(s["candidates"], ["A", "B"])

    # ═══ ۷) محتوای نام هرگز PII واقعی نیست ════════════════════════════════
    def test_no_real_pii_in_default_candidates(self):
        """نام‌های seed نباید اسمِ واقعیِ اشخاص داشته باشن."""
        for c in brand_naming.DEFAULT_CANDIDATES:
            low = c.lower()
            for bad in ("محبی", "armin", "saba", "mohebiazal"):
                self.assertNotIn(bad, low,
                                 f"نامِ برند نباید PII داشته باشه: {bad}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
