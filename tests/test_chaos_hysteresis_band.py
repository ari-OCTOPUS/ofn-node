"""Owner-absent chaos for hysteresis_class / band_pin.

While the owner cannot be reached: missing stays UNKNOWN, a
timeout does not invent a writer, HALT does not block the
classify, ready never becomes authorized, a later hold still
supersedes an older claim, and a latched band never grants
a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.band_pin import (
    PINNED,
    grants_send as pin_grants_send,
    halt_blocks_pin,
    peek_pin,
    pin_allows_send,
    pin_band,
    rearms_send as pin_rearms,
    retcon_refused,
    timeout_proves_concurrent_write as pin_timeout,
    try_latch,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.hysteresis_class import (
    FALL,
    HIGH,
    HOLD,
    LOW,
    RISE,
    UNKNOWN,
    admit_send_after_edge,
    classify_edge,
    classify_timeout,
    grants_send as edge_grants_send,
    halt_blocks_classify,
    later_hold_supersedes_older,
    rearms_send as edge_rearms,
    timeout_proves_concurrent_write as edge_timeout,
    try_pin,
)


_RUN = "run-1780000000-abcdefghij"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertEqual(classify_edge(None, 10, 0, 10), UNKNOWN)
        self.assertNotEqual(classify_edge(None, 10, 0, 10), "FALSE")
        self.assertIsNone(try_pin(None, 10, 0, 10))
        self.assertIsNone(try_latch(None, 10, 0, 10))
        self.assertIsNone(peek_pin({}, _RUN))
        self.assertIsNone(admit_send_after_edge(None, 10, 0, 10))


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_flag_is_structurally_false(self):
        self.assertEqual(classify_timeout(), UNKNOWN)
        self.assertFalse(edge_timeout())
        self.assertFalse(pin_timeout())


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_pin())
        self.assertEqual(classify_edge(LOW, 10, 0, 10), RISE)
        params = inspect.signature(classify_edge).parameters
        self.assertNotIn("halted", params)
        pin_params = inspect.signature(pin_band).parameters
        self.assertNotIn("halted", pin_params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_hold_and_edge_do_not_grant_send(self):
        self.assertEqual(classify_edge(HIGH, 5, 0, 10), HOLD)
        self.assertFalse(pin_allows_send(HIGH))
        self.assertFalse(edge_grants_send())
        self.assertFalse(pin_grants_send())
        self.assertIs(admit_send_after_edge(LOW, 10, 0, 10), False)


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_be_a_prior_or_run_id(self):
        with self.assertRaises(FailClosedError):
            classify_edge("campaign_envelope_ready", 10, 0, 10)
        with self.assertRaises(FailClosedError):
            pin_band({}, "campaign_envelope_ready", HIGH)
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertFalse(edge_rearms())
        self.assertFalse(pin_rearms())


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_rise_fall_hold_and_retcon(self):
        self.assertEqual(classify_edge(LOW, 10, 0, 10), RISE)
        self.assertEqual(classify_edge(HIGH, 0, 0, 10), FALL)
        self.assertEqual(classify_edge(HIGH, 5, 0, 10), HOLD)
        table: dict[str, str] = {}
        pin_band(table, _RUN, HIGH)
        self.assertIs(retcon_refused(table, _RUN, LOW), True)
        self.assertIsNone(retcon_refused({}, _RUN, HIGH))


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_hold_holds(self):
        a = classify_edge(LOW, 10, 0, 10)
        b = classify_edge(LOW, 10, 0, 10)
        self.assertEqual(a, b)
        self.assertEqual(a, RISE)
        table: dict[str, str] = {}
        self.assertEqual(pin_band(table, _RUN, HIGH), PINNED)
        self.assertEqual(pin_band(table, _RUN, HIGH), "already_pinned")
        self.assertTrue(later_hold_supersedes_older())
        self.assertFalse(pin_allows_send(HIGH))
        with self.assertRaises(FailClosedError):
            classify_edge("send_authorized", 10, 0, 10)


if __name__ == "__main__":
    unittest.main()
