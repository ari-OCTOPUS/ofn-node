#!/usr/bin/env python3
"""test_pf_os_phase1.py — تست‌های فاز ۱: config, cortex_client, events, __init__.

همه‌ی تست‌ها $0، آفلاین، و مستقل از ارگانیسمِ زنده‌اند. هیچ network واقعی نیست
(cortex_client با flag-off تست می‌شود = همیشه fallback).
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

import pf_os  # noqa: E402
from pf_os import config, cortex_client, events  # noqa: E402


class TestConfig(unittest.TestCase):
    def test_flag_off_by_default(self):
        os.environ.pop("PF_OS_TEST_FLAG_X", None)
        self.assertFalse(config.flag("PF_OS_TEST_FLAG_X"))

    def test_flag_on_only_for_one(self):
        os.environ["PF_OS_TEST_FLAG_X"] = "1"
        try:
            self.assertTrue(config.flag("PF_OS_TEST_FLAG_X"))
        finally:
            del os.environ["PF_OS_TEST_FLAG_X"]

    def test_flag_not_one_is_off(self):
        # "true"/"yes"/"on" نباید True باشند — فقط "1"
        for val in ("true", "yes", "on", "TRUE", "0", ""):
            os.environ["PF_OS_TEST_FLAG_X"] = val
            try:
                self.assertFalse(config.flag("PF_OS_TEST_FLAG_X"),
                                 f"value {val!r} must be False")
            finally:
                del os.environ["PF_OS_TEST_FLAG_X"]

    def test_paths_resolve(self):
        # PF_ROOT باید شاملِ "pf_os" نباشه ولی پدرِ pf_os باشه
        self.assertTrue(config.PF_ROOT.endswith("اونلی فنز") or
                        "اونلی فنز" in config.PF_ROOT)
        self.assertTrue(config.OPS_STATE.endswith(os.path.join("_ops", "state")))
        self.assertTrue(config.VAULT.endswith("backup") or "backup" in config.VAULT)

    def test_cortex_url_default(self):
        os.environ.pop("OCTOPUS_CORTEX_URL", None)
        # reimport نمی‌کنیم — مقدار تو import-time set شد؛ ولی چک می‌کنیم فرمت درست است
        self.assertTrue(config.CORTEX_URL.startswith("http://127.0.0.1"))

    def test_organ_constant(self):
        self.assertEqual(config.ORGAN, "PROJECT_F")

    def test_ensure_pf_state_idempotent(self):
        p = config.ensure_pf_state()
        self.assertTrue(os.path.isdir(p))
        # فراخوانیِ دوباره نباید شکست بخورد
        self.assertEqual(config.ensure_pf_state(), p)


class TestCortexClient(unittest.TestCase):
    def setUp(self):
        os.environ.pop(config.WIRE_CORTEX, None)

    def test_ask_flag_off_returns_fallback(self):
        """وقتی WIRE_CORTEX خاموشه، ask باید فوراً fallback برگرداند."""
        r = cortex_client.ask("daily", "test prompt")
        self.assertFalse(r["ok"])
        self.assertEqual(r["source"], "fallback")
        self.assertIn("heuristic-only", r["reason"])
        self.assertEqual(r["tier"], "none")

    def test_ask_never_raises(self):
        """ask هیچ‌وقت exception بیرون نمی‌دهد، حتی اگر cortex بسته/رفع کنترل کند."""
        os.environ[config.WIRE_CORTEX] = "1"
        try:
            r = cortex_client.ask("daily", "x", timeout=1.5)
            self.assertIsInstance(r, dict)
            if not r["ok"]:
                self.assertEqual(r["source"], "fallback")
                self.assertIn("reason", r)
                self.assertIsInstance(r["reason"], str)
        finally:
            os.environ.pop(config.WIRE_CORTEX, None)

    def test_ask_dead_port_transport_error(self):
        """به یک port قطعاً بسته، cortex_client باید transport error برگرداند."""
        os.environ[config.WIRE_CORTEX] = "1"
        orig_url = config.CORTEX_URL
        config.CORTEX_URL = "http://127.0.0.1:1"  # port مسدود
        try:
            r = cortex_client.ask("daily", "x", timeout=0.5)
            self.assertFalse(r["ok"])
            self.assertEqual(r["source"], "fallback")
            self.assertTrue(any(k in r["reason"] for k in
                                ("URLError", "Connection", "Error", "timed out",
                                 "Refused", "Cannot", "reset", "EOF")),
                            f"reason should be transport error: {r['reason']}")
        finally:
            os.environ.pop(config.WIRE_CORTEX, None)
            config.CORTEX_URL = orig_url

    def test_health_flag_off(self):
        os.environ.pop(config.WIRE_CORTEX, None)
        h = cortex_client.health()
        self.assertFalse(h["wired"])
        self.assertFalse(h["reachable"])
        self.assertIn("off", h["reason"])


class TestEvents(unittest.TestCase):
    def test_available_returns_bool(self):
        # ممکن است True یا False باشد بسته به scope — ولی bool است
        self.assertIsInstance(events.available(), bool)

    def test_emit_no_raise(self):
        # emit هرگز exception نمی‌دهد
        ok = events.emit("system.heartbeat", summary="pf_os test",
                         status="ok")
        self.assertIsInstance(ok, bool)

    def test_emit_bad_event_name_no_raise(self):
        # حتی با event_name ناشناخته نباید شکست بخورد (fail-soft)
        ok = events.emit("nonsense.event", summary="x")
        self.assertIsInstance(ok, bool)

    def test_begin_end_run_safe(self):
        token = events.begin_run("test-cid")
        # token می‌تواند None باشد اگر events نباشد
        events.end_run(token)  # نباید شکست بخورد
        events.end_run(None)   # نباید شکست بخورد


class TestPackageInit(unittest.TestCase):
    def test_version_string(self):
        self.assertIsInstance(pf_os.__version__, str)
        self.assertTrue(pf_os.__version__.count(".") >= 1)

    def test_submodules_importable(self):
        self.assertTrue(hasattr(pf_os, "config"))
        self.assertTrue(hasattr(pf_os, "cortex_client"))
        self.assertTrue(hasattr(pf_os, "events"))


if __name__ == "__main__":
    unittest.main()
