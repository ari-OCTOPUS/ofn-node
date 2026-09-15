"""Kernel-pure once pin — complementary to nonce_class / event_id / dedup.

A first consume is admitted. A second consume of the same pair is
refused. Peek never writes. Ready is not authorized. Not wired
into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.once_pin import (
    INTENTS,
    REFUSAL_REASONS,
    OnceDecision,
    OnceIndex,
    burns_idempotency_key,
    claims_immutable,
    classify_timeout,
    grants_send,
    halt_blocks_consume,
    pin_once,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent,
    unknown_is_false,
    wires_into_run_store,
)

_RUN = "run-1780000000-abcdefghij"
_RUN2 = "run-1780000001-klmnopqrst"
_NCE = "nce-0123456789abcdef"
_NCE2 = "nce-fedcba9876543210"


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_consume(self):
        self.assertFalse(halt_blocks_consume())

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

    def test_does_not_burn_envelope_key(self):
        self.assertFalse(burns_idempotency_key())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(pin_once).parameters
        self.assertEqual(
            list(params),
            ["index", "intended", "nonce", "run_id"],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt",
            "halt_raw",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            OnceDecision(
                allowed=True, reason=None, intended="peek",
                nonce=_NCE, run_id=_RUN, seen=False, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            OnceDecision(
                allowed=True, reason="already_consumed", intended="peek",
                nonce=_NCE, run_id=_RUN, seen=False)

    def test_allowed_consume_cannot_be_seen(self):
        with self.assertRaises(FailClosedError):
            OnceDecision(
                allowed=True, reason=None, intended="consume",
                nonce=_NCE, run_id=_RUN, seen=True)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            OnceDecision(
                allowed=False, reason=None, intended="consume",
                nonce=_NCE, run_id=_RUN, seen=False)
        with self.assertRaises(FailClosedError):
            OnceDecision(
                allowed=False, reason="send_authorized", intended="consume",
                nonce=_NCE, run_id=_RUN, seen=False)
        self.assertIn("already_consumed", REFUSAL_REASONS)
        self.assertIn("nonce_collision", REFUSAL_REASONS)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_closed_intents(self):
        self.assertEqual(INTENTS, frozenset({"consume", "peek"}))


class ConsumeOnce(unittest.TestCase):
    def test_first_consume_admitted(self):
        idx = OnceIndex()
        d = pin_once(idx, intended="consume", nonce=_NCE, run_id=_RUN)
        self.assertTrue(d.allowed)
        self.assertIsNone(d.reason)
        self.assertFalse(d.seen)
        self.assertFalse(d.grants_send)
        self.assertEqual(len(idx), 1)

    def test_second_consume_refused(self):
        idx = OnceIndex()
        first = pin_once(idx, intended="consume", nonce=_NCE, run_id=_RUN)
        second = pin_once(idx, intended="consume", nonce=_NCE, run_id=_RUN)
        self.assertTrue(first.allowed)
        self.assertFalse(second.allowed)
        self.assertEqual(second.reason, "already_consumed")
        self.assertTrue(second.seen)
        self.assertFalse(second.grants_send)
        self.assertEqual(len(idx), 1)

    def test_same_nonce_different_run_is_collision(self):
        idx = OnceIndex()
        first = pin_once(idx, intended="consume", nonce=_NCE, run_id=_RUN)
        other = pin_once(idx, intended="consume", nonce=_NCE, run_id=_RUN2)
        self.assertTrue(first.allowed)
        self.assertFalse(other.allowed)
        self.assertEqual(other.reason, "nonce_collision")
        self.assertFalse(other.seen)
        self.assertEqual(len(idx), 1)

    def test_different_nonce_same_run_ok(self):
        idx = OnceIndex()
        a = pin_once(idx, intended="consume", nonce=_NCE, run_id=_RUN)
        b = pin_once(idx, intended="consume", nonce=_NCE2, run_id=_RUN)
        self.assertTrue(a.allowed)
        self.assertTrue(b.allowed)
        self.assertEqual(len(idx), 2)

    def test_peek_does_not_write(self):
        idx = OnceIndex()
        peek = pin_once(idx, intended="peek", nonce=_NCE, run_id=_RUN)
        self.assertTrue(peek.allowed)
        self.assertFalse(peek.seen)
        self.assertEqual(len(idx), 0)
        pin_once(idx, intended="consume", nonce=_NCE, run_id=_RUN)
        seen = pin_once(idx, intended="peek", nonce=_NCE, run_id=_RUN)
        self.assertTrue(seen.allowed)
        self.assertTrue(seen.seen)
        self.assertEqual(len(idx), 1)

    def test_index_record_raises_on_second(self):
        idx = OnceIndex()
        idx.record(_NCE, _RUN)
        with self.assertRaises(FailClosedError) as ctx:
            idx.record(_NCE, _RUN)
        self.assertIn("already_consumed", str(ctx.exception))

    def test_index_record_raises_on_collision(self):
        idx = OnceIndex()
        idx.record(_NCE, _RUN)
        with self.assertRaises(FailClosedError) as ctx:
            idx.record(_NCE, _RUN2)
        self.assertIn("nonce_collision", str(ctx.exception))


class OnceRefusals(unittest.TestCase):
    def test_sealed_nonce(self):
        idx = OnceIndex()
        d = pin_once(
            idx, intended="consume", nonce="send_authorized", run_id=_RUN)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")
        self.assertEqual(len(idx), 0)

    def test_sealed_run_id(self):
        idx = OnceIndex()
        d = pin_once(
            idx, intended="consume", nonce=_NCE, run_id="quote_sent")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")

    def test_sealed_ready_alias(self):
        idx = OnceIndex()
        d = pin_once(
            idx, intended="consume",
            nonce="campaign-envelope-ready", run_id=_RUN)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")

    def test_malformed_nonce(self):
        idx = OnceIndex()
        d = pin_once(idx, intended="consume", nonce="nce-zz", run_id=_RUN)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "malformed_nonce")
        self.assertEqual(len(idx), 0)

    def test_malformed_run_id(self):
        idx = OnceIndex()
        d = pin_once(idx, intended="consume", nonce=_NCE, run_id="run-x")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "malformed_id")

    def test_unknown_intent_fails_closed(self):
        idx = OnceIndex()
        with self.assertRaises(FailClosedError) as ctx:
            pin_once(idx, intended="resend", nonce=_NCE, run_id=_RUN)
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertEqual(len(idx), 0)

    def test_wrong_index_type_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_once({}, intended="consume", nonce=_NCE, run_id=_RUN)

    def test_empty_nonce_fails_closed(self):
        idx = OnceIndex()
        with self.assertRaises(FailClosedError):
            pin_once(idx, intended="consume", nonce="", run_id=_RUN)


class DistinctFromSiblings(unittest.TestCase):
    def test_does_not_import_run_store(self):
        import ofn.kernel.once_pin as mod
        self.assertFalse(hasattr(mod, "RunStore"))
        src = inspect.getsource(mod)
        self.assertNotIn("adapters.run_store", src)
        self.assertNotIn("from ofn.adapters", src)

    def test_does_not_import_dedup_or_event_id(self):
        import ofn.kernel.once_pin as mod
        src = inspect.getsource(mod)
        self.assertNotIn("KindRefIndex", src)
        self.assertNotIn("EventIdIndex", src)
        self.assertNotIn("evt-", src)


if __name__ == "__main__":
    unittest.main()
