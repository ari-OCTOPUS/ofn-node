"""تستِ B4/B7: fallback با seed متغیر + throttle مستقلِ per-source."""
from tests import _bootstrap  # noqa: F401

import unittest

import numpy as np

import data.real_api as ra


class TestFallbackVariedSeed(unittest.TestCase):
    def test_two_fallbacks_differ(self):
        """قبلاً seed ثابت ۹۹ → سریِ بایت‌به‌بایت یکسان بارها واردِ آمار می‌شد."""
        a = ra._fallback("test-a")
        b = ra._fallback("test-b")
        self.assertFalse(np.array_equal(a["series"], b["series"]))
        self.assertNotEqual(a["info"]["seed"], b["info"]["seed"])

    def test_honest_labels(self):
        r = ra._fallback("why")
        self.assertEqual(r["source"], "synthetic_fallback")
        self.assertTrue(r["label"].startswith("[SYNTHETIC FALLBACK]"))
        self.assertTrue(r["info"]["fallback"])


class TestPerSourceThrottle(unittest.TestCase):
    def setUp(self):
        # ایزوله‌سازیِ تایمرها + حذفِ فاصله‌ی سراسری برای تستِ قطعی
        self._g = ra._GLOBAL_MIN_INTERVAL
        self._m = ra._MIN_LIVE_INTERVAL
        ra._GLOBAL_MIN_INTERVAL = 0.0
        ra._last_live_fetch[0] = 0.0
        ra._last_live_by_source.clear()

    def tearDown(self):
        ra._GLOBAL_MIN_INTERVAL = self._g
        ra._MIN_LIVE_INTERVAL = self._m
        ra._last_live_fetch[0] = 0.0
        ra._last_live_by_source.clear()

    def test_same_source_throttled_other_source_not(self):
        """رگرسیونِ باگِ قدیم: تایمرِ سراسری منبعِ دوم را هم مسدود می‌کرد."""
        self.assertFalse(ra._throttled("src-A"))   # اولین دریافت: آزاد
        self.assertTrue(ra._throttled("src-A"))    # همان منبع بلافاصله: مسدود
        self.assertFalse(ra._throttled("src-B"))   # منبعِ دیگر: آزاد (فیکسِ B4)
        self.assertTrue(ra._throttled("src-B"))


class TestRetryHelper(unittest.TestCase):
    def test_retries_then_succeeds(self):
        import requests
        calls = {"n": 0}

        real_exc = requests.exceptions.ConnectionError("blip")

        def fake_get(url, **kw):
            calls["n"] += 1
            if calls["n"] < 2:
                raise real_exc
            return "OK"

        from unittest import mock
        with mock.patch("requests.get", side_effect=fake_get), \
             mock.patch("time.sleep"):
            out = ra._requests_get("http://x")
        self.assertEqual(out, "OK")
        self.assertEqual(calls["n"], 2)

    def test_raises_after_all_attempts(self):
        import requests
        from unittest import mock
        err = requests.exceptions.Timeout("t")
        with mock.patch("requests.get", side_effect=err), \
             mock.patch("time.sleep"):
            with self.assertRaises(requests.exceptions.Timeout):
                ra._requests_get("http://x")


if __name__ == "__main__":
    unittest.main()
