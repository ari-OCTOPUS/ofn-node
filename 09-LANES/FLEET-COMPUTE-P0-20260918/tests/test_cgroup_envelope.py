#!/usr/bin/env python3
"""Tests for cgroup envelope verification.

The scheduler must never accept a result whose resource limits it cannot
confirm. A receipt that only shows a scope path is a claim, not proof.

Run:  python -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import compute_scheduler as cs  # noqa: E402


def cfg(quota="50%", weight="50", mem_max="512M", mem_high="384M"):
    return {
        "cgroup": {
            "CPUQuota": quota, "CPUWeight": weight,
            "MemoryMax": mem_max, "MemoryHigh": mem_high, "IOWeight": "50",
        }
    }


class TestExpectedLimits(unittest.TestCase):
    def test_quota_percent_translates_to_cpu_max(self):
        want = cs.expected_cgroup_limits(cfg(quota="50%"))
        # 50% of one CPU over a 100 ms period.
        self.assertEqual(want["cpu_max"], "50000 100000")

    def test_quota_25_percent(self):
        want = cs.expected_cgroup_limits(cfg(quota="25%"))
        self.assertEqual(want["cpu_max"], "25000 100000")

    def test_memory_sizes_translate_to_bytes(self):
        want = cs.expected_cgroup_limits(cfg(mem_max="512M", mem_high="384M"))
        self.assertEqual(want["memory_max"], str(512 * 1024 ** 2))
        self.assertEqual(want["memory_high"], str(384 * 1024 ** 2))

    def test_cpu_weight_passes_through(self):
        want = cs.expected_cgroup_limits(cfg(weight="50"))
        self.assertEqual(want["cpu_weight"], "50")


class TestVerifyCgroup(unittest.TestCase):
    def test_verified_when_all_observed_match(self):
        observed = {
            "cpu_max": "50000 100000",
            "cpu_weight": "50",
            "memory_max": str(512 * 1024 ** 2),
            "memory_high": str(384 * 1024 ** 2),
        }
        res = cs.verify_cgroup(observed, cfg())
        self.assertEqual(res["verdict"], "VERIFIED")
        self.assertEqual(res["mismatches"], [])

    def test_unverified_when_scope_only(self):
        """The first canary receipt looked like this: a scope with no limit files."""
        observed = {"path": "0::/system.slice/octopus-compute-abc.scope"}
        res = cs.verify_cgroup(observed, cfg())
        self.assertEqual(res["verdict"], "UNVERIFIED")
        self.assertIn("cpu_max", res["unknown"])

    def test_mismatch_when_quota_not_applied(self):
        observed = {"cpu_max": "max", "cpu_weight": "50",
                    "memory_max": str(512 * 1024 ** 2), "memory_high": str(384 * 1024 ** 2)}
        res = cs.verify_cgroup(observed, cfg())
        self.assertEqual(res["verdict"], "MISMATCH")
        self.assertTrue(any("cpu_max" in m for m in res["mismatches"]))

    def test_mismatch_when_memory_cap_missing_but_others_present(self):
        observed = {"cpu_max": "50000 100000", "cpu_weight": "50",
                    "memory_max": str(1024 ** 3), "memory_high": str(384 * 1024 ** 2)}
        res = cs.verify_cgroup(observed, cfg())
        self.assertEqual(res["verdict"], "MISMATCH")

    def test_empty_observation_is_unverified_not_verified(self):
        res = cs.verify_cgroup({}, cfg())
        self.assertEqual(res["verdict"], "UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
