"""Kernel-pure format class — complementary to envelope / event_id / receipt_bind.

classify is a START. inspect is not. This module does not mint a
run_id and is not wired into the run store. Ready is not authorized.
Malformed is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.envelope import RUN_ID_RE, SHA256_HEX_RE
from ofn.kernel.errors import FailClosedError
from ofn.kernel.event_id import EVENT_ID_RE
from ofn.kernel.format_class import (
    FAMILIES,
    INTENTS,
    REFUSAL_REASONS,
    STATUSES,
    FormatDecision,
    admit_format,
    claims_immutable,
    classify_format,
    classify_timeout,
    grants_send,
    halt_blocks_inspect,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent,
    unknown_is_false,
    wires_into_run_store,
)

_RUN = "run-1780000000-abcdefghij"
_EVT = "evt-0123456789abcdef"
_DIGEST = "a" * 64


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_inspect(self):
        self.assertFalse(halt_blocks_inspect())

    def test_does_not_mint_run_id(self):
        self.assertFalse(mints_run_id())

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
        params = inspect.signature(admit_format).parameters
        self.assertEqual(
            list(params),
            ["intended", "family", "value", "halted", "timed_out"],
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
            FormatDecision(
                allowed=True, reason=None, status="FORMAT_FIT",
                intended="inspect", family="run_id", timed_out=False,
                grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            FormatDecision(
                allowed=True, reason="halt_active", status="FORMAT_FIT",
                intended="inspect", family="run_id", timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            FormatDecision(
                allowed=False, reason=None, status="UNKNOWN",
                intended="classify", family="run_id", timed_out=False)
        with self.assertRaises(FailClosedError):
            FormatDecision(
                allowed=False, reason="send_authorized", status="UNKNOWN",
                intended="classify", family="run_id", timed_out=False)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("halt_active", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_closed_vocabularies(self):
        self.assertEqual(FAMILIES, frozenset({"run_id", "event_id", "digest"}))
        self.assertEqual(INTENTS, frozenset({"classify", "inspect"}))
        self.assertEqual(STATUSES, frozenset({"FORMAT_FIT", "UNKNOWN"}))


class ClassifyShape(unittest.TestCase):
    def test_run_id_fit_matches_envelope_regex(self):
        self.assertTrue(RUN_ID_RE.match(_RUN))
        self.assertEqual(
            classify_format(family="run_id", value=_RUN), "FORMAT_FIT")

    def test_event_id_fit_matches_event_id_regex(self):
        self.assertTrue(EVENT_ID_RE.match(_EVT))
        self.assertEqual(
            classify_format(family="event_id", value=_EVT), "FORMAT_FIT")

    def test_digest_fit_matches_sha256_regex(self):
        self.assertTrue(SHA256_HEX_RE.match(_DIGEST))
        self.assertEqual(
            classify_format(family="digest", value=_DIGEST), "FORMAT_FIT")

    def test_malformed_is_unknown_not_false(self):
        self.assertEqual(
            classify_format(family="run_id", value="run-nope"), "UNKNOWN")
        self.assertEqual(
            classify_format(family="event_id", value="evt-ZZ"), "UNKNOWN")
        self.assertEqual(
            classify_format(family="digest", value="AA" * 32), "UNKNOWN")
        self.assertIsNot(classify_format(family="run_id", value=""), False)

    def test_missing_is_unknown(self):
        self.assertEqual(
            classify_format(family="run_id", value=None), "UNKNOWN")
        self.assertEqual(
            classify_format(family="run_id", value=""), "UNKNOWN")
        self.assertEqual(
            classify_format(family="run_id", value="   "), "UNKNOWN")

    def test_wrong_family_is_unknown(self):
        self.assertEqual(
            classify_format(family="event_id", value=_RUN), "UNKNOWN")
        self.assertEqual(
            classify_format(family="run_id", value=_EVT), "UNKNOWN")
        self.assertEqual(
            classify_format(family="digest", value=_RUN), "UNKNOWN")

    def test_timeout_is_unknown(self):
        self.assertEqual(
            classify_format(family="run_id", value=_RUN, timed_out=True),
            "UNKNOWN")

    def test_unknown_family_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_format(family="nonce", value=_RUN)
        self.assertIn("unknown", str(ctx.exception).lower())
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_bool_family_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_format(family=True, value=_RUN)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            classify_format(family="run_id", value=_RUN, timed_out="yes")


class AdmitFormat(unittest.TestCase):
    def test_inspect_fit_allowed(self):
        d = admit_format(intended="inspect", family="run_id", value=_RUN)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "FORMAT_FIT")
        self.assertFalse(d.grants_send)
        self.assertIsNone(d.reason)

    def test_classify_fit_allowed(self):
        d = admit_format(intended="classify", family="event_id", value=_EVT)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "FORMAT_FIT")
        self.assertFalse(d.grants_send)

    def test_inspect_malformed_is_unknown_allowed(self):
        d = admit_format(intended="inspect", family="run_id", value="nope")
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(d.grants_send)

    def test_halt_refuses_classify_not_inspect(self):
        refused = admit_format(
            intended="classify", family="run_id", value=_RUN, halted=True)
        self.assertFalse(refused.allowed)
        self.assertEqual(refused.reason, "halt_active")
        self.assertFalse(refused.grants_send)
        inspect = admit_format(
            intended="inspect", family="run_id", value=_RUN, halted=True)
        self.assertTrue(inspect.allowed)
        self.assertEqual(inspect.status, "FORMAT_FIT")

    def test_timeout_is_unknown_not_a_race(self):
        d = admit_format(
            intended="inspect", family="run_id", value=_RUN, timed_out=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertTrue(d.timed_out)
        self.assertFalse(timeout_proves_concurrent())

    def test_sealed_value_refused(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "send-authorized",
        ):
            d = admit_format(intended="inspect", family="run_id", value=name)
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)

    def test_sealed_intended_refused(self):
        d = admit_format(
            intended="send_authorized", family="run_id", value=_RUN)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")

    def test_unknown_intended_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_format(intended="mint", family="run_id", value=_RUN)
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_halted_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_format(
                intended="inspect", family="run_id", value=_RUN, halted=1)

    def test_digest_inspect(self):
        d = admit_format(intended="inspect", family="digest", value=_DIGEST)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "FORMAT_FIT")
        self.assertEqual(d.family, "digest")


if __name__ == "__main__":
    unittest.main()
