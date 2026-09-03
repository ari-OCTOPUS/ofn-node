"""Kernel-pure flag freeze — complementary to write_fence and start_permit.

A later hold outranks an older authorization. Opening a frozen
family is refused. Closing is admitted. Ready is not authorized.
This module is not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.flag_freeze import (
    FAMILIES,
    INTENTS,
    REFUSAL_REASONS,
    FlagDecision,
    admit_flag,
    claims_immutable,
    classify_family,
    grants_send,
    halt_blocks_flag,
    proposal_is_execution,
    ready_is_authorized,
    rearms_send,
    unknown_is_false,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_does_not_rearm_send(self):
        self.assertFalse(rearms_send())

    def test_halt_does_not_block_flag_classify(self):
        self.assertFalse(halt_blocks_flag())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(admit_flag).parameters
        self.assertEqual(list(params), ["name", "intended", "later_hold"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            FlagDecision(allowed=True, reason=None, family="wire",
                         name="OFN_WIRE_OUTBOUND", intended="closed",
                         later_hold=False, grants_send=True)
        with self.assertRaises(FailClosedError):
            FlagDecision(allowed=False, reason="frozen_open",
                         family="wire", name="OFN_WIRE_OUTBOUND",
                         intended="open", later_hold=False,
                         grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            FlagDecision(allowed=True, reason="frozen_open",
                         family="wire", name="OFN_WIRE_OUTBOUND",
                         intended="closed", later_hold=False)

    def test_allowed_cannot_be_open(self):
        with self.assertRaises(FailClosedError):
            FlagDecision(allowed=True, reason=None, family="wire",
                         name="OFN_WIRE_OUTBOUND", intended="open",
                         later_hold=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            FlagDecision(allowed=False, reason=None, family="wire",
                         name="OFN_WIRE_OUTBOUND", intended="open",
                         later_hold=False)
        with self.assertRaises(FailClosedError):
            FlagDecision(allowed=False, reason="send_authorized",
                         family="wire", name="OFN_WIRE_OUTBOUND",
                         intended="open", later_hold=False)
        self.assertIn("frozen_open", REFUSAL_REASONS)
        self.assertIn("later_hold", REFUSAL_REASONS)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_allowed_decision_refuses_sealed_names(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    FlagDecision(allowed=True, reason=None,
                                 family="wire", name=name,
                                 intended="closed", later_hold=False)


class FamiliesAndIntents(unittest.TestCase):
    def test_closed_family_vocabulary(self):
        self.assertEqual(
            FAMILIES,
            frozenset({
                "wire", "observatory", "hypothesis",
                "auto_email", "keep_gates_open",
            }),
        )

    def test_closed_intent_vocabulary(self):
        self.assertEqual(INTENTS, frozenset({"closed", "open"}))

    def test_wire_family_from_ofn_prefix(self):
        self.assertEqual(classify_family("OFN_WIRE_OUTBOUND"), "wire")
        self.assertEqual(classify_family("OFN_WIRE_EMAIL"), "wire")

    def test_wire_family_from_leading_wire(self):
        self.assertEqual(classify_family("WIRE_LEAD_OUTBOUND"), "wire")

    def test_other_frozen_families(self):
        self.assertEqual(classify_family("OBSERVATORY"), "observatory")
        self.assertEqual(classify_family("CORTEX_HYPOTHESIS"), "hypothesis")
        self.assertEqual(classify_family("auto_email"), "auto_email")
        self.assertEqual(classify_family("OFN_KEEP_GATES_OPEN"), "keep_gates_open")
        self.assertEqual(classify_family("keep_gates_open"), "keep_gates_open")

    def test_hyphen_fold(self):
        self.assertEqual(classify_family("ofn-wire-outbound"), "wire")
        self.assertEqual(classify_family("keep-gates-open"), "keep_gates_open")


class CloseIsAdmittedOpenIsRefused(unittest.TestCase):
    def test_close_every_family(self):
        samples = (
            ("OFN_WIRE_OUTBOUND", "wire"),
            ("OBSERVATORY", "observatory"),
            ("CORTEX_HYPOTHESIS", "hypothesis"),
            ("auto_email", "auto_email"),
            ("OFN_KEEP_GATES_OPEN", "keep_gates_open"),
        )
        for name, family in samples:
            with self.subTest(name=name):
                d = admit_flag(name=name, intended="closed")
                self.assertTrue(d.allowed)
                self.assertIsNone(d.reason)
                self.assertEqual(d.family, family)
                self.assertFalse(d.grants_send)
                self.assertEqual(d.intended, "closed")

    def test_open_every_family_is_frozen(self):
        for name in ("OFN_WIRE_OUTBOUND", "OBSERVATORY",
                     "CORTEX_HYPOTHESIS", "auto_email",
                     "OFN_KEEP_GATES_OPEN"):
            with self.subTest(name=name):
                d = admit_flag(name=name, intended="open")
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "frozen_open")
                self.assertFalse(d.grants_send)
                self.assertFalse(rearms_send())

    def test_close_with_later_hold_still_admitted(self):
        d = admit_flag(name="OFN_WIRE_OUTBOUND", intended="closed",
                       later_hold=True)
        self.assertTrue(d.allowed)
        self.assertTrue(d.later_hold)
        self.assertFalse(d.grants_send)

    def test_open_with_later_hold_is_later_hold(self):
        d = admit_flag(name="auto_email", intended="open",
                       later_hold=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "later_hold")
        self.assertFalse(d.grants_send)
        self.assertFalse(rearms_send())

    def test_replay_is_byte_identical(self):
        a = admit_flag(name="OFN_WIRE_EMAIL", intended="closed")
        b = admit_flag(name="OFN_WIRE_EMAIL", intended="closed")
        self.assertEqual(a, b)
        self.assertTrue(a.allowed)


class LaterHoldOutranksOlderAuth(unittest.TestCase):
    def test_later_hold_reason_beats_frozen_open(self):
        held = admit_flag(name="OFN_WIRE_OUTBOUND", intended="open",
                          later_hold=True)
        plain = admit_flag(name="OFN_WIRE_OUTBOUND", intended="open",
                           later_hold=False)
        self.assertEqual(held.reason, "later_hold")
        self.assertEqual(plain.reason, "frozen_open")
        self.assertFalse(held.allowed)
        self.assertFalse(plain.allowed)
        self.assertFalse(held.grants_send)

    def test_int_one_is_not_later_hold(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_flag(name="OFN_WIRE_OUTBOUND", intended="closed",
                       later_hold=1)
        self.assertIn("exact bool", str(ctx.exception))
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_string_true_is_not_later_hold(self):
        with self.assertRaises(FailClosedError):
            admit_flag(name="OFN_WIRE_OUTBOUND", intended="closed",
                       later_hold="true")


class SealedNameRefusesFlag(unittest.TestCase):
    def test_sealed_flag_aliases(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "SEND_AUTHORIZED",
                     "quote-sent", "campaign-envelope-ready"):
            with self.subTest(name=name):
                d = admit_flag(name=name, intended="closed")
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.grants_send)

    def test_ready_is_not_authorized(self):
        ready = admit_flag(name="campaign_envelope_ready", intended="open")
        auth = admit_flag(name="send_authorized", intended="open")
        sent = admit_flag(name="quote_sent", intended="open")
        self.assertEqual(ready.reason, "sealed_effect")
        self.assertEqual(auth.reason, "sealed_effect")
        self.assertEqual(sent.reason, "sealed_effect")
        self.assertFalse(ready.grants_send)
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertNotEqual(ready.name, auth.name)

    def test_classify_family_refuses_sealed(self):
        with self.assertRaises(FailClosedError):
            classify_family("send_authorized")


class UnknownFailsClosed(unittest.TestCase):
    def test_unknown_flag_is_not_false_and_not_admitted(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_flag(name="NOT_A_FLAG", intended="closed")
        self.assertIn("unknown flag name", str(ctx.exception))
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_unknown_intended_is_not_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_flag(name="OFN_WIRE_OUTBOUND", intended="1")
        self.assertIn("unknown intended", str(ctx.exception))
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_bool_intended_fails_closed(self):
        for value in (True, False):
            with self.subTest(value=value):
                with self.assertRaises(FailClosedError):
                    admit_flag(name="OFN_WIRE_OUTBOUND", intended=value)

    def test_empty_and_bool_names_fail_closed(self):
        for value in ("", "   ", None, True, False, 0, 1):
            with self.subTest(value=value):
                with self.assertRaises(FailClosedError):
                    admit_flag(name=value, intended="closed")

    def test_wireless_is_unknown_not_wire(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_family("wireless")
        self.assertIn("unknown flag name", str(ctx.exception))


class NoRetryAfterInvariant(unittest.TestCase):
    def test_same_bad_input_fails_again(self):
        with self.assertRaises(FailClosedError):
            admit_flag(name="NOT_A_FLAG", intended="closed")
        with self.assertRaises(FailClosedError):
            admit_flag(name="NOT_A_FLAG", intended="closed")

    def test_frozen_open_does_not_become_a_grant(self):
        first = admit_flag(name="auto_email", intended="open")
        second = admit_flag(name="auto_email", intended="open")
        self.assertFalse(first.allowed)
        self.assertFalse(second.allowed)
        self.assertEqual(first.reason, second.reason)


if __name__ == "__main__":
    unittest.main()
