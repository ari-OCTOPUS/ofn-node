"""Kernel-pure local pin — complementary to listen_class.

Wildcard and LAN stay foreign. Unknown stays unknown.
Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.local_pin import (
    PIN_VERDICTS,
    LocalPin,
    grants_send,
    halt_blocks_pin,
    lan_is_local,
    missing_lan_proves_absent,
    missing_probe_inference,
    pin_allows_bind,
    pin_family,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    claims_immutable,
    timeout_proves_absent,
    timeout_proves_concurrent,
    unknown_family_is_local,
    wildcard_is_local,
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

    def test_wildcard_and_lan_and_unknown_are_not_local(self):
        self.assertFalse(wildcard_is_local())
        self.assertFalse(lan_is_local())
        self.assertFalse(unknown_family_is_local())

    def test_timeout_and_missing_lan_do_not_prove(self):
        self.assertFalse(timeout_proves_absent())
        self.assertFalse(timeout_proves_concurrent())
        self.assertFalse(missing_lan_proves_absent())
        self.assertIsNone(missing_probe_inference())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())
        self.assertFalse(promotes_ready_to_send())
        self.assertFalse(wires_into_run_store())

    def test_closed_vocabulary(self):
        self.assertEqual(PIN_VERDICTS, {"local", "foreign", "unknown"})

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(pin_family).parameters
        self.assertEqual(list(params), ["family"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            LocalPin(
                verdict="local", family="loopback",
                local=True, grants_send=True)

    def test_constructor_refuses_local_without_loopback(self):
        with self.assertRaises(FailClosedError):
            LocalPin(verdict="local", family="wildcard", local=True)

    def test_constructor_refuses_foreign_claiming_local(self):
        with self.assertRaises(FailClosedError):
            LocalPin(verdict="foreign", family="lan", local=True)

    def test_constructor_refuses_unknown_on_loopback(self):
        with self.assertRaises(FailClosedError):
            LocalPin(verdict="unknown", family="loopback", local=False)

    def test_constructor_refuses_foreign_verdict(self):
        with self.assertRaises(FailClosedError):
            LocalPin(verdict="ok", family="loopback", local=True)


class PinPrecedence(unittest.TestCase):
    def test_loopback_is_local_and_allows_bind(self):
        p = pin_family(family="loopback")
        self.assertEqual(p.verdict, "local")
        self.assertTrue(p.local)
        self.assertTrue(pin_allows_bind(p))
        self.assertFalse(p.grants_send)

    def test_wildcard_is_foreign_and_refuses_bind(self):
        p = pin_family(family="wildcard")
        self.assertEqual(p.verdict, "foreign")
        self.assertFalse(p.local)
        self.assertFalse(pin_allows_bind(p))
        self.assertFalse(wildcard_is_local())

    def test_lan_is_foreign_and_refuses_bind(self):
        p = pin_family(family="lan")
        self.assertEqual(p.verdict, "foreign")
        self.assertFalse(pin_allows_bind(p))
        self.assertFalse(lan_is_local())

    def test_unknown_is_unknown_and_refuses_bind(self):
        p = pin_family(family="unknown")
        self.assertEqual(p.verdict, "unknown")
        self.assertFalse(p.local)
        self.assertFalse(pin_allows_bind(p))
        self.assertFalse(unknown_family_is_local())


class FailClosedInputs(unittest.TestCase):
    def test_missing_family_is_unknown_not_loopback(self):
        with self.assertRaises(FailClosedError):
            pin_family(family=None)

    def test_string_bool_family_refuses(self):
        with self.assertRaises(FailClosedError):
            pin_family(family=True)
        with self.assertRaises(FailClosedError):
            pin_family(family="")

    def test_foreign_family_name_refuses(self):
        with self.assertRaises(FailClosedError):
            pin_family(family="ok")

    def test_sealed_family_refuses(self):
        with self.assertRaises(FailClosedError):
            pin_family(family="send_authorized")
        with self.assertRaises(FailClosedError):
            pin_family(family="campaign_envelope_ready")

    def test_pin_allows_bind_rejects_foreign_object(self):
        with self.assertRaises(FailClosedError):
            pin_allows_bind("loopback")


if __name__ == "__main__":
    unittest.main()
