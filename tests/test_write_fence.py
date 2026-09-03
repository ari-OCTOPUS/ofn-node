"""Kernel-pure write fence — complementary to start_permit and close_gate.

A write is admitted to a named durable surface. HALT is not a
parameter. A sealed send/ready name refuses. Ready is not authorized.
This module is not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import (
    BUDGET_DEBIT,
    EVENT_KINDS,
    EXECUTION_RECEIPT,
    RUN_CLOSED,
    RUN_CREATED,
    RUN_REJECTED,
    TOOL_INVOKED,
)
from ofn.kernel.write_fence import (
    LEDGER_KINDS,
    RECEIPT_KINDS,
    REFUSAL_REASONS,
    SIDE_LOG_KINDS,
    SURFACES,
    WriteDecision,
    admit_write,
    burns_idempotency_key,
    claims_immutable,
    grants_send,
    halt_blocks_write,
    ready_is_authorized,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_writes(self):
        self.assertFalse(halt_blocks_write())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_refused_write_does_not_burn_key(self):
        self.assertFalse(burns_idempotency_key())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(admit_write).parameters
        self.assertEqual(list(params), ["surface", "kind", "payload"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            WriteDecision(allowed=True, reason=None, surface="ledger",
                          kind=RUN_CREATED, grants_send=True)
        with self.assertRaises(FailClosedError):
            WriteDecision(allowed=False, reason="sealed_effect",
                          surface="ledger", kind=RUN_CREATED,
                          grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            WriteDecision(allowed=True, reason="sealed_effect",
                          surface="ledger", kind=RUN_CREATED)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            WriteDecision(allowed=False, reason=None,
                          surface="ledger", kind=RUN_CREATED)
        with self.assertRaises(FailClosedError):
            WriteDecision(allowed=False, reason="send_authorized",
                          surface="ledger", kind=RUN_CREATED)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("surface_mismatch", REFUSAL_REASONS)
        self.assertIn("smuggled_effect", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_allowed_decision_refuses_sealed_names(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    WriteDecision(allowed=True, reason=None,
                                  surface=name, kind=RUN_CREATED)
                with self.assertRaises(FailClosedError):
                    WriteDecision(allowed=True, reason=None,
                                  surface="ledger", kind=name)

    def test_mismatch_refusal_cannot_carry_a_sealed_name(self):
        with self.assertRaises(FailClosedError):
            WriteDecision(allowed=False, reason="surface_mismatch",
                          surface="ledger", kind="send_authorized")

    def test_sealed_effect_refusal_names_the_subject(self):
        d = WriteDecision(allowed=False, reason="sealed_effect",
                          surface="ledger", kind="send_authorized")
        self.assertEqual(d.kind, "send_authorized")
        self.assertFalse(d.allowed)
        self.assertFalse(d.grants_send)


class SurfacesAndKinds(unittest.TestCase):
    def test_closed_surface_vocabulary(self):
        self.assertEqual(SURFACES, frozenset({"ledger", "receipt", "side_log"}))

    def test_ledger_excludes_run_rejected(self):
        self.assertEqual(LEDGER_KINDS, EVENT_KINDS - {RUN_REJECTED})
        self.assertNotIn(RUN_REJECTED, LEDGER_KINDS)
        self.assertIn(RUN_CREATED, LEDGER_KINDS)
        self.assertIn(TOOL_INVOKED, LEDGER_KINDS)
        self.assertIn(EXECUTION_RECEIPT, LEDGER_KINDS)
        self.assertIn(BUDGET_DEBIT, LEDGER_KINDS)
        self.assertIn(RUN_CLOSED, LEDGER_KINDS)

    def test_receipt_is_execution_receipt_only(self):
        self.assertEqual(RECEIPT_KINDS, frozenset({EXECUTION_RECEIPT}))

    def test_side_log_is_run_rejected_only(self):
        self.assertEqual(SIDE_LOG_KINDS, frozenset({RUN_REJECTED}))


class LedgerAdmitsSpine(unittest.TestCase):
    def test_every_ledger_kind_is_admitted(self):
        for kind in sorted(LEDGER_KINDS):
            with self.subTest(kind=kind):
                d = admit_write(surface="ledger", kind=kind)
                self.assertTrue(d.allowed)
                self.assertIsNone(d.reason)
                self.assertFalse(d.grants_send)
                self.assertEqual(d.surface, "ledger")
                self.assertEqual(d.kind, kind)

    def test_run_rejected_is_not_a_ledger_write(self):
        d = admit_write(surface="ledger", kind=RUN_REJECTED)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "surface_mismatch")
        self.assertFalse(d.grants_send)

    def test_empty_payload_mapping_is_fine(self):
        d = admit_write(surface="ledger", kind=TOOL_INVOKED, payload={})
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)

    def test_replay_is_byte_identical(self):
        a = admit_write(surface="ledger", kind=TOOL_INVOKED,
                        payload={"arm": "B"})
        b = admit_write(surface="ledger", kind=TOOL_INVOKED,
                        payload={"arm": "B"})
        self.assertEqual(a, b)
        self.assertEqual(a.kind, b.kind)
        self.assertTrue(a.allowed)


class ReceiptAndSideLog(unittest.TestCase):
    def test_receipt_admits_execution_receipt(self):
        d = admit_write(surface="receipt", kind=EXECUTION_RECEIPT)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)

    def test_receipt_refuses_other_spine_kinds(self):
        for kind in (RUN_CREATED, TOOL_INVOKED, RUN_CLOSED, RUN_REJECTED):
            with self.subTest(kind=kind):
                d = admit_write(surface="receipt", kind=kind)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "surface_mismatch")

    def test_side_log_admits_run_rejected(self):
        d = admit_write(surface="side_log", kind=RUN_REJECTED)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)

    def test_side_log_refuses_spine_kinds(self):
        d = admit_write(surface="side_log", kind=RUN_CREATED)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "surface_mismatch")


class SealedNameRefusesWrite(unittest.TestCase):
    def test_sealed_kind_aliases(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "SEND_AUTHORIZED",
                     "quote-sent", "campaign-envelope-ready"):
            with self.subTest(name=name):
                d = admit_write(surface="ledger", kind=name)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.grants_send)

    def test_sealed_surface_aliases(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "send-authorized"):
            with self.subTest(name=name):
                d = admit_write(surface=name, kind=RUN_CREATED)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.grants_send)

    def test_ready_is_not_authorized(self):
        ready = admit_write(surface="ledger", kind="campaign_envelope_ready")
        auth = admit_write(surface="ledger", kind="send_authorized")
        sent = admit_write(surface="ledger", kind="quote_sent")
        self.assertEqual(ready.reason, "sealed_effect")
        self.assertEqual(auth.reason, "sealed_effect")
        self.assertEqual(sent.reason, "sealed_effect")
        self.assertFalse(ready.grants_send)
        self.assertFalse(auth.grants_send)
        self.assertFalse(sent.grants_send)
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertNotEqual(ready.kind, auth.kind)

    def test_smuggled_payload_key(self):
        d = admit_write(surface="ledger", kind=TOOL_INVOKED,
                        payload={"send_authorized": True})
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "smuggled_effect")
        self.assertFalse(d.grants_send)

    def test_smuggled_payload_value(self):
        d = admit_write(surface="ledger", kind=EXECUTION_RECEIPT,
                        payload={"state": "quote_sent"})
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "smuggled_effect")

    def test_smuggled_ready_is_still_not_authorized(self):
        d = admit_write(surface="ledger", kind=TOOL_INVOKED,
                        payload={"state": "campaign_envelope_ready"})
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "smuggled_effect")
        self.assertFalse(d.grants_send)
        self.assertFalse(ready_is_authorized())


class UnknownFailsClosed(unittest.TestCase):
    def test_unknown_kind_is_not_false_and_not_admitted(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_write(surface="ledger", kind="NOT_A_KIND")
        self.assertIn("unknown event kind", str(ctx.exception))
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_unknown_surface_is_not_false_and_not_admitted(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_write(surface="outbox", kind=RUN_CREATED)
        self.assertIn("unknown write surface", str(ctx.exception))

    def test_empty_and_bool_names_fail_closed(self):
        for value in ("", "   ", None, True, False, 0, 1):
            with self.subTest(value=value):
                with self.assertRaises(FailClosedError):
                    admit_write(surface=value, kind=RUN_CREATED)
                with self.assertRaises(FailClosedError):
                    admit_write(surface="ledger", kind=value)

    def test_non_mapping_payload_fails_closed(self):
        for payload in ("{}", ["x"], b"{}", True, 1):
            with self.subTest(payload=payload):
                with self.assertRaises(FailClosedError):
                    admit_write(surface="ledger", kind=TOOL_INVOKED,
                                payload=payload)

    def test_whitespace_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_write(surface="ledger", kind="  \n")


class NoRetryAfterInvariant(unittest.TestCase):
    def test_same_bad_input_fails_again(self):
        with self.assertRaises(FailClosedError):
            admit_write(surface="ledger", kind="NOT_A_KIND")
        with self.assertRaises(FailClosedError):
            admit_write(surface="ledger", kind="NOT_A_KIND")

    def test_sealed_refusal_does_not_become_a_grant(self):
        first = admit_write(surface="ledger", kind="send_authorized")
        second = admit_write(surface="ledger", kind="send_authorized")
        self.assertFalse(first.allowed)
        self.assertFalse(second.allowed)
        self.assertEqual(first.reason, second.reason)


if __name__ == "__main__":
    unittest.main()
