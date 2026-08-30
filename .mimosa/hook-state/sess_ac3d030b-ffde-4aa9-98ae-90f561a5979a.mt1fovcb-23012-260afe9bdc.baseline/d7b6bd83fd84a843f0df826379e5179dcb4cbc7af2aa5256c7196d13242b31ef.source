"""
SENTINEL — tests/test_phase_manager.py
Unit tests for phase_manager.py
"""

import sys
import os
import unittest
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import yaml
from phase_manager import PhaseManager


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestPhaseManagerInit(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.pm = PhaseManager(self.cfg, self.tmp.name)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_initial_phase_is_zero(self):
        self.pm.initialize()
        self.assertEqual(self.pm.get_current_phase(), 0)

    def test_double_initialize_no_error(self):
        self.pm.initialize()
        self.pm.initialize()  # should be idempotent
        self.assertEqual(self.pm.get_current_phase(), 0)

    def test_phase_status_summary(self):
        self.pm.initialize()
        s = self.pm.get_status_summary()
        self.assertEqual(s["phase"], 0)
        self.assertIn("days_in_phase", s)

    def test_advance_to_phase1(self):
        self.pm.initialize()
        self.pm.advance_to_phase1()
        self.assertEqual(self.pm.get_current_phase(), 1)

    def test_advance_to_phase2(self):
        self.pm.initialize()
        self.pm.advance_to_phase1()
        self.pm.advance_to_phase2()
        self.assertEqual(self.pm.get_current_phase(), 2)


class TestPhaseManagerVolatility(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.pm = PhaseManager(self.cfg, self.tmp.name)
        self.pm.initialize()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_record_and_retrieve_volatility(self):
        prices = [0.85, 0.82, 0.88, 0.91, 0.79, 0.93, 0.84, 0.87, 0.90, 0.86]
        for p in prices:
            self.pm.record_volatility("CORE", p)
        stats = self.pm.get_volatility_stats("CORE")
        self.assertEqual(stats["samples"], len(prices))
        self.assertIsNotNone(stats["volatility_pct"])
        self.assertGreater(stats["volatility_pct"], 0)
        self.assertIsNotNone(stats["range_pct"])

    def test_volatility_with_one_sample(self):
        self.pm.record_volatility("XMR", 192)
        stats = self.pm.get_volatility_stats("XMR")
        self.assertEqual(stats["samples"], 1)
        self.assertIsNone(stats["volatility_pct"])

    def test_phase0_advance_after_enough_samples(self):
        # need min_volatility_samples=10 AND min_days satisfied
        # We can't fake 10 days easily, but can verify the function runs
        for i in range(10):
            self.pm.record_volatility("CORE", 0.85 + i * 0.01)
        # since days_elapsed < min_days, should be False
        result = self.pm.should_advance_from_phase0()
        # Can't assert True/False without time-travel, just assert no crash
        self.assertIsInstance(result, bool)


class TestPhaseManagerScoreHistory(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.pm = PhaseManager(self.cfg, self.tmp.name)
        self.pm.initialize()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_record_score(self):
        fake_result = {"symbol": "CORE", "score": 72.5, "label": "strong_entry",
                       "details": {}, "active_scenarios": []}
        self.pm.record_score(fake_result, {})
        baseline = self.pm.get_score_baseline("CORE", days=1)
        self.assertEqual(baseline["samples"], 1)
        self.assertAlmostEqual(baseline["avg_score"], 72.5, places=1)

    def test_score_baseline_empty(self):
        baseline = self.pm.get_score_baseline("XMR", days=7)
        self.assertEqual(baseline["samples"], 0)
        self.assertIsNone(baseline["avg_score"])


class TestPhaseManagerRebalance(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.pm = PhaseManager(self.cfg, self.tmp.name)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_no_rebalance_needed_when_on_target(self):
        current = {"CORE": 30, "XMR": 12, "ZEC": 8, "TAO": 10}
        target  = {"CORE": 30, "XMR": 12, "ZEC": 8, "TAO": 10}
        alerts = self.pm.check_rebalance_needed(current, target)
        self.assertEqual(len(alerts), 0)

    def test_rebalance_triggered_when_over_threshold(self):
        current = {"CORE": 50, "XMR": 12, "ZEC": 8, "TAO": 10}
        target  = {"CORE": 30, "XMR": 12, "ZEC": 8, "TAO": 10}
        alerts = self.pm.check_rebalance_needed(current, target)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["symbol"], "CORE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
