"""تستِ dedup هم‌جنس در autoloop._save_pattern.

باگِ قبلی: temporal_mi فعلی با delta_self ذخیره‌شده (که در واقع E_shadow_proxy است)
مقایسه می‌شد — دو کمیتِ بی‌ربط. نتیجه: dedup تصادفی.
"""
from tests import _bootstrap  # noqa: F401

import unittest
from unittest import mock

from brain.autoloop import AutoLoopEngine


def _analysis(e_shadow: float, mi: float = 0.02) -> dict:
    return {
        "source": "synthetic:ar1",
        "temporal_mi": mi,
        "E_shadow_proxy": e_shadow,
        "rho_hat": 0.7,
        "detectable": True,
    }


class TestDedupSameQuantity(unittest.TestCase):
    def setUp(self):
        self.engine = AutoLoopEngine()
        self.existing = [{"tags": "auto,synthetic:ar1", "delta_self": 0.5}]

    def test_duplicate_within_10pct_is_skipped(self):
        """E_shadow_proxy=۰٫۵۲ در برابرِ ۰٫۵ ذخیره‌شده → تکراری، ذخیره نشود."""
        with mock.patch("memory.research_store.get_patterns",
                        return_value=self.existing), \
             mock.patch("memory.research_store.save_pattern") as save:
            pid = self.engine._save_pattern(_analysis(e_shadow=0.52), "insight")
        self.assertIsNone(pid)
        save.assert_not_called()

    def test_genuinely_new_is_saved(self):
        """E_shadow_proxy=۰٫۹ (فاصله‌ی ۸۰٪) → کشفِ نو، باید ذخیره شود."""
        with mock.patch("memory.research_store.get_patterns",
                        return_value=self.existing), \
             mock.patch("memory.research_store.save_pattern",
                        return_value=7) as save:
            pid = self.engine._save_pattern(_analysis(e_shadow=0.9), "insight")
        self.assertEqual(pid, 7)
        save.assert_called_once()

    def test_mi_dedup_preferred_when_stored(self):
        """B6: ردیف‌های جدید MI دارند → مقایسه‌ی دقیقِ MI↔MI مقدم است."""
        existing = [{"tags": "auto,synthetic:ar1", "delta_self": 0.5,
                     "temporal_mi": 0.02}]
        with mock.patch("memory.research_store.get_patterns",
                        return_value=existing), \
             mock.patch("memory.research_store.save_pattern") as save:
            pid = self.engine._save_pattern(
                _analysis(e_shadow=0.9, mi=0.021), "insight")  # MI در ۵٪ → dup
        self.assertIsNone(pid)
        save.assert_not_called()

    def test_mi_differs_saves_even_if_eshadow_close(self):
        """MI متفاوت = کشفِ نو، حتی اگر E_shadow نزدیک باشد."""
        existing = [{"tags": "auto,synthetic:ar1", "delta_self": 0.5,
                     "temporal_mi": 0.02}]
        with mock.patch("memory.research_store.get_patterns",
                        return_value=existing), \
             mock.patch("memory.research_store.save_pattern",
                        return_value=5) as save:
            pid = self.engine._save_pattern(
                _analysis(e_shadow=0.51, mi=0.2), "insight")
        self.assertEqual(pid, 5)
        save.assert_called_once()

    def test_regression_old_bug_mi_vs_delta_self(self):
        """رگرسیونِ باگِ قدیم: MI فعلی برابرِ delta_self ذخیره‌شده ولی
        E_shadow واقعاً متفاوت → کدِ قدیمی به‌غلط dup می‌گفت؛ حالا باید ذخیره شود."""
        with mock.patch("memory.research_store.get_patterns",
                        return_value=self.existing), \
             mock.patch("memory.research_store.save_pattern",
                        return_value=11) as save:
            pid = self.engine._save_pattern(
                _analysis(e_shadow=0.9, mi=0.5), "insight")  # mi == stored 0.5
        self.assertEqual(pid, 11)
        save.assert_called_once()


if __name__ == "__main__":
    unittest.main()
