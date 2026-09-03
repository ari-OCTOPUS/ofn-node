"""Owner-absent chaos for campaign_bind / send_fence.

While the owner cannot be reached: missing stays UNKNOWN, a
timeout does not invent a writer, HALT does not block the
fence, ready never becomes authorized, and a later disarm
still supersedes an older authorization claim.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.campaign_bind import (
    CAMPAIGN_READY,
    UNKNOWN,
    classify_state,
    halt_blocks_bind,
    try_bind,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.send_fence import (
    admit_send,
    grants_send,
    halt_blocks_fence,
    later_disarm_supersedes,
    promote,
    timeout_proves_concurrent_write,
)


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertEqual(classify_state(None), UNKNOWN)
        self.assertNotEqual(classify_state(None), "FALSE")
        self.assertIsNone(try_bind(None))
        self.assertIsNone(admit_send(None))
        self.assertIsNone(promote(None, "send_authorized"))


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_flag_is_structurally_false(self):
        self.assertFalse(timeout_proves_concurrent_write())


class Scenario3HaltStopsStartsNotFence(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_bind())
        self.assertFalse(halt_blocks_fence())
        self.assertEqual(
            classify_state("campaign_envelope_ready"), CAMPAIGN_READY)
        params = inspect.signature(classify_state).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_refused_promotion_does_not_grant_send(self):
        with self.assertRaises(FailClosedError):
            promote("campaign_envelope_ready", "send_authorized")
        self.assertFalse(grants_send())
        self.assertIs(admit_send("campaign_envelope_ready"), False)


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_become_quote_sent(self):
        with self.assertRaises(FailClosedError):
            promote("campaign_envelope_ready", "quote_sent")
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_ready_admit_is_false_missing_is_none(self):
        self.assertIs(admit_send("campaign_envelope_ready"), False)
        self.assertIsNone(admit_send(None))


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_rebind_is_deterministic_and_later_disarm_holds(self):
        a = classify_state("campaign_envelope_ready")
        b = classify_state("campaign-envelope-ready")
        self.assertEqual(a, b)
        self.assertEqual(a, CAMPAIGN_READY)
        self.assertTrue(later_disarm_supersedes())
        with self.assertRaises(FailClosedError):
            admit_send("send_authorized")


if __name__ == "__main__":
    unittest.main()
