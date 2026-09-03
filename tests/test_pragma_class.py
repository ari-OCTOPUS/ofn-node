"""Contract tests for pragma_class (P1 complementary).

WAL+FULL is admitted. NORMAL is refused. Unknown names are
UNKNOWN, not FALSE. Ready ≠ authorized. Distinct from
run_store.py and token_ceiling.py.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.pragma_class import (
    ADMITTED_JOURNAL,
    ADMITTED_SYNC,
    JOURNAL_MODES,
    PRAGMA_NAMES,
    REFUSAL_REASONS,
    SYNC_MODES,
    PragmaDecision,
    admit_pragma,
    admits_normal_sync,
    claims_immutable,
    classify_unknown_pragma,
    grants_send,
    halt_blocks_pragma,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    unknown_is_false,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_pragma(self):
        self.assertFalse(halt_blocks_pragma())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())
        self.assertEqual(classify_unknown_pragma(), "UNKNOWN")
        self.assertNotEqual(classify_unknown_pragma(), "FALSE")

    def test_does_not_admit_normal_sync(self):
        self.assertFalse(admits_normal_sync())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(admit_pragma).parameters
        self.assertEqual(list(params), ["name", "value"])
        for forbidden in (
            "resend",
            "send_authorized",
            "halt",
            "halted",
            "quote_sent",
        ):
            self.assertNotIn(forbidden, params)

    def test_vocabularies_are_closed(self):
        self.assertEqual(PRAGMA_NAMES, frozenset({"journal_mode", "synchronous"}))
        self.assertIn("WAL", ADMITTED_JOURNAL)
        self.assertNotIn("NORMAL", ADMITTED_SYNC)
        self.assertIn("NORMAL", SYNC_MODES)
        self.assertIn("unknown_pragma", REFUSAL_REASONS)
        self.assertTrue(JOURNAL_MODES > ADMITTED_JOURNAL)
        self.assertTrue(SYNC_MODES > ADMITTED_SYNC)


class AdmitWalFull(unittest.TestCase):
    def test_wal_is_admitted(self):
        d = admit_pragma(name="journal_mode", value="WAL")
        self.assertTrue(d.allowed)
        self.assertIsNone(d.reason)
        self.assertFalse(d.grants_send)

    def test_full_is_admitted(self):
        d = admit_pragma(name="synchronous", value="FULL")
        self.assertTrue(d.allowed)
        self.assertIsNone(d.reason)

    def test_extra_is_admitted_as_stricter_than_full(self):
        d = admit_pragma(name="synchronous", value="EXTRA")
        self.assertTrue(d.allowed)
        self.assertIn("EXTRA", ADMITTED_SYNC)


class RefuseUnsafe(unittest.TestCase):
    def test_normal_sync_is_refused(self):
        d = admit_pragma(name="synchronous", value="NORMAL")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sync_not_full")
        self.assertFalse(d.grants_send)

    def test_off_sync_is_refused(self):
        d = admit_pragma(name="synchronous", value="OFF")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sync_not_full")

    def test_non_wal_journal_modes_are_refused(self):
        for mode in ("DELETE", "TRUNCATE", "PERSIST", "MEMORY", "OFF"):
            with self.subTest(mode=mode):
                d = admit_pragma(name="journal_mode", value=mode)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "journal_not_wal")

    def test_unknown_pragma_name_is_unknown_not_false(self):
        d = admit_pragma(name="cache_size", value="0")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_pragma")
        self.assertEqual(classify_unknown_pragma(), "UNKNOWN")

    def test_unknown_journal_mode_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_pragma(name="journal_mode", value="MEMORY_MAPPED")

    def test_unknown_sync_mode_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_pragma(name="synchronous", value="MOSTLY")

    def test_bool_name_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_pragma(name=True, value="WAL")

    def test_empty_value_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_pragma(name="journal_mode", value="  ")

    def test_int_value_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_pragma(name="synchronous", value=2)


class SealedNames(unittest.TestCase):
    def test_sealed_pragma_name_refused(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "Send_Authorized",
            "send-authorized",
        ):
            with self.subTest(name=name):
                d = admit_pragma(name=name, value="WAL")
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")

    def test_sealed_pragma_value_refused(self):
        d = admit_pragma(name="journal_mode", value="campaign_envelope_ready")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")

    def test_decision_cannot_grant_send(self):
        with self.assertRaises(FailClosedError):
            PragmaDecision(
                allowed=True,
                reason=None,
                name="journal_mode",
                value="WAL",
                grants_send=True,
            )


class RunStoreUntouched(unittest.TestCase):
    def test_run_store_does_not_import_pragma_class(self):
        import ofn.adapters.run_store as run_store
        source = inspect.getsource(run_store)
        self.assertNotIn("pragma_class", source)
        self.assertNotIn("admit_pragma", source)
