#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OCTOPUS v3.0 P0 overlay — unique test file (WORKLOCK: not registered in run_all.py).

Run:
  python _ops/tests/test_octopus_v3_p0_20260816.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

OPS = Path(__file__).resolve().parents[1]
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

from octopus_v3 import WIRED, VERSION  # noqa: E402
from octopus_v3.budget import DAILY_CENTS, OverlayBudget  # noqa: E402
from octopus_v3.exceptions import (  # noqa: E402
    BudgetExceeded,
    KillEngaged,
    LedgerIntegrityError,
    LeaseError,
    PolicyDenied,
    TaintNetworkDenied,
)
from octopus_v3.freedom import freedom_metrics  # noqa: E402
from octopus_v3.gate import Action, P0ExecutionGate  # noqa: E402
from octopus_v3.kill import KillState, KillSwitch  # noqa: E402
from octopus_v3.ledger import IntentLedger  # noqa: E402
from octopus_v3.lease import LeaseStore  # noqa: E402
from octopus_v3.profile import HARD_NO_GO, SYSTEM_PROFILE  # noqa: E402
from octopus_v3.taint import TaskTaintLatch  # noqa: E402
from octopus_v3.verify_evidence import lint_text  # noqa: E402


class P0V3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        self.key = b"unit-test-hmac-key-not-for-production"
        self.ledger = IntentLedger(self.root / "intent.jsonl", hmac_key=self.key)
        self.kill = KillSwitch(
            self.root / "KILL",
            compose_paths=(self.root / "STOP-ORGANISM",),
            write_live_stop=False,
            live_stop_path=self.root / "LIVE-STOP",
            ledger=self.ledger,
        )
        self.budget = OverlayBudget(self.root / "budget.json", day_key="2026-08-16", month_key="2026-08")
        self.taint = TaskTaintLatch()
        self.leases = LeaseStore(self.key)
        self.ran: list[str] = []
        self.gate = P0ExecutionGate(
            ledger=self.ledger,
            kill=self.kill,
            budget=self.budget,
            taint=self.taint,
            leases=self.leases,
            execute_fn=lambda a: self.ran.append(a.name),
        )

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_not_wired_to_live_organism(self) -> None:
        self.assertFalse(WIRED)
        self.assertTrue(VERSION.startswith("3.0"))
        self.assertFalse(SYSTEM_PROFILE["wired"])
        self.assertEqual(SYSTEM_PROFILE["hardware"]["model"], "81Y6")
        self.assertLess(float(SYSTEM_PROFILE["hardware"]["ram_gib_approx"]), 20.0)
        self.assertIn("abliterate_brain", HARD_NO_GO)

    def test_l0_action_records_intent_then_executes(self) -> None:
        v = self.gate.admit_and_run(Action(name="local_classify", actor="test", task_id="t1", cost_cents=0))
        self.assertTrue(v.ok)
        self.assertEqual(self.ran, ["local_classify"])
        self.assertEqual(self.ledger.verify_integrity(), 2)  # INTENT + RESULT

    def test_hash_chain_three_records(self) -> None:
        for i in range(3):
            self.ledger.append("INTENT", {"i": i})
        self.assertEqual(self.ledger.verify_integrity(), 3)

    def test_tamper_on_disk_is_detected(self) -> None:
        self.ledger.append("INTENT", {"ok": True})
        raw = self.ledger.path.read_text("utf-8")
        self.ledger.path.write_text(raw.replace("true", "false", 1), encoding="utf-8")
        with self.assertRaises(LedgerIntegrityError):
            self.ledger.verify_integrity()

    def test_budget_over_per_action_denied(self) -> None:
        with self.assertRaises(BudgetExceeded):
            self.gate.admit_and_run(Action(name="think", actor="test", task_id="t", cost_cents=201))
        self.assertEqual(self.ran, [])

    def test_overlay_cannot_loosen_live_caps(self) -> None:
        with self.assertRaises(BudgetExceeded):
            OverlayBudget(self.root / "loose.json", daily_cents=DAILY_CENTS + 1)

    def test_financial_without_owner_blocked(self) -> None:
        with self.assertRaises(PolicyDenied):
            self.gate.admit_and_run(
                Action(name="payout", actor="test", task_id="t", financial=True, cost_cents=1, owner_approved=False)
            )
        self.assertEqual(self.ran, [])

    def test_financial_with_owner_runs(self) -> None:
        v = self.gate.admit_and_run(
            Action(name="payout", actor="owner", task_id="t", financial=True, cost_cents=1, owner_approved=True)
        )
        self.assertTrue(v.ok)

    def test_hard_no_go_abliteration(self) -> None:
        with self.assertRaises(PolicyDenied):
            self.gate.admit_and_run(Action(name="abliterate_brain", actor="test", task_id="t"))

    def test_kill_blocks_in_sub_millisecond_window(self) -> None:
        elapsed = self.kill.trigger("test")
        self.assertLess(elapsed, 0.05)
        self.assertTrue(self.kill.engaged())
        t0 = time.perf_counter()
        with self.assertRaises(KillEngaged):
            self.gate.admit_and_run(Action(name="local_classify", actor="test", task_id="t"))
        self.assertLess(time.perf_counter() - t0, 0.01)
        self.assertEqual(self.ran, [])
        self.assertFalse((self.root / "LIVE-STOP").exists())

    def test_composed_stop_file_engages_without_overlay(self) -> None:
        (self.root / "STOP-ORGANISM").write_text("halt\n", encoding="utf-8")
        self.assertTrue(self.kill.engaged())
        with self.assertRaises(KillEngaged):
            self.kill.assert_clear()

    def test_taint_latch_forces_network_none_for_rest_of_task(self) -> None:
        v = self.gate.admit_and_run(
            Action(name="read_paste", actor="test", task_id="task-9", untrusted_input=True, network_requested="none")
        )
        self.assertTrue(v.ok)
        self.assertTrue(self.taint.is_tainted("task-9"))
        self.assertEqual(self.taint.network_mode("task-9", "open"), "none")
        with self.assertRaises(TaintNetworkDenied):
            self.gate.admit_and_run(
                Action(name="fetch_url", actor="test", task_id="task-9", network_requested="open")
            )
        # a different task is not latched
        v2 = self.gate.admit_and_run(
            Action(name="local_classify", actor="test", task_id="task-other", network_requested="none")
        )
        self.assertTrue(v2.ok)

    def test_lease_binds_params_and_burns_on_exhaust(self) -> None:
        params = {"dest": "127.0.0.1", "tool": "search"}
        lease = self.leases.issue(
            capability="search_hybrid",
            cost_cap_cents=50,
            max_calls=1,
            network_allow=("none",),
            ttl_s=60,
            bound_params=params,
        )
        v = self.gate.admit_and_run(
            Action(name="search_hybrid", actor="brain", task_id="t", cost_cents=10, params=params, lease=lease)
        )
        self.assertTrue(v.ok)
        with self.assertRaises(LeaseError):
            self.gate.admit_and_run(
                Action(name="search_hybrid", actor="brain", task_id="t", cost_cents=10, params=params, lease=lease)
            )
        with self.assertRaises(LeaseError):
            self.leases.consume(lease, params={"dest": "evil.example", "tool": "search"}, cost_cents=1)

    def test_lease_expiry(self) -> None:
        params = {"q": "x"}
        lease = self.leases.issue(
            capability="think",
            cost_cap_cents=10,
            max_calls=2,
            network_allow=(),
            ttl_s=1,
            bound_params=params,
            now=1_000.0,
        )
        with self.assertRaises(LeaseError):
            self.leases.consume(lease, params=params, cost_cents=1, now=1_002.0)

    def test_freedom_metrics_not_a_slogan(self) -> None:
        m = freedom_metrics({
            "local_calls": 8,
            "cloud_calls": 2,
            "undocumented_external_egress": 0,
            "weight_license": "Apache-2.0",
            "policy_author": "owner",
            "abliteration_of_brain": False,
        })
        self.assertTrue(m["sovereign"])
        self.assertGreaterEqual(m["local_execution_ratio"], 0.70)
        bad = freedom_metrics({
            "local_calls": 1,
            "cloud_calls": 9,
            "undocumented_external_egress": 0,
            "weight_license": "Qwen3.8-Max",
            "policy_author": "model",
            "abliteration_of_brain": True,
        })
        self.assertFalse(bad["sovereign"])

    def test_evidence_linter_unverified_near_tier1(self) -> None:
        errs = lint_text(
            "TIER-1 adopt vaara [UNVERIFIED] because stars",
            root=OPS.parent,
            source="mem",
        )
        self.assertTrue(any("TIER-1" in e for e in errs))

    def test_evidence_linter_repo_line_count(self) -> None:
        errs = lint_text(
            "[REPO] `04 - Architect System/scripts/budget_gate.py:1` caps",
            root=OPS.parent,
            source="mem",
        )
        self.assertEqual(errs, [])
        errs2 = lint_text(
            "[REPO] `04 - Architect System/scripts/budget_gate.py:999999` caps",
            root=OPS.parent,
            source="mem",
        )
        self.assertTrue(any("999999" in e for e in errs2))

    def test_kill_arm_state(self) -> None:
        self.assertEqual(self.kill.state(), KillState.DISARMED)
        self.kill.arm()
        self.assertEqual(self.kill.state(), KillState.ARMED)
        self.assertFalse(self.kill.engaged())


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    raise SystemExit(unittest.main(verbosity=2))
