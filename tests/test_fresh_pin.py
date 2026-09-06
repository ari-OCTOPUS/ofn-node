"""Contract tests for fresh_pin (P1 complementary).

A FRESH classification may be pinned once per (run_id, event_id).
STALE / UNKNOWN cannot be pinned as FRESH. Peek never writes.
Timeout is UNKNOWN, not a concurrent-write proof. Ready ≠ authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.fresh_pin import (
    FreshIndex,
    FreshPin,
    claims_immutable,
    grants_send,
    halt_blocks_pin,
    persist_is_send,
    pin_fresh,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    stale_is_fresh,
    timeout_proves_concurrent_write,
    unknown_is_false,
    unknown_is_fresh,
    wires_into_run_store,
)

_RUN = "run-1780000000-a1b2c3d4e5"
_EVT = "evt-0123456789abcdef"


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_pin(self):
        self.assertFalse(halt_blocks_pin())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_unknown_is_not_fresh(self):
        self.assertFalse(unknown_is_fresh())

    def test_stale_is_not_fresh(self):
        self.assertFalse(stale_is_fresh())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_does_not_wire_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_persist_is_not_send(self):
        self.assertFalse(persist_is_send())

    def test_signature_has_no_send_halt_knob(self):
        params = inspect.signature(pin_fresh).parameters
        self.assertEqual(
            list(params),
            ["index", "intended", "kind", "run_id", "event_id"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready", "halt", "halt_raw",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            FreshPin(
                allowed=True, reason=None, intended="pin", kind="FRESH",
                run_id=_RUN, event_id=_EVT, seen=False, grants_send=True)


class PinFresh(unittest.TestCase):
    def test_first_fresh_pin_is_allowed(self):
        idx = FreshIndex()
        got = pin_fresh(
            idx, intended="pin", kind="FRESH", run_id=_RUN, event_id=_EVT)
        self.assertTrue(got.allowed)
        self.assertFalse(got.seen)
        self.assertEqual(len(idx), 1)
        self.assertFalse(got.grants_send)

    def test_second_pin_is_already_pinned(self):
        idx = FreshIndex()
        pin_fresh(idx, intended="pin", kind="FRESH", run_id=_RUN, event_id=_EVT)
        got = pin_fresh(
            idx, intended="pin", kind="FRESH", run_id=_RUN, event_id=_EVT)
        self.assertFalse(got.allowed)
        self.assertEqual(got.reason, "already_pinned")
        self.assertTrue(got.seen)
        self.assertEqual(len(idx), 1)

    def test_stale_cannot_be_pinned(self):
        idx = FreshIndex()
        got = pin_fresh(
            idx, intended="pin", kind="STALE", run_id=_RUN, event_id=_EVT)
        self.assertFalse(got.allowed)
        self.assertEqual(got.reason, "stale_not_fresh")
        self.assertEqual(len(idx), 0)

    def test_unknown_cannot_be_pinned(self):
        idx = FreshIndex()
        got = pin_fresh(
            idx, intended="pin", kind="UNKNOWN", run_id=_RUN, event_id=_EVT)
        self.assertFalse(got.allowed)
        self.assertEqual(got.reason, "unknown_not_fresh")
        self.assertEqual(len(idx), 0)
        self.assertNotEqual(got.reason, "FALSE")

    def test_peek_never_writes(self):
        idx = FreshIndex()
        got = pin_fresh(
            idx, intended="peek", kind="FRESH", run_id=_RUN, event_id=_EVT)
        self.assertTrue(got.allowed)
        self.assertFalse(got.seen)
        self.assertEqual(len(idx), 0)

    def test_peek_after_pin_reports_seen(self):
        idx = FreshIndex()
        pin_fresh(idx, intended="pin", kind="FRESH", run_id=_RUN, event_id=_EVT)
        got = pin_fresh(
            idx, intended="peek", kind="FRESH", run_id=_RUN, event_id=_EVT)
        self.assertTrue(got.seen)
        self.assertEqual(len(idx), 1)

    def test_other_event_is_a_different_pair(self):
        idx = FreshIndex()
        pin_fresh(idx, intended="pin", kind="FRESH", run_id=_RUN, event_id=_EVT)
        other = pin_fresh(
            idx, intended="pin", kind="FRESH",
            run_id=_RUN, event_id="evt-aaaaaaaaaaaaaaaa")
        self.assertTrue(other.allowed)
        self.assertEqual(len(idx), 2)

    def test_malformed_ids_refuse_not_false(self):
        idx = FreshIndex()
        got = pin_fresh(
            idx, intended="pin", kind="FRESH",
            run_id="not-a-run", event_id=_EVT)
        self.assertFalse(got.allowed)
        self.assertEqual(got.reason, "malformed_id")
        got2 = pin_fresh(
            idx, intended="pin", kind="FRESH",
            run_id=_RUN, event_id="evt-short")
        self.assertEqual(got2.reason, "malformed_id")

    def test_sealed_names_refuse(self):
        idx = FreshIndex()
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
        ):
            with self.subTest(name=name):
                got = pin_fresh(
                    idx, intended="pin", kind=name, run_id=_RUN, event_id=_EVT)
                self.assertFalse(got.allowed)
                self.assertEqual(got.reason, "sealed_effect")
                self.assertEqual(len(idx), 0)

    def test_unknown_intent_fail_closed(self):
        idx = FreshIndex()
        with self.assertRaises(FailClosedError):
            pin_fresh(
                idx, intended="consume", kind="FRESH",
                run_id=_RUN, event_id=_EVT)

    def test_unknown_kind_fail_closed(self):
        idx = FreshIndex()
        with self.assertRaises(FailClosedError):
            pin_fresh(
                idx, intended="pin", kind="WARM",
                run_id=_RUN, event_id=_EVT)

    def test_index_must_be_fresh_index(self):
        with self.assertRaises(FailClosedError):
            pin_fresh(
                {}, intended="pin", kind="FRESH",  # type: ignore[arg-type]
                run_id=_RUN, event_id=_EVT)

    def test_run_store_does_not_import(self):
        import ofn.adapters.run_store as store
        source = inspect.getsource(store)
        self.assertNotIn("fresh_pin", source)
        self.assertNotIn("stale_class", source)


if __name__ == "__main__":
    unittest.main()
