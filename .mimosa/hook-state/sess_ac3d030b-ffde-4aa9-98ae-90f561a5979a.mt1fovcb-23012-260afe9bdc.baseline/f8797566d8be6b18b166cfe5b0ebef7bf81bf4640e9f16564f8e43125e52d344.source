"""تستِ مرزِ دانش — باندبندیِ علامت‌دارِ کشیدگی (فیکسِ abs-on-kurtosis)."""
from tests import _bootstrap  # noqa: F401

import unittest

from brain.frontier import (_band, cell_key, KURT_EDGES, RHO_EDGES,
                            SOURCE_FAMILIES, TOTAL_CELLS)


class TestKurtosisBanding(unittest.TestCase):
    def test_subgaussian_band_reachable(self):
        """kurt=-0.6 باید در باندِ ۰ (زیرگوسی) بیفتد — قبلاً دست‌نیافتنی بود."""
        self.assertEqual(_band(-0.6, KURT_EDGES, signed=True), 0)

    def test_sub_and_super_gaussian_distinct_cells(self):
        """سریِ زیرگوسی و فوق‌گوسی نباید در یک خانه‌ی مرز بیفتند."""
        k_sub = cell_key("synthetic:x", rho=0.3, kurt=-0.6, detectable=True)
        k_sup = cell_key("synthetic:x", rho=0.3, kurt=+0.6, detectable=True)
        self.assertNotEqual(k_sub, k_sup)

    def test_near_zero_kurt_band(self):
        """kurt در (-۰٫۵..۰٫۵) → باندِ ۱ (تقریباً گوسی)."""
        self.assertEqual(_band(-0.4, KURT_EDGES, signed=True), 1)
        self.assertEqual(_band(0.0, KURT_EDGES, signed=True), 1)
        self.assertEqual(_band(0.4, KURT_EDGES, signed=True), 1)

    def test_rho_stays_unsigned(self):
        """محورِ ρ عمداً قدرِ مطلق است (قدرتِ حافظه): -۰٫۳ و +۰٫۳ یک خانه."""
        k_neg = cell_key("synthetic:x", rho=-0.3, kurt=2.0, detectable=True)
        k_pos = cell_key("synthetic:x", rho=+0.3, kurt=2.0, detectable=True)
        self.assertEqual(k_neg, k_pos)

    def test_total_cells_now_truthful(self):
        """با فیکس، هر ۷ باندِ کشیدگی دست‌یافتنی‌اند → مخرجِ ۵۶۰ صادق است."""
        expected = (len(SOURCE_FAMILIES) * (len(RHO_EDGES) + 1)
                    * (len(KURT_EDGES) + 1) * 2)
        self.assertEqual(TOTAL_CELLS, expected)
        self.assertEqual(TOTAL_CELLS, 560)
        # همه‌ی باندهای کشیدگی قابلِ‌رسیدن:
        reachable = {_band(v, KURT_EDGES, signed=True)
                     for v in [-1.0, -0.1, 1.0, 2.0, 4.0, 8.0, 20.0]}
        self.assertEqual(reachable, set(range(len(KURT_EDGES) + 1)))


if __name__ == "__main__":
    unittest.main()
