"""Owner-absent chaos for kind_class / role_pin.

While the owner cannot be reached: missing stays UNKNOWN, a
timeout does not invent a writer, HALT does not block the
classifier, a start pin never becomes authorized, and a
later disarm still supersedes an older authorization claim.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import (
    BUDGET_DEBIT,
    CLAIM_CREATED,
    PROPOSAL_CREATED,
    RUN_CLOSED,
    RUN_CREATED,
)
from ofn.kernel.halt import is_halted
from ofn.kernel.kind_class import (
    START,
    classify_role,
    grants_send,
    halt_blocks_classify,
    timeout_proves_concurrent_write,
)
from ofn.kernel.role_pin import (
    RolePin,
    later_disarm_supersedes,
    pin_allows_send,
    ready_is_authorized,
)

_RUN = "run-1780000000-a1b2c3d4e5"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertIsNone(classify_role(None))
        self.assertIsNot(classify_role(None), False)
        self.assertIsNone(RolePin().try_pin(_RUN, None))


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_is_unknown(self):
        self.assertIsNone(classify_role(RUN_CREATED, timeout=True))
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertIsNone(RolePin().try_pin(_RUN, RUN_CREATED, timeout=True))


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertEqual(classify_role(RUN_CREATED), START)
        params = inspect.signature(classify_role).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_reject_and_close_do_not_grant_send(self):
        self.assertEqual(classify_role(RUN_CLOSED), "close")
        self.assertFalse(grants_send())
        self.assertFalse(pin_allows_send())


class Scenario5StartStaysUnsent(unittest.TestCase):
    def test_start_cannot_become_quote_sent(self):
        with self.assertRaises(FailClosedError):
            classify_role("quote_sent")
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_second_start_and_after_close_are_fail_closed(self):
        pin = RolePin()
        pin.pin(_RUN, RUN_CREATED)
        with self.assertRaises(FailClosedError):
            pin.pin(_RUN, RUN_CREATED)
        self.assertEqual(pin.peek(_RUN), START)
        pin.pin(_RUN, RUN_CLOSED)
        with self.assertRaises(FailClosedError):
            pin.pin(_RUN, CLAIM_CREATED)


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_disarm_holds(self):
        a = classify_role(PROPOSAL_CREATED)
        b = classify_role(PROPOSAL_CREATED)
        self.assertEqual(a, b)
        self.assertEqual(a, "proposal")
        self.assertTrue(later_disarm_supersedes())
        pin = RolePin()
        self.assertEqual(pin.pin(_RUN, CLAIM_CREATED), "pinned")
        self.assertEqual(pin.pin(_RUN, CLAIM_CREATED), "already_pinned")
        self.assertEqual(pin.pin(_RUN, BUDGET_DEBIT), "pinned")
        with self.assertRaises(FailClosedError):
            pin.pin(_RUN, BUDGET_DEBIT)


if __name__ == "__main__":
    unittest.main()
