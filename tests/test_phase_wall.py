"""Kernel-pure phase wall — complementary to flag_freeze and write_fence.

Ready is a named phase. Authorized is a different name. Send is
refused. This module is not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.phase_wall import (
    BANDS,
    INTENTS,
    REFUSAL_REASONS,
    PhaseDecision,
    admit_phase,
    claims_immutable,
    classify_band,
    grants_send,
    halt_blocks_phase,
    proposal_is_execution,
    ready_equals_authorized,
    ready_is_authorized,
    rearms_send,
    unknown_is_false,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_does_not_rearm_send(self):
        self.assertFalse(rearms_send())

    def test_halt_does_not_block_phase_classify(self):
        self.assertFalse(halt_blocks_phase())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertFalse(ready_equals_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(admit_phase).parameters
        self.assertEqual(list(params), ["name", "intended", "later_hold"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            PhaseDecision(allowed=True, reason=None, band="ready",
                          name="campaign_envelope_ready",
                          intended="classify", later_hold=False,
                          grants_send=True)
        with self.assertRaises(FailClosedError):
            PhaseDecision(allowed=False, reason="sealed_effect",
                          band="send", name="send_authorized",
                          intended="advance", later_hold=False,
                          grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            PhaseDecision(allowed=True, reason="sealed_effect",
                          band="ready", name="campaign_envelope_ready",
                          intended="classify", later_hold=False)

    def test_allowed_cannot_be_send_band(self):
        with self.assertRaises(FailClosedError):
            PhaseDecision(allowed=True, reason=None, band="send",
                          name="send_authorized", intended="classify",
                          later_hold=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            PhaseDecision(allowed=False, reason=None, band="send",
                          name="send_authorized", intended="advance",
                          later_hold=False)
        with self.assertRaises(FailClosedError):
            PhaseDecision(allowed=False, reason="send_authorized",
                          band="send", name="send_authorized",
                          intended="advance", later_hold=False)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("later_hold", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_refused_cannot_be_ready_band(self):
        with self.assertRaises(FailClosedError):
            PhaseDecision(allowed=False, reason="sealed_effect",
                          band="ready", name="campaign_envelope_ready",
                          intended="classify", later_hold=False)


class BandsAndIntents(unittest.TestCase):
    def test_closed_band_vocabulary(self):
        self.assertEqual(BANDS, frozenset({"ready", "send"}))

    def test_closed_intent_vocabulary(self):
        self.assertEqual(INTENTS, frozenset({"classify", "advance"}))

    def test_ready_band_names(self):
        self.assertEqual(classify_band("campaign_envelope_ready"), "ready")
        self.assertEqual(classify_band("quote_drafted"), "ready")
        self.assertEqual(classify_band("campaign-envelope-ready"), "ready")
        self.assertEqual(classify_band("QUOTE_DRAFTED"), "ready")

    def test_send_band_names(self):
        self.assertEqual(classify_band("send_authorized"), "send")
        self.assertEqual(classify_band("quote_sent"), "send")
        self.assertEqual(classify_band("send-authorized"), "send")
        self.assertEqual(classify_band("QUOTE_SENT"), "send")

    def test_ready_and_send_are_different_bands(self):
        self.assertNotEqual(
            classify_band("campaign_envelope_ready"),
            classify_band("send_authorized"),
        )


class ReadyIsAdmittedSendIsRefused(unittest.TestCase):
    def test_classify_ready_is_admitted(self):
        for name in ("campaign_envelope_ready", "quote_drafted"):
            with self.subTest(name=name):
                d = admit_phase(name=name, intended="classify")
                self.assertTrue(d.allowed)
                self.assertIsNone(d.reason)
                self.assertEqual(d.band, "ready")
                self.assertFalse(d.grants_send)
                self.assertEqual(d.name, name)

    def test_advance_ready_is_admitted(self):
        d = admit_phase(name="campaign_envelope_ready", intended="advance")
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)
        self.assertFalse(ready_is_authorized())

    def test_classify_send_is_sealed(self):
        for name in ("send_authorized", "quote_sent"):
            with self.subTest(name=name):
                d = admit_phase(name=name, intended="classify")
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.grants_send)
                self.assertEqual(d.band, "send")

    def test_advance_send_is_sealed(self):
        d = admit_phase(name="send_authorized", intended="advance")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")
        self.assertFalse(d.grants_send)
        self.assertFalse(rearms_send())

    def test_ready_stays_admitted_under_later_hold(self):
        d = admit_phase(name="campaign_envelope_ready",
                        intended="advance", later_hold=True)
        self.assertTrue(d.allowed)
        self.assertTrue(d.later_hold)
        self.assertFalse(d.grants_send)
        self.assertFalse(ready_is_authorized())

    def test_send_under_later_hold_is_later_hold(self):
        d = admit_phase(name="quote_sent", intended="advance",
                        later_hold=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "later_hold")
        self.assertFalse(d.grants_send)
        self.assertFalse(rearms_send())

    def test_replay_is_byte_identical(self):
        a = admit_phase(name="quote_drafted", intended="classify")
        b = admit_phase(name="quote_drafted", intended="classify")
        self.assertEqual(a, b)
        self.assertTrue(a.allowed)


class LaterHoldOutranksOlderAuth(unittest.TestCase):
    def test_later_hold_reason_beats_sealed_effect(self):
        held = admit_phase(name="send_authorized", intended="advance",
                           later_hold=True)
        plain = admit_phase(name="send_authorized", intended="advance",
                            later_hold=False)
        self.assertEqual(held.reason, "later_hold")
        self.assertEqual(plain.reason, "sealed_effect")
        self.assertFalse(held.allowed)
        self.assertFalse(plain.allowed)
        self.assertFalse(held.grants_send)

    def test_int_one_is_not_later_hold(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_phase(name="campaign_envelope_ready",
                        intended="classify", later_hold=1)
        self.assertIn("exact bool", str(ctx.exception))
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_string_true_is_not_later_hold(self):
        with self.assertRaises(FailClosedError):
            admit_phase(name="campaign_envelope_ready",
                        intended="classify", later_hold="true")


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_ready_decision_name_differs_from_send(self):
        ready = admit_phase(name="campaign_envelope_ready",
                            intended="advance")
        auth = admit_phase(name="send_authorized", intended="advance")
        sent = admit_phase(name="quote_sent", intended="advance")
        self.assertTrue(ready.allowed)
        self.assertFalse(auth.allowed)
        self.assertFalse(sent.allowed)
        self.assertNotEqual(ready.name, auth.name)
        self.assertNotEqual(ready.band, auth.band)
        self.assertFalse(ready.grants_send)
        self.assertFalse(ready_equals_authorized())

    def test_hyphen_fold_still_separates_bands(self):
        ready = admit_phase(name="campaign-envelope-ready",
                            intended="classify")
        auth = admit_phase(name="send-authorized", intended="classify")
        self.assertEqual(ready.band, "ready")
        self.assertEqual(auth.band, "send")
        self.assertTrue(ready.allowed)
        self.assertFalse(auth.allowed)


class UnknownFailsClosed(unittest.TestCase):
    def test_unknown_phase_is_not_false_and_not_admitted(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_phase(name="NOT_A_PHASE", intended="classify")
        self.assertIn("unknown phase name", str(ctx.exception))
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_unknown_intended_is_not_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_phase(name="campaign_envelope_ready", intended="1")
        self.assertIn("unknown intended", str(ctx.exception))
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_bool_intended_fails_closed(self):
        for value in (True, False):
            with self.subTest(value=value):
                with self.assertRaises(FailClosedError):
                    admit_phase(name="campaign_envelope_ready",
                                intended=value)

    def test_empty_and_bool_names_fail_closed(self):
        for value in ("", "   ", None, True, False, 0, 1):
            with self.subTest(value=value):
                with self.assertRaises(FailClosedError):
                    admit_phase(name=value, intended="classify")

    def test_readyish_is_unknown_not_ready(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_band("readyish")
        self.assertIn("unknown phase name", str(ctx.exception))


class NoRetryAfterInvariant(unittest.TestCase):
    def test_same_bad_input_fails_again(self):
        with self.assertRaises(FailClosedError):
            admit_phase(name="NOT_A_PHASE", intended="classify")
        with self.assertRaises(FailClosedError):
            admit_phase(name="NOT_A_PHASE", intended="classify")

    def test_sealed_send_does_not_become_a_grant(self):
        first = admit_phase(name="send_authorized", intended="advance")
        second = admit_phase(name="send_authorized", intended="advance")
        self.assertFalse(first.allowed)
        self.assertFalse(second.allowed)
        self.assertEqual(first.reason, second.reason)
        self.assertFalse(first.grants_send)


if __name__ == "__main__":
    unittest.main()
