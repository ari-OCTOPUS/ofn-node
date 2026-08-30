#!/usr/bin/env python3
"""test_langar_failclosed.py — R-08 LANGAR-FAILCLOSED regression suite.

Offline, $0, no token, network POST fully mocked. Asserts:
  (i)   empty / unloadable blocklist  → egress BLOCKED (fail-closed).
  (ii)  valid non-empty policy        → scrubber allows + redacts.
  (iii) outbound identifiers (User-Agent + source defaults) carry no partner name.

Run: PYTHONIOENCODING=utf-8 python -m unittest test_langar_failclosed -v
"""
from __future__ import annotations
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path

# langar_bot lives one dir up in langar/ — add it to the import path.
LANGAR_DIR = Path(__file__).resolve().parent.parent / "langar"
sys.path.insert(0, str(LANGAR_DIR))

import langar_bot as L  # noqa: E402


class FailClosedScrubber(unittest.TestCase):
    # (i) empty / broken policy → block
    def test_empty_blocklist_blocks(self):
        g = L.OpsecGuard({"blocklist": [], "name_map": {}, "city_terms": []})
        allowed, out = g.scrub("any content whatsoever")
        self.assertFalse(allowed)
        self.assertEqual(out, "")
        self.assertFalse(g.policy_ok())

    def test_placeholder_only_blocklist_blocks(self):
        # entries that are only underscores/whitespace are not a real policy
        g = L.OpsecGuard({"blocklist": ["__", "  "], "name_map": {}, "city_terms": []})
        self.assertFalse(g.policy_ok())
        self.assertFalse(g.scrub("hello")[0])

    def test_unloaded_policy_blocks(self):
        # simulate corrupt/missing config: policy never loaded → deny-by-default
        g = L.OpsecGuard({"blocklist": ["RealSurname"]})
        g.policy_loaded = False
        self.assertFalse(g.scrub("hello")[0])

    def test_scrub_error_blocks(self):
        # any internal scrub error must fail closed, not leak
        g = L.OpsecGuard({"blocklist": ["RealSurname"]})

        def boom(_):
            raise RuntimeError("scrub exploded")

        g.clean = boom  # type: ignore[method-assign]
        allowed, out = g.scrub("hello")
        self.assertFalse(allowed)
        self.assertEqual(out, "")

    def test_send_blocked_and_logged(self):
        with tempfile.TemporaryDirectory() as d:
            orig_log = L.LOG_FILE
            L.LOG_FILE = Path(d) / "log.jsonl"
            try:
                captured = []
                bot = L.LangarBot(token="T", ari_chat_id=111,
                                  http_get=lambda *a, **k: {"result": []},
                                  http_post=lambda url, body, timeout=10: captured.append(body) or {})
                bot.guard = L.OpsecGuard({"blocklist": [], "name_map": {}, "city_terms": []})
                bot.send("leak me if you can")
                self.assertEqual(captured, [])            # network POST never happened
                log = L.LOG_FILE.read_text(encoding="utf-8")
                self.assertIn("send_blocked", log)
                self.assertIn("opsec_fail_closed", log)
            finally:
                L.LOG_FILE = orig_log


class ValidPolicyPasses(unittest.TestCase):
    # (ii) explicit non-empty policy → allowed + redacted
    def test_valid_policy_allows(self):
        g = L.OpsecGuard({"blocklist": ["RealSurname"], "name_map": {}, "city_terms": []})
        self.assertTrue(g.policy_ok())
        allowed, out = g.scrub("a normal safe payload")
        self.assertTrue(allowed)
        self.assertEqual(out, "a normal safe payload")

    def test_valid_policy_still_redacts(self):
        g = L.OpsecGuard({"blocklist": ["RealSurname"], "name_map": {}, "city_terms": []})
        allowed, out = g.scrub("contact RealSurname now")
        self.assertTrue(allowed)
        self.assertNotIn("RealSurname", out)

    def test_send_passes_with_policy(self):
        captured = []
        bot = L.LangarBot(token="T", ari_chat_id=111,
                          http_get=lambda *a, **k: {"result": []},
                          http_post=lambda url, body, timeout=10: captured.append(body) or {})
        bot.guard = L.OpsecGuard({"blocklist": ["RealSurname"], "name_map": {}, "city_terms": []})
        bot.send("weekly status is green")
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0]["text"], "weekly status is green")


class NoPartnerNameInIdentifiers(unittest.TestCase):
    # (iii) outbound identifiers carry no partner name
    def test_user_agent_is_neutral(self):
        seen = {}

        class _Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return b"{}"

        def fake_urlopen(req, timeout=0):
            seen["ua"] = req.get_header("User-agent") or ""
            return _Resp()

        orig = urllib.request.urlopen
        urllib.request.urlopen = fake_urlopen  # type: ignore[assignment]
        try:
            L.LangarBot._default_post("https://api.telegram.org/botX/sendMessage",
                                      {"chat_id": 1, "text": "hi"})
            post_ua = seen["ua"]
            L.LangarBot._default_get("https://api.telegram.org/botX/getUpdates")
            get_ua = seen["ua"]
        finally:
            urllib.request.urlopen = orig  # type: ignore[assignment]

        for ua in (post_ua, get_ua):
            self.assertEqual(ua, "octopus-langar")
            self.assertNotIn("/0.1", ua)           # old identifier form gone

    def test_source_defaults_carry_no_hardcoded_name(self):
        # partner/operator real names must not be hardcoded in the source defaults
        self.assertEqual(L.OpsecGuard.DEFAULT["name_map"], {})
        self.assertEqual(L.OpsecGuard.DEFAULT["blocklist"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
