"""Kernel-pure census class — complementary to write_fence and dual_record.

A worktree row is classified. Observe is read-only inventory.
Write is admitted only when VERIFIED and idle. Prune is never
admitted. Timeout is UNKNOWN, not a concurrent-write proof.
Ready is not authorized. This module is not wired into the
run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.census_class import (
    ACTIVITIES,
    DISK_LABELS,
    INTENTS,
    REFUSAL_REASONS,
    STATUSES,
    CensusDecision,
    admit_census,
    body_missing_is_valid_label,
    claims_immutable,
    classify_status,
    classify_timeout,
    grants_send,
    halt_blocks_census,
    promotes_ready_to_send,
    proposal_is_execution,
    prunes_worktree,
    ready_is_authorized,
    timeout_proves_concurrent,
    unknown_is_false,
)
from ofn.kernel.errors import FailClosedError


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_census(self):
        self.assertFalse(halt_blocks_census())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent())
        self.assertEqual(classify_timeout(), "UNKNOWN")

    def test_does_not_prune(self):
        self.assertFalse(prunes_worktree())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_body_missing_is_not_a_valid_label(self):
        self.assertFalse(body_missing_is_valid_label())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(admit_census).parameters
        self.assertEqual(
            list(params),
            ["path", "activity", "intended", "timed_out", "disk_label"],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt",
            "halt_raw",
            "prune",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            CensusDecision(
                allowed=True, reason=None, status="VERIFIED",
                path="/tmp/a", intended="observe", timed_out=False,
                grants_send=True)
        with self.assertRaises(FailClosedError):
            CensusDecision(
                allowed=False, reason="sealed_effect", status="UNKNOWN",
                path="send_authorized", intended="write", timed_out=False,
                grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            CensusDecision(
                allowed=True, reason="sealed_effect", status="VERIFIED",
                path="/tmp/a", intended="observe", timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            CensusDecision(
                allowed=False, reason=None, status="UNKNOWN",
                path="/tmp/a", intended="write", timed_out=False)
        with self.assertRaises(FailClosedError):
            CensusDecision(
                allowed=False, reason="send_authorized", status="UNKNOWN",
                path="/tmp/a", intended="write", timed_out=False)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("unknown_activity", REFUSAL_REASONS)
        self.assertIn("suspected_concurrent", REFUSAL_REASONS)
        self.assertIn("prune_forbidden", REFUSAL_REASONS)
        self.assertIn("body_not_on_this_host", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_allowed_write_requires_verified(self):
        for status in ("SUSPECTED", "UNKNOWN"):
            with self.subTest(status=status):
                with self.assertRaises(FailClosedError):
                    CensusDecision(
                        allowed=True, reason=None, status=status,
                        path="/tmp/a", intended="write", timed_out=False)

    def test_allowed_cannot_be_prune(self):
        with self.assertRaises(FailClosedError):
            CensusDecision(
                allowed=True, reason=None, status="VERIFIED",
                path="/tmp/a", intended="prune", timed_out=False)

    def test_allowed_decision_refuses_sealed_names(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    CensusDecision(
                        allowed=True, reason=None, status="VERIFIED",
                        path=name, intended="observe", timed_out=False)

    def test_non_sealed_refusal_cannot_carry_a_sealed_path(self):
        with self.assertRaises(FailClosedError):
            CensusDecision(
                allowed=False, reason="unknown_activity", status="UNKNOWN",
                path="send_authorized", intended="write", timed_out=True)

    def test_sealed_effect_refusal_names_the_subject(self):
        d = CensusDecision(
            allowed=False, reason="sealed_effect", status="UNKNOWN",
            path="send_authorized", intended="write", timed_out=False)
        self.assertEqual(d.path, "send_authorized")
        self.assertFalse(d.allowed)
        self.assertFalse(d.grants_send)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            CensusDecision(
                allowed=True, reason=None, status="VERIFIED",
                path="/tmp/a", intended="observe", timed_out="false")  # type: ignore[arg-type]


class ClosedVocabularies(unittest.TestCase):
    def test_statuses(self):
        self.assertEqual(STATUSES, frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"}))

    def test_activities(self):
        self.assertEqual(ACTIVITIES, frozenset({"idle", "concurrent", "unknown"}))

    def test_intents(self):
        self.assertEqual(INTENTS, frozenset({"observe", "write", "prune"}))

    def test_disk_labels_exclude_body_missing(self):
        self.assertEqual(
            DISK_LABELS, frozenset({"none", "body_not_on_this_host"}))
        self.assertNotIn("body_missing", DISK_LABELS)


class StatusDerivation(unittest.TestCase):
    def test_idle_is_verified(self):
        self.assertEqual(
            classify_status(activity="idle", timed_out=False), "VERIFIED")

    def test_concurrent_is_suspected(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=False),
            "SUSPECTED")

    def test_unknown_activity_is_unknown(self):
        self.assertEqual(
            classify_status(activity="unknown", timed_out=False), "UNKNOWN")

    def test_timeout_outranks_concurrent(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=True), "UNKNOWN")

    def test_timeout_outranks_idle(self):
        self.assertEqual(
            classify_status(activity="idle", timed_out=True), "UNKNOWN")

    def test_unknown_activity_token_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_status(activity="racing", timed_out=False)
        self.assertNotIn("FALSE", str(ctx.exception))


class ObserveIsReadOnlyInventory(unittest.TestCase):
    def test_observe_idle_is_verified_and_admitted(self):
        d = admit_census(
            path="/tmp/ofn-p1-census-class", activity="idle",
            intended="observe")
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "VERIFIED")
        self.assertIsNone(d.reason)
        self.assertFalse(d.grants_send)

    def test_observe_unknown_is_admitted_as_unknown(self):
        d = admit_census(
            path="/tmp/a", activity="unknown", intended="observe")
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(d.grants_send)

    def test_observe_concurrent_is_admitted_as_suspected(self):
        d = admit_census(
            path="/tmp/a", activity="concurrent", intended="observe")
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "SUSPECTED")
        self.assertFalse(d.grants_send)

    def test_observe_timeout_is_unknown_not_suspected(self):
        d = admit_census(
            path="/tmp/a", activity="concurrent", intended="observe",
            timed_out=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertNotEqual(d.status, "SUSPECTED")
        self.assertFalse(d.grants_send)

    def test_observe_body_not_on_this_host_is_admitted(self):
        d = admit_census(
            path="/tmp/a", activity="idle", intended="observe",
            disk_label="body_not_on_this_host")
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "VERIFIED")
        self.assertFalse(d.grants_send)

    def test_replay_is_byte_identical(self):
        a = admit_census(
            path="/tmp/a", activity="idle", intended="observe")
        b = admit_census(
            path="/tmp/a", activity="idle", intended="observe")
        self.assertEqual(a, b)


class WriteAdmission(unittest.TestCase):
    def test_write_idle_verified_is_admitted(self):
        d = admit_census(
            path="/tmp/a", activity="idle", intended="write")
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "VERIFIED")
        self.assertFalse(d.grants_send)

    def test_write_unknown_is_refused(self):
        d = admit_census(
            path="/tmp/a", activity="unknown", intended="write")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_activity")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(d.grants_send)

    def test_write_concurrent_is_refused(self):
        d = admit_census(
            path="/tmp/a", activity="concurrent", intended="write")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "suspected_concurrent")
        self.assertEqual(d.status, "SUSPECTED")
        self.assertFalse(d.grants_send)

    def test_write_timeout_is_unknown_not_suspected(self):
        d = admit_census(
            path="/tmp/a", activity="concurrent", intended="write",
            timed_out=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_activity")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)

    def test_write_body_not_on_this_host_is_refused(self):
        d = admit_census(
            path="/tmp/a", activity="idle", intended="write",
            disk_label="body_not_on_this_host")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "body_not_on_this_host")
        self.assertFalse(d.grants_send)


class PruneIsNeverAdmitted(unittest.TestCase):
    def test_prune_idle_is_refused(self):
        d = admit_census(
            path="/tmp/a", activity="idle", intended="prune")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "prune_forbidden")
        self.assertFalse(prunes_worktree())
        self.assertFalse(d.grants_send)

    def test_prune_unknown_is_still_refused(self):
        d = admit_census(
            path="/tmp/a", activity="unknown", intended="prune")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "prune_forbidden")


class UnknownFailsClosed(unittest.TestCase):
    def test_unknown_activity_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_census(
                path="/tmp/a", activity="racing", intended="observe")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_intended_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_census(
                path="/tmp/a", activity="idle", intended="delete")
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_body_missing_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_census(
                path="/tmp/a", activity="idle", intended="observe",
                disk_label="body_missing")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_empty_path_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_census(path="  ", activity="idle", intended="observe")

    def test_bool_path_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_census(path=True, activity="idle", intended="observe")

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_census(
                path="/tmp/a", activity="idle", intended="observe",
                timed_out=1)
        with self.assertRaises(FailClosedError):
            admit_census(
                path="/tmp/a", activity="idle", intended="observe",
                timed_out="true")


class SealedNameRefusesCensus(unittest.TestCase):
    def test_sealed_path_aliases(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "SEND_AUTHORIZED",
            "quote-sent",
            "campaign-envelope-ready",
        ):
            with self.subTest(name=name):
                d = admit_census(
                    path=name, activity="idle", intended="observe")
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.grants_send)

    def test_ready_and_authorized_stay_distinct_subjects(self):
        ready = admit_census(
            path="campaign_envelope_ready", activity="idle",
            intended="write")
        auth = admit_census(
            path="send_authorized", activity="idle", intended="write")
        self.assertNotEqual(ready.path, auth.path)
        self.assertFalse(ready.allowed)
        self.assertFalse(auth.allowed)
        self.assertFalse(ready_is_authorized())


if __name__ == "__main__":
    unittest.main()
