"""Kernel-pure parse pin — first field-split of a FORMAT_FIT identifier.

parse is a START. peek is not. Second parse is already_parsed.
Not wired into the run store. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.parse_pin import (
    INTENTS,
    REFUSAL_REASONS,
    STATUSES,
    ParsePin,
    already_parsed_is_first,
    claims_immutable,
    grants_send,
    halt_blocks_peek,
    mints_run_id,
    pin_parse,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    split_fit,
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

    def test_halt_does_not_block_peek(self):
        self.assertFalse(halt_blocks_peek())

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

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_second_parse_is_not_first(self):
        self.assertFalse(already_parsed_is_first())

    def test_signature_has_no_send_or_resend_knob(self):
        params = inspect.signature(pin_parse).parameters
        self.assertEqual(
            list(params),
            ["intended", "family", "value", "prior_parsed", "halted",
             "timed_out"],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            ParsePin(
                allowed=True, reason=None, status="PARSED",
                intended="parse", family="run_id", stem="run",
                body="1780000000-abcdefghij", timed_out=False,
                grants_send=True)

    def test_allowed_parse_requires_parsed(self):
        with self.assertRaises(FailClosedError):
            ParsePin(
                allowed=True, reason=None, status="UNKNOWN",
                intended="parse", family="run_id", stem="run",
                body="x", timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            ParsePin(
                allowed=False, reason="send_authorized", status="UNKNOWN",
                intended="parse", family="run_id", stem="", body="",
                timed_out=False)
        self.assertIn("already_parsed", REFUSAL_REASONS)
        self.assertIn("not_fit", REFUSAL_REASONS)
        self.assertIn("unknown_shape", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_closed_vocabularies(self):
        self.assertEqual(INTENTS, frozenset({"parse", "peek"}))
        self.assertEqual(STATUSES, frozenset({"PARSED", "UNKNOWN"}))


class SplitFit(unittest.TestCase):
    def test_run_id_splits_on_first_hyphen(self):
        stem, body = split_fit(family="run_id", value=_RUN)
        self.assertEqual(stem, "run")
        self.assertEqual(body, "1780000000-abcdefghij")

    def test_event_id_splits(self):
        stem, body = split_fit(family="event_id", value=_EVT)
        self.assertEqual(stem, "evt")
        self.assertEqual(body, "0123456789abcdef")

    def test_digest_has_empty_stem(self):
        stem, body = split_fit(family="digest", value=_DIGEST)
        self.assertEqual(stem, "")
        self.assertEqual(body, _DIGEST)


class PinParse(unittest.TestCase):
    def test_first_parse_run_id(self):
        d = pin_parse(intended="parse", family="run_id", value=_RUN)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "PARSED")
        self.assertEqual(d.stem, "run")
        self.assertEqual(d.body, "1780000000-abcdefghij")
        self.assertFalse(d.grants_send)

    def test_first_parse_event_id(self):
        d = pin_parse(intended="parse", family="event_id", value=_EVT)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "PARSED")
        self.assertEqual(d.stem, "evt")
        self.assertEqual(d.body, "0123456789abcdef")

    def test_first_parse_digest(self):
        d = pin_parse(intended="parse", family="digest", value=_DIGEST)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "PARSED")
        self.assertEqual(d.stem, "")
        self.assertEqual(d.body, _DIGEST)

    def test_peek_does_not_claim_parsed(self):
        d = pin_parse(intended="peek", family="run_id", value=_RUN)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.stem, "run")
        self.assertFalse(d.grants_send)

    def test_second_parse_is_already_parsed(self):
        d = pin_parse(
            intended="parse", family="run_id", value=_RUN, prior_parsed=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "already_parsed")
        self.assertFalse(already_parsed_is_first())

    def test_malformed_is_not_fit(self):
        d = pin_parse(intended="parse", family="run_id", value="run-nope")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "not_fit")
        self.assertEqual(d.status, "UNKNOWN")

    def test_missing_is_not_fit(self):
        d = pin_parse(intended="parse", family="run_id", value="")
        # empty fails closed at require_name on intended path... value=""
        # classify_format returns UNKNOWN, pin refuses not_fit.
        # admit uses _require_name only on intended/family.
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "not_fit")

    def test_halt_refuses_parse_not_peek(self):
        refused = pin_parse(
            intended="parse", family="run_id", value=_RUN, halted=True)
        self.assertFalse(refused.allowed)
        self.assertEqual(refused.reason, "halt_active")
        peek = pin_parse(
            intended="peek", family="run_id", value=_RUN, halted=True)
        self.assertTrue(peek.allowed)
        self.assertEqual(peek.stem, "run")

    def test_timeout_is_unknown_not_already_parsed(self):
        d = pin_parse(
            intended="parse", family="run_id", value=_RUN, timed_out=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.reason, "unknown_shape")
        self.assertNotEqual(d.reason, "already_parsed")
        self.assertFalse(timeout_proves_concurrent())
        peek = pin_parse(
            intended="peek", family="run_id", value=_RUN, timed_out=True)
        self.assertTrue(peek.allowed)
        self.assertEqual(peek.status, "UNKNOWN")

    def test_sealed_value_refused(self):
        d = pin_parse(
            intended="parse", family="run_id", value="campaign_envelope_ready")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")
        self.assertFalse(d.grants_send)

    def test_unknown_intended_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_parse(intended="classify", family="run_id", value=_RUN)

    def test_prior_parsed_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            pin_parse(
                intended="parse", family="run_id", value=_RUN,
                prior_parsed="yes")


if __name__ == "__main__":
    unittest.main()
