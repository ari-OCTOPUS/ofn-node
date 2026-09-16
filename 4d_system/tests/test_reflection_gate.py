"""تستِ گیتِ بازتاب (B1) — منطقِ خالص در brain/patterns.py."""
from tests import _bootstrap  # noqa: F401

import os
import unittest
from unittest import mock

from brain.patterns import reflect_should_revise, ReflectionGate


class TestReflectGateFlagOff(unittest.TestCase):
    """فلگ خاموش = مثلِ قبل REVISE را دنبال می‌کند، ولی زیرِ سقفِ سختِ بی‌قیدوشرط."""

    def test_mirrors_revise_under_hard_cap(self):
        with mock.patch.dict(os.environ, {"REFLECT_GATE": "0"}):
            # زیرِ سقفِ سخت (۵) → مثلِ قبل REVISE را دنبال می‌کند
            self.assertTrue(reflect_should_revise({"quality": "REVISE",
                                                   "reflect_count": 0}))
            self.assertFalse(reflect_should_revise({"quality": "ACCEPT"}))
            self.assertFalse(reflect_should_revise({}))

    def test_hard_cap_bounds_loop_even_with_flag_off(self):
        # فیکسِ بازبینی: فلگ خاموش دیگر بی‌سقف نیست (حلقه‌ی ابری منفجر نمی‌شود)
        with mock.patch.dict(os.environ, {"REFLECT_GATE": "0", "REFLECT_HARD_MAX": "5"}):
            self.assertFalse(reflect_should_revise({"quality": "REVISE",
                                                    "reflect_count": 5}))
            self.assertFalse(reflect_should_revise({"quality": "REVISE",
                                                    "reflect_count": 999}))


class TestReflectGateFlagOn(unittest.TestCase):
    def test_caps_at_reflect_max(self):
        with mock.patch.dict(os.environ, {"REFLECT_GATE": "1", "REFLECT_MAX": "3"}):
            s = {"quality": "REVISE"}
            self.assertTrue(reflect_should_revise({**s, "reflect_count": 0}))
            self.assertTrue(reflect_should_revise({**s, "reflect_count": 2}))
            self.assertFalse(reflect_should_revise({**s, "reflect_count": 3}))
            self.assertFalse(reflect_should_revise({**s, "reflect_count": 10}))

    def test_non_revise_never_loops(self):
        with mock.patch.dict(os.environ, {"REFLECT_GATE": "1"}):
            self.assertFalse(reflect_should_revise({"quality": "ACCEPT",
                                                    "reflect_count": 0}))

    def test_explicit_cap_overrides_env(self):
        with mock.patch.dict(os.environ, {"REFLECT_GATE": "1", "REFLECT_MAX": "9"}):
            s = {"quality": "REVISE", "reflect_count": 1}
            self.assertFalse(reflect_should_revise(s, max_reflections=1))


class TestReflectionGateDataclass(unittest.TestCase):
    """قراردادِ ReflectionGate (الگوی طراحی) سرِ جایش بماند."""

    def test_hard_cap(self):
        rg = ReflectionGate(max_reflections=3)
        rg.update(1.0)  # gain بالا
        self.assertTrue(rg.should_reflect(2))
        self.assertFalse(rg.should_reflect(3))

    def test_low_gain_stops(self):
        rg = ReflectionGate(cost_per_reflection=0.02)
        rg.update(0.005)
        self.assertFalse(rg.should_reflect(0))


if __name__ == "__main__":
    unittest.main()
