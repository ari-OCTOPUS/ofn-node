#!/usr/bin/env python3
"""Regression tests for the runaway-scope failure found on 2026-09-18.

What happened: an 8-worker task on node 114 exceeded its envelope, the control
plane's ssh call timed out, and the systemd scope kept running. A retry then hit
"Unit ... was already loaded". Three 8-worker scopes ended up alive at once.

Three independent defects produced that, and each gets a test here:
  1. pool children inherited the parent's soft SIGTERM handler, so termination
     was silently a no-op
  2. params.seconds could exceed the envelope's max_seconds, so a workload
     outlived the deadline it was leased under
  3. scope names were derived from the task id alone, so a retry collided with a
     still-loaded unit
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import compute_scheduler as cs  # noqa: E402
import compute_worker as cw  # noqa: E402


class TestUnitNames(unittest.TestCase):
    def test_retry_gets_a_distinct_unit(self):
        """A retry must never reuse the previous attempt's scope name."""
        first = cs.unit_name("task-51c0e8a55bc4b6be", 1)
        second = cs.unit_name("task-51c0e8a55bc4b6be", 2)
        self.assertNotEqual(first, second)
        self.assertTrue(first.startswith("octopus-compute-"))
        self.assertTrue(first.endswith("-a1"))
        self.assertTrue(second.endswith("-a2"))

    def test_distinct_tasks_get_distinct_units(self):
        self.assertNotEqual(cs.unit_name("task-aaaaaaaaaaaa1111", 1),
                            cs.unit_name("task-bbbbbbbbbbbb2222", 1))

    def test_unit_name_is_deterministic(self):
        """Reclaim must be able to recompute it to stop an abandoned scope."""
        self.assertEqual(cs.unit_name("task-51c0e8a55bc4b6be", 3),
                         cs.unit_name("task-51c0e8a55bc4b6be", 3))


class TestDurationIsClamped(unittest.TestCase):
    def make_task(self, seconds, **over):
        task = {
            "schema": "compute_task.v1",
            "task_id": "task-clamp0001",
            "profile": "cpu_bench",
            "params": {"seconds": seconds, "block_mb": 1, "workers": 1},
            "input_digest": "d",
            "external_effects": 0,
            "customer_send": False,
        }
        task.update(over)
        return task

    def test_requested_duration_cannot_exceed_envelope(self):
        """The 2026-09-18 case: seconds=120 arrived with max_seconds=110."""
        receipt = cw.run_task(self.make_task(120, max_seconds=4))
        self.assertEqual(receipt["status"], "SUCCEEDED")
        self.assertLessEqual(receipt["params_applied"]["seconds"], receipt["max_seconds"])
        self.assertIn("seconds", receipt["params_clamped"])
        self.assertEqual(receipt["params_clamped"]["seconds"]["requested"], 120)

    def test_task_finishes_within_its_envelope(self):
        receipt = cw.run_task(self.make_task(120, max_seconds=4))
        # 4 s envelope + margin, not the 120 s that was requested.
        self.assertLess(receipt["duration_s"], 10.0)

    def test_no_clamp_when_request_fits(self):
        receipt = cw.run_task(self.make_task(2, max_seconds=30))
        self.assertEqual(receipt["params_clamped"], {})
        self.assertEqual(receipt["params_applied"]["seconds"], 2)


class TestChildrenDieOnSigterm(unittest.TestCase):
    """The deadlock: children that ignore SIGTERM make terminate() a no-op."""

    def test_worker_process_is_killable(self):
        """A multi-worker task must terminate promptly when signalled."""
        script = textwrap.dedent(
            """
            import sys, time
            sys.path.insert(0, %r)
            import compute_worker as cw
            task = {
                "schema": "compute_task.v1", "task_id": "task-killme0001",
                "profile": "cpu_bench",
                "params": {"seconds": 120, "block_mb": 1, "workers": 2},
                "input_digest": "d", "external_effects": 0, "customer_send": False,
                "max_seconds": 120,
            }
            cw.run_task(task)
            """
        ) % str(Path(__file__).resolve().parent.parent / "tools")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run_killable.py"
            path.write_text(script, encoding="utf-8", newline="\n")
            proc = subprocess.Popen([sys.executable, str(path)],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(6)  # let the worker processes start and begin churning
            self.assertIsNone(proc.poll(), "worker should still be running")
            started = time.time()
            proc.terminate()
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill()
                self.fail("worker ignored SIGTERM — pool children are not killable")
            self.assertLess(time.time() - started, 20)

    def test_child_resets_signal_handlers(self):
        """The child-side reset is what makes the test above pass."""
        code = (
            "import signal, sys;"
            f"sys.path.insert(0, r'{Path(__file__).resolve().parent.parent / 'tools'}');"
            "import compute_worker as cw;"
            "cw._child_reset_signals();"
            "print(signal.getsignal(signal.SIGTERM) == signal.SIG_DFL)"
        )
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                             timeout=60)
        self.assertEqual(out.stdout.strip(), "True", out.stderr)


class TestSchedulerWiring(unittest.TestCase):
    def test_scheduler_calls_stop_scope_on_no_receipt(self):
        """Static guarantee: the failure path tears the scope down."""
        source = (Path(__file__).resolve().parent.parent / "tools" / "compute_scheduler.py").read_text(
            encoding="utf-8"
        )
        body = source.split("def dispatch(")[1].split("\ndef ")[0]
        self.assertIn("stop_scope", body)
        # It must be called on the no-receipt path, before the task is failed.
        no_receipt = body.split("no_receipt")[0]
        self.assertIn("stop_scope", no_receipt)
        # And the cgroup mismatch path must also tear down.
        self.assertIn("stop_scope", body.split('cgroup_check["verdict"] == "MISMATCH"')[1])

    def test_reclaim_path_stops_scopes(self):
        source = (Path(__file__).resolve().parent.parent / "tools" / "compute_scheduler.py").read_text(
            encoding="utf-8"
        )
        reclaim_block = source.split("reclaimed = store.reclaim_expired()")[1].split("shadow =")[0]
        self.assertIn("stop_scope", reclaim_block)
        self.assertIn("unit_name", reclaim_block)


if __name__ == "__main__":
    unittest.main()
