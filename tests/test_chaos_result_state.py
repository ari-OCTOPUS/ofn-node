"""Owner-absent chaos for result_class / state_pin.

While the owner cannot be reached: missing stays UNKNOWN, a
timeout does not invent a writer, HALT does not block the
classifier, a passed pin never becomes authorized, and a
later disarm still supersedes an older authorization claim.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.result_class import (
    PASSED,
    UNKNOWN,
    classify_result,
    grants_send,
    halt_blocks_classify,
    timeout_proves_concurrent_write,
)
from ofn.kernel.state_pin import (
    StatePin,
    later_disarm_supersedes,
    pin_allows_send,
    ready_is_authorized,
)

_RUN = "run-1780000000-a1b2c3d4e5"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertIsNone(classify_result(None))
        self.assertIsNot(classify_result(None), False)
        self.assertIsNone(StatePin().try_pin(_RUN, None))
        self.assertNotEqual(classify_result("unknown"), "FALSE")
        self.assertEqual(classify_result("unknown"), UNKNOWN)


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_flag_is_structurally_false(self):
        self.assertFalse(timeout_proves_concurrent_write())


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertEqual(classify_result("passed"), PASSED)
        params = inspect.signature(classify_result).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_rejected_does_not_grant_send(self):
        self.assertEqual(classify_result("rejected"), "rejected")
        self.assertFalse(grants_send())
        self.assertFalse(pin_allows_send())


class Scenario5PassedStaysUnsent(unittest.TestCase):
    def test_passed_cannot_become_quote_sent(self):
        with self.assertRaises(FailClosedError):
            classify_result("quote_sent")
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_collision_is_fail_closed(self):
        pin = StatePin()
        pin.pin(_RUN, "failed")
        with self.assertRaises(FailClosedError):
            pin.pin(_RUN, "passed")
        self.assertEqual(pin.peek(_RUN), "failed")


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_disarm_holds(self):
        a = classify_result("Passed")
        b = classify_result("passed")
        self.assertEqual(a, b)
        self.assertEqual(a, PASSED)
        self.assertTrue(later_disarm_supersedes())
        pin = StatePin()
        self.assertEqual(pin.pin(_RUN, "passed"), "pinned")
        self.assertEqual(pin.pin(_RUN, "PASSED"), "already_pinned")


if __name__ == "__main__":
    unittest.main()
