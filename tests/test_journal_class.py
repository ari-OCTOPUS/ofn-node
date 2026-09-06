"""Contract tests for journal_class (P1 complementary).

Open/fsync of wal/shm/events_jsonl/sqlite_db is admitted only
when VERIFIED. Unlink, truncate, and recursive chmod are
refused. Timeout is UNKNOWN, not a concurrent-write proof.
Ready ≠ authorized. Distinct from run_store.py and census_class.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.journal_class import (
    ACTIVITIES,
    ARTIFACTS,
    INTENTS,
    REFUSAL_REASONS,
    STATUSES,
    JournalDecision,
    admit_journal,
    claims_immutable,
    classify_status,
    classify_timeout,
    deletes_wal_shm,
    grants_send,
    halt_blocks_journal,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent,
    unknown_is_false,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_journal(self):
        self.assertFalse(halt_blocks_journal())

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
        self.assertNotEqual(classify_timeout(), "FALSE")

    def test_does_not_delete_wal_shm(self):
        self.assertFalse(deletes_wal_shm())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(admit_journal).parameters
        self.assertEqual(
            list(params),
            ["artifact", "intended", "activity", "timed_out"],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "halt",
            "halted",
            "quote_sent",
        ):
            self.assertNotIn(forbidden, params)

    def test_vocabularies_are_closed(self):
        self.assertEqual(
            ARTIFACTS,
            frozenset({"wal", "shm", "events_jsonl", "sqlite_db"}),
        )
        self.assertIn("unlink", INTENTS)
        self.assertIn("idle", ACTIVITIES)
        self.assertEqual(STATUSES, frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"}))
        self.assertIn("unlink_forbidden", REFUSAL_REASONS)


class AdmitDurableOpen(unittest.TestCase):
    def test_open_wal_when_verified(self):
        d = admit_journal(
            artifact="wal", intended="open", activity="idle")
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "VERIFIED")
        self.assertIsNone(d.reason)
        self.assertFalse(d.grants_send)

    def test_fsync_each_artifact_when_verified(self):
        for artifact in ARTIFACTS:
            with self.subTest(artifact=artifact):
                d = admit_journal(
                    artifact=artifact, intended="fsync", activity="idle")
                self.assertTrue(d.allowed)
                self.assertEqual(d.artifact, artifact)


class RefuseDestroy(unittest.TestCase):
    def test_unlink_wal_refused(self):
        d = admit_journal(
            artifact="wal", intended="unlink", activity="idle")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unlink_forbidden")

    def test_unlink_shm_refused(self):
        d = admit_journal(
            artifact="shm", intended="unlink", activity="idle")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unlink_forbidden")

    def test_unlink_events_jsonl_refused(self):
        d = admit_journal(
            artifact="events_jsonl", intended="unlink", activity="idle")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unlink_forbidden")

    def test_truncate_refused(self):
        d = admit_journal(
            artifact="sqlite_db", intended="truncate", activity="idle")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "truncate_forbidden")

    def test_recursive_chmod_refused(self):
        d = admit_journal(
            artifact="sqlite_db",
            intended="chmod_recursive_root",
            activity="idle",
        )
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "recursive_chmod_forbidden")


class TimeoutAndUnknown(unittest.TestCase):
    def test_timeout_outranks_concurrent(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=True),
            "UNKNOWN",
        )
        d = admit_journal(
            artifact="wal",
            intended="open",
            activity="concurrent",
            timed_out=True,
        )
        self.assertFalse(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.reason, "unknown_activity")

    def test_unknown_activity_is_unknown_not_false(self):
        d = admit_journal(
            artifact="wal", intended="open", activity="unknown")
        self.assertFalse(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertNotEqual(d.status, "FALSE")

    def test_suspected_concurrent_blocks_open(self):
        d = admit_journal(
            artifact="wal", intended="open", activity="concurrent")
        self.assertFalse(d.allowed)
        self.assertEqual(d.status, "SUSPECTED")
        self.assertEqual(d.reason, "suspected_concurrent")

    def test_unlink_still_refused_when_unknown(self):
        d = admit_journal(
            artifact="wal", intended="unlink", activity="unknown")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unlink_forbidden")

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_journal(
                artifact="wal",
                intended="open",
                activity="idle",
                timed_out=1,
            )

    def test_unknown_artifact_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_journal(
                artifact="core", intended="open", activity="idle")

    def test_bool_artifact_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_journal(
                artifact=True, intended="open", activity="idle")


class SealedNames(unittest.TestCase):
    def test_sealed_artifact_fails_closed(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "Send_Authorized",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    admit_journal(
                        artifact=name, intended="open", activity="idle")

    def test_sealed_intent_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_journal(
                artifact="wal",
                intended="send_authorized",
                activity="idle",
            )

    def test_decision_cannot_grant_send(self):
        with self.assertRaises(FailClosedError):
            JournalDecision(
                allowed=True,
                reason=None,
                status="VERIFIED",
                artifact="wal",
                intended="open",
                timed_out=False,
                grants_send=True,
            )


class DistinctFromCensus(unittest.TestCase):
    def test_module_is_not_census_class(self):
        import ofn.kernel.journal_class as journal
        import ofn.kernel.census_class as census
        self.assertIsNot(journal.admit_journal, census.admit_census)
        self.assertNotEqual(journal.ARTIFACTS, census.STATUSES)

    def test_run_store_does_not_import_journal_class(self):
        import ofn.adapters.run_store as run_store
        source = inspect.getsource(run_store)
        self.assertNotIn("journal_class", source)
        self.assertNotIn("admit_journal", source)
