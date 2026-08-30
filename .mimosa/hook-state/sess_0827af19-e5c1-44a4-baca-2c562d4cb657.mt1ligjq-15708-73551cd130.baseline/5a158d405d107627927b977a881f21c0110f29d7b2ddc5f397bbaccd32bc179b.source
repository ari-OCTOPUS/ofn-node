"""
SENTINEL — tests/test_data_fetcher.py
Unit tests for data_fetcher.py (mock mode — no live API)
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import yaml
from data_fetcher import DataFetcher, COINGECKO_IDS, LUNARCRUSH_SYMBOLS, CRYPTOQUANT_SLUGS


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestDataFetcherMockMode(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()
        self.fetcher = DataFetcher(self.cfg, mock_mode=True)

    def test_mock_mode_flag(self):
        self.assertTrue(self.fetcher.mock_mode)

    def test_price_data_all_assets(self):
        for sym in COINGECKO_IDS:
            data = self.fetcher.get_price_data(sym)
            if data:
                self.assertIn("price", data)
                self.assertIn("drawdown_from_90d_high", data)
                self.assertGreaterEqual(data["drawdown_from_90d_high"], 0)
                self.assertLessEqual(data["drawdown_from_90d_high"], 1)

    def test_fear_greed_returns_value(self):
        fg = self.fetcher.get_fear_greed()
        self.assertIsNotNone(fg)
        self.assertIn("value", fg)
        self.assertGreaterEqual(fg["value"], 0)
        self.assertLessEqual(fg["value"], 100)

    def test_fear_greed_override(self):
        fg = self.fetcher.get_fear_greed(override_value=15)
        self.assertEqual(fg["value"], 15)

    def test_social_data_core(self):
        social = self.fetcher.get_social_data("CORE")
        self.assertIsNotNone(social)
        self.assertIn("sentiment", social)
        self.assertGreaterEqual(social["sentiment"], 0)
        self.assertLessEqual(social["sentiment"], 1)

    def test_social_data_usdc_none(self):
        """USDC is not in LunarCrush symbols"""
        social = self.fetcher.get_social_data("USDC")
        self.assertIsNone(social)

    def test_onchain_btc_available(self):
        """BTC onchain still available as macro context (CryptoQuant)"""
        oc = self.fetcher.get_onchain_data("BTC")
        self.assertIsNotNone(oc)
        self.assertIn("exchange_netflow", oc)

    def test_onchain_xmr_none(self):
        """XMR has no transparent on-chain"""
        oc = self.fetcher.get_onchain_data("XMR")
        self.assertIsNone(oc)

    def test_onchain_core_none(self):
        """CORE is not in CRYPTOQUANT_SLUGS — no onchain signal"""
        oc = self.fetcher.get_onchain_data("CORE")
        self.assertIsNone(oc)

    def test_fetch_all_core_full_quality(self):
        result = self.fetcher.fetch_all("CORE")
        self.assertEqual(result["symbol"], "CORE")
        self.assertIn("price", result["available_signals"])
        self.assertIn("social", result["available_signals"])

    def test_fetch_all_xmr_partial_quality(self):
        result = self.fetcher.fetch_all("XMR")
        self.assertNotIn("onchain", result["available_signals"])

    def test_fetch_all_stable_no_social_no_onchain(self):
        result = self.fetcher.fetch_all("USDC")
        self.assertNotIn("social", result["available_signals"])
        self.assertNotIn("onchain", result["available_signals"])


class TestDataFetcherCacheLogic(unittest.TestCase):
    """Test in-memory cache helpers (_cached / _store) directly."""

    def setUp(self):
        self.cfg = load_config()
        self.fetcher = DataFetcher(self.cfg, mock_mode=True)

    def test_cache_store_and_retrieve(self):
        """_store then _cached returns the value within TTL"""
        self.fetcher._store("test_key", {"value": 42})
        result = self.fetcher._cached("test_key")
        self.assertIsNotNone(result)
        self.assertEqual(result["value"], 42)

    def test_cache_miss_returns_none(self):
        """Unknown key returns None"""
        result = self.fetcher._cached("nonexistent_key_xyz_abc")
        self.assertIsNone(result)

    def test_cache_expired_returns_none(self):
        """Entry older than TTL returns None"""
        import time
        self.fetcher._store("old_key", {"x": 1})
        self.fetcher._cache_ts["old_key"] = time.time() - self.fetcher._cache_ttl - 1
        result = self.fetcher._cached("old_key")
        self.assertIsNone(result)

    def test_mock_mode_returns_data_without_crash(self):
        """Mock mode must not crash on any supported symbol"""
        for sym in ("CORE", "XEL", "XMR", "ZEC", "TAO", "DIL", "USDC", "USDT"):
            data = self.fetcher.get_price_data(sym)
            self.assertIsInstance(data, (dict, type(None)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
