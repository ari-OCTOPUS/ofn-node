"""Owner-absent chaos for later_hold / scoped_authz.

While the owner cannot be reached: missing stays UNKNOWN, a
timeout does not invent a writer, HALT does not block the
classify, ready never becomes authorized, a later hold still
supersedes an older claim, and scoped never grants a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.later_hold import (
    LATER_HOLD,
    UNKNOWN as HOLD_UNKNOWN,
    admit_send_after_hold,
    classify_hold,
    grants_send as hold_grants_send,
    halt_blocks_classify,
    later_supersedes_older,
    rearms_send as hold_rearms,
    supersedes,
    timeout_proves_concurrent_write as hold_timeout,
    try_pin as try_hold,
)
from ofn.kernel.scoped_authz import (
    AUTHZ_SCOPED,
    AUTHZ_STALE,
    UNKNOWN as AUTHZ_UNKNOWN,
    classify_authz,
    grants_send as authz_grants_send,
    halt_blocks_pin,
    later_hold_supersedes_older,
    pin_allows_effect,
    rearms_send as authz_rearms,
    try_pin as try_authz,
)


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertEqual(classify_hold(None, 10), HOLD_UNKNOWN)
        self.assertNotEqual(classify_hold(None, 10), "FALSE")
        self.assertEqual(classify_authz(None, 10, "lead"), AUTHZ_UNKNOWN)
        self.assertIsNone(try_hold(None, 10))
        self.assertIsNone(try_authz(20, 10, None))
        self.assertIsNone(admit_send_after_hold(None, 10))


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_flag_is_structurally_false(self):
        self.assertFalse(hold_timeout())


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_pin())
        self.assertEqual(classify_hold(20, 10), LATER_HOLD)
        params = inspect.signature(classify_hold).parameters
        self.assertNotIn("halted", params)
        params_a = inspect.signature(classify_authz).parameters
        self.assertNotIn("halted", params_a)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_stale_and_later_do_not_grant_send(self):
        self.assertEqual(classify_authz(10, 20, "lead"), AUTHZ_STALE)
        self.assertFalse(pin_allows_effect(AUTHZ_STALE))
        self.assertFalse(pin_allows_effect(AUTHZ_SCOPED))
        self.assertFalse(hold_grants_send())
        self.assertFalse(authz_grants_send())
        self.assertIs(admit_send_after_hold(20, 10), False)


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_be_an_epoch_or_scope(self):
        with self.assertRaises(FailClosedError):
            classify_hold("campaign_envelope_ready", 10)
        with self.assertRaises(FailClosedError):
            classify_authz(20, 10, "campaign_envelope_ready")
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertFalse(hold_rearms())
        self.assertFalse(authz_rearms())


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_later_true_older_false_missing_none(self):
        self.assertIs(supersedes(20, 10), True)
        self.assertIs(supersedes(10, 20), False)
        self.assertIsNone(supersedes(None, 10))
        self.assertEqual(classify_authz(20, 10, "lead"), AUTHZ_SCOPED)
        self.assertEqual(classify_authz(10, 20, "lead"), AUTHZ_STALE)


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_hold_holds(self):
        a = classify_hold(20, 10)
        b = classify_hold(20, 10)
        self.assertEqual(a, b)
        self.assertEqual(a, LATER_HOLD)
        self.assertTrue(later_supersedes_older())
        self.assertTrue(later_hold_supersedes_older())
        self.assertFalse(pin_allows_effect(AUTHZ_SCOPED))
        with self.assertRaises(FailClosedError):
            classify_authz(20, 10, "send_authorized")


if __name__ == "__main__":
    unittest.main()
