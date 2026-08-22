#!/usr/bin/env python3
"""Journal-only self_insight cycle + doctor epistemics C1 wire."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "doctor"))

import self_insight as si  # noqa: E402
import calibration as cal  # noqa: E402


class JournalOnceTests(unittest.TestCase):
    def test_run_once_journal_writes_one_row_without_self_scan(self):
        root = Path(tempfile.mkdtemp())
        out = si.run_once_journal(root, limit=10)
        self.assertEqual(out["mode"], "journal_once")
        self.assertGreaterEqual(out["counts"]["total"], 1)
        self.assertLessEqual(out["counts"]["total"], 10)
        j = root / "state" / "self-insight.jsonl"
        self.assertTrue(j.exists())
        rows = [json.loads(l) for l in j.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema"], si.SCHEMA)
        self.assertEqual(rows[0].get("mode"), "journal_once")
        self.assertLess(out["elapsed_s"], 5.0)

    def test_card_reads_journal_once_row(self):
        root = Path(tempfile.mkdtemp())
        si.run_once_journal(root, limit=5)
        text = si.card(root)
        self.assertIsInstance(text, str)
        self.assertTrue(len(text) > 10)


class EpistemicsWireTests(unittest.TestCase):
    def test_draft_epistemic_uncertainty_loads_policy_and_claim(self):
        out = cal.draft_epistemic_uncertainty({"coherence": 0.42})
        self.assertIsNotNone(out)
        self.assertTrue(out["wired"])
        self.assertEqual(out["max_authority"], "propose")
        self.assertFalse(out["may_execute"])
        self.assertEqual(out["draft"]["metric"], "coherence")
        self.assertEqual(out["draft"]["observed_value"], 0.42)
        self.assertFalse(out["draft"]["may_execute"])

    def test_effective_mine_attaches_epistemic_on_allow(self):
        class FakeDoctor:
            def mine(self, trace=None):
                return {"bottleneck": "noise", "severity": "high",
                        "evidence": {"key": "k", "score": 0.31}}

            class _R:
                status = "merged"
            _rfcs = {"x": _R()}

        bn = cal.effective_mine(FakeDoctor(), db=None)
        self.assertIsNotNone(bn)
        self.assertIn("_epistemic", bn)
        self.assertEqual(bn["_epistemic"]["draft"]["metric"], "coherence")


if __name__ == "__main__":
    unittest.main(verbosity=2)