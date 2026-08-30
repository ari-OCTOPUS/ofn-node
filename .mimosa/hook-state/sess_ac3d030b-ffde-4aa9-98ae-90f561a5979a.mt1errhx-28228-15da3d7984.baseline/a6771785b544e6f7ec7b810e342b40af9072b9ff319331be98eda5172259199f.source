"""تستِ استقلالِ نویزِ مشاهده از سیگنال در ar1_plus_noise (فیکسِ هم‌جریانیِ seed)."""
from tests import _bootstrap  # noqa: F401

import unittest

import numpy as np

from data.synthetic import ar1, ar1_plus_noise


class TestObservationNoiseIndependence(unittest.TestCase):
    def test_noise_uncorrelated_with_signal(self):
        """corr(s, ε) باید ~۰ باشد — قبلاً با seed یکسان ~۰٫۷ بود (کپیِ نوآوری‌ها)."""
        n, rho, ss, ns, seed = 20000, 0.7, 0.1, 0.3, 7
        y = ar1_plus_noise(n, rho=rho, signal_sigma=ss, noise_sigma=ns, seed=seed)
        s = ar1(n, rho, ss, seed=seed)          # همان سیگنالِ درونی
        eps = y - s                              # نویزِ مشاهده‌ی بازسازی‌شده
        corr = float(np.corrcoef(s, eps)[0, 1])
        self.assertLess(abs(corr), 0.05,
                        f"نویزِ مشاهده با سیگنال همبسته است (corr={corr:.3f})")

    def test_noise_std_correct(self):
        """σ نویزِ مشاهده باید ~noise_sigma باشد (نه مقیاسِ عجیبِ دیگری)."""
        n, seed = 20000, 3
        y = ar1_plus_noise(n, rho=0.7, signal_sigma=0.1, noise_sigma=0.3, seed=seed)
        s = ar1(n, 0.7, 0.1, seed=seed)
        self.assertAlmostEqual(float(np.std(y - s)), 0.3, delta=0.02)

    def test_reproducible_with_seed(self):
        a = ar1_plus_noise(5000, rho=0.7, seed=42)
        b = ar1_plus_noise(5000, rho=0.7, seed=42)
        self.assertTrue(np.array_equal(a, b))

    def test_different_seeds_differ(self):
        a = ar1_plus_noise(5000, rho=0.7, seed=1)
        b = ar1_plus_noise(5000, rho=0.7, seed=2)
        self.assertFalse(np.array_equal(a, b))


if __name__ == "__main__":
    unittest.main()
