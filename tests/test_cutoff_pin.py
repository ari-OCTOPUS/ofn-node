"""Kernel-pure cutoff pin — complementary to deadline_window / horizon_class.

A cutoff is cited by name + exact-int epoch. Optional now classifies
position. Equal is at_pin / UNKNOWN, not closed-as-False. Ready is
not authorized. Distinct from clock_bind and deadline_window.
Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.cutoff_pin import (
    CUTOFF_NAMES,
    POSITIONS,
    CutoffPin,
    claims_immutable,
    classify_position,
    copies_clock_bind,
    copies_deadline_window,
    copies_horizon_class,
    equal_is_closed,
    grants_send,
    halt_blocks_pin,
    pin_cutoff,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent,
    unknown_epoch_is_zero,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.deadline_window import window_open
from ofn.kernel.errors import FailClosedError


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

    def test_does_not_copy_neighbors(self):
        self.assertFalse(copies_deadline_window())
        self.assertFalse(copies_horizon_class())
        self.assertFalse(copies_clock_bind())

    def test_equal_is_not_closed(self):
        self.assertFalse(equal_is_closed())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_unknown_epoch_is_not_zero(self):
        self.assertFalse(unknown_epoch_is_zero())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_signature_has_no_send_halt_or_immutable_knob(self):
        params = inspect.signature(pin_cutoff).parameters
        self.assertEqual(list(params), ["cutoff", "epoch_s", "now_epoch_s"])
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt",
            "halt_raw",
            "immutable",
        ):
            self.assertNotIn(forbidden, params)

    def test_closed_vocabularies(self):
        self.assertEqual(
            CUTOFF_NAMES,
            frozenset({
                "mint_cutoff", "validate_cutoff", "replay_cutoff",
                "store_cutoff", "receipt_cutoff",
            }),
        )
        self.assertEqual(
            POSITIONS, frozenset({"before", "at_pin", "after", "unknown"}))


class ConstructorGuards(unittest.TestCase):
    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            CutoffPin(
                cutoff="mint_cutoff", epoch_s=10, now_epoch_s=9,
                position="before", grants_send=True)

    def test_mismatched_position_fails_closed(self):
        with self.assertRaises(FailClosedError):
            CutoffPin(
                cutoff="mint_cutoff", epoch_s=10, now_epoch_s=9,
                position="after")

    def test_pin_is_not_independently_verified(self):
        p = pin_cutoff(cutoff="mint_cutoff", epoch_s=10, now_epoch_s=9)
        self.assertFalse(p.independently_verified())
        self.assertFalse(p.grants_send)


class PositionRules(unittest.TestCase):
    def test_before_strictly_earlier(self):
        p = pin_cutoff(cutoff="validate_cutoff", epoch_s=20, now_epoch_s=19)
        self.assertEqual(p.position, "before")
        self.assertEqual(
            classify_position(now_epoch_s=19, cutoff_epoch_s=20), "before")

    def test_at_pin_on_equal(self):
        p = pin_cutoff(cutoff="replay_cutoff", epoch_s=20, now_epoch_s=20)
        self.assertEqual(p.position, "at_pin")
        self.assertFalse(p.grants_send)

    def test_after_strictly_later(self):
        p = pin_cutoff(cutoff="store_cutoff", epoch_s=20, now_epoch_s=21)
        self.assertEqual(p.position, "after")

    def test_missing_now_is_unknown_not_zero(self):
        p = pin_cutoff(cutoff="receipt_cutoff", epoch_s=20)
        self.assertEqual(p.position, "unknown")
        self.assertTrue(p.now_is_unknown())
        zero = pin_cutoff(cutoff="receipt_cutoff", epoch_s=20, now_epoch_s=0)
        self.assertEqual(zero.position, "before")
        self.assertFalse(zero.now_is_unknown())

    def test_zero_cutoff_is_a_measurement(self):
        p = pin_cutoff(cutoff="mint_cutoff", epoch_s=0, now_epoch_s=0)
        self.assertEqual(p.position, "at_pin")
        self.assertEqual(p.epoch_s, 0)

    def test_equal_is_unknown_not_deadline_closed(self):
        self.assertFalse(window_open(20, 20))
        self.assertEqual(
            classify_position(now_epoch_s=20, cutoff_epoch_s=20), "at_pin")
        self.assertFalse(equal_is_closed())


class FailClosedInputs(unittest.TestCase):
    def test_unknown_cutoff_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_cutoff(cutoff="DEAD_SOURCE", epoch_s=10)
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_sealed_cutoff_fails_closed(self):
        for name in (
            "send_authorized", "quote_sent", "campaign_envelope_ready",
            "send-authorized",
        ):
            with self.assertRaises(FailClosedError):
                pin_cutoff(cutoff=name, epoch_s=10)

    def test_bool_epoch_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_cutoff(cutoff="mint_cutoff", epoch_s=True)
        with self.assertRaises(FailClosedError):
            pin_cutoff(cutoff="mint_cutoff", epoch_s=10, now_epoch_s=True)

    def test_str_float_epoch_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_cutoff(cutoff="mint_cutoff", epoch_s="10")
        with self.assertRaises(FailClosedError):
            pin_cutoff(cutoff="mint_cutoff", epoch_s=10, now_epoch_s=10.0)

    def test_none_cutoff_epoch_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_cutoff(cutoff="mint_cutoff", epoch_s=None)

    def test_empty_name_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_cutoff(cutoff="", epoch_s=10)
        with self.assertRaises(FailClosedError):
            pin_cutoff(cutoff="  ", epoch_s=10)

    def test_ready_and_authorized_are_distinct_sealed(self):
        with self.assertRaises(FailClosedError):
            pin_cutoff(cutoff="campaign_envelope_ready", epoch_s=10)
        with self.assertRaises(FailClosedError):
            pin_cutoff(cutoff="send_authorized", epoch_s=10)


if __name__ == "__main__":
    unittest.main()
