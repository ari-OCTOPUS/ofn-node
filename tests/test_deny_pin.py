"""Contract tests for deny_pin (P1 complementary).

A pin is DENIED or UNKNOWN. It never grants leave. Sealed
send/ready names refuse. Ready ≠ authorized. HALT does not
block a pin. Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.deny_pin import (
    DENIED,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    pin_allows_leave,
    pin_deny,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.egress_class import classify_dest
from ofn.kernel.errors import FailClosedError


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_pin_never_allows_leave(self):
        self.assertFalse(pin_allows_leave())

    def test_halt_does_not_block_pin(self):
        self.assertFalse(halt_blocks_pin())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertFalse(promotes_ready_to_send())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_timeout_does_not_prove_writer(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_later_disarm_supersedes(self):
        self.assertTrue(later_disarm_supersedes())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())
        import ofn.adapters.run_store as rs
        self.assertNotIn("deny_pin", inspect.getsource(rs))

    def test_signature_has_no_send_halt_or_resend(self):
        params = inspect.signature(pin_deny).parameters
        self.assertEqual(list(params), ["target"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt"):
            self.assertNotIn(forbidden, params)


class PinDeny(unittest.TestCase):
    def test_none_is_unknown_not_false(self):
        self.assertIsNone(pin_deny(None))
        self.assertIsNot(pin_deny(None), False)

    def test_outbox_and_loopback_are_denied(self):
        self.assertEqual(pin_deny("outbox"), DENIED)
        self.assertEqual(pin_deny("loopback"), DENIED)
        self.assertEqual(pin_deny(classify_dest("outbox")), DENIED)
        self.assertEqual(pin_deny(classify_dest("loopback")), DENIED)

    def test_unknown_class_is_none(self):
        self.assertIsNone(pin_deny(classify_dest(None)))
        self.assertIsNone(pin_deny("UNKNOWN"))

    def test_external_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_deny("external")

    def test_sealed_names_refuse(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    pin_deny(name)

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_deny(True)
        with self.assertRaises(FailClosedError):
            pin_deny(False)

    def test_timeout_class_stays_unknown(self):
        self.assertIsNone(pin_deny(classify_dest("outbox", kind="timeout")))


if __name__ == "__main__":
    unittest.main()
