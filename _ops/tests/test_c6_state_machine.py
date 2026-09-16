#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_c6_state_machine — unified C6 reproduction lifecycle recorder.

Covers: full legal lifecycle, fail-closed illegal edges, verdict derivation,
deterministic repro_id, append-only per-lineage journal, and fail-soft (never
raises). stdlib-only, no live state touched (uses a temp state_dir)."""
import os
import sys
import json
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import c6_state_machine as sm  # noqa: E402


class C6StateMachine(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="c6sm_")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _t(self, cid, to, **kw):
        return sm.transition(state_dir=self.dir, contract_id=cid, to_state=to, **kw)

    def test_full_legal_lifecycle_to_birth(self):
        cid = "contract-A"
        chain = ["PROPOSED", "RUNNING", "VERIFIED", "PENDING_ADMISSION",
                 "ADMITTED", "TRANSPLANTED"]
        for st in chain:
            r = self._t(cid, st)
            self.assertTrue(r["ok"], f"{st} should be legal: {r}")
        hist = sm.history(self.dir, cid)
        self.assertEqual([h["to"] for h in hist], chain)
        # TRANSPLANTED (generational birth) is the terminal owner-tap state
        self.assertEqual(hist[-1]["to"], "TRANSPLANTED")

    def test_illegal_edge_is_refused_failclosed(self):
        cid = "contract-B"
        self.assertTrue(self._t(cid, "PROPOSED")["ok"])
        r = self._t(cid, "ADMITTED")  # PROPOSED -> ADMITTED is not allowed
        self.assertFalse(r["ok"])
        self.assertIn("illegal edge", r["reason"])
        # journal must not record the refused edge
        self.assertEqual([h["to"] for h in sm.history(self.dir, cid)], ["PROPOSED"])

    def test_unknown_state_refused(self):
        r = self._t("c", "NOT_A_STATE")
        self.assertFalse(r["ok"])
        self.assertIn("unknown state", r["reason"])

    def test_verdict_derivation(self):
        self.assertEqual(sm.derive({"verdict": "accepted"}), "ADMITTED")
        self.assertEqual(sm.derive({"verdict": "rejected"}), "REJECTED")
        self.assertEqual(sm.derive({"verdict": "quarantined"}), "QUARANTINED")
        # accepted but promotion crashed (still PENDING) -> PENDING_ADMISSION
        self.assertEqual(
            sm.derive({"verdict": "accepted",
                       "ledger_entry": {"admission_state": "PENDING"}}),
            "PENDING_ADMISSION")
        # unknown/empty verdict fails safe to TERMINATED
        self.assertEqual(sm.derive({"verdict": "???"}), "TERMINATED")
        self.assertEqual(sm.derive({}), "TERMINATED")

    def test_repro_id_deterministic_and_scoped(self):
        self.assertEqual(sm.repro_id("x"), sm.repro_id("x"))
        self.assertNotEqual(sm.repro_id("x"), sm.repro_id("y"))
        self.assertTrue(sm.repro_id("x").startswith("repro_"))

    def test_two_lineages_do_not_cross(self):
        self._t("A", "PROPOSED")
        self._t("B", "PROPOSED")
        self._t("A", "RUNNING")
        self.assertEqual([h["to"] for h in sm.history(self.dir, "A")],
                         ["PROPOSED", "RUNNING"])
        self.assertEqual([h["to"] for h in sm.history(self.dir, "B")], ["PROPOSED"])

    def test_failsoft_never_raises_on_bad_input(self):
        # None contract, weird result — must return a dict, never raise
        r = sm.transition(state_dir=self.dir, contract_id=None,
                          to_state="PROPOSED", result={"verdict": None})
        self.assertIn("ok", r)

    def test_receipt_store_optional_and_isolated(self):
        # a throwing receipt_store must not break the transition (fail-soft)
        class Boom:
            def record(self, *_a, **_k):
                raise RuntimeError("receipt down")
        r = sm.transition(state_dir=self.dir, contract_id="R",
                          to_state="PROPOSED", receipt_store=Boom())
        self.assertTrue(r["ok"])
        self.assertIsNone(r["row"]["receipt_id"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
