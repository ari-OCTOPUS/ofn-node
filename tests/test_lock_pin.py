"""Kernel-pure lock-pin — admit a freeze kind without rewriting.

LF_MATCH pins frozen_ok. CRLF_CHECKOUT is an artefact, not a
source edit. UNKNOWN stays unknown. MISMATCH fail-closes.
Ready is not authorized. The pin does not rewrite the lock.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.freeze_class import CRLF_CHECKOUT, LF_MATCH, UNKNOWN
from ofn.kernel.lock_pin import (
    LockPin,
    claims_immutable,
    crlf_is_source_edit,
    grants_send,
    halt_blocks_pin,
    pin_lock,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rewrites_lock,
    timeout_proves_concurrent_write,
    unknown_is_false,
    wires_into_run_store,
)


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

    def test_does_not_rewrite_lock(self):
        self.assertFalse(rewrites_lock())

    def test_crlf_is_not_a_source_edit(self):
        self.assertFalse(crlf_is_source_edit())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_does_not_wire_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_signature_has_no_send_halt_or_rewrite_knob(self):
        params = inspect.signature(pin_lock).parameters
        self.assertEqual(list(params), ["kind"])
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt",
            "immutable",
            "rewrite",
            "path",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            LockPin(
                kind=LF_MATCH, frozen_ok=True, artefact=False,
                unknown=False, grants_send=True)

    def test_constructor_refuses_mismatch(self):
        with self.assertRaises(FailClosedError):
            LockPin(
                kind="MISMATCH", frozen_ok=False, artefact=False,
                unknown=False)


class PinLock(unittest.TestCase):
    def test_lf_match_is_frozen_ok(self):
        pin = pin_lock(LF_MATCH)
        self.assertEqual(pin.kind, LF_MATCH)
        self.assertTrue(pin.frozen_ok)
        self.assertFalse(pin.artefact)
        self.assertFalse(pin.unknown)
        self.assertFalse(pin.grants_send)

    def test_crlf_is_artefact_not_frozen(self):
        pin = pin_lock(CRLF_CHECKOUT)
        self.assertEqual(pin.kind, CRLF_CHECKOUT)
        self.assertFalse(pin.frozen_ok)
        self.assertTrue(pin.artefact)
        self.assertFalse(pin.unknown)
        self.assertFalse(crlf_is_source_edit())

    def test_unknown_stays_unknown(self):
        pin = pin_lock(UNKNOWN)
        self.assertTrue(pin.unknown)
        self.assertFalse(pin.frozen_ok)
        self.assertNotEqual(pin.kind, "FALSE")

    def test_mismatch_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_lock("MISMATCH")
        self.assertIn("content edit", str(ctx.exception))
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_kind_is_folded(self):
        pin = pin_lock("lf-match")
        self.assertEqual(pin.kind, LF_MATCH)

    def test_unknown_kind_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_lock("THAW")
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_sealed_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_lock("send_authorized")

    def test_ready_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_lock("campaign_envelope_ready")

    def test_bool_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_lock(True)

    def test_missing_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_lock(None)
