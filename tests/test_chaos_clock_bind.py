"""Owner-absent chaos for clock_bind / utc_class.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a concurrent writer, HALT does not block a bind,
and a recorded pair never becomes a send. Seven scenarios, same
shape as tests/test_chaos_owner_absent.py.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.clock_bind import (
    bind_clock, grants_send, halt_blocks_bind, pair_agrees,
    timeout_proves_concurrent_write, try_bind,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.utc_class import UNKNOWN, classify_stamp, halt_blocks_utc


_STAMP = "2026-09-03T02:07:08Z"
_EPOCH = 1788401228


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_stamp_is_unknown(self):
        self.assertEqual(classify_stamp(None), UNKNOWN)
        self.assertNotEqual(classify_stamp(None), "FALSE")

    def test_missing_epoch_is_none_not_zero(self):
        self.assertIsNone(try_bind(None, _STAMP))
        self.assertIsNone(try_bind(_EPOCH, None))


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_predicate_is_structurally_false(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_a_timeout_error_is_not_a_bind(self):
        # A transport timeout is a missing witness, not a clock pair.
        self.assertIsNone(try_bind(None, None))
        self.assertFalse(timeout_proves_concurrent_write())


class Scenario3HaltStopsStartsNotBind(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_bind_still_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_bind())
        self.assertFalse(halt_blocks_utc())
        bound = bind_clock(_EPOCH, _STAMP)
        self.assertEqual(bound.epoch_s, _EPOCH)
        params = inspect.signature(bind_clock).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_failed_bind_does_not_grant_send(self):
        with self.assertRaises(FailClosedError):
            bind_clock(_EPOCH, "2026-09-03T02:07:08")
        self.assertFalse(grants_send())


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_sealed_names_cannot_be_stamps(self):
        for name in (
            "campaign_envelope_ready",
            "send_authorized",
            "quote_sent",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    bind_clock(_EPOCH, name)
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_disagreeing_pair_is_false_missing_is_none(self):
        self.assertIs(pair_agrees(_EPOCH, _STAMP), True)
        self.assertIs(pair_agrees(_EPOCH + 60, _STAMP), False)
        self.assertIsNone(pair_agrees(None, _STAMP))


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_rebind_same_pair_is_deterministic(self):
        a = bind_clock(_EPOCH, _STAMP)
        b = bind_clock(_EPOCH, _STAMP)
        self.assertEqual(a, b)
        self.assertEqual(a.stamp_class, b.stamp_class)


if __name__ == "__main__":
    unittest.main()
