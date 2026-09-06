"""Owner-absent chaos for lease_class / renew_pin.

While the owner cannot be reached: missing stays UNKNOWN, a
timeout does not invent a writer, HALT does not block inspect
or expire, ready never becomes authorized, a later disarm still
supersedes, and a live renew never grants a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.lease_class import (
    LEASE_ADMIT,
    LEASE_EXPIRE,
    LEASE_INSPECT,
    LEASE_RENEW,
    UNKNOWN as LEASE_UNKNOWN,
    admit_send,
    classify_lease,
    grants_send as lease_grants,
    halt_blocks_classify,
    halt_blocks_expire,
    halt_blocks_inspect,
    later_disarm_supersedes as lease_later,
    may_proceed,
    rearms_send as lease_rearms,
    timeout_proves_concurrent_write as lease_timeout,
    try_pin as try_lease,
)
from ofn.kernel.renew_pin import (
    LEASE_EXPIRED,
    LEASE_LIVE,
    UNKNOWN as WIN_UNKNOWN,
    classify_window,
    grants_send as renew_grants,
    halt_blocks_pin,
    later_disarm_supersedes as renew_later,
    peek_window,
    pin_renew,
    rearms_send as renew_rearms,
    try_pin as try_renew,
)

_LEASE = "lse-0123456789abcdef"
_RUN = "run-1780000000-leaseaaaaaa"
_RUN_B = "run-1780000000-leasebbbbbb"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertEqual(classify_lease(None, _RUN, "admit"), LEASE_UNKNOWN)
        self.assertNotEqual(classify_lease(None, _RUN, "admit"), "FALSE")
        self.assertEqual(classify_window(None, 10), WIN_UNKNOWN)
        self.assertNotEqual(classify_window(None, 10), LEASE_EXPIRED)
        self.assertIsNone(try_lease(None, _RUN, "admit"))
        self.assertIsNone(try_renew(_LEASE, _RUN, None, 10))
        self.assertIsNone(admit_send(None))


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_flag_is_structurally_false(self):
        self.assertFalse(lease_timeout())


class Scenario3HaltStopsStartsNotInspect(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_inspect_continues(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_inspect())
        self.assertFalse(halt_blocks_expire())
        self.assertFalse(halt_blocks_pin())
        self.assertEqual(classify_lease(_LEASE, _RUN, "inspect"), LEASE_INSPECT)
        self.assertEqual(classify_lease(_LEASE, _RUN, "expire"), LEASE_EXPIRE)
        self.assertIs(may_proceed(LEASE_INSPECT, True), True)
        self.assertIs(may_proceed(LEASE_ADMIT, True), False)
        self.assertIs(may_proceed(LEASE_RENEW, True), False)
        params = inspect.signature(classify_lease).parameters
        self.assertNotIn("halted", params)
        params_w = inspect.signature(classify_window).parameters
        self.assertNotIn("halted", params_w)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_live_and_expired_do_not_grant_send(self):
        self.assertEqual(classify_window(20, 10), LEASE_LIVE)
        self.assertEqual(classify_window(10, 20), LEASE_EXPIRED)
        self.assertFalse(lease_grants())
        self.assertFalse(renew_grants())
        self.assertIs(admit_send(LEASE_RENEW), False)
        self.assertIs(admit_send(LEASE_ADMIT), False)
        with self.assertRaises(FailClosedError):
            classify_lease(_LEASE, _RUN, "steal")


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_be_a_lease_or_epoch(self):
        with self.assertRaises(FailClosedError):
            classify_lease("campaign_envelope_ready", _RUN, "admit")
        with self.assertRaises(FailClosedError):
            classify_window("campaign_envelope_ready", 10)
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertFalse(lease_rearms())
        self.assertFalse(renew_rearms())


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_live_expired_missing_and_collision(self):
        self.assertEqual(classify_window(20, 10), LEASE_LIVE)
        self.assertEqual(classify_window(10, 20), LEASE_EXPIRED)
        self.assertEqual(peek_window(None, 10), WIN_UNKNOWN)
        self.assertEqual(classify_lease(_LEASE, _RUN, "renew"), LEASE_RENEW)
        with self.assertRaises(FailClosedError):
            pin_renew(_LEASE, _RUN, 20, 10, prior_renew=True)
        with self.assertRaises(FailClosedError):
            pin_renew(_LEASE, _RUN, 20, 10, bound_run_id=_RUN_B)


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_disarm_holds(self):
        a = classify_lease(_LEASE, _RUN, "renew")
        b = classify_lease(_LEASE, _RUN, "renew")
        self.assertEqual(a, b)
        self.assertEqual(a, LEASE_RENEW)
        self.assertEqual(classify_window(20, 10), classify_window(20, 10))
        self.assertTrue(lease_later())
        self.assertTrue(renew_later())
        pinned = pin_renew(_LEASE, _RUN, 20, 10)
        self.assertEqual(pinned.window_class, LEASE_LIVE)
        with self.assertRaises(FailClosedError):
            classify_lease(_LEASE, _RUN, "send_authorized")


if __name__ == "__main__":
    unittest.main()
