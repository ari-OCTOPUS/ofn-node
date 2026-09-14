"""Kernel-pure rollup pin — complementary to attest_class.

Unknown files are incomplete, not tamper and not a grant.
Truncation is incomplete. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.rollup_pin import (
    OVERALL_VERDICTS,
    RollupDecision,
    empty_truncated_is_consistent,
    grants_send,
    halt_blocks_rollup,
    proposal_is_execution,
    ready_is_authorized,
    claims_immutable,
    rollup,
    truncated_is_consistent,
    unknown_file_is_consistent,
    unknown_file_is_inconsistent,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_rollup(self):
        self.assertFalse(halt_blocks_rollup())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_file_is_not_consistent_or_inconsistent(self):
        self.assertFalse(unknown_file_is_consistent())
        self.assertFalse(unknown_file_is_inconsistent())

    def test_truncated_is_not_consistent(self):
        self.assertFalse(truncated_is_consistent())
        self.assertFalse(empty_truncated_is_consistent())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_overall_vocabulary_has_no_unknown(self):
        self.assertEqual(
            OVERALL_VERDICTS,
            {"consistent", "incomplete", "inconsistent"})
        self.assertNotIn("unknown", OVERALL_VERDICTS)

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(rollup).parameters
        self.assertEqual(list(params), ["file_verdicts", "truncated"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            RollupDecision(
                verdict="consistent", truncated=False,
                file_count=0, unknown_count=0, grants_send=True)

    def test_constructor_refuses_consistent_with_truncated_or_unknown(self):
        with self.assertRaises(FailClosedError):
            RollupDecision(
                verdict="consistent", truncated=True,
                file_count=0, unknown_count=0)
        with self.assertRaises(FailClosedError):
            RollupDecision(
                verdict="consistent", truncated=False,
                file_count=1, unknown_count=1)

    def test_constructor_refuses_unknown_count_above_file_count(self):
        with self.assertRaises(FailClosedError):
            RollupDecision(
                verdict="incomplete", truncated=False,
                file_count=1, unknown_count=2)

    def test_constructor_refuses_foreign_overall(self):
        with self.assertRaises(FailClosedError):
            RollupDecision(
                verdict="unknown", truncated=False,
                file_count=1, unknown_count=1)


class RollupPrecedence(unittest.TestCase):
    def test_all_consistent_is_consistent(self):
        d = rollup(
            file_verdicts=("consistent", "consistent"), truncated=False)
        self.assertEqual(d.verdict, "consistent")
        self.assertFalse(d.truncated)
        self.assertEqual(d.file_count, 2)
        self.assertEqual(d.unknown_count, 0)
        self.assertFalse(d.grants_send)

    def test_empty_not_truncated_is_consistent(self):
        d = rollup(file_verdicts=(), truncated=False)
        self.assertEqual(d.verdict, "consistent")
        self.assertEqual(d.file_count, 0)
        self.assertEqual(d.unknown_count, 0)

    def test_empty_truncated_is_incomplete(self):
        d = rollup(file_verdicts=(), truncated=True)
        self.assertEqual(d.verdict, "incomplete")
        self.assertTrue(d.truncated)
        self.assertFalse(empty_truncated_is_consistent())

    def test_inconsistent_wins_over_incomplete_and_unknown(self):
        d = rollup(
            file_verdicts=("incomplete", "unknown", "inconsistent"),
            truncated=True)
        self.assertEqual(d.verdict, "inconsistent")
        self.assertEqual(d.unknown_count, 1)
        self.assertTrue(d.truncated)

    def test_unknown_file_rolls_up_incomplete_not_tamper(self):
        d = rollup(file_verdicts=("consistent", "unknown"), truncated=False)
        self.assertEqual(d.verdict, "incomplete")
        self.assertEqual(d.unknown_count, 1)
        self.assertFalse(unknown_file_is_inconsistent())
        self.assertFalse(unknown_file_is_consistent())

    def test_incomplete_file_rolls_up_incomplete(self):
        d = rollup(
            file_verdicts=("consistent", "incomplete"), truncated=False)
        self.assertEqual(d.verdict, "incomplete")
        self.assertEqual(d.unknown_count, 0)

    def test_truncated_consistent_files_are_incomplete(self):
        d = rollup(
            file_verdicts=("consistent", "consistent"), truncated=True)
        self.assertEqual(d.verdict, "incomplete")
        self.assertFalse(truncated_is_consistent())


class FailClosedInputs(unittest.TestCase):
    def test_missing_list_is_unknown_not_empty(self):
        with self.assertRaises(FailClosedError):
            rollup(file_verdicts=None, truncated=False)

    def test_string_is_not_a_verdict_list(self):
        with self.assertRaises(FailClosedError):
            rollup(file_verdicts="consistent", truncated=False)

    def test_missing_truncated_is_unknown_not_false(self):
        with self.assertRaises(FailClosedError):
            rollup(file_verdicts=("consistent",), truncated=None)

    def test_string_truncated_is_not_a_claim(self):
        with self.assertRaises(FailClosedError):
            rollup(file_verdicts=("consistent",), truncated="no")

    def test_foreign_file_verdict_refuses(self):
        with self.assertRaises(FailClosedError):
            rollup(file_verdicts=("ok",), truncated=False)

    def test_sealed_file_verdict_refuses(self):
        with self.assertRaises(FailClosedError):
            rollup(file_verdicts=("send_authorized",), truncated=False)
        with self.assertRaises(FailClosedError):
            rollup(
                file_verdicts=("campaign_envelope_ready",), truncated=False)

    def test_bool_and_blank_verdicts_refuse(self):
        with self.assertRaises(FailClosedError):
            rollup(file_verdicts=(True,), truncated=False)
        with self.assertRaises(FailClosedError):
            rollup(file_verdicts=("",), truncated=False)


if __name__ == "__main__":
    unittest.main()
