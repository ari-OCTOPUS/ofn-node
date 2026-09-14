"""Kernel-pure host pin — bind a presence class to one node.

this_host_only stays this_host_only. system_wide refuses.
Missing is UNKNOWN. Sealed send/ready names refuse. Timeout is
UNKNOWN, not a concurrent-write proof. Ready is not authorized.
Does not invent a second node. Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.host_pin import (
    PIN_CLASSES,
    REFUSAL_REASONS,
    VANTAGES,
    HostPin,
    burns_idempotency_key,
    claims_immutable,
    classify_pin,
    classify_timeout,
    grants_send,
    halt_blocks_pin,
    invents_second_node,
    later_disarm_supersedes,
    pin_host,
    promotes_ready_to_send,
    promotes_to_system_wide,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

NODE_A = "node-a"
NODE_B = "node:b.1"


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

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent())
        self.assertEqual(classify_timeout(), "UNKNOWN")

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_does_not_promote_to_system_wide(self):
        self.assertFalse(promotes_to_system_wide())

    def test_does_not_burn_idempotency_key(self):
        self.assertFalse(burns_idempotency_key())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_does_not_invent_second_node(self):
        self.assertFalse(invents_second_node())

    def test_later_disarm_supersedes(self):
        self.assertTrue(later_disarm_supersedes())

    def test_pin_signature_has_no_halt_or_send(self):
        params = inspect.signature(pin_host).parameters
        for forbidden in (
            "halt",
            "halt_raw",
            "send_authorized",
            "quote_sent",
            "resend",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            HostPin(
                location="on_this_host", node_id=NODE_A,
                vantage="this_host_only", body_class="ON_THIS_HOST",
                pin_class="BOUND", allowed=True, reason=None,
                timed_out=False, grants_send=True)

    def test_closed_vocabularies(self):
        self.assertEqual(PIN_CLASSES, frozenset({"BOUND", "UNKNOWN"}))
        self.assertEqual(VANTAGES, frozenset({"this_host_only"}))
        self.assertEqual(
            REFUSAL_REASONS,
            frozenset({"sealed_effect", "missing_claim", "promotion_refused"}),
        )


class ClassifyAndPin(unittest.TestCase):
    def test_on_this_host_binds(self):
        p = pin_host("on_this_host", NODE_A)
        self.assertTrue(p.allowed)
        self.assertEqual(p.pin_class, "BOUND")
        self.assertEqual(p.body_class, "ON_THIS_HOST")
        self.assertEqual(p.vantage, "this_host_only")
        self.assertFalse(p.grants_send)
        self.assertEqual(classify_pin("on_this_host", NODE_A), "BOUND")

    def test_not_on_this_host_still_binds(self):
        p = pin_host("body_not_on_this_host", NODE_B)
        self.assertTrue(p.allowed)
        self.assertEqual(p.pin_class, "BOUND")
        self.assertEqual(p.body_class, "NOT_ON_THIS_HOST")
        self.assertFalse(p.grants_send)

    def test_missing_location_is_unknown(self):
        self.assertIsNone(classify_pin(None, NODE_A))
        p = pin_host(None, NODE_A)
        self.assertEqual(p.pin_class, "UNKNOWN")
        self.assertTrue(p.allowed)
        self.assertFalse(p.grants_send)

    def test_missing_node_is_unknown(self):
        self.assertIsNone(classify_pin("on_this_host", None))
        p = pin_host("on_this_host", None)
        self.assertEqual(p.pin_class, "UNKNOWN")
        self.assertTrue(p.allowed)
        self.assertIsNone(p.node_id)

    def test_try_pin_missing_is_none(self):
        self.assertIsNone(try_pin(None, NODE_A))
        self.assertIsNone(try_pin("on_this_host", None))
        bound = try_pin("on_this_host", NODE_A)
        self.assertIsNotNone(bound)
        self.assertEqual(bound.pin_class, "BOUND")

    def test_system_wide_is_promotion_refused(self):
        p = pin_host("on_this_host", NODE_A, vantage="system_wide")
        self.assertFalse(p.allowed)
        self.assertEqual(p.reason, "promotion_refused")
        self.assertEqual(p.pin_class, "UNKNOWN")
        self.assertFalse(p.grants_send)
        hyphen = pin_host("on_this_host", NODE_A, vantage="system-wide")
        self.assertEqual(hyphen.reason, "promotion_refused")

    def test_unknown_vantage_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_host("on_this_host", NODE_A, vantage="fleet")
        with self.assertRaises(FailClosedError):
            pin_host("on_this_host", NODE_A, vantage=1)  # type: ignore[arg-type]

    def test_sealed_location_refuses(self):
        p = pin_host("send_authorized", NODE_A)
        self.assertFalse(p.allowed)
        self.assertEqual(p.reason, "sealed_effect")
        self.assertFalse(p.grants_send)

    def test_sealed_node_refuses(self):
        p = pin_host("on_this_host", "quote_sent")
        self.assertFalse(p.allowed)
        self.assertEqual(p.reason, "sealed_effect")

    def test_body_missing_is_missing_claim(self):
        p = pin_host("body_missing", NODE_A)
        self.assertFalse(p.allowed)
        self.assertEqual(p.reason, "missing_claim")
        self.assertFalse(p.grants_send)

    def test_timeout_forces_unknown(self):
        p = pin_host("on_this_host", NODE_A, timed_out=True)
        self.assertEqual(p.pin_class, "UNKNOWN")
        self.assertEqual(p.body_class, "UNKNOWN")
        self.assertTrue(p.allowed)
        self.assertTrue(p.timed_out)
        self.assertFalse(p.grants_send)

    def test_timeout_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            pin_host("on_this_host", NODE_A, timed_out=1)  # type: ignore[arg-type]

    def test_bad_node_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_host("on_this_host", "")
        with self.assertRaises(FailClosedError):
            pin_host("on_this_host", "node a")
        with self.assertRaises(FailClosedError):
            pin_host("on_this_host", 12)  # type: ignore[arg-type]

    def test_bound_requires_both_sides(self):
        with self.assertRaises(FailClosedError):
            HostPin(
                location=None, node_id=NODE_A, vantage="this_host_only",
                body_class="ON_THIS_HOST", pin_class="BOUND",
                allowed=True, reason=None, timed_out=False)

    def test_timed_out_cannot_be_bound(self):
        with self.assertRaises(FailClosedError):
            HostPin(
                location="on_this_host", node_id=NODE_A,
                vantage="this_host_only", body_class="ON_THIS_HOST",
                pin_class="BOUND", allowed=True, reason=None, timed_out=True)

    def test_allowed_cannot_be_system_wide(self):
        with self.assertRaises(FailClosedError):
            HostPin(
                location="on_this_host", node_id=NODE_A,
                vantage="system_wide", body_class="ON_THIS_HOST",
                pin_class="BOUND", allowed=True, reason=None, timed_out=False)


if __name__ == "__main__":
    unittest.main()
