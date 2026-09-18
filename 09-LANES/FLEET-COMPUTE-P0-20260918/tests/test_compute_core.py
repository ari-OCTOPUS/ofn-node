#!/usr/bin/env python3
"""Failure-mode tests for the fleet compute control plane.

Covers the failure list the fleet CPU scan requires before any dispatch:
duplicate delivery, reboot during execution, lease expiry, stale heartbeat,
thermal pressure, memory pressure, OOM-adjacent reservation, disk-full,
poisoned task payload, retry budget, owner pause, and unknown telemetry.

Run:  python -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import compute_core as cc  # noqa: E402


def healthy_telemetry(node_id: str = "160", **over) -> dict:
    t = {
        "ok": True,
        "node_id": node_id,
        "node_utc": cc.utc_now(),
        "nproc": 8,
        "load1": 0.05,
        "cpu_pct": 0.3,
        "mem_used_pct": 6.6,
        "mem_avail_kb": 3_600_000,
        "hottest_millic": 24_100,
        "disk_root_used_pct": "5%",
    }
    t.update(over)
    return t


class StoreTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = cc.Store(Path(self.tmp.name) / "compute_tasks.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def enqueue(self, **over):
        kw = dict(
            profile="cpu_bench",
            params={"seconds": 5},
            input_digest=cc.sha({"p": "cpu_bench"}),
            idempotency_key="idem-1",
        )
        kw.update(over)
        return self.store.enqueue(**kw)


class TestDurability(StoreTestBase):
    def test_survives_reopen(self):
        """A task must outlive the process that enqueued it."""
        task = self.enqueue()["task"]
        self.store.close()
        self.store = cc.Store(Path(self.tmp.name) / "compute_tasks.db")
        again = self.store.get(task["task_id"])
        self.assertIsNotNone(again)
        self.assertEqual(again["state"], "QUEUED")

    def test_external_effects_refused_by_schema(self):
        """A poisoned payload cannot smuggle an external effect into the store."""
        with self.assertRaises(Exception):
            self.store.db.execute(
                """INSERT INTO tasks(task_id, idempotency_key, profile, params_json, input_digest,
                       resource_class, max_attempts, attempt, state, created_utc, updated_utc,
                       external_effects, customer_send)
                   VALUES('t-x','k-x','cpu_bench','{}','d','cpu_batch',1,0,'QUEUED',
                          '2026-01-01T00:00:00Z','2026-01-01T00:00:00Z', 1, 0)"""
            )

    def test_idempotency_key_dedupes(self):
        first = self.enqueue()
        second = self.enqueue()
        self.assertTrue(second["deduped"])
        self.assertEqual(first["task"]["task_id"], second["task"]["task_id"])

    def test_task_id_deterministic_from_profile_and_key(self):
        a = self.enqueue(idempotency_key="same")["task"]["task_id"]
        b = self.store.enqueue(
            profile="cpu_bench", params={"seconds": 5},
            input_digest=cc.sha({"p": "cpu_bench"}), idempotency_key="same",
        )
        self.assertTrue(b["deduped"])
        self.assertEqual(a, b["task"]["task_id"])


class TestLeases(StoreTestBase):
    def test_claim_grants_real_expiry(self):
        task = self.enqueue()["task"]
        res = self.store.claim(task["task_id"], "160", lease_seconds=120)
        self.assertTrue(res["ok"])
        # The old fleet jobs parked expiry at year 2099; a real lease must expire.
        self.assertLess(res["expiry_utc"], "2030-01-01T00:00:00Z")

    def test_claim_refuses_non_queued(self):
        task = self.enqueue()["task"]
        self.store.claim(task["task_id"], "160", lease_seconds=60)
        second = self.store.claim(task["task_id"], "114", lease_seconds=60)
        self.assertFalse(second["ok"])
        self.assertEqual(second["error"], "not_queued")

    def test_reboot_during_run_requeues(self):
        """Reboot mid-execution: the lease expires and the task is reassigned."""
        task = self.enqueue()["task"]
        self.store.claim(task["task_id"], "160", lease_seconds=60)
        self.store.start(task["task_id"])
        past = "2026-01-01T00:00:00Z"
        self.store.db.execute(
            "UPDATE tasks SET lease_expiry_utc=? WHERE task_id=?", (past, task["task_id"])
        )
        reclaimed = self.store.reclaim_expired()
        self.assertIn(task["task_id"], [r["task_id"] for r in reclaimed])
        self.assertEqual(self.store.get(task["task_id"])["state"], "QUEUED")
        self.assertIsNone(self.store.get(task["task_id"])["worker_node_id"])
        # The caller needs node + attempt to stop the abandoned scope, because
        # the task row has just forgotten both.
        row = [r for r in reclaimed if r["task_id"] == task["task_id"]][0]
        self.assertEqual(row["node_id"], "160")
        self.assertEqual(row["attempt"], 1)
        self.assertEqual(row["kind"], "LEASE_EXPIRED_REQUEUED")

    def test_expired_lease_with_exhausted_budget_is_final(self):
        task = self.enqueue(max_attempts=1)["task"]
        self.store.claim(task["task_id"], "160", lease_seconds=60)
        self.store.start(task["task_id"])  # attempt -> 1
        self.store.db.execute(
            "UPDATE tasks SET lease_expiry_utc='2026-01-01T00:00:00Z' WHERE task_id=?",
            (task["task_id"],),
        )
        self.store.reclaim_expired()
        self.assertEqual(self.store.get(task["task_id"])["state"], "FAILED_FINAL")

    def test_late_result_after_reassignment_is_ignored(self):
        """Exactly-once: a straggler result must not overwrite or re-settle."""
        task = self.enqueue()["task"]
        self.store.claim(task["task_id"], "160", lease_seconds=60)
        self.store.start(task["task_id"])
        self.store.db.execute(
            "UPDATE tasks SET lease_expiry_utc='2026-01-01T00:00:00Z' WHERE task_id=?",
            (task["task_id"],),
        )
        self.store.reclaim_expired()
        # Reassigned to 114 and completed there.
        self.store.claim(task["task_id"], "114", lease_seconds=60)
        self.store.start(task["task_id"])
        first = self.store.succeed(task["task_id"], output_digest="digest-a")
        self.assertFalse(first["duplicate"])
        # The old worker finally reports.
        late = self.store.succeed(task["task_id"], output_digest="digest-late")
        self.assertTrue(late["duplicate"])
        self.assertEqual(self.store.get(task["task_id"])["output_digest"], "digest-a")

    def test_double_delivery_of_same_result_is_idempotent(self):
        task = self.enqueue()["task"]
        self.store.claim(task["task_id"], "160", lease_seconds=60)
        self.store.start(task["task_id"])
        self.store.succeed(task["task_id"], output_digest="d1")
        self.store.succeed(task["task_id"], output_digest="d1")
        kinds = [e["kind"] for e in self.store.events(task["task_id"], limit=20)]
        self.assertIn("SETTLE_DUPLICATE_IGNORED", kinds)


class TestRetryBudget(StoreTestBase):
    def test_retry_until_budget_exhausted(self):
        task = self.enqueue(max_attempts=2)["task"]
        self.store.claim(task["task_id"], "160", lease_seconds=60)
        self.store.start(task["task_id"])
        first = self.store.fail(task["task_id"], error="io_error")
        self.assertEqual(first["task"]["state"], "QUEUED")
        self.store.claim(task["task_id"], "160", lease_seconds=60)
        self.store.start(task["task_id"])
        second = self.store.fail(task["task_id"], error="io_error")
        self.assertEqual(second["task"]["state"], "FAILED_FINAL")

    def test_non_retryable_failure_is_final_immediately(self):
        task = self.enqueue(max_attempts=5)["task"]
        self.store.claim(task["task_id"], "160", lease_seconds=60)
        self.store.start(task["task_id"])
        res = self.store.fail(task["task_id"], error="profile_not_allowed", retryable=False)
        self.assertEqual(res["task"]["state"], "FAILED_FINAL")

    def test_failure_clears_worker_binding(self):
        task = self.enqueue()["task"]
        self.store.claim(task["task_id"], "160", lease_seconds=60)
        self.store.start(task["task_id"])
        self.store.fail(task["task_id"], error="x")
        t = self.store.get(task["task_id"])
        self.assertIsNone(t["worker_node_id"])
        self.assertIsNone(t["lease_id"])


class TestAdmission(unittest.TestCase):
    def setUp(self):
        self.policy = dict(cc.DEFAULT_POLICY)

    def test_healthy_idle_node_admitted(self):
        v = cc.evaluate_node("160", healthy_telemetry(), self.policy)
        self.assertTrue(v["admit"], v["reasons"])
        self.assertEqual(v["reasons"], [])

    def test_missing_telemetry_is_unknown_and_not_admitted(self):
        v = cc.evaluate_node("160", None, self.policy)
        self.assertFalse(v["admit"])
        self.assertEqual(v["verdict"], "UNKNOWN")

    def test_stale_heartbeat_refused(self):
        old = cc.plus_seconds(cc.utc_now(), -600)
        v = cc.evaluate_node("160", healthy_telemetry(node_utc=old), self.policy)
        self.assertFalse(v["admit"])
        self.assertTrue(any(r.startswith("STALE_TELEMETRY") for r in v["reasons"]))

    def test_thermal_pressure_refused(self):
        v = cc.evaluate_node("160", healthy_telemetry(hottest_millic=72_000), self.policy)
        self.assertFalse(v["admit"])
        self.assertTrue(any(r.startswith("THERMAL_CEILING") for r in v["reasons"]))

    def test_memory_pressure_refused(self):
        v = cc.evaluate_node("160", healthy_telemetry(mem_used_pct=91.0, mem_avail_kb=100_000), self.policy)
        self.assertFalse(v["admit"])
        self.assertIn("MEMORY_PRESSURE(91.0%)", v["reasons"])

    def test_disk_full_refused(self):
        v = cc.evaluate_node("160", healthy_telemetry(disk_root_used_pct="96%"), self.policy)
        self.assertFalse(v["admit"])
        self.assertTrue(any(r.startswith("DISK_PRESSURE") for r in v["reasons"]))

    def test_busy_node_refused(self):
        v = cc.evaluate_node("138", healthy_telemetry(cpu_pct=88.0, load1=12.0), self.policy)
        self.assertFalse(v["admit"])
        self.assertTrue(any(r.startswith("CPU_BUSY") for r in v["reasons"]))
        self.assertTrue(any(r.startswith("LOAD_HIGH") for r in v["reasons"]))

    def test_owner_pause_blocks_placement(self):
        policy = dict(self.policy, allowed_nodes=[])
        v = cc.evaluate_node("160", healthy_telemetry(), policy)
        self.assertFalse(v["admit"])
        self.assertIn("NODE_NOT_ALLOWED", v["reasons"])

    def test_control_plane_never_reaches_full_capacity(self):
        v = cc.evaluate_node("180", healthy_telemetry(nproc=1), self.policy)
        self.assertFalse(v["admit"])
        self.assertIn("NO_SPARE_CORE", v["reasons"])

    def test_thermal_unknown_refused(self):
        tel = healthy_telemetry()
        del tel["hottest_millic"]
        v = cc.evaluate_node("160", tel, self.policy)
        self.assertFalse(v["admit"])
        self.assertIn("THERMAL_UNKNOWN", v["reasons"])


class TestPlacement(unittest.TestCase):
    def setUp(self):
        self.policy = dict(cc.DEFAULT_POLICY)

    def test_coldest_node_wins(self):
        res = cc.select_placement(
            [
                {"node_id": "114", "telemetry": healthy_telemetry(hottest_millic=45_000, cpu_pct=20.0)},
                {"node_id": "160", "telemetry": healthy_telemetry(hottest_millic=23_000, cpu_pct=0.2)},
            ],
            self.policy,
        )
        self.assertEqual(res["chosen"]["node_id"], "160")

    def test_no_admissible_node_reports_reason(self):
        res = cc.select_placement(
            [{"node_id": "114", "telemetry": healthy_telemetry(hottest_millic=80_000)}],
            self.policy,
        )
        self.assertIsNone(res["chosen"])
        self.assertEqual(res["reason"], "NO_ADMISSIBLE_NODE")

    def test_refusal_not_overridden_by_score(self):
        """An inadmissible node must never be chosen even if it looks fastest."""
        res = cc.select_placement(
            [
                {"node_id": "114", "telemetry": healthy_telemetry(cpu_pct=0.0, hottest_millic=78_000)},
                {"node_id": "160", "telemetry": healthy_telemetry(cpu_pct=40.0, hottest_millic=30_000)},
            ],
            self.policy,
        )
        self.assertEqual(res["chosen"]["node_id"], "160")

    def test_failing_node_quarantined(self):
        """A node over the failure threshold is excluded even if it is colder."""
        res = cc.select_placement(
            [
                {"node_id": "114", "telemetry": healthy_telemetry(hottest_millic=20_000), "failure_count": 3},
                {"node_id": "160", "telemetry": healthy_telemetry(hottest_millic=26_000), "failure_count": 0},
            ],
            self.policy,
        )
        self.assertEqual(res["chosen"]["node_id"], "160")
        quarantined = [e for e in res["evaluated"] if e["node_id"] == "114"][0]
        self.assertFalse(quarantined["admit"])
        self.assertIn("NODE_QUARANTINED(3)", quarantined["reasons"])

    def test_quarantine_is_not_overridable_by_score(self):
        res = cc.select_placement(
            [{"node_id": "114", "telemetry": healthy_telemetry(cpu_pct=0.0), "failure_count": 5}],
            self.policy,
        )
        self.assertIsNone(res["chosen"])


class TestParkingAndCancel(StoreTestBase):
    def test_park_does_not_consume_attempt(self):
        task = self.enqueue()["task"]
        self.store.park(task["task_id"], reason="NO_ADMISSIBLE_NODE")
        t = self.store.get(task["task_id"])
        self.assertEqual(t["state"], "PARKED")
        self.assertEqual(t["attempt"], 0)

    def test_unpark_returns_to_queue(self):
        task = self.enqueue()["task"]
        self.store.park(task["task_id"], reason="stale")
        self.store.unpark(task["task_id"])
        self.assertEqual(self.store.get(task["task_id"])["state"], "QUEUED")

    def test_cancel_releases_lease(self):
        task = self.enqueue()["task"]
        self.store.claim(task["task_id"], "160", lease_seconds=60)
        lease_id = self.store.get(task["task_id"])["lease_id"]
        self.store.cancel(task["task_id"], reason="owner_pause")
        row = self.store.db.execute("SELECT * FROM leases WHERE lease_id=?", (lease_id,)).fetchone()
        self.assertIsNotNone(row["released_utc"])
        self.assertEqual(row["release_reason"], "cancelled")

    def test_stats_shape(self):
        self.enqueue()
        s = self.store.stats()
        self.assertEqual(s["by_state"].get("QUEUED"), 1)


class TestEventLogAudit(StoreTestBase):
    def test_every_transition_is_recorded(self):
        task = self.enqueue()["task"]
        self.store.claim(task["task_id"], "160", lease_seconds=60)
        self.store.start(task["task_id"])
        self.store.succeed(task["task_id"], output_digest="d")
        kinds = [e["kind"] for e in self.store.events(task["task_id"], limit=50)]
        for expected in ("ENQUEUED", "LEASED", "STARTED", "SUCCEEDED"):
            self.assertIn(expected, kinds)

    def test_event_payload_is_json(self):
        self.enqueue()
        for e in self.store.events(limit=5):
            json.loads(e["payload_json"] or "{}")


if __name__ == "__main__":
    unittest.main()
