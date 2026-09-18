"""Paired tests for the 2026-09-18 runtime export (lane/runtime-export-20260918).

Each test pins the CONTRACT of one exported change so a later edit that silently
reverts it (the way the pulse key drifted for days) fails here instead:

  1. gate flip        — Ziman GatePolicy.hold_external is released (owner vote A1)
  2. notify retry     — owner_notify retries a transient send instead of dropping it
  3. pulse key        — the pulse publishes `nats_leaf_active`, the key the hub reads
  4. telegram buttons — owner_reply understands `go:<8hex>:<channel>` and the
                        approve/reject vocabulary, and glass spools callback_query
  5. W1 collector     — PASS criteria constants + the pgrep bracket trick (a
                        self-match once produced a false FAIL)
  6. no secrets       — none of the exported files carries a token, a mailbox or PII
"""
from __future__ import annotations

import compileall
import importlib.util
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(path: pathlib.Path, name: str):
    # registering in sys.modules first: dataclasses look the module up by name
    import sys
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class GateFlip(unittest.TestCase):
    def test_hold_external_released(self):
        src = (ROOT / "ofn/ziman_cycle/gates.py").read_text(encoding="utf-8")
        self.assertRegex(src, r"hold_external:\s*bool\s*=\s*False",
                         "A1 flip reverted: hold_external default is not False")
        self.assertNotRegex(src, r"hold_external:\s*bool\s*=\s*True")

    def test_module_imports_when_deps_present(self):
        try:
            mod = load(ROOT / "ofn/ziman_cycle/gates.py", "ziman_gates_export")
        except Exception as exc:  # noqa: BLE001 — env-dependent import surface
            self.skipTest("import skipped: %s: %s" % (type(exc).__name__, exc))
        policy = getattr(mod, "GatePolicy", None)
        if policy is not None:
            self.assertFalse(policy().hold_external)


class NotifyRetry(unittest.TestCase):
    def test_transient_send_is_retried(self):
        """Contract: a helper retries >1 times, send() uses it, and a persistent
        failure still propagates so notify.failed is recorded (fail-soft, not silent)."""
        src = (ROOT / "ofn/agents/owner_notify.py").read_text(encoding="utf-8")
        self.assertIn("def _urlopen_retry(", src, "retry helper missing")
        self.assertRegex(src, r"attempts:\s*int\s*=\s*(\d+)")
        n = int(re.search(r"attempts:\s*int\s*=\s*(\d+)", src).group(1))
        self.assertGreater(n, 1, "retry count must be > 1 to absorb a network blip")
        self.assertIn("_urlopen_retry(req", src, "send() no longer uses the retry helper")
        self.assertIn("raise last", src, "persistent failure must propagate")
        self.assertIn("notify.failed", src, "failure must still leave a receipt")


class PulseKeyContract(unittest.TestCase):
    def test_publishes_the_key_the_hub_reads(self):
        src = (ROOT / "tools/octopus-138-pulse.sh").read_text(encoding="utf-8")
        self.assertIn("nats_leaf_active", src,
                      "hub consumer reads nats_leaf_active; publishing 'leaf' renders leaf=None")
        self.assertNotIn('"leaf": True', src)
        self.assertIn("SIZE = 160", src)

    def test_leaf_value_is_probed_not_hardcoded(self):
        src = (ROOT / "tools/octopus-138-pulse.sh").read_text(encoding="utf-8")
        self.assertIn("create_connection", src, "leaf flag must be a real probe")


class TelegramButtons(unittest.TestCase):
    def setUp(self):
        self.mod = load(ROOT / "tools/revenue-drive/owner_reply.py", "owner_reply_export")

    def test_callback_identity_and_channel(self):
        m = self.mod.CALLBACK_PAT.match("go:dead3f1a:email")
        self.assertIsNotNone(m, "button payload no longer parsed")
        self.assertEqual((m.group(1), m.group(2), m.group(3)), ("go", "dead3f1a", "email"))
        self.assertIsNotNone(self.mod.CALLBACK_PAT.match("no:dead3f1a"))
        self.assertIsNotNone(self.mod.CALLBACK_PAT.match("later:dead3f1a"))

    def test_vocabulary_and_channel_word(self):
        self.assertEqual(self.mod.classify("بفرست")[0], "APPROVE")
        self.assertEqual(self.mod.classify("نه")[0], "REJECT")
        self.assertIsNotNone(self.mod.CHANNEL_WORD_PAT.search("تأیید ایمیل"))

    def test_button_label_names_the_channel(self):
        ask = (ROOT / "tools/revenue-drive/owner_ask.py").read_text(encoding="utf-8")
        self.assertIn("go:%s:email", ask, "approval button no longer carries the channel")

    def test_glass_spools_callbacks(self):
        src = (ROOT / "ofn/agents/glass_runner.py").read_text(encoding="utf-8")
        self.assertIn("callback_query", src, "glass no longer spools button taps")
        self.assertIn("glass.callback_spool_error", src)


class W1CollectorContract(unittest.TestCase):
    def setUp(self):
        self.src = (ROOT / "tools/w1_verdict_collector.py").read_text(encoding="utf-8")

    def test_pass_criteria_constants(self):
        self.assertIn('"07:18:41"', self.src)
        self.assertIn('"07:18:32"', self.src)
        self.assertRegex(self.src, r"MAX_GAP_S\s*=\s*900")
        self.assertIn("2026-09-18T09:11:20Z", self.src)

    def test_pgrep_self_match_guard(self):
        self.assertIn("[a]pply_signed_inbound", self.src,
                      "bracket trick missing: a pgrep self-match produces a false FAIL")

    def test_unreadable_is_never_a_pass(self):
        self.assertIn('verdict = "UNVERIFIED"', self.src)


class NoSecretsInExport(unittest.TestCase):
    PATTERNS = [r"shpat_", r"shpss_", r"\d{8,10}:AA[A-Za-z0-9_-]{30,}",
                r"BEGIN (RSA|OPENSSH|EC|PRIVATE)", r"@gmail\.com", r"leads_master\.json"]

    def test_exported_files_carry_no_secret_or_pii(self):
        targets = ["ofn/ziman_cycle/gates.py", "ofn/agents/owner_notify.py",
                   "ofn/agents/glass_runner.py", "tools/w1_verdict_collector.py",
                   "tools/octopus-138-pulse.sh", "tools/revenue-drive/owner_ask.py",
                   "tools/revenue-drive/owner_reply.py",
                   "tools/systemd/octopus-w1-verdict.service",
                   "tools/systemd/octopus-w1-verdict.timer"]
        for rel in targets:
            text = (ROOT / rel).read_text(encoding="utf-8")
            for pat in self.PATTERNS:
                self.assertIsNone(re.search(pat, text), "%s matched %s" % (rel, pat))

    def test_exported_python_compiles(self):
        for rel in ("ofn/agents/owner_notify.py", "ofn/agents/glass_runner.py",
                    "tools/revenue-drive/owner_ask.py", "tools/revenue-drive/owner_reply.py",
                    "tools/w1_verdict_collector.py"):
            self.assertTrue(compileall.compile_file(str(ROOT / rel), quiet=2, force=True),
                            "compile failed: %s" % rel)


if __name__ == "__main__":
    unittest.main()
