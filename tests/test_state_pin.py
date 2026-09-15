"""Contract tests for state_pin (P1 complementary).

Pin records (run_id → result) at most once per distinct label.
peek never writes. Missing is None, not False. Never grants a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.state_pin import (
    StatePin,
    claims_immutable,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    pin_allows_passed_only,
    pin_allows_send,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    unknown_is_false,
    wires_into_run_store,
)

_RUN = "run-1780000000-a1b2c3d4e5"


class PinStates(unittest.TestCase):
    def setUp(self):
        self.pin = StatePin()

    def test_first_pin_records(self):
        self.assertEqual(self.pin.pin(_RUN, "passed"), "pinned")
        self.assertEqual(self.pin.peek(_RUN), "passed")

    def test_same_pair_is_already_pinned(self):
        self.pin.pin(_RUN, "rejected")
        self.assertEqual(self.pin.pin(_RUN, "Rejected"), "already_pinned")
        self.assertEqual(self.pin.peek(_RUN), "rejected")

    def test_different_result_is_collision(self):
        self.pin.pin(_RUN, "failed")
        with self.assertRaises(FailClosedError) as ctx:
            self.pin.pin(_RUN, "passed")
        self.assertIn("result_collision", str(ctx.exception))

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(self.pin.peek(_RUN))
        self.assertIsNot(self.pin.peek(_RUN), False)

    def test_peek_does_not_write(self):
        self.pin.peek(_RUN)
        self.assertIsNone(self.pin.peek(_RUN))

    def test_try_pin_missing_is_none(self):
        self.assertIsNone(self.pin.try_pin(_RUN, None))
        self.assertIsNone(self.pin.peek(_RUN))

    def test_try_pin_present_writes(self):
        self.assertEqual(self.pin.try_pin(_RUN, "unknown"), "pinned")
        self.assertEqual(self.pin.peek(_RUN), "unknown")

    def test_bad_run_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            self.pin.pin("not-a-run", "passed")

    def test_send_name_fails_closed(self):
        with self.assertRaises(FailClosedError):
            self.pin.pin(_RUN, "send_authorized")

    def test_ok_true_sent_false_fails_closed(self):
        with self.assertRaises(FailClosedError):
            self.pin.pin(_RUN, "passed", sent=False, ok=True)

    def test_pin_missing_result_fails_closed(self):
        with self.assertRaises(FailClosedError):
            self.pin.pin(_RUN, None)


class PassedPin(unittest.TestCase):
    def test_passed_only_is_not_a_send(self):
        self.assertTrue(pin_allows_passed_only("passed"))
        self.assertFalse(pin_allows_passed_only("rejected"))
        self.assertFalse(pin_allows_passed_only(None))
        self.assertFalse(pin_allows_send())
        self.assertFalse(grants_send())

    def test_bool_label_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_allows_passed_only(True)


class StructuralRefusals(unittest.TestCase):
    def test_flags(self):
        self.assertFalse(grants_send())
        self.assertFalse(halt_blocks_pin())
        self.assertFalse(pin_allows_send())
        self.assertFalse(ready_is_authorized())
        self.assertFalse(unknown_is_false())
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertFalse(claims_immutable())
        self.assertFalse(wires_into_run_store())
        self.assertTrue(later_disarm_supersedes())

    def test_pin_has_no_halt_or_now_parameter(self):
        params = inspect.signature(StatePin.pin).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)


if __name__ == "__main__":
    unittest.main()
