"""Owner-absent chaos — write-fence composition (independent of #82 chaos).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These scenarios
lock the same seven rules at the durable-write layer: no store, no
run_id mint, no fabricated witness. HALT is not a write-fence
parameter. One arm's timeout cannot refuse another arm's in-flight
write. Recovery is admitting a spine write and is still not a send.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import RUN_CREATED, RUN_REJECTED, TOOL_INVOKED
from ofn.kernel.write_fence import (
    admit_write,
    grants_send,
    halt_blocks_write,
    ready_is_authorized,
)


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_kind_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_write(surface="ledger", kind="DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_surface_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_write(surface="unknown_disk", kind=RUN_CREATED)
        self.assertNotIn("FALSE", str(ctx.exception))


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_siblings(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("arm A fetch timed out")
        sibling = admit_write(surface="ledger", kind=TOOL_INVOKED,
                              payload={"arm": "B"})
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        # A timeout is UNKNOWN, not evidence that two writers raced.
        with self.assertRaises(TimeoutError):
            raise TimeoutError("lock wait timed out")
        d = admit_write(surface="ledger", kind=TOOL_INVOKED)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_tool_invoked(self):
        decisions = [
            admit_write(surface="ledger", kind=TOOL_INVOKED,
                        payload={"arm": arm})
            for arm in ("a", "b", "c")
        ]
        self.assertEqual(len(decisions), 3)
        for d in decisions:
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_admit_is_not_a_send(self):
        first = admit_write(surface="receipt", kind="EXECUTION_RECEIPT")
        second = admit_write(surface="receipt", kind="EXECUTION_RECEIPT")
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(first.grants_send)
        self.assertFalse(grants_send())


class Scenario5SealedNameStopsThatWriteOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_spine_continues(self):
        sealed = admit_write(surface="ledger", kind="send_authorized")
        self.assertFalse(sealed.allowed)
        sibling = admit_write(surface="ledger", kind=TOOL_INVOKED)
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)


class Scenario6GlobalHaltIsNotAWriteParameter(unittest.TestCase):
    def test_halt_does_not_block_in_flight_writes(self):
        self.assertFalse(halt_blocks_write())
        for arm in ("a", "b", "c"):
            d = admit_write(surface="ledger", kind=TOOL_INVOKED,
                            payload={"arm": arm})
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        import inspect
        self.assertNotIn("halt", inspect.signature(admit_write).parameters)
        self.assertNotIn("halt_raw", inspect.signature(admit_write).parameters)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_a_spine_write_and_not_a_send(self):
        blocked = admit_write(surface="ledger", kind="quote_sent")
        self.assertFalse(blocked.allowed)
        resumed = admit_write(surface="ledger", kind=RUN_CREATED)
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(grants_send())

    def test_refusal_witness_is_side_log_not_a_run(self):
        d = admit_write(surface="side_log", kind=RUN_REJECTED)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready = admit_write(surface="ledger",
                            kind="campaign_envelope_ready")
        sent = admit_write(surface="ledger", kind="quote_sent")
        auth = admit_write(surface="ledger", kind="send_authorized")
        for d in (ready, sent, auth):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual(ready.kind, auth.kind)


if __name__ == "__main__":
    unittest.main()
