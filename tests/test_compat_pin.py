"""Kernel-pure compatibility pin — complementary to version_class.

A pin cites two schema versions. It does not admit a START,
does not rewrite supported version, and does not grant send.
UNKNOWN compatible is None, not False.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.compat_pin import (
    CompatPin,
    claims_immutable,
    copies_envelope_class,
    grants_send,
    halt_blocks_pin,
    pin_compat,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rewrites_supported_version,
    timeout_is_unknown,
    timeout_proves_concurrent,
    unknown_is_false,
    unknown_version_is_false,
    wires_into_run_store,
)
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

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_unknown_version_is_not_false(self):
        self.assertFalse(unknown_version_is_false())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent())
        self.assertEqual(timeout_is_unknown(), "UNKNOWN")

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_does_not_rewrite_supported_version(self):
        self.assertFalse(rewrites_supported_version())

    def test_does_not_copy_envelope_class(self):
        self.assertFalse(copies_envelope_class())

    def test_signature_has_no_send_or_resend_knob(self):
        params = inspect.signature(pin_compat).parameters
        self.assertEqual(list(params), ["left", "right", "timed_out"])
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt_raw",
            "immutable",
            "halted",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            CompatPin(
                left_class="SUPPORTED", right_class="SUPPORTED",
                compatible=True, timed_out=False, grants_send=True)


class PinCompatMeasurements(unittest.TestCase):
    def test_two_supported_are_compatible(self):
        p = pin_compat(left=1, right=1)
        self.assertTrue(p.compatible)
        self.assertEqual(p.left_class, "SUPPORTED")
        self.assertEqual(p.right_class, "SUPPORTED")
        self.assertFalse(p.grants_send)
        self.assertFalse(p.compatible_is_unknown())

    def test_missing_left_is_unknown_not_false(self):
        p = pin_compat(left=None, right=1)
        self.assertIsNone(p.compatible)
        self.assertTrue(p.compatible_is_unknown())
        self.assertEqual(p.left_class, "UNKNOWN")
        self.assertEqual(p.right_class, "SUPPORTED")
        self.assertFalse(p.grants_send)

    def test_missing_right_is_unknown_not_false(self):
        p = pin_compat(left=1, right=None)
        self.assertIsNone(p.compatible)
        self.assertTrue(p.compatible_is_unknown())

    def test_both_missing_is_unknown(self):
        p = pin_compat(left=None, right=None)
        self.assertIsNone(p.compatible)
        self.assertEqual(p.left_class, "UNKNOWN")
        self.assertEqual(p.right_class, "UNKNOWN")

    def test_unknown_version_is_not_compatible_and_not_false_claim(self):
        p = pin_compat(left=2, right=1)
        self.assertIs(p.compatible, False)
        self.assertEqual(p.left_class, "UNKNOWN_VERSION")
        self.assertEqual(p.right_class, "SUPPORTED")
        self.assertFalse(unknown_version_is_false())
        self.assertFalse(p.grants_send)

    def test_two_unknown_versions_do_not_invent_support(self):
        p = pin_compat(left=2, right=2)
        self.assertIs(p.compatible, False)
        self.assertEqual(p.left_class, "UNKNOWN_VERSION")
        self.assertEqual(p.right_class, "UNKNOWN_VERSION")

    def test_timeout_forces_unknown_compatible(self):
        p = pin_compat(left=1, right=1, timed_out=True)
        self.assertIsNone(p.compatible)
        self.assertTrue(p.compatible_is_unknown())
        self.assertEqual(p.left_class, "UNKNOWN")
        self.assertEqual(p.right_class, "UNKNOWN")
        self.assertTrue(p.timed_out)
        self.assertFalse(timeout_proves_concurrent())

    def test_timeout_on_unknown_version_is_still_unknown(self):
        p = pin_compat(left=2, right=1, timed_out=True)
        self.assertIsNone(p.compatible)
        self.assertNotEqual(p.left_class, "SUSPECTED")


class FailClosedShapes(unittest.TestCase):
    def test_bool_version_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_compat(left=True, right=1)
        with self.assertRaises(FailClosedError):
            pin_compat(left=1, right=False)

    def test_str_float_fail_closed(self):
        with self.assertRaises(FailClosedError):
            pin_compat(left="1", right=1)
        with self.assertRaises(FailClosedError):
            pin_compat(left=1, right=1.0)

    def test_sealed_left_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_compat(left="send_authorized", right=1)
        self.assertIn("sealed", str(ctx.exception).lower())

    def test_sealed_right_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_compat(left=1, right="campaign_envelope_ready")

    def test_quote_sent_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_compat(left="quote_sent", right="quote_sent")

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            pin_compat(left=1, right=1, timed_out=1)

    def test_constructor_refuses_unknown_treated_as_false(self):
        with self.assertRaises(FailClosedError):
            CompatPin(
                left_class="UNKNOWN", right_class="SUPPORTED",
                compatible=False, timed_out=False)

    def test_constructor_refuses_timeout_with_bool_compatible(self):
        with self.assertRaises(FailClosedError):
            CompatPin(
                left_class="UNKNOWN", right_class="UNKNOWN",
                compatible=False, timed_out=True)

    def test_constructor_refuses_unknown_version_as_compatible(self):
        with self.assertRaises(FailClosedError):
            CompatPin(
                left_class="UNKNOWN_VERSION", right_class="SUPPORTED",
                compatible=True, timed_out=False)


if __name__ == "__main__":
    unittest.main()
