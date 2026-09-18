#!/usr/bin/env python3
"""Paired test for PERFUSION P1 — registry-aware brain routing.

The behaviour that matters: a pin pointing at a provider with no credit must NOT
be called, the free local model must be preferred for the general order, and a
consumer that can only name certain models must get a token it can actually use.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))

import provider_routing as pr  # noqa: E402

LIVE_ALL = {
    "anthropic": {"state": "LIVE", "paid": True},
    "deepseek": {"state": "LIVE", "paid": True},
    "gemini": {"state": "LIVE", "paid": True},
    "openai": {"state": "LIVE", "paid": True},
    "local-llamacpp-180": {"state": "LIVE", "paid": False},
    "sakana-fugu": {"state": "EXHAUSTED", "paid": True},
}


class TestDecide(unittest.TestCase):
    def test_pin_is_honoured_when_routable(self):
        d = pr.decide(pin="deepseek", states=LIVE_ALL)
        self.assertEqual(d["chosen"], "deepseek")
        self.assertEqual(d["reason"], "PIN_ROUTABLE")

    def test_pin_to_exhausted_provider_falls_back(self):
        """The live 2026-09-18 case: BRAIN_PROVIDER=fugu with no credit."""
        d = pr.decide(pin="sakana-fugu", states=LIVE_ALL)
        self.assertNotEqual(d["chosen"], "sakana-fugu")
        self.assertIn("PIN_BLOCKED", d["reason"])
        self.assertEqual(d["pin_state"], "EXHAUSTED")

    def test_free_provider_wins_without_a_pin(self):
        d = pr.decide(pin=None, states=LIVE_ALL)
        self.assertEqual(d["chosen"], "local-llamacpp-180")

    def test_exhausted_provider_is_excluded_from_order(self):
        d = pr.decide(pin=None, states=LIVE_ALL)
        self.assertNotIn("sakana-fugu", d["order"])
        self.assertIn("sakana-fugu", d["excluded"])

    def test_unknown_pin_falls_back_with_reason(self):
        d = pr.decide(pin="never-heard-of-it", states=LIVE_ALL)
        self.assertEqual(d["reason"], "PIN_UNKNOWN_FALLBACK")
        self.assertIsNotNone(d["chosen"])


class TestBrainportToken(unittest.TestCase):
    def test_brainport_gets_a_token_it_can_name_a_model_for(self):
        d = pr.decide_brainport("sakana-fugu", states=LIVE_ALL)
        # brainport knows models only for fugu/deepseek; the free local model is
        # first overall but unusable here, so deepseek must be selected.
        self.assertEqual(d["token"], "deepseek")
        self.assertEqual(d["chosen"], "deepseek")

    def test_brainport_keeps_a_healthy_pin(self):
        d = pr.decide_brainport("deepseek", states=LIVE_ALL)
        self.assertEqual(d["token"], "deepseek")
        self.assertEqual(d["reason"], "PIN_ROUTABLE")

    def test_no_usable_provider_yields_no_token(self):
        """Every brainport-capable provider blocked -> no token, not a bad one."""
        states = {"gemini": {"state": "LIVE", "paid": True},
                  "local-llamacpp-180": {"state": "LIVE", "paid": False},
                  "sakana-fugu": {"state": "EXHAUSTED", "paid": True},
                  "deepseek": {"state": "EXHAUSTED", "paid": True}}
        d = pr.decide_brainport(pin=None, states=states)
        self.assertIsNone(d["token"])
        self.assertIn("NO_BRAINPORT_PROVIDER", d["reason"])

    def test_brainport_skips_free_model_it_cannot_name(self):
        """The free local model is first overall but brainport has no model map for it."""
        d = pr.decide_brainport(pin=None, states=LIVE_ALL)
        self.assertEqual(d["chosen"], "deepseek")
        self.assertEqual(d["token"], "deepseek")

    def test_env_pin_translates_fugu_to_registry_name(self):
        import os
        old = os.environ.get("BRAIN_PROVIDER")
        try:
            os.environ["BRAIN_PROVIDER"] = "fugu"
            self.assertEqual(pr.env_pin(), "sakana-fugu")
            os.environ["BRAIN_PROVIDER"] = "deepseek"
            self.assertEqual(pr.env_pin(), "deepseek")
            os.environ.pop("BRAIN_PROVIDER")
            self.assertIsNone(pr.env_pin())
        finally:
            if old is not None:
                os.environ["BRAIN_PROVIDER"] = old


if __name__ == "__main__":
    unittest.main()
