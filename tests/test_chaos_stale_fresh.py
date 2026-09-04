"""Owner-absent chaos for stale_class / fresh_pin.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a concurrent writer, HALT blocks refresh but not
classify, a pin never becomes a send, and ready stays unsent.
Seven scenarios, same shape as tests/test_chaos_owner_absent.py.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.fresh_pin import (
    FreshIndex,
    grants_send as pin_grants_send,
    pin_fresh,
    timeout_proves_concurrent_write as pin_timeout,
)
from ofn.kernel.halt import is_halted
from ofn.kernel.stale_class import (
    FRESH,
    STALE,
    UNKNOWN,
    admit_refresh,
    classify_age,
    grants_send,
    halt_blocks_classify,
    halt_blocks_refresh,
    timeout_proves_concurrent_write,
)

_OBS = 1_780_000_000
_TTL = 60
_RUN = "run-1780000000-a1b2c3d4e5"
_EVT = "evt-0123456789abcdef"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_epoch_is_unknown(self):
        got = classify_age(ttl_s=_TTL)
        self.assertEqual(got.kind, UNKNOWN)
        self.assertNotEqual(got.kind, "FALSE")
        self.assertNotEqual(got.kind, STALE)


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_predicate_is_structurally_false(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertFalse(pin_timeout())

    def test_error_witness_is_unknown_not_stale(self):
        got = classify_age(
            observed_epoch_s=_OBS, as_of_epoch_s=_OBS + 10_000,
            ttl_s=_TTL, error=TimeoutError("socket dead"))
        self.assertEqual(got.kind, UNKNOWN)
        self.assertFalse(timeout_proves_concurrent_write())


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_still_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertTrue(halt_blocks_refresh())
        got = classify_age(
            observed_epoch_s=_OBS, as_of_epoch_s=_OBS, ttl_s=_TTL)
        self.assertEqual(got.kind, FRESH)
        params = inspect.signature(classify_age).parameters
        self.assertNotIn("halt", params)
        refused = admit_refresh(classified=got, halt="???")
        self.assertFalse(refused.allowed)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_failed_classify_does_not_grant_send(self):
        with self.assertRaises(FailClosedError):
            classify_age(
                observed_epoch_s=_OBS + 1, as_of_epoch_s=_OBS, ttl_s=_TTL)
        self.assertFalse(grants_send())
        self.assertFalse(pin_grants_send())


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_sealed_names_cannot_be_intents(self):
        for name in (
            "campaign_envelope_ready",
            "send_authorized",
            "quote_sent",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_age(
                        observed_epoch_s=_OBS, as_of_epoch_s=_OBS,
                        ttl_s=_TTL, intent=name)
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_fresh_and_stale_are_different_kinds(self):
        fresh = classify_age(
            observed_epoch_s=_OBS, as_of_epoch_s=_OBS, ttl_s=_TTL)
        stale = classify_age(
            observed_epoch_s=_OBS, as_of_epoch_s=_OBS + _TTL + 1, ttl_s=_TTL)
        self.assertEqual(fresh.kind, FRESH)
        self.assertEqual(stale.kind, STALE)
        self.assertNotEqual(fresh.kind, stale.kind)
        idx = FreshIndex()
        pin = pin_fresh(
            idx, intended="pin", kind=stale.kind, run_id=_RUN, event_id=_EVT)
        self.assertFalse(pin.allowed)
        self.assertEqual(pin.reason, "stale_not_fresh")


class Scenario7RecoveryIsReversible(unittest.TestCase):
    def test_peek_then_pin_is_deterministic(self):
        idx = FreshIndex()
        peek1 = pin_fresh(
            idx, intended="peek", kind="FRESH", run_id=_RUN, event_id=_EVT)
        peek2 = pin_fresh(
            idx, intended="peek", kind="FRESH", run_id=_RUN, event_id=_EVT)
        self.assertEqual(peek1.seen, peek2.seen)
        self.assertEqual(len(idx), 0)
        first = pin_fresh(
            idx, intended="pin", kind="FRESH", run_id=_RUN, event_id=_EVT)
        second = pin_fresh(
            idx, intended="pin", kind="FRESH", run_id=_RUN, event_id=_EVT)
        self.assertTrue(first.allowed)
        self.assertFalse(second.allowed)
        self.assertEqual(second.reason, "already_pinned")


if __name__ == "__main__":
    unittest.main()
