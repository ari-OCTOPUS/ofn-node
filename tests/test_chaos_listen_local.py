"""Owner-absent chaos for listen class + local pin.

Faults that must not flip UNKNOWN into a permission or a wildcard
into a local bind. HALT is not a parameter on classify/pin.
Send names stay sealed. Ready ≠ authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.listen_class import (
    admit_listen,
    classify_family,
    classify_timeout,
    grants_send as listen_grants_send,
    halt_blocks_classify,
    missing_lan_proves_absent,
    ready_is_authorized as listen_ready,
    timeout_proves_absent,
    timeout_proves_concurrent,
    unknown_is_false,
    wildcard_is_local,
)
from ofn.kernel.local_pin import (
    grants_send as pin_grants_send,
    halt_blocks_pin,
    pin_allows_bind,
    pin_family,
    ready_is_authorized as pin_ready,
    timeout_proves_absent as pin_timeout_absent,
    wildcard_is_local as pin_wildcard_local,
)


class ChaosUnknownStaysUnknown(unittest.TestCase):
    def test_timeout_under_pressure_to_call_it_a_race(self):
        d = admit_listen(
            intended="bind", address="127.0.0.1",
            timed_out=True, lan_probe="open")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(d.allowed)
        self.assertFalse(timeout_proves_concurrent())
        self.assertFalse(timeout_proves_absent())
        self.assertEqual(classify_timeout(), "UNKNOWN")
        self.assertFalse(unknown_is_false())
        self.assertFalse(d.grants_send)

    def test_closed_lan_under_pressure_to_call_loopback_absent(self):
        d = admit_listen(
            intended="observe", address="10.0.0.8", lan_probe="closed")
        self.assertEqual(d.family, "lan")
        self.assertFalse(missing_lan_proves_absent())
        loop = admit_listen(
            intended="bind", address="127.0.0.1", lan_probe="closed")
        self.assertTrue(loop.allowed)
        self.assertFalse(missing_lan_proves_absent())

    def test_unknown_family_cannot_be_pinned_local(self):
        p = pin_family(family="unknown")
        self.assertEqual(p.verdict, "unknown")
        self.assertFalse(pin_allows_bind(p))
        self.assertFalse(p.grants_send)


class ChaosHaltAndSend(unittest.TestCase):
    def test_halt_is_not_a_parameter_on_classify_or_pin(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_pin())
        for fn in (admit_listen, classify_family, pin_family):
            params = inspect.signature(fn).parameters
            self.assertNotIn("halt", params)
            self.assertNotIn("halt_raw", params)

    def test_neither_entry_grants_send(self):
        self.assertFalse(listen_grants_send())
        self.assertFalse(pin_grants_send())
        d = admit_listen(
            intended="bind", address="127.0.0.1", lan_probe="open")
        p = pin_family(family="loopback")
        self.assertFalse(d.grants_send)
        self.assertFalse(p.grants_send)

    def test_ready_is_not_authorized_on_either_module(self):
        self.assertFalse(listen_ready())
        self.assertFalse(pin_ready())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_sealed_names_stay_sealed_under_chaos(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                d = admit_listen(
                    intended="bind", address=name, lan_probe="open")
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.allowed)
                with self.assertRaises(FailClosedError):
                    classify_family(name)
                with self.assertRaises(FailClosedError):
                    pin_family(family=name)

    def test_wildcard_cannot_be_argued_local_under_chaos(self):
        d = admit_listen(
            intended="bind", address="0.0.0.0", lan_probe="open")
        self.assertEqual(d.reason, "sealed_wildcard")
        self.assertFalse(wildcard_is_local())
        self.assertFalse(pin_wildcard_local())
        p = pin_family(family="wildcard")
        self.assertFalse(pin_allows_bind(p))
        self.assertFalse(d.grants_send)

    def test_halt_does_not_stop_naming_a_wildcard(self):
        d = admit_listen(
            intended="classify", address="0.0.0.0",
            halted=True, lan_probe="timeout")
        self.assertTrue(d.allowed)
        self.assertEqual(d.family, "wildcard")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(pin_timeout_absent())
        self.assertFalse(d.grants_send)


if __name__ == "__main__":
    unittest.main()
