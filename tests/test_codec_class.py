"""Kernel-pure codec class — complementary to typed_event / receipts.

A proposed encode is a START. Inspect and replay are not STARTS.
This module does not produce encoded bytes and is not wired into
the run store. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.codec_class import (
    ACTIVITIES,
    CODECS,
    INTENTS,
    REFUSAL_REASONS,
    STATUSES,
    CodecDecision,
    admit_codec,
    claims_immutable,
    classify_status,
    classify_timeout,
    encodes_bytes,
    grants_send,
    halt_blocks_inspect,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError

_PAYLOAD = "receipt-body"


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_inspect(self):
        self.assertFalse(halt_blocks_inspect())

    def test_does_not_encode_bytes(self):
        self.assertFalse(encodes_bytes())

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

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_signature_has_no_send_or_resend_knob(self):
        params = inspect.signature(admit_codec).parameters
        self.assertEqual(
            list(params),
            ["intended", "codec", "payload", "width", "activity",
             "halted", "timed_out"],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt_raw",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            CodecDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="inspect", codec="utf8", timed_out=False,
                grants_send=True)
        with self.assertRaises(FailClosedError):
            CodecDecision(
                allowed=False, reason="sealed_effect", status="UNKNOWN",
                intended="inspect", codec="send_authorized",
                timed_out=False, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            CodecDecision(
                allowed=True, reason="halt_active", status="VERIFIED",
                intended="encode", codec="utf8", timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            CodecDecision(
                allowed=False, reason=None, status="UNKNOWN",
                intended="encode", codec="utf8", timed_out=False)
        with self.assertRaises(FailClosedError):
            CodecDecision(
                allowed=False, reason="send_authorized", status="UNKNOWN",
                intended="encode", codec="utf8", timed_out=False)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("halt_active", REFUSAL_REASONS)
        self.assertIn("unknown_codec", REFUSAL_REASONS)
        self.assertIn("empty_payload", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_allowed_encode_requires_verified(self):
        for status in ("SUSPECTED", "UNKNOWN"):
            with self.subTest(status=status):
                with self.assertRaises(FailClosedError):
                    CodecDecision(
                        allowed=True, reason=None, status=status,
                        intended="encode", codec="utf8", timed_out=False)

    def test_allowed_decision_refuses_sealed_codec(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    CodecDecision(
                        allowed=True, reason=None, status="VERIFIED",
                        intended="inspect", codec=name, timed_out=False)

    def test_non_sealed_refusal_cannot_carry_a_sealed_codec(self):
        with self.assertRaises(FailClosedError):
            CodecDecision(
                allowed=False, reason="unknown_activity", status="UNKNOWN",
                intended="encode", codec="send_authorized", timed_out=True)

    def test_sealed_effect_refusal_names_the_subject(self):
        d = CodecDecision(
            allowed=False, reason="sealed_effect", status="UNKNOWN",
            intended="inspect", codec="send_authorized", timed_out=False)
        self.assertEqual(d.codec, "send_authorized")
        self.assertFalse(d.allowed)
        self.assertFalse(d.grants_send)

    def test_closed_vocabularies(self):
        self.assertEqual(INTENTS, frozenset({"encode", "inspect", "replay"}))
        self.assertEqual(CODECS, frozenset({"utf8", "hex", "ascii"}))
        self.assertEqual(STATUSES, frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"}))
        self.assertEqual(ACTIVITIES, frozenset({"idle", "concurrent", "unknown"}))


class ClassifyStatus(unittest.TestCase):
    def test_timeout_outranks_concurrent(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=True),
            "UNKNOWN")

    def test_idle_verified(self):
        self.assertEqual(
            classify_status(activity="idle", timed_out=False),
            "VERIFIED")

    def test_concurrent_suspected(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=False),
            "SUSPECTED")

    def test_unknown_activity_unknown(self):
        self.assertEqual(
            classify_status(activity="unknown", timed_out=False),
            "UNKNOWN")

    def test_unknown_activity_name_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_status(activity="DEAD_SOURCE", timed_out=False)
        self.assertNotIn("FALSE", str(ctx.exception))


class AdmitHappyPath(unittest.TestCase):
    def test_encode_utf8_idle(self):
        d = admit_codec(intended="encode", codec="utf8", payload=_PAYLOAD)
        self.assertTrue(d.allowed)
        self.assertIsNone(d.reason)
        self.assertEqual(d.status, "VERIFIED")
        self.assertEqual(d.codec, "utf8")
        self.assertFalse(d.grants_send)

    def test_inspect_and_replay_under_halt(self):
        for intent in ("inspect", "replay"):
            with self.subTest(intent=intent):
                d = admit_codec(
                    intended=intent, codec="hex", payload="ab",
                    halted=True)
                self.assertTrue(d.allowed)
                self.assertFalse(d.grants_send)

    def test_width_match_admits(self):
        d = admit_codec(
            intended="encode", codec="ascii", payload="ab", width=2)
        self.assertTrue(d.allowed)

    def test_replay_under_timeout_is_unknown_not_false(self):
        d = admit_codec(
            intended="replay", codec="utf8", payload=_PAYLOAD,
            timed_out=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(d.grants_send)


class AdmitRefusals(unittest.TestCase):
    def test_halt_refuses_encode_only(self):
        d = admit_codec(
            intended="encode", codec="utf8", payload=_PAYLOAD, halted=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "halt_active")
        self.assertFalse(d.grants_send)

    def test_unknown_codec_is_refused_not_false(self):
        d = admit_codec(
            intended="encode", codec="latin1", payload=_PAYLOAD)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_codec")
        self.assertNotEqual(d.reason, "FALSE")

    def test_empty_payload_refused(self):
        d = admit_codec(intended="encode", codec="utf8", payload="")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "empty_payload")

    def test_width_mismatch_refused(self):
        d = admit_codec(
            intended="inspect", codec="utf8", payload="ab", width=9)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "width_mismatch")

    def test_timeout_refuses_encode_as_unknown_not_concurrent(self):
        d = admit_codec(
            intended="encode", codec="utf8", payload=_PAYLOAD,
            activity="concurrent", timed_out=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.reason, "unknown_activity")
        self.assertNotEqual(d.reason, "suspected_concurrent")

    def test_concurrent_refuses_encode(self):
        d = admit_codec(
            intended="encode", codec="utf8", payload=_PAYLOAD,
            activity="concurrent")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "suspected_concurrent")

    def test_sealed_intent_and_codec(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "send-authorized"):
            with self.subTest(name=name):
                as_intent = admit_codec(
                    intended=name, codec="utf8", payload=_PAYLOAD)
                as_codec = admit_codec(
                    intended="encode", codec=name, payload=_PAYLOAD)
                self.assertFalse(as_intent.allowed)
                self.assertFalse(as_codec.allowed)
                self.assertEqual(as_intent.reason, "sealed_effect")
                self.assertEqual(as_codec.reason, "sealed_effect")
                self.assertFalse(as_intent.grants_send)
                self.assertFalse(as_codec.grants_send)
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


class FailClosedInputs(unittest.TestCase):
    def test_missing_names_fail_closed(self):
        with self.assertRaises(FailClosedError):
            admit_codec(intended="", codec="utf8", payload=_PAYLOAD)
        with self.assertRaises(FailClosedError):
            admit_codec(intended="encode", codec="", payload=_PAYLOAD)
        with self.assertRaises(FailClosedError):
            admit_codec(intended=None, codec="utf8", payload=_PAYLOAD)

    def test_bool_payload_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_codec(intended="encode", codec="utf8", payload=True)

    def test_sealed_payload_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_codec(
                intended="encode", codec="utf8",
                payload="send_authorized")

    def test_bool_flags_fail_closed(self):
        with self.assertRaises(FailClosedError):
            admit_codec(
                intended="encode", codec="utf8", payload=_PAYLOAD,
                halted="yes")
        with self.assertRaises(FailClosedError):
            admit_codec(
                intended="encode", codec="utf8", payload=_PAYLOAD,
                timed_out=1)
        with self.assertRaises(FailClosedError):
            admit_codec(
                intended="encode", codec="utf8", payload=_PAYLOAD,
                width=True)

    def test_unknown_intent_fails_closed_not_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_codec(intended="resend", codec="utf8", payload=_PAYLOAD)
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_unknown_activity_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_codec(
                intended="encode", codec="utf8", payload=_PAYLOAD,
                activity="DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
