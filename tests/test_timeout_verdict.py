"""Kernel-pure timeout verdict — timeout is UNKNOWN, not a write proof.

Independent of ``run_store.py`` (owned by an open PR) and of
``source_health.py`` (owned by another). HALT stops STARTS, not
in-flight classification. Ready ≠ authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.timeout_verdict import (
    COMPLETED,
    RUNNING,
    TIMEOUT,
    VERDICTS,
    classify_progress,
    concurrent_write_from_timeout,
    grants_send,
    halt_blocks_timeout,
    timeout_is_false,
    timeout_proves_concurrent_write,
)


class ClassifyProgress(unittest.TestCase):
    def test_completed_beats_the_clock(self):
        self.assertEqual(
            classify_progress(elapsed_s=99, budget_s=10, completed=True),
            COMPLETED,
        )
        self.assertEqual(
            classify_progress(elapsed_s=0, budget_s=0, completed=True),
            COMPLETED,
        )

    def test_equal_elapsed_is_timeout(self):
        self.assertEqual(
            classify_progress(elapsed_s=10, budget_s=10, completed=False),
            TIMEOUT,
        )

    def test_overrun_is_timeout(self):
        self.assertEqual(
            classify_progress(elapsed_s=11, budget_s=10, completed=False),
            TIMEOUT,
        )

    def test_inside_window_is_running(self):
        self.assertEqual(
            classify_progress(elapsed_s=0, budget_s=10, completed=False),
            RUNNING,
        )
        self.assertEqual(
            classify_progress(elapsed_s=9, budget_s=10, completed=False),
            RUNNING,
        )

    def test_zero_budget_without_completion_is_timeout(self):
        # budget 0 authorizes no wait — the window is already closed.
        self.assertEqual(
            classify_progress(elapsed_s=0, budget_s=0, completed=False),
            TIMEOUT,
        )


class ExactIntAndBoolPins(unittest.TestCase):
    def test_bool_is_not_an_int_clock(self):
        for bad in (True, False):
            with self.subTest(bad=bad):
                with self.assertRaises(FailClosedError):
                    classify_progress(
                        elapsed_s=bad, budget_s=10, completed=False)
                with self.assertRaises(FailClosedError):
                    classify_progress(
                        elapsed_s=1, budget_s=bad, completed=False)

    def test_float_and_str_clock_fail_closed(self):
        for bad in (1.5, "10", None, 10.0):
            with self.subTest(bad=bad):
                with self.assertRaises(FailClosedError):
                    classify_progress(
                        elapsed_s=bad, budget_s=10, completed=False)
                with self.assertRaises(FailClosedError):
                    classify_progress(
                        elapsed_s=1, budget_s=bad, completed=False)

    def test_negative_clock_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_progress(elapsed_s=-1, budget_s=10, completed=False)
        with self.assertRaises(FailClosedError):
            classify_progress(elapsed_s=1, budget_s=-1, completed=False)

    def test_int_one_is_not_completed(self):
        with self.assertRaises(FailClosedError):
            classify_progress(elapsed_s=1, budget_s=10, completed=1)
        with self.assertRaises(FailClosedError):
            classify_progress(elapsed_s=1, budget_s=10, completed=0)
        with self.assertRaises(FailClosedError):
            classify_progress(elapsed_s=1, budget_s=10, completed="true")


class TimeoutIsNotAWriteProof(unittest.TestCase):
    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertEqual(
            list(inspect.signature(timeout_proves_concurrent_write).parameters),
            [],
        )
        self.assertFalse(timeout_is_false())
        for verdict in VERDICTS:
            with self.subTest(verdict=verdict):
                self.assertFalse(concurrent_write_from_timeout(verdict))

    def test_unknown_verdict_fails_closed_not_false(self):
        with self.assertRaises(FailClosedError):
            concurrent_write_from_timeout("CONCURRENT_WRITE")
        with self.assertRaises(FailClosedError):
            concurrent_write_from_timeout(None)


class ReadyIsNotAuthorized(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertEqual(list(inspect.signature(grants_send).parameters), [])

    def test_halt_does_not_block_timeout(self):
        self.assertFalse(halt_blocks_timeout())
        params = inspect.signature(classify_progress).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("halt", params)
        self.assertEqual(
            classify_progress(elapsed_s=1, budget_s=2, completed=False),
            RUNNING,
        )

    def test_sealed_clock_labels_refused(self):
        for name in ("send_authorized", "quote_sent", "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_progress(
                        elapsed_s=name, budget_s=10, completed=False)


if __name__ == "__main__":
    unittest.main()
