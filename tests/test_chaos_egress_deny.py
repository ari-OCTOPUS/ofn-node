"""Owner-absent chaos for egress_class + deny_pin.

Faults that must not flip a destination class into a leave grant.
HALT stops STARTS only. Send names stay sealed. Ready ≠ authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.deny_pin import pin_allows_leave, pin_deny
from ofn.kernel.egress_class import (
    admit_leave,
    classify_dest,
    grants_send,
    halt_blocks_classify,
    later_disarm_supersedes,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    unknown_is_false,
)
from ofn.kernel.errors import FailClosedError


class ChaosUnknownStaysUnknown(unittest.TestCase):
    def test_timeout_under_pressure_to_call_it_a_write(self):
        d = classify_dest("outbox", kind="timeout")
        self.assertEqual(d.klass, "UNKNOWN")
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertIsNone(admit_leave("outbox", kind="timeout"))
        self.assertIsNone(pin_deny(d))

    def test_missing_dest_is_not_a_negative_finding(self):
        d = classify_dest(None)
        self.assertEqual(d.klass, "UNKNOWN")
        self.assertFalse(unknown_is_false())
        self.assertIsNone(admit_leave(None))

    def test_unknown_string_is_not_classified_false(self):
        with self.assertRaises(FailClosedError):
            classify_dest("webhook")


class ChaosHaltAndSend(unittest.TestCase):
    def test_classify_has_no_halt_knob(self):
        self.assertNotIn("halt", inspect.signature(classify_dest).parameters)
        self.assertFalse(halt_blocks_classify())

    def test_halt_refuses_leave_start_not_classify(self):
        d = classify_dest("outbox")
        self.assertEqual(d.klass, "OUTBOX")
        with self.assertRaises(FailClosedError):
            admit_leave("outbox", halt=True)
        self.assertEqual(pin_deny(d), "DENIED")

    def test_sealed_send_names_cannot_be_a_dest(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_dest(name)
                with self.assertRaises(FailClosedError):
                    admit_leave(name)
                with self.assertRaises(FailClosedError):
                    pin_deny(name)

    def test_ready_never_equals_authorized_after_chaos(self):
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertFalse(ready_is_authorized())
        self.assertFalse(grants_send())
        self.assertFalse(pin_allows_leave())

    def test_later_disarm_still_holds(self):
        self.assertTrue(later_disarm_supersedes())
        self.assertIs(admit_leave("outbox"), False)

    def test_payload_cannot_smuggle_a_send_under_halt_story(self):
        with self.assertRaises(FailClosedError):
            classify_dest("outbox", payload={"send_authorized": "held"})


class ChaosCoercion(unittest.TestCase):
    def test_bool_true_cannot_bypass_classify(self):
        with self.assertRaises(FailClosedError):
            classify_dest(True)
        with self.assertRaises(FailClosedError):
            admit_leave(True)
        with self.assertRaises(FailClosedError):
            pin_deny(True)


if __name__ == "__main__":
    unittest.main()
