#!/usr/bin/env python3
"""تستِ لایهٔ بینش.

قانونی که محافظت می‌شود: **هیچ فرضیه‌ای بدونِ ابطال‌کننده و بدونِ پیش‌بینیِ
سنجیدنی وارد خروجی نمی‌شود.** یک ادعای رتبه‌دار که نشود غلط بودنش را نشان داد،
دقیقاً همان چیزی است که کلِ این پروژه علیهش است.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))
import self_insight as si  # noqa: E402


def scan_with(**checks):
    base = {"flags": {}, "state": {}, "tests": {}, "markers": {}, "symbols": {}}
    base.update(checks)
    return {"checks": base}


class ContractTests(unittest.TestCase):
    REQUIRED = ("id", "rule", "subject", "claim", "mechanism",
                "predicted_observation", "falsifier", "confidence",
                "confidence_why", "impact", "cost", "rank", "cheapest_test")

    def _all_hypotheses(self):
        scan = scan_with(
            flags={"defaults": {"OCTOPUS_ALPHA": [{"module": "m.py", "default": "1"}]},
                   "armed_unread": ["OCTOPUS_GHOST"]},
            state={"single_referencer": [{"file": "x.jsonl", "by": ["w.py"],
                                          "bytes": 50_000}]},
            tests={"untested": [{"module": "big.py", "lines": 900, "fan_in": 9}]},
            symbols={"dead": [{"file": "d.py", "symbol": f"s{i}", "lines": 10}
                              for i in range(4)]})
        out = []
        for rule in si.RULES:
            out.extend(rule(scan))
        return out

    def test_every_rule_produces_at_least_one_hypothesis(self):
        rules = {h["rule"] for h in self._all_hypotheses()}
        self.assertEqual(len(rules), len(si.RULES), rules)

    def test_no_hypothesis_ships_without_a_falsifier_or_prediction(self):
        for h in self._all_hypotheses():
            for k in self.REQUIRED:
                self.assertIn(k, h, h.get("id"))
            self.assertTrue(str(h["falsifier"]).strip(), h["id"])
            self.assertIsInstance(h["predicted_observation"], dict)
            self.assertIn("check", h["predicted_observation"])

    def test_rank_is_exactly_impact_times_confidence_over_cost(self):
        for h in self._all_hypotheses():
            expect = h["impact"] * h["confidence"] / si.COST[h["cost"]]
            self.assertAlmostEqual(h["rank"], round(expect, 3), places=3)

    def test_confidence_is_a_probability(self):
        for h in self._all_hypotheses():
            self.assertGreaterEqual(h["confidence"], 0.0)
            self.assertLessEqual(h["confidence"], 1.0)


class SilentDefaultTests(unittest.TestCase):
    def _claim(self, default):
        scan = scan_with(flags={"defaults": {
            "OCTOPUS_X": [{"module": "m.py", "default": default}]}})
        return si.rule_silent_default(scan)[0]

    def test_truthy_default_is_reported_as_on_and_weighs_most(self):
        h = self._claim("1")
        self.assertIn("روشن", h["claim"])
        self.assertEqual(h["impact"], 4)

    def test_falsy_default_is_reported_as_off(self):
        self.assertIn("خاموش", self._claim("0")["claim"])

    def test_a_duration_is_never_called_off(self):
        """باگِ نسخهٔ اول: `'3600'` را «خاموش» می‌خواند — ادعایی صریحاً غلط."""
        h = self._claim("3600")
        self.assertNotIn("خاموش", h["claim"])
        self.assertNotIn("روشن", h["claim"])
        self.assertIn("3600", h["claim"])
        self.assertEqual(h["impact"], 3)

    def test_a_path_default_is_treated_as_unvoted_config(self):
        h = self._claim("F:\\backup")
        self.assertIn("مقدارِ", h["claim"])
        self.assertEqual(h["impact"], 3)


class HonestyTests(unittest.TestCase):
    def test_ghost_flag_confidence_stays_low_because_the_tree_may_be_partial(self):
        scan = scan_with(flags={"armed_unread": ["A", "B", "C"]})
        h = si.rule_ghost_flag(scan)[0]
        self.assertLess(h["confidence"], 0.6)
        self.assertIn("ناقص", h["falsifier"])

    def test_ghost_flags_are_one_hypothesis_not_n(self):
        scan = scan_with(flags={"armed_unread": [f"F{i}" for i in range(40)]})
        self.assertEqual(len(si.rule_ghost_flag(scan)), 1)

    def test_low_fan_in_modules_are_not_promoted(self):
        scan = scan_with(tests={"untested": [
            {"module": "tiny.py", "lines": 20, "fan_in": 1}]})
        self.assertEqual(si.rule_blast_radius(scan), [])

    def test_dead_symbols_below_threshold_are_not_a_cluster(self):
        scan = scan_with(symbols={"dead": [
            {"file": "a.py", "symbol": "s1", "lines": 9},
            {"file": "a.py", "symbol": "s2", "lines": 9}]})
        self.assertEqual(si.rule_dead_cluster(scan), [])

    def test_empty_scan_yields_no_hypotheses_and_does_not_raise(self):
        for rule in si.RULES:
            self.assertEqual(rule(scan_with()), [])


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.j = self.tmp / "self-insight.jsonl"

    def _write_prior(self, hyps):
        self.j.write_text(json.dumps({"hypotheses": hyps}, ensure_ascii=False)
                          + "\n", encoding="utf-8")

    def test_prediction_counts_as_resolved_when_the_subject_disappears(self):
        self._write_prior([{"id": "silent_default:OCTOPUS_X",
                            "predicted_observation":
                                {"check": "flags.read_unarmed", "absent": "OCTOPUS_X"}}])
        scan = scan_with(flags={"read_unarmed": [{"flag": "OCTOPUS_Y"}]})
        c = si.score_previous(scan, self.j)
        self.assertEqual(c["resolved"], ["silent_default:OCTOPUS_X"])
        self.assertEqual(c["resolution_rate"], 1.0)

    def test_prediction_stays_open_while_the_subject_is_still_there(self):
        self._write_prior([{"id": "silent_default:OCTOPUS_X",
                            "predicted_observation":
                                {"check": "flags.read_unarmed", "absent": "OCTOPUS_X"}}])
        scan = scan_with(flags={"read_unarmed": [{"flag": "OCTOPUS_X"}]})
        c = si.score_previous(scan, self.j)
        self.assertEqual(c["still_open"], ["silent_default:OCTOPUS_X"])
        self.assertEqual(c["resolution_rate"], 0.0)

    def test_unmeasurable_predictions_are_excluded_from_the_rate(self):
        """نمرهٔ خوب از حذفِ سؤالِ سخت به‌دست نمی‌آید — جدا شمرده می‌شود."""
        self._write_prior([
            {"id": "a", "predicted_observation": {"check": "symbols.dead",
                                                  "file_count_below": 3}},
            {"id": "b", "predicted_observation": {"check": "flags.read_unarmed",
                                                  "absent": "GONE"}}])
        c = si.score_previous(scan_with(flags={"read_unarmed": []}), self.j)
        self.assertEqual(c["unmeasurable"], ["a"])
        self.assertEqual(c["measured"], 1)
        self.assertEqual(c["resolution_rate"], 1.0)

    def test_no_journal_means_no_score_not_a_perfect_score(self):
        c = si.score_previous(scan_with(), self.tmp / "missing.jsonl")
        self.assertEqual(c["previous_hypotheses"], 0)
        self.assertIsNone(c["resolution_rate"])

    def test_corrupt_journal_is_survived(self):
        self.j.write_text("NOT JSON\n", encoding="utf-8")
        self.assertEqual(si.score_previous(scan_with(), self.j)["previous_hypotheses"], 0)

    def test_correlation_not_causation_is_stated(self):
        self.assertIn("همبستگی", si.score_previous(scan_with(), self.j)["note"])


class RunTests(unittest.TestCase):
    def test_a_broken_rule_does_not_kill_the_run(self):
        def boom(_scan):
            raise RuntimeError("منفجر شد")
        original = si.RULES
        si.RULES = original + (boom,)
        try:
            root = Path(tempfile.mkdtemp())
            (root / "a.py").write_text("x = 1\n", encoding="utf-8")
            r = si.run(root, journal=False)
            self.assertIn("boom", r["rule_errors"])
            self.assertIn("hypotheses", r)
        finally:
            si.RULES = original

    def test_hypotheses_come_back_sorted_by_rank(self):
        root = Path(tempfile.mkdtemp())
        (root / "a.py").write_text(
            'import os\nos.environ.get("OCTOPUS_ALPHA", "1")\n', encoding="utf-8")
        (root / "OCTOPUS-flags.cmd").write_bytes(b'@set "OCTOPUS_BETA=1"\r\n')
        ranks = [h["rank"] for h in si.run(root, journal=False)["hypotheses"]]
        self.assertEqual(ranks, sorted(ranks, reverse=True))

    def test_journal_round_trip_then_self_score(self):
        root = Path(tempfile.mkdtemp())
        (root / "a.py").write_text(
            'import os\nos.environ.get("OCTOPUS_ALPHA", "1")\n', encoding="utf-8")
        first = si.run(root)
        self.assertGreater(first["counts"]["total"], 0)
        second = si.run(root)
        self.assertEqual(second["calibration"]["previous_hypotheses"],
                         first["counts"]["total"])

    def test_card_never_raises_on_an_empty_tree(self):
        self.assertIsInstance(si.card(Path(tempfile.mkdtemp())), str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
