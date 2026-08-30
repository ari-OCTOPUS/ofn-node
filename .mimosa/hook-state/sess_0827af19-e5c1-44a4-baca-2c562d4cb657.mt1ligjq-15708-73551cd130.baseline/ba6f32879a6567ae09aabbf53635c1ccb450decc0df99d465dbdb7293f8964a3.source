"""
SENTINEL — tests/test_scorer.py
Unit tests for scorer.py
تست‌های واحد برای منطق امتیازدهی

Covers:
  - Happy path for CORE (hedge pole), XMR/ZEC (privacy pole), TAO (ai pole)
  - Every API-fallback branch (None social, None on-chain, None price)
  - Threshold edges: 24/25, 44/45, 69/70
  - Drawdown extremes: 0% and 90%
  - Scenario modifier addition (positive and negative)
  - Stablecoin returns correct labels
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import yaml
from scorer import EntryScorer

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def make_market(symbol, price=1.0, drawdown=0.30, ma50=1.05, ma200=0.95,
                fg=35, social_sentiment=0.30, galaxy=60,
                onchain_netflow=-2000, onchain_miner=-100, nvt=55,
                no_social=False, no_onchain=False, no_price=False,
                no_fg=False):
    """Factory for market_data dicts fed to scorer.score()"""
    price_data = None if no_price else {
        "price": price,
        "change_24h": -3.0,
        "high_90d": price / (1 - drawdown) if drawdown < 1 else price * 10,
        "low_90d": price * 0.6,
        "drawdown_from_90d_high": drawdown,
        "ma50": ma50,
        "ma200": ma200,
    }

    fg_data = None if no_fg else {"value": fg, "classification": "Fear"}

    social_data = None if no_social else {
        "social_score": 400,
        "sentiment": social_sentiment,
        "galaxy_score": galaxy,
        "alt_rank": 1,
        "social_volume_24h": 100000,
        "bullish_pct": -5,
    }

    # None of our new assets (CORE/XEL/XMR/ZEC/TAO/DIL) have onchain in signals
    # onchain is kept as macro context (BTC/ETH only in CryptoQuant) — not added to available
    available = []
    if price_data:  available.append("price")
    if fg_data:     available.append("fear_greed")
    if social_data: available.append("social")

    return {
        "symbol": symbol,
        "price": price_data,
        "fear_greed": fg_data,
        "social": social_data,
        "onchain": None,   # no onchain for portfolio assets
        "available_signals": available,
        "data_quality": "full" if len(available) >= 3 else "partial",
    }


# ─────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────

class TestScorerHappyPath(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()
        self.scorer = EntryScorer(self.cfg)

    def test_core_limited_mode_returns_score(self):
        """CORE (hedge pole, no onchain in signals) → limited mode, valid score"""
        md = make_market("CORE", price=0.85, ma50=0.95, ma200=0.78)
        r = self.scorer.score("CORE", md)
        self.assertEqual(r["mode"], "limited")
        self.assertIsNotNone(r["score"])
        self.assertGreaterEqual(r["score"], 0)
        self.assertLessEqual(r["score"], 100)

    def test_tao_limited_mode_returns_score(self):
        """TAO (ai pole — social heavy) → limited mode, valid score"""
        md = make_market("TAO", price=380, ma50=420, ma200=360)
        r = self.scorer.score("TAO", md)
        self.assertEqual(r["mode"], "limited")
        self.assertIsNotNone(r["score"])

    def test_xmr_limited_mode(self):
        """XMR (privacy pole) → limited mode"""
        md = make_market("XMR", price=195)
        r = self.scorer.score("XMR", md)
        self.assertEqual(r["mode"], "limited")
        self.assertIsNotNone(r["score"])

    def test_zec_limited_mode(self):
        """ZEC (privacy pole) → limited mode"""
        md = make_market("ZEC", price=35)
        r = self.scorer.score("ZEC", md)
        self.assertEqual(r["mode"], "limited")

    def test_xel_limited_mode(self):
        """XEL (privacy pole) → limited mode"""
        md = make_market("XEL", price=0.012)
        r = self.scorer.score("XEL", md)
        self.assertEqual(r["mode"], "limited")
        self.assertIsNotNone(r["score"])

    def test_dil_limited_mode(self):
        """DIL (quantum pole) → limited mode, valid score"""
        md = make_market("DIL", price=0.003, no_social=True)
        r = self.scorer.score("DIL", md)
        self.assertEqual(r["mode"], "limited")
        self.assertIsNotNone(r["score"])

    def test_usdc_no_score(self):
        """Stablecoins: no entry score"""
        md = make_market("USDC", price=1.0, drawdown=0.0)
        r = self.scorer.score("USDC", md)
        self.assertIsNone(r["score"])
        self.assertEqual(r["label"], "stable_parking")

    def test_usdt_no_score(self):
        md = make_market("USDT", price=1.0, drawdown=0.0)
        r = self.scorer.score("USDT", md)
        self.assertIsNone(r["score"])


class TestScorerFallbackPaths(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()
        self.scorer = EntryScorer(self.cfg)

    def test_no_social_core_still_scores(self):
        """CORE without social → still produces score"""
        md = make_market("CORE", no_social=True)
        r = self.scorer.score("CORE", md)
        self.assertIsNotNone(r["score"])

    def test_no_fg_core_still_scores(self):
        md = make_market("CORE", no_fg=True)
        r = self.scorer.score("CORE", md)
        self.assertIsNotNone(r["score"])

    def test_no_price_does_not_crash(self):
        """Without price data we cannot score meaningfully but must not crash"""
        md = make_market("CORE", no_price=True)
        r = self.scorer.score("CORE", md)
        self.assertIsNotNone(r)  # must not crash

    def test_all_fallback_core(self):
        """Only price available → must still return a number"""
        md = make_market("CORE", no_social=True, no_fg=True)
        r = self.scorer.score("CORE", md)
        self.assertIsNotNone(r["score"])

    def test_all_fallback_xmr(self):
        md = make_market("XMR", no_social=True, no_fg=True)
        r = self.scorer.score("XMR", md)
        self.assertIsNotNone(r["score"])


class TestScorerThresholdEdges(unittest.TestCase):
    """
    Test label boundaries at 24/25, 44/45, 69/70.
    We construct market data engineered to land near each threshold.
    We disable scenario modifiers to get clean math.
    """

    def setUp(self):
        self.cfg = load_config()
        # Disable all scenario modifiers for clean threshold testing
        for sc in self.cfg["scenarios"].values():
            sc["status"] = "inactive"
        self.scorer = EntryScorer(self.cfg)

    def _score_core(self, drawdown, fg, sentiment, ma50=None, ma200=None):
        price = 1.0
        md = make_market("CORE", price=price, drawdown=drawdown, fg=fg,
                         social_sentiment=sentiment,
                         ma50=ma50 or price * 1.05,
                         ma200=ma200 or price * 0.95)
        return self.scorer.score("CORE", md)

    def test_score_below_25_is_watch_only(self):
        """Very unfavorable: low drawdown, extreme greed, above both MAs"""
        r = self._score_core(drawdown=0.02, fg=90, sentiment=0.90,
                              ma50=0.90, ma200=0.80)  # price above both MAs
        self.assertLess(r["score"], 25, f"Expected < 25, got {r['score']}")
        self.assertEqual(r["label"], "watch_only")

    def test_score_above_70_is_strong_entry(self):
        """Very favorable: deep drawdown, extreme fear, strong social signal"""
        r = self._score_core(drawdown=0.65, fg=10, sentiment=0.15,
                              ma50=1.20, ma200=1.10)
        self.assertGreaterEqual(r["score"], 70, f"Expected >= 70, got {r['score']}")
        self.assertEqual(r["label"], "strong_entry")

    def test_moderate_band_45_to_69(self):
        """Mid scenario → moderate_entry label"""
        r = self._score_core(drawdown=0.30, fg=40, sentiment=0.42)
        self.assertGreaterEqual(r["score"], 45, f"Expected >= 45, got {r['score']}")
        self.assertLessEqual(r["score"], 69, f"Expected <= 69, got {r['score']}")
        self.assertEqual(r["label"], "moderate_entry")


class TestScorerDrawdownExtremes(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()
        for sc in self.cfg["scenarios"].values():
            sc["status"] = "inactive"
        self.scorer = EntryScorer(self.cfg)

    def test_drawdown_zero(self):
        """At the 90-day high → drawdown score = 0"""
        md = make_market("CORE", drawdown=0.0, fg=50, social_sentiment=0.5)
        r = self.scorer.score("CORE", md)
        self.assertAlmostEqual(r["details"]["drawdown_score"], 0.0, places=0)

    def test_drawdown_90pct(self):
        """At 90% below high → drawdown score = 100"""
        md = make_market("CORE", drawdown=0.90, fg=50, social_sentiment=0.5)
        r = self.scorer.score("CORE", md)
        self.assertAlmostEqual(r["details"]["drawdown_score"], 100.0, places=0)

    def test_drawdown_30pct(self):
        """30% drawdown → score = 50"""
        md = make_market("CORE", drawdown=0.30, fg=50, social_sentiment=0.5)
        r = self.scorer.score("CORE", md)
        self.assertAlmostEqual(r["details"]["drawdown_score"], 50.0, places=0)


class TestScenarioModifiers(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()
        self.scorer = EntryScorer(self.cfg)

    def test_fiat_erosion_boosts_core(self):
        """fiat_erosion active → CORE score higher than with no scenarios"""
        # baseline: all inactive
        cfg_off = load_config()
        for sc in cfg_off["scenarios"].values():
            sc["status"] = "inactive"
        scorer_off = EntryScorer(cfg_off)

        # active: fiat_erosion
        cfg_on = load_config()
        for sc in cfg_on["scenarios"].values():
            sc["status"] = "inactive"
        cfg_on["scenarios"]["fiat_erosion"]["status"] = "active"
        scorer_on = EntryScorer(cfg_on)

        md = make_market("CORE")
        score_off = scorer_off.score("CORE", md)["score"]
        score_on  = scorer_on.score("CORE", md)["score"]
        core_mod = cfg_on["scenarios"]["fiat_erosion"]["score_modifier"].get("CORE", 0)
        self.assertAlmostEqual(score_on - score_off, core_mod, places=0)

    def test_regulatory_crackdown_reduces_xmr(self):
        """regulatory_crackdown active → XMR score lower"""
        cfg_off = load_config()
        for sc in cfg_off["scenarios"].values():
            sc["status"] = "inactive"
        scorer_off = EntryScorer(cfg_off)

        cfg_on = load_config()
        for sc in cfg_on["scenarios"].values():
            sc["status"] = "inactive"
        cfg_on["scenarios"]["regulatory_crackdown"]["status"] = "active"
        scorer_on = EntryScorer(cfg_on)

        md = make_market("XMR")
        score_off = scorer_off.score("XMR", md)["score"]
        score_on  = scorer_on.score("XMR", md)["score"]
        xmr_mod = cfg_on["scenarios"]["regulatory_crackdown"]["score_modifier"].get("XMR", 0)
        self.assertAlmostEqual(score_on - score_off, xmr_mod, places=0)

    def test_quantum_threat_boosts_dil(self):
        """quantum_threat active → DIL score higher"""
        cfg_off = load_config()
        for sc in cfg_off["scenarios"].values():
            sc["status"] = "inactive"
        scorer_off = EntryScorer(cfg_off)

        cfg_on = load_config()
        for sc in cfg_on["scenarios"].values():
            sc["status"] = "inactive"
        cfg_on["scenarios"]["quantum_threat"]["status"] = "active"
        scorer_on = EntryScorer(cfg_on)

        md = make_market("DIL", no_social=True)
        score_off = scorer_off.score("DIL", md)["score"]
        score_on  = scorer_on.score("DIL", md)["score"]
        dil_mod = cfg_on["scenarios"]["quantum_threat"]["score_modifier"].get("DIL", 0)
        self.assertAlmostEqual(score_on - score_off, dil_mod, places=0)

    def test_emerging_scenario_half_modifier(self):
        """emerging status → only 50% of modifier applied"""
        cfg = load_config()
        for sc in cfg["scenarios"].values():
            sc["status"] = "inactive"
        cfg["scenarios"]["fiat_erosion"]["status"] = "emerging"
        scorer = EntryScorer(cfg)

        md = make_market("CORE")
        r = scorer.score("CORE", md)
        for sc in r["active_scenarios"]:
            if sc["name"] == "fiat_erosion":
                full_mod = cfg["scenarios"]["fiat_erosion"]["score_modifier"]["CORE"]
                self.assertAlmostEqual(sc["modifier"], full_mod * 0.5, places=1)

    def test_score_never_exceeds_100(self):
        """Score always clamped [0, 100] regardless of modifiers"""
        cfg = load_config()
        for sc in cfg["scenarios"].values():
            sc["status"] = "active"
        scorer = EntryScorer(cfg)
        md = make_market("CORE", drawdown=0.90, fg=5, social_sentiment=0.05)
        r = scorer.score("CORE", md)
        self.assertLessEqual(r["score"], 100)
        self.assertGreaterEqual(r["score"], 0)


class TestScorerUpdateScenario(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()
        self.scorer = EntryScorer(self.cfg)

    def test_update_valid_scenario(self):
        ok = self.scorer.update_scenario("quantum_threat", "active")
        self.assertTrue(ok)
        self.assertEqual(self.scorer.scenarios["quantum_threat"]["status"], "active")

    def test_update_invalid_status(self):
        ok = self.scorer.update_scenario("quantum_threat", "WRONG")
        self.assertFalse(ok)

    def test_update_unknown_scenario(self):
        ok = self.scorer.update_scenario("does_not_exist", "active")
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main(verbosity=2)
