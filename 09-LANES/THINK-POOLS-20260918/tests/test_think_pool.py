#!/usr/bin/env python3
"""Tests for think_pool — truthful provider classification and routing order.

The case that motivated this module is the first test: a provider whose own
evidence says HTTP 429 but whose declared status says LIVE must be classified
EXHAUSTED, because that is the state the owner described ("one gets charged,
then runs out") and the state a router must act on.
"""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import think_pool as tp  # noqa: E402

NOW = datetime(2026, 9, 18, 1, 30, 0, tzinfo=timezone.utc)
FRESH = "2026-09-18T01:00:00Z"


class TestClassification(unittest.TestCase):
    def test_declared_live_but_evidence_says_429_is_exhausted(self):
        """The live sakana-fugu record, verbatim in shape."""
        entry = {
            "status": "LIVE", "http_status": 200, "models_count": 8,
            "consecutive_failures": 0, "cooldown_until": None,
            "checked_at": FRESH, "paid": True,
            "evidence": "canary AND models-scope call -> HTTP 429 usage_limit_reached",
        }
        got = tp.classify(entry, now=NOW)
        self.assertEqual(got["state"], "EXHAUSTED")
        self.assertEqual(got["reason"], "CREDIT_OR_QUOTA_EXHAUSTED")
        self.assertEqual(got["cooldown_s"], 6 * 3600)

    def test_healthy_provider_is_live(self):
        entry = {"status": "LIVE", "http_status": 200, "models_count": 11,
                 "consecutive_failures": 0, "checked_at": FRESH, "paid": True,
                 "evidence": "canary served claude-sonnet-5"}
        self.assertEqual(tp.classify(entry, now=NOW)["state"], "LIVE")

    def test_quota_wording_variants_all_exhaust(self):
        for ev in ("insufficient_quota", "billing hard limit reached", "credit exhausted",
                   "HTTP 402 Payment Required", "out of budget"):
            entry = {"status": "LIVE", "http_status": 200, "models_count": 5,
                     "consecutive_failures": 0, "checked_at": FRESH, "evidence": ev}
            self.assertEqual(tp.classify(entry, now=NOW)["state"], "EXHAUSTED", ev)

    def test_401_is_auth_error_not_exhausted(self):
        entry = {"status": "LIVE", "http_status": 401, "models_count": 0,
                 "consecutive_failures": 3, "checked_at": FRESH,
                 "evidence": "invalid api key"}
        got = tp.classify(entry, now=NOW)
        self.assertEqual(got["state"], "AUTH_ERROR")
        self.assertEqual(got["cooldown_s"], 24 * 3600)

    def test_stale_probe_is_unknown_not_live(self):
        entry = {"status": "LIVE", "http_status": 200, "models_count": 5,
                 "consecutive_failures": 0, "checked_at": "2026-09-10T00:00:00Z",
                 "evidence": "canary ok"}
        got = tp.classify(entry, now=NOW)
        self.assertEqual(got["state"], "UNKNOWN")
        self.assertIn("PROBE_STALE", got["reason"])

    def test_missing_probe_is_unknown(self):
        self.assertEqual(tp.classify(None, now=NOW)["state"], "UNKNOWN")

    def test_free_local_endpoint_is_live_without_models_count(self):
        """local-llamacpp reports a /health 200 and no model list."""
        entry = {"status": "LIVE", "paid": False, "checked_at": FRESH,
                 "evidence": "GET http://192.168.0.180:8081/health -> 200 {'status':'ok'}"}
        got = tp.classify(entry, now=NOW)
        self.assertEqual(got["state"], "LIVE")


class TestRoutingOrder(unittest.TestCase):
    def setUp(self):
        self.states = {
            "anthropic": {"state": "LIVE", "paid": True},
            "deepseek": {"state": "LIVE", "paid": True},
            "local-llamacpp-180": {"state": "LIVE", "paid": False},
            "sakana-fugu": {"state": "EXHAUSTED", "paid": True},
            "openai": {"state": "AUTH_ERROR", "paid": True},
        }

    def test_free_provider_is_tried_first(self):
        order = tp.routing_order(self.states, usage={})
        self.assertEqual(order[0], "local-llamacpp-180")

    def test_blocked_providers_are_excluded(self):
        order = tp.routing_order(self.states, usage={})
        self.assertNotIn("sakana-fugu", order)
        self.assertNotIn("openai", order)

    def test_least_used_paid_provider_comes_first(self):
        order = tp.routing_order(self.states, usage={"anthropic": 40, "deepseek": 2})
        self.assertEqual(order[1], "deepseek")
        self.assertEqual(order[2], "anthropic")

    def test_unknown_state_is_never_routed_to(self):
        states = {"mystery": {"state": "UNKNOWN", "paid": False}}
        self.assertEqual(tp.routing_order(states, usage={}), [])

    def test_all_blocked_yields_empty_order(self):
        states = {"a": {"state": "EXHAUSTED", "paid": True}, "b": {"state": "DOWN", "paid": True}}
        self.assertEqual(tp.routing_order(states, usage={}), [])


class TestRechargeAndShare(unittest.TestCase):
    def test_recharge_detected_when_blocked_becomes_live(self):
        previous = {"sakana-fugu": {"state": "EXHAUSTED"}}
        current = {"sakana-fugu": {"state": "LIVE"}, "gemini": {"state": "LIVE"}}
        self.assertEqual(tp.recharge_detected(previous, current), ["sakana-fugu"])

    def test_no_recharge_when_still_blocked(self):
        previous = {"x": {"state": "EXHAUSTED"}}
        current = {"x": {"state": "EXHAUSTED"}}
        self.assertEqual(tp.recharge_detected(previous, current), [])

    def test_usage_share_sums_to_one(self):
        share = tp.usage_share({"a": 3, "b": 1})
        self.assertAlmostEqual(sum(share.values()), 1.0, places=3)
        self.assertAlmostEqual(share["a"], 0.75, places=3)

    def test_usage_share_handles_empty(self):
        self.assertEqual(tp.usage_share({}), {})


class TestRegistry(unittest.TestCase):
    def test_registry_rejects_credential_values(self):
        """Only env-var NAMES are allowed; a pasted value must be refused."""
        with self.assertRaises(ValueError):
            tp.build_registry({"x": {"key_names": ["sk-live-abc123def456"]}})

    def test_registry_accepts_names_and_marks_local_free(self):
        reg = tp.build_registry({
            "openai": {"paid": True, "key_names": ["OPENAI_API_KEY"], "models_count": 130},
            "local-llamacpp-180": {"paid": False, "kind": "local",
                                   "base_url_env": "LOCAL_LLAMACPP_BASE_URL"},
        })
        self.assertEqual(reg["schema"], "think_provider.v1")
        self.assertTrue(reg["providers"]["openai"]["paid"])
        self.assertFalse(reg["providers"]["local-llamacpp-180"]["paid"])

    def test_classify_all_skips_meta(self):
        record = {"_meta": {"probe_method": "zero spend"},
                  "gemini": {"status": "LIVE", "http_status": 200, "models_count": 50,
                             "consecutive_failures": 0, "checked_at": FRESH}}
        states = tp.classify_all(record, now=NOW)
        self.assertEqual(list(states), ["gemini"])
        self.assertEqual(states["gemini"]["state"], "LIVE")


if __name__ == "__main__":
    unittest.main()
