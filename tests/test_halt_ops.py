"""Kernel-pure HALT operation classifier (complementary P1).

``halt.py`` answers "is the switch on?". This module locks the next
question on main: which operations may proceed. Run-gate / chaos
files are owned by open PRs and are not imported here.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import FORBIDDEN_EFFECT_KINDS
from ofn.kernel.halt_ops import (
    APPEND_IN_FLIGHT,
    CLOSE_IN_FLIGHT,
    DEDUP_IN_FLIGHT,
    HOLD_IN_FLIGHT,
    IN_FLIGHT_OPS,
    ISSUE_CLAIM,
    KNOWN_OPS,
    NEVER_OPS,
    RECORD_REJECTION,
    RECOVER_AFTER_RESTART,
    RESEND,
    SETTLE_IN_FLIGHT,
    START_OPS,
    START_RUN,
    classify,
    grants_send,
    halt_blocks_inflight,
    may_proceed,
)


class VocabularyIsClosed(unittest.TestCase):
    def test_known_ops_partition(self):
        self.assertEqual(KNOWN_OPS, START_OPS | IN_FLIGHT_OPS | NEVER_OPS)
        self.assertFalse(START_OPS & IN_FLIGHT_OPS)
        self.assertFalse(START_OPS & NEVER_OPS)
        self.assertFalse(IN_FLIGHT_OPS & NEVER_OPS)

    def test_start_ops_are_new_work(self):
        self.assertEqual(START_OPS, frozenset({START_RUN, ISSUE_CLAIM}))

    def test_resend_is_never_an_in_flight_op(self):
        self.assertIn(RESEND, NEVER_OPS)
        self.assertNotIn(RESEND, IN_FLIGHT_OPS)
        self.assertNotIn(RESEND, START_OPS)

    def test_sealed_names_are_not_operations(self):
        for name in FORBIDDEN_EFFECT_KINDS:
            self.assertNotIn(name, KNOWN_OPS)


class ClassifyBuckets(unittest.TestCase):
    def test_start_bucket(self):
        self.assertEqual(classify(START_RUN), "start")
        self.assertEqual(classify(ISSUE_CLAIM), "start")

    def test_in_flight_bucket(self):
        for op in (
            APPEND_IN_FLIGHT, CLOSE_IN_FLIGHT, HOLD_IN_FLIGHT,
            SETTLE_IN_FLIGHT, DEDUP_IN_FLIGHT, RECORD_REJECTION,
            RECOVER_AFTER_RESTART,
        ):
            with self.subTest(op=op):
                self.assertEqual(classify(op), "in_flight")

    def test_never_bucket(self):
        self.assertEqual(classify(RESEND), "never")

    def test_unknown_op_refused(self):
        with self.assertRaises(FailClosedError):
            classify("invented_op")

    def test_sealed_op_refused(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "send-authorized"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify(name)


class MayProceedUnderHalt(unittest.TestCase):
    def test_starts_refused_while_halted(self):
        for op in START_OPS:
            with self.subTest(op=op):
                self.assertFalse(may_proceed(True, op))
                self.assertTrue(may_proceed(False, op))

    def test_in_flight_survives_halt(self):
        for op in IN_FLIGHT_OPS:
            with self.subTest(op=op):
                self.assertTrue(may_proceed(True, op))
                self.assertTrue(may_proceed(False, op))

    def test_resend_never_proceeds(self):
        self.assertFalse(may_proceed(False, RESEND))
        self.assertFalse(may_proceed(True, RESEND))

    def test_unknown_halted_is_not_false(self):
        for bad in (None, 1, 0, "true", "1"):
            with self.subTest(bad=bad):
                with self.assertRaises(FailClosedError):
                    may_proceed(bad, START_RUN)  # type: ignore[arg-type]

    def test_empty_op_refused(self):
        with self.assertRaises(FailClosedError):
            may_proceed(False, "")

    def test_sealed_op_is_error_not_false(self):
        with self.assertRaises(FailClosedError):
            may_proceed(False, "quote_sent")


class StructuralPromises(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertIs(grants_send(), False)
        self.assertEqual(list(inspect.signature(grants_send).parameters), [])

    def test_halt_does_not_block_inflight(self):
        self.assertIs(halt_blocks_inflight(), False)

    def test_may_proceed_has_only_halted_and_op(self):
        params = list(inspect.signature(may_proceed).parameters)
        self.assertEqual(params, ["halted", "op"])
        self.assertNotIn("resend", params)
        self.assertNotIn("send_authorized", params)


if __name__ == "__main__":
    unittest.main()
