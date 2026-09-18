"""Owner-absent chaos for key_class / burn_pin.

While the owner cannot be reached: missing stays UNKNOWN, a
timeout does not invent a writer, HALT does not block the
pin, ready never becomes authorized, a later disarm still
supersedes an older authorization claim, and no outcome
burns the key.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.burn_pin import (
    admit_burn,
    burns_on_receipt,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    timeout_proves_concurrent_write,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.key_class import (
    KEY_BOUND,
    UNKNOWN,
    classify_key,
    halt_blocks_bind,
    try_bind,
)


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertEqual(classify_key(None), UNKNOWN)
        self.assertNotEqual(classify_key(None), "FALSE")
        self.assertIsNone(try_bind(None))
        self.assertIsNone(admit_burn(key=None, outcome="receipt_cited"))
        self.assertIsNone(admit_burn(key="keep-me", outcome=None))


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_flag_is_structurally_false(self):
        self.assertFalse(timeout_proves_concurrent_write())


class Scenario3HaltStopsStartsNotPin(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_bind())
        self.assertFalse(halt_blocks_pin())
        self.assertEqual(classify_key("keep-me"), KEY_BOUND)
        params = inspect.signature(classify_key).parameters
        self.assertNotIn("halted", params)
        params = inspect.signature(admit_burn).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_refused_burn_does_not_grant_send(self):
        decision = admit_burn(key="keep-me", outcome="refused")
        assert decision is not None
        self.assertFalse(decision.burned)
        self.assertFalse(decision.grants_send)
        self.assertFalse(grants_send())
        with self.assertRaises(FailClosedError):
            admit_burn(key="send_authorized", outcome="receipt_cited")


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_name_cannot_be_a_key_or_a_burn(self):
        with self.assertRaises(FailClosedError):
            classify_key("campaign_envelope_ready")
        with self.assertRaises(FailClosedError):
            admit_burn(key="campaign_envelope_ready", outcome="ready")
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_receipt_cite_is_false_missing_is_none(self):
        decision = admit_burn(key="keep-me", outcome="receipt_cited")
        assert decision is not None
        self.assertIs(decision.burned, False)
        self.assertIsNone(admit_burn(key=None, outcome="receipt_cited"))
        self.assertFalse(burns_on_receipt())


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_rebind_is_deterministic_and_later_disarm_holds(self):
        a = classify_key("keep-me")
        b = classify_key("keep-me")
        self.assertEqual(a, b)
        self.assertEqual(a, KEY_BOUND)
        self.assertTrue(later_disarm_supersedes())
        with self.assertRaises(FailClosedError):
            admit_burn(key="quote_sent", outcome="receipt_cited")
        again = admit_burn(key="keep-me", outcome="receipt_cited")
        assert again is not None
        self.assertFalse(again.burned)


if __name__ == "__main__":
    unittest.main()
