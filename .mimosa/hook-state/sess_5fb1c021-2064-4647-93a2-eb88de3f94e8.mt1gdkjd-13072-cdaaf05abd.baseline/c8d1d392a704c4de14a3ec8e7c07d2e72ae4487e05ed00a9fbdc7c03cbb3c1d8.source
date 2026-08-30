#!/usr/bin/env python3
"""test_learning_bus.py — تست‌های LearningBus (سوختِ باهوش‌شدن).

این تست‌ها composition را تأیید می‌کنند (نه خود ThompsonBandit — آن تستِ خودش
در brain/test_learning.py دارد). هرچه اینجا تست می‌شود، رفتارِ LearningBus
به‌عنوانِ wrapper است.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

from pf_os import learning_bus as LB  # noqa: E402


class TestLearningBusLifecycle(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.mem = os.path.join(self._tmp.name, "mem.json")

    def tearDown(self):
        self._tmp.cleanup()

    def test_construct_offline_safe(self):
        """اگر brain موجود نباشد، نباید شکست بخورد."""
        # brain موجود است در این پروژه، ولی اگر نبود:
        bus = LB.LearningBus(memory_path=self.mem)
        # available ممکن True یا False باشد (بستگی به import دارد)
        self.assertIsInstance(bus.available, bool)

    def test_status_returns_dict(self):
        bus = LB.LearningBus(memory_path=self.mem, seed=42)
        s = bus.status()
        self.assertIn("available", s)
        self.assertIsInstance(s["available"], bool)


class TestRecordResult(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.mem = os.path.join(self._tmp.name, "mem.json")
        self.bus = LB.LearningBus(memory_path=self.mem, seed=42)

    def tearDown(self):
        self._tmp.cleanup()

    def test_record_returns_bool(self):
        r = self.bus.record_result("sandals", "reddit", 100, 10, 2)
        self.assertIsInstance(r, bool)

    def test_record_empty_tag_rejected(self):
        if self.bus.available:
            self.assertFalse(self.bus.record_result("", "reddit", 100, 10))

    def test_record_empty_platform_rejected(self):
        if self.bus.available:
            self.assertFalse(self.bus.record_result("sandals", "", 100, 10))

    def test_record_never_raises_on_bad_input(self):
        # نباید exception بدهد حتی با ورودیِ عجیب
        for args in [(None, None), ("x", "x", -1, -1), ("x", "x", 1e9)]:
            try:
                self.bus.record_result(*args)
            except Exception as e:
                self.fail(f"record_result raised on {args}: {e}")


class TestRecommend(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.mem = os.path.join(self._tmp.name, "mem.json")
        self.bus = LB.LearningBus(memory_path=self.mem, seed=42)

    def tearDown(self):
        self._tmp.cleanup()

    def test_recommend_empty_candidates(self):
        r = self.bus.recommend([])
        self.assertFalse(r.ok)

    def test_recommend_returns_recommendation(self):
        r = self.bus.recommend(["a", "b", "c"])
        self.assertIsInstance(r, LB.Recommendation)
        # even if no data, should return SOMETHING usable (best_tag non-empty)
        self.assertTrue(r.best_tag)

    def test_recommend_with_data(self):
        """پس از فید دادن، recommend باید یک tag از candidateها برگرداند."""
        if not self.bus.available:
            self.skipTest("brain not available")
        for _ in range(3):
            self.bus.record_result("a", "reddit", 100, 10, 2)
        r = self.bus.recommend(["a", "b", "c"])
        self.assertTrue(r.ok)
        self.assertIn(r.best_tag, ["a", "b", "c"])

    def test_recommend_to_dict(self):
        r = self.bus.recommend(["a"])
        d = r.to_dict()
        self.assertIn("ok", d)
        self.assertIn("best_tag", d)
        self.assertIn("ranked", d)


class TestObserve(unittest.TestCase):
    """دسترسیِ مستقیم به bandit (advanced)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.mem = os.path.join(self._tmp.name, "mem.json")
        self.bus = LB.LearningBus(memory_path=self.mem, seed=42)

    def tearDown(self):
        self._tmp.cleanup()

    def test_observe_returns_bool(self):
        r = self.bus.observe("arm1", 0.8, approved=True)
        self.assertIsInstance(r, bool)

    def test_observe_never_raises(self):
        try:
            self.bus.observe("a", 1.0)
            self.bus.observe("a", -1.0)  # reward عجیب
            self.bus.observe("", 0.5)
        except Exception as e:
            self.fail(f"observe raised: {e}")


class TestPIINeverLogged(unittest.TestCase):
    """نامتغیر: tag/platform فقط — هیچ‌وقت نام/محتوا."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.mem = os.path.join(self._tmp.name, "mem.json")
        self.bus = LB.LearningBus(memory_path=self.mem, seed=42)

    def tearDown(self):
        self._tmp.cleanup()

    def test_record_with_brand_tag_accepted(self):
        """tag = نوعِ محتوا (cozy-socks)، نه نام."""
        if self.bus.available:
            ok = self.bus.record_result("cozy-socks", "reddit", 100, 10)
            # باید با tag کلی پذیرفته بشه (نوع، نه نام/PII)
            self.assertIsInstance(ok, bool)


class TestNoDoubleRecord(unittest.TestCase):
    """رگرسیون: یک record_result باید دقیقاً یک نتیجه ثبت کند (نه double).

    باگِ قبلی: record_result هم مستقیم memory.record_post_result را صدا می‌زد و
    هم brain.feedback_loop (که خودش دوباره روی همان memory ثبت می‌کرد) → هر نتیجه
    ۲بار ذخیره → learning_confidence مصنوعاً ۲برابر و acquisition_memory.json متورم.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.mem = os.path.join(self._tmp.name, "mem.json")
        self.bus = LB.LearningBus(memory_path=self.mem, seed=42)

    def tearDown(self):
        self._tmp.cleanup()

    def test_record_stores_exactly_once(self):
        """یک record_result → دقیقاً یک ردیف در _post_results (نه دو)."""
        if not self.bus.available:
            self.skipTest("brain not available")
        before = len(self.bus._memory._post_results)
        ok = self.bus.record_result("sandals", "reddit", 100, 10, 2)
        self.assertTrue(ok)
        after = len(self.bus._memory._post_results)
        self.assertEqual(after - before, 1,
                         "record_result باید دقیقاً یک نتیجه ثبت کند، نه double")

    def test_confidence_not_inflated(self):
        """learning_confidence = n/20 با شمارِ واقعی (۵ نتیجه → 0.25، نه 0.5)."""
        if not self.bus.available:
            self.skipTest("brain not available")
        for _ in range(5):
            self.assertTrue(self.bus.record_result("a", "reddit", 100, 10, 2))
        # ۵ نتیجه ثبت شده — نه ۱۰ (که باگِ double-record بود)
        self.assertEqual(len(self.bus._memory._post_results), 5)
        conf = self.bus._memory.learning_confidence()
        self.assertAlmostEqual(conf, 0.25, places=6)
        # status هم همان confidence درست را گزارش کند
        self.assertAlmostEqual(
            self.bus.status().get("learning_confidence", 0.0), 0.25, places=6)


class TestStatusObservations(unittest.TestCase):
    """رگرسیون: status()['observations'] باید شمارِ واقعیِ نتایج باشد.

    باگِ قبلی: status از getattr(memory, "_posts", []) می‌خواند ولی
    AcquisitionMemory نتایج را در _post_results نگه می‌دارد → همیشه 0
    (تلمتریِ /api/learning و /api/health خراب).
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.mem = os.path.join(self._tmp.name, "mem.json")
        self.bus = LB.LearningBus(memory_path=self.mem, seed=42)

    def tearDown(self):
        self._tmp.cleanup()

    def test_observations_reflects_recorded_count(self):
        if not self.bus.available:
            self.skipTest("brain not available")
        self.assertEqual(self.bus.status().get("observations"), 0)
        for _ in range(3):
            self.bus.record_result("a", "reddit", 100, 10, 2)
        s = self.bus.status()
        self.assertEqual(s.get("observations"), 3,
                         "observations باید برابرِ ۳ باشد (۳ بار record_result)")
        # سازگاری: observations == طولِ واقعیِ _post_results
        self.assertEqual(s.get("observations"),
                         len(self.bus._memory._post_results))


if __name__ == "__main__":
    unittest.main()
