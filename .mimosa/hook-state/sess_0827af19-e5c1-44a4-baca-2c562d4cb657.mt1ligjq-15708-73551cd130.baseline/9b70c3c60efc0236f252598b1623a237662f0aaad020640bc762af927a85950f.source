"""تستِ MI غیرخطی (B12) — آشوبِ قطعی باید دیده شود، نویزِ خالص نه."""
from tests import _bootstrap  # noqa: F401

import unittest

import numpy as np

from core.nonlinear_mi import binned_mi_lag, gaussian_mi_lag1, nonlinear_gain


def _ar1(n, rho, sigma, seed):
    rng = np.random.default_rng(seed)
    s = np.zeros(n)
    noise = rng.normal(0, sigma, n)
    for t in range(1, n):
        s[t] = rho * s[t - 1] + noise[t]
    return s


def _logistic(n, r=3.9, x0=0.5):
    x = np.zeros(n)
    x[0] = x0
    for t in range(n - 1):
        x[t + 1] = r * x[t] * (1 - x[t])
    return x


class TestBinnedMI(unittest.TestCase):
    def test_iid_noise_near_zero(self):
        rng = np.random.default_rng(1)
        mi = binned_mi_lag(rng.normal(0, 1, 30000))
        self.assertLess(mi, 0.03, f"نویزِ iid نباید MI معنادار بدهد (شد {mi:.4f})")

    def test_ar1_positive(self):
        mi = binned_mi_lag(_ar1(30000, 0.7, 0.1, seed=2))
        self.assertGreater(mi, 0.15)

    def test_chaos_visible_to_nonlinear_only(self):
        """نکته‌ی اصلیِ B12: logistic map برای تخمین‌گرِ خطی کم‌رنگ است ولی
        MI باندی آن را چند برابر قوی‌تر می‌بیند (وابستگیِ قطعیِ غیرخطی)."""
        lg = _logistic(30000)
        g = nonlinear_gain(lg)
        self.assertGreater(g["mi_nonlinear"], 0.5)
        self.assertGreater(g["mi_nonlinear"], 4 * g["mi_linear"])
        self.assertGreater(g["gain"], 0.4)

    def test_deterministic(self):
        s = _ar1(5000, 0.5, 0.1, seed=3)
        self.assertEqual(binned_mi_lag(s), binned_mi_lag(s))

    def test_guards(self):
        self.assertEqual(binned_mi_lag(np.ones(5000)), 0.0)     # سریِ ثابت
        self.assertEqual(binned_mi_lag(np.arange(20)), 0.0)     # خیلی کوتاه
        self.assertEqual(gaussian_mi_lag1(np.ones(100)), 0.0)

    def test_monotone_invariance(self):
        """rank-bins باید به تبدیلِ یکنوا (مثلاً exp) بی‌تفاوت باشد."""
        s = _ar1(20000, 0.6, 0.1, seed=4)
        a = binned_mi_lag(s)
        b = binned_mi_lag(np.exp(s))
        self.assertAlmostEqual(a, b, delta=0.02)


if __name__ == "__main__":
    unittest.main()
