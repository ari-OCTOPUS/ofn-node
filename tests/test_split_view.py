"""Kernel-pure split view — complementary to arbiter_claim and numeric_claim.

Both sides of a contradicted claim are recorded. An agent cannot
close the row. Ready is not authorized. This module is not wired
into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.split_view import (
    STATUSES,
    SplitRow,
    agent_reported_is_verified,
    claims_immutable,
    classify,
    grants_send,
    halt_blocks_row,
    mint_row,
    pick_a,
    pick_b,
    proposal_is_execution,
    ready_is_authorized,
    resolve,
    silently_picks,
    timeout_proves_concurrent_write,
    unknown_is_false,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_agent_reported_is_not_verified(self):
        self.assertFalse(agent_reported_is_verified())

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_halt_does_not_block_classification(self):
        self.assertFalse(halt_blocks_row())

    def test_does_not_silently_pick(self):
        self.assertFalse(silently_picks())

    def test_closed_status_vocabulary(self):
        self.assertEqual(STATUSES, frozenset({"match", "open", "unknown"}))
        self.assertNotIn("send_authorized", STATUSES)
        self.assertNotIn("resolved", STATUSES)

    def test_signature_has_no_send_halt_or_resolution_knob(self):
        params = inspect.signature(mint_row).parameters
        self.assertEqual(
            list(params),
            ["claim", "value_a", "source_a", "value_b", "source_b"],
        )
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw",
                          "resolution"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            SplitRow(
                claim="origin_main",
                value_a="aaa",
                source_a="git_fetch",
                value_b="bbb",
                source_b="memory",
                status="open",
                resolution=None,
                grants_send=True,
            )


class ClassifyRelation(unittest.TestCase):
    def test_equal_present_values_are_match(self):
        self.assertEqual(classify("608adb7", "608adb7"), "match")
        self.assertEqual(classify(12, 12), "match")

    def test_unequal_present_values_are_open(self):
        self.assertEqual(classify("aaa", "bbb"), "open")
        self.assertEqual(classify(1, 2), "open")

    def test_missing_either_side_is_unknown_not_a_pick(self):
        self.assertEqual(classify(None, "bbb"), "unknown")
        self.assertEqual(classify("aaa", None), "unknown")
        self.assertEqual(classify(None, None), "unknown")

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify(1.5, 1)
        self.assertIn("float", str(ctx.exception).lower())

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify(True, 1)
        with self.assertRaises(FailClosedError):
            classify(1, False)

    def test_empty_string_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify("", "x")
        with self.assertRaises(FailClosedError):
            classify("x", "   ")

    def test_unsupported_type_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify(["a"], "a")


class MintRecordsBothSides(unittest.TestCase):
    def test_open_row_keeps_both_values_and_null_resolution(self):
        row = mint_row(
            claim="origin_main",
            value_a="58e87774f4428b247601f8b49956948491155f74",
            source_a="prior_memory",
            value_b="608adb75487142e1431f5ada254b6abe3537337f",
            source_b="git_fetch",
        )
        self.assertEqual(row.status, "open")
        self.assertIsNone(row.resolution)
        self.assertEqual(row.value_a, "58e87774f4428b247601f8b49956948491155f74")
        self.assertEqual(row.value_b, "608adb75487142e1431f5ada254b6abe3537337f")
        self.assertFalse(row.grants_send)
        self.assertFalse(grants_send())

    def test_match_is_agreement_not_inattention(self):
        row = mint_row(
            claim="d27_sha256",
            value_a="c55f90852fe2753a8a1650662d256a6b7a20549c67de578a32ddfd7d07041ea9",
            source_a="this_host_file",
            value_b="c55f90852fe2753a8a1650662d256a6b7a20549c67de578a32ddfd7d07041ea9",
            source_b="prior_memory",
        )
        self.assertEqual(row.status, "match")
        self.assertIsNone(row.resolution)
        self.assertEqual(row.value_a, row.value_b)
        self.assertFalse(row.grants_send)

    def test_missing_side_is_unknown_and_keeps_the_other(self):
        row = mint_row(
            claim="effect_replay_pr",
            value_a=None,
            source_a="this_host_origin",
            value_b="unpublished",
            source_b="prior_memory",
        )
        self.assertEqual(row.status, "unknown")
        self.assertIsNone(row.value_a)
        self.assertEqual(row.value_b, "unpublished")
        self.assertFalse(row.grants_send)

    def test_replay_is_byte_identical(self):
        kwargs = dict(
            claim="incidents_pr",
            value_a="73",
            source_a="pull_73",
            value_b="120",
            source_b="pull_120",
        )
        a = mint_row(**kwargs)
        b = mint_row(**kwargs)
        self.assertEqual(a, b)
        self.assertEqual(a.status, "open")

    def test_int_values_are_exact(self):
        row = mint_row(
            claim="passed_count",
            value_a=16,
            source_a="check_suite_a",
            value_b=16,
            source_b="check_suite_b",
        )
        self.assertEqual(row.status, "match")
        self.assertEqual(row.value_a, 16)


class IndependentSources(unittest.TestCase):
    def test_same_source_both_sides_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            mint_row(
                claim="origin_main",
                value_a="aaa",
                source_a="git_fetch",
                value_b="bbb",
                source_b="git_fetch",
            )
        self.assertIn("independent", str(ctx.exception).lower())

    def test_empty_source_fails_closed(self):
        with self.assertRaises(FailClosedError):
            mint_row(
                claim="origin_main",
                value_a="aaa",
                source_a="",
                value_b="bbb",
                source_b="memory",
            )

    def test_bool_source_fails_closed(self):
        with self.assertRaises(FailClosedError):
            mint_row(
                claim="origin_main",
                value_a="aaa",
                source_a=True,
                value_b="bbb",
                source_b="memory",
            )

    def test_empty_claim_fails_closed(self):
        with self.assertRaises(FailClosedError):
            mint_row(
                claim="  ",
                value_a="aaa",
                source_a="git_fetch",
                value_b="bbb",
                source_b="memory",
            )


class SealedNamesRefuse(unittest.TestCase):
    def test_sealed_claim_aliases(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "SEND_AUTHORIZED",
                     "quote-sent", "campaign-envelope-ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    mint_row(
                        claim=name,
                        value_a="held",
                        source_a="flag",
                        value_b="held",
                        source_b="later_hold",
                    )

    def test_sealed_value_refused(self):
        with self.assertRaises(FailClosedError):
            mint_row(
                claim="revenue_phase",
                value_a="send_authorized",
                source_a="proposal",
                value_b="held",
                source_b="later_hold",
            )

    def test_ready_and_authorized_stay_distinct_names(self):
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        with self.assertRaises(FailClosedError):
            mint_row(
                claim="campaign_envelope_ready",
                value_a="struct",
                source_a="kernel",
                value_b="struct",
                source_b="test",
            )


class AgentCannotClose(unittest.TestCase):
    def _open_row(self) -> SplitRow:
        return mint_row(
            claim="origin_main",
            value_a="aaa",
            source_a="git_fetch",
            value_b="bbb",
            source_b="memory",
        )

    def test_resolve_is_refused(self):
        row = self._open_row()
        with self.assertRaises(FailClosedError) as ctx:
            resolve(row, "pick_b")
        self.assertIn("owner", str(ctx.exception).lower())
        self.assertEqual(row.status, "open")
        self.assertIsNone(row.resolution)

    def test_pick_a_is_refused(self):
        row = self._open_row()
        with self.assertRaises(FailClosedError):
            pick_a(row)
        self.assertEqual(row.value_a, "aaa")
        self.assertEqual(row.value_b, "bbb")

    def test_pick_b_is_refused(self):
        row = self._open_row()
        with self.assertRaises(FailClosedError):
            pick_b(row)

    def test_constructor_refuses_a_resolution(self):
        with self.assertRaises(FailClosedError):
            SplitRow(
                claim="origin_main",
                value_a="aaa",
                source_a="git_fetch",
                value_b="bbb",
                source_b="memory",
                status="open",
                resolution="pick_b",
            )

    def test_constructor_refuses_mismatched_status(self):
        with self.assertRaises(FailClosedError):
            SplitRow(
                claim="origin_main",
                value_a="aaa",
                source_a="git_fetch",
                value_b="aaa",
                source_b="memory",
                status="open",
                resolution=None,
            )


if __name__ == "__main__":
    unittest.main()
