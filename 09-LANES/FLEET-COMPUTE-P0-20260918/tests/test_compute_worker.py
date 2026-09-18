#!/usr/bin/env python3
"""Failure-mode tests for the node-side worker agent.

The critical property: a poisoned or oversized task must be refused by
validation, before any workload runs, and the refusal must be visible as a
receipt rather than an exception.

Run:  python -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import compute_worker as cw  # noqa: E402


def task(**over) -> dict:
    t = {
        "schema": "compute_task.v1",
        "task_id": "task-abc123",
        "profile": "cpu_bench",
        "params": {"seconds": 1},
        "input_digest": "deadbeef",
        "external_effects": 0,
        "customer_send": False,
    }
    t.update(over)
    return t


class TestValidation(unittest.TestCase):
    def test_valid_task_accepted(self):
        ok, err = cw.validate_task(task())
        self.assertTrue(ok, err)

    def test_unknown_profile_refused(self):
        ok, err = cw.validate_task(task(profile="rm_rf"))
        self.assertFalse(ok)
        self.assertEqual(err, "PROFILE_NOT_ALLOWED")

    def test_schema_mismatch_refused(self):
        ok, err = cw.validate_task(task(schema="whatever.v9"))
        self.assertFalse(ok)
        self.assertEqual(err, "SCHEMA_MISMATCH")

    def test_unknown_param_refused(self):
        ok, err = cw.validate_task(task(params={"seconds": 1, "shell": "rm -rf /"}))
        self.assertFalse(ok)
        self.assertEqual(err, "PARAM_NOT_ALLOWED")

    def test_param_out_of_range_refused(self):
        ok, err = cw.validate_task(task(params={"seconds": 99999}))
        self.assertFalse(ok)
        self.assertEqual(err, "PARAM_RANGE")

    def test_bool_is_not_an_int(self):
        """`true` must not satisfy an integer parameter (bool subclasses int)."""
        ok, err = cw.validate_task(task(params={"seconds": True}))
        self.assertFalse(ok)
        self.assertEqual(err, "PARAM_TYPE")

    def test_string_where_number_expected_refused(self):
        ok, err = cw.validate_task(task(params={"seconds": "60; shutdown -h now"}))
        self.assertFalse(ok)
        self.assertEqual(err, "PARAM_TYPE")

    def test_params_must_be_object(self):
        ok, err = cw.validate_task(task(params=["seconds"]))
        self.assertFalse(ok)
        self.assertEqual(err, "PARAMS_NOT_OBJECT")

    def test_external_effects_refused(self):
        ok, err = cw.validate_task(task(external_effects=1))
        self.assertFalse(ok)
        self.assertEqual(err, "EXTERNAL_EFFECTS_REFUSED")

    def test_customer_send_refused(self):
        ok, err = cw.validate_task(task(customer_send=True))
        self.assertFalse(ok)
        self.assertEqual(err, "EXTERNAL_EFFECTS_REFUSED")

    def test_task_id_required(self):
        ok, err = cw.validate_task(task(task_id=""))
        self.assertFalse(ok)
        self.assertEqual(err, "TASK_ID_MISSING")


class TestRefusalReceipt(unittest.TestCase):
    def test_refused_task_produces_receipt_not_exception(self):
        receipt = cw.run_task(task(profile="definitely_not_allowed"))
        self.assertEqual(receipt["status"], "REFUSED")
        self.assertEqual(receipt["error"], "PROFILE_NOT_ALLOWED")
        self.assertEqual(receipt["schema"], "compute_receipt.v1")
        self.assertNotIn("result", receipt)

    def test_receipt_carries_input_digest(self):
        receipt = cw.run_task(task(profile="definitely_not_allowed"))
        self.assertEqual(receipt["input_digest"], "deadbeef")


class TestCpuBench(unittest.TestCase):
    def test_cpu_bench_is_deterministic(self):
        first = cw.run_task(task(params={"seconds": 1, "block_mb": 1}))
        second = cw.run_task(task(params={"seconds": 1, "block_mb": 1}))
        self.assertEqual(first["status"], "SUCCEEDED")
        # The churn count depends on scheduling, but the hash chain of a fixed
        # number of rounds is fixed; the final digest must match for equal ops.
        if first["result"]["ops"] == second["result"]["ops"]:
            self.assertEqual(first["result"]["final_digest"], second["result"]["final_digest"])

    def test_cpu_bench_reports_rate(self):
        receipt = cw.run_task(task(params={"seconds": 1, "block_mb": 1}))
        self.assertGreater(receipt["result"]["ops_per_sec"], 0)
        self.assertGreater(receipt["result"]["elapsed_s"], 0)

    def test_receipt_has_output_digest_and_cgroup(self):
        receipt = cw.run_task(task(params={"seconds": 1, "block_mb": 1}))
        self.assertTrue(receipt["output_digest"])
        self.assertIn("cgroup", receipt)
        self.assertIn("host", receipt)

    def test_cpu_bench_single_worker_still_works(self):
        receipt = cw.run_task(task(params={"seconds": 1, "block_mb": 1, "workers": 1}))
        self.assertEqual(receipt["status"], "SUCCEEDED")
        self.assertEqual(receipt["result"]["workers"], 1)

    def test_cpu_bench_multi_worker_sums_ops(self):
        receipt = cw.run_task(task(params={"seconds": 1, "block_mb": 1, "workers": 2}))
        self.assertEqual(receipt["status"], "SUCCEEDED")
        self.assertEqual(receipt["result"]["workers"], 2)
        self.assertEqual(receipt["result"]["ops"], sum(receipt["result"]["per_worker_ops"]))
        self.assertEqual(len(receipt["result"]["per_worker_ops"]), 2)

    def test_workers_param_out_of_range_refused(self):
        ok, err = cw.validate_task(task(params={"seconds": 1, "workers": 64}))
        self.assertFalse(ok)
        self.assertEqual(err, "PARAM_RANGE")

    def test_timeout_is_capped_by_profile(self):
        """A task cannot ask for more than the profile allows."""
        receipt = cw.run_task(task(params={"seconds": 1, "block_mb": 1}, max_seconds=100000))
        self.assertLessEqual(receipt["max_seconds"], cw.PROFILES["cpu_bench"]["max_seconds"])


class TestManifestProfile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        # Point the profile at a temp root by temporarily extending allowlist.
        self.orig_roots = cw.ALLOWED_ROOTS
        cw.ALLOWED_ROOTS = tuple(list(self.orig_roots) + [self.tmp.name])

    def tearDown(self):
        cw.ALLOWED_ROOTS = self.orig_roots
        self.tmp.cleanup()

    def test_manifest_hashes_files(self):
        root = Path(self.tmp.name)
        (root / "a.txt").write_text("alpha", encoding="utf-8")
        (root / "b.txt").write_text("beta", encoding="utf-8")
        receipt = cw.run_task({
            "schema": "compute_task.v1", "task_id": "t-manifest",
            "profile": "sha256_manifest",
            "params": {"root": str(root), "max_files": 10},
            "input_digest": "d", "external_effects": 0, "customer_send": False,
        })
        self.assertEqual(receipt["status"], "SUCCEEDED")
        self.assertEqual(receipt["result"]["files"], 2)
        self.assertEqual(receipt["result"]["bytes"], 9)
        self.assertEqual(receipt["result"]["sample"][0]["sha256"],
                         hashlib.sha256(b"alpha").hexdigest())

    def test_manifest_respects_max_files(self):
        root = Path(self.tmp.name)
        for i in range(10):
            (root / f"f{i}.txt").write_text("x", encoding="utf-8")
        receipt = cw.run_task({
            "schema": "compute_task.v1", "task_id": "t-manifest-cap",
            "profile": "sha256_manifest",
            "params": {"root": str(root), "max_files": 3},
            "input_digest": "d", "external_effects": 0, "customer_send": False,
        })
        self.assertEqual(receipt["result"]["files"], 3)
        self.assertFalse(receipt["result"]["complete"])

    def test_manifest_refuses_root_outside_allowlist(self):
        receipt = cw.run_task({
            "schema": "compute_task.v1", "task_id": "t-escape",
            "profile": "sha256_manifest",
            "params": {"root": "/etc"},
            "input_digest": "d", "external_effects": 0, "customer_send": False,
        })
        self.assertEqual(receipt["status"], "REFUSED")
        self.assertIn("PERMISSION", receipt["error"])

    def test_manifest_digest_stable_across_runs(self):
        root = Path(self.tmp.name)
        (root / "a.txt").write_text("alpha", encoding="utf-8")
        params = {"schema": "compute_task.v1", "task_id": "t-stable",
                  "profile": "sha256_manifest",
                  "params": {"root": str(root), "max_files": 10},
                  "input_digest": "d", "external_effects": 0, "customer_send": False}
        first = cw.run_task(params)
        second = cw.run_task(params)
        self.assertEqual(first["result"]["manifest_digest"], second["result"]["manifest_digest"])


class TestCapabilityRecord(unittest.TestCase):
    def test_capability_shape(self):
        cap = cw.build_capability()
        self.assertEqual(cap["schema"], "worker_capability.v1")
        for key in ("nproc", "mem_total_kb", "boot_id", "machine_id", "profiles", "thermal_zones"):
            self.assertIn(key, cap)

    def test_capability_is_json_serialisable(self):
        json.dumps(cw.build_capability())

    def test_profiles_advertise_params(self):
        cap = cw.build_capability()
        names = {p["name"] for p in cap["profiles"]}
        self.assertIn("cpu_bench", names)
        for p in cap["profiles"]:
            self.assertTrue(p["params"])


if __name__ == "__main__":
    unittest.main()
