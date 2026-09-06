"""Contract tests for role_pin (P1 complementary).

First role pins. Same pair is already_pinned. Second start,
second debit, and after_close fail closed. peek never writes.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import (
    BUDGET_DEBIT,
    CLAIM_CREATED,
    EXECUTION_RECEIPT,
    PROPOSAL_CREATED,
    RUN_CLOSED,
    RUN_CREATED,
    RUN_REJECTED,
    TOOL_INVOKED,
)
from ofn.kernel.kind_class import CLOSE, DEBIT, INFLIGHT, PROPOSAL, START
from ofn.kernel.role_pin import (
    RolePin,
    claims_immutable,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    pin_allows_send,
    pin_allows_start_only,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    unknown_is_false,
    wires_into_run_store,
)

_RUN = "run-1780000000-a1b2c3d4e5"


class PinRoles(unittest.TestCase):
    def test_first_start_pins(self):
        pin = RolePin()
        self.assertEqual(pin.pin(_RUN, RUN_CREATED), "pinned")
        self.assertEqual(pin.peek(_RUN), START)

    def test_second_start_fails_closed(self):
        pin = RolePin()
        pin.pin(_RUN, RUN_CREATED)
        with self.assertRaises(FailClosedError) as ctx:
            pin.pin(_RUN, RUN_CREATED)
        self.assertIn("second_start", str(ctx.exception))

    def test_inflight_after_start_pins(self):
        pin = RolePin()
        pin.pin(_RUN, RUN_CREATED)
        self.assertEqual(pin.pin(_RUN, CLAIM_CREATED), "pinned")
        self.assertEqual(pin.peek(_RUN), INFLIGHT)

    def test_same_inflight_is_already_pinned(self):
        pin = RolePin()
        pin.pin(_RUN, CLAIM_CREATED)
        self.assertEqual(pin.pin(_RUN, TOOL_INVOKED), "already_pinned")
        self.assertEqual(pin.peek(_RUN), INFLIGHT)

    def test_debit_once_then_second_fails(self):
        pin = RolePin()
        pin.pin(_RUN, EXECUTION_RECEIPT)
        self.assertEqual(pin.pin(_RUN, BUDGET_DEBIT), "pinned")
        with self.assertRaises(FailClosedError) as ctx:
            pin.pin(_RUN, BUDGET_DEBIT)
        self.assertIn("second_debit", str(ctx.exception))
        self.assertEqual(pin.peek(_RUN), INFLIGHT)

    def test_after_close_refuses_inflight(self):
        pin = RolePin()
        pin.pin(_RUN, RUN_CLOSED)
        with self.assertRaises(FailClosedError) as ctx:
            pin.pin(_RUN, CLAIM_CREATED)
        self.assertIn("after_close", str(ctx.exception))
        self.assertEqual(pin.peek(_RUN), CLOSE)

    def test_close_then_close_is_already_pinned(self):
        pin = RolePin()
        pin.pin(_RUN, RUN_CLOSED)
        self.assertEqual(pin.pin(_RUN, RUN_CLOSED), "already_pinned")

    def test_reject_after_close_is_allowed(self):
        pin = RolePin()
        pin.pin(_RUN, RUN_CLOSED)
        self.assertEqual(pin.pin(_RUN, RUN_REJECTED), "pinned")

    def test_proposal_pins_and_is_not_execution(self):
        pin = RolePin()
        self.assertEqual(pin.pin(_RUN, PROPOSAL_CREATED), "pinned")
        self.assertEqual(pin.peek(_RUN), PROPOSAL)
        self.assertNotEqual(pin.peek(_RUN), EXECUTION_RECEIPT)

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(RolePin().peek(_RUN))
        self.assertIsNot(RolePin().peek(_RUN), False)

    def test_try_pin_missing_is_none(self):
        self.assertIsNone(RolePin().try_pin(_RUN, None))

    def test_try_pin_timeout_is_none(self):
        self.assertIsNone(RolePin().try_pin(_RUN, RUN_CREATED, timeout=True))

    def test_pin_timeout_fails_closed(self):
        with self.assertRaises(FailClosedError):
            RolePin().pin(_RUN, RUN_CREATED, timeout=True)

    def test_bad_run_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            RolePin().pin("not-a-run", RUN_CREATED)

    def test_sealed_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            RolePin().pin(_RUN, "send_authorized")
        with self.assertRaises(FailClosedError):
            RolePin().pin(_RUN, "campaign_envelope_ready")

    def test_pin_allows_start_only_is_not_a_send(self):
        self.assertTrue(pin_allows_start_only(START))
        self.assertFalse(pin_allows_start_only(INFLIGHT))
        self.assertFalse(pin_allows_start_only(None))
        self.assertFalse(pin_allows_send())
        self.assertFalse(grants_send())


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


if __name__ == "__main__":
    unittest.main()
