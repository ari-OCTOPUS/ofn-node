"""Owner-absent chaos — flag-freeze composition (independent of #82 chaos).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These scenarios
lock the same seven rules at the flag layer: no store, no run_id mint,
no fabricated witness. HALT is not a flag-freeze parameter. One arm's
timeout cannot unfreeze another arm's flag. Recovery is admitting a
close and is still not a send.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.flag_freeze import (
    admit_flag,
    grants_send,
    halt_blocks_flag,
    ready_is_authorized,
    rearms_send,
)


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_flag_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_flag(name="DEAD_SOURCE", intended="closed")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_intended_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_flag(name="OFN_WIRE_OUTBOUND", intended="maybe")
        self.assertNotIn("FALSE", str(ctx.exception))


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_unfreeze_siblings(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("arm A fetch timed out")
        sibling = admit_flag(name="OFN_WIRE_EMAIL", intended="closed")
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("lock wait timed out")
        d = admit_flag(name="auto_email", intended="closed")
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_can_close_distinct_flags(self):
        decisions = [
            admit_flag(name=name, intended="closed")
            for name in ("OFN_WIRE_OUTBOUND", "OBSERVATORY", "auto_email")
        ]
        self.assertEqual(len(decisions), 3)
        for d in decisions:
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)


class Scenario4DuplicateCloseStillNotASend(unittest.TestCase):
    def test_second_identical_close_is_not_a_send(self):
        first = admit_flag(name="OFN_KEEP_GATES_OPEN", intended="closed")
        second = admit_flag(name="OFN_KEEP_GATES_OPEN", intended="closed")
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(first.grants_send)
        self.assertFalse(grants_send())


class Scenario5SealedNameStopsThatFlagOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_close_continues(self):
        sealed = admit_flag(name="send_authorized", intended="open")
        self.assertFalse(sealed.allowed)
        sibling = admit_flag(name="OFN_WIRE_OUTBOUND", intended="closed")
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)


class Scenario6GlobalHaltIsNotAFlagParameter(unittest.TestCase):
    def test_halt_does_not_block_flag_classify(self):
        self.assertFalse(halt_blocks_flag())
        for name in ("OFN_WIRE_OUTBOUND", "OBSERVATORY", "auto_email"):
            d = admit_flag(name=name, intended="closed")
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        import inspect
        self.assertNotIn("halt", inspect.signature(admit_flag).parameters)
        self.assertNotIn("halt_raw", inspect.signature(admit_flag).parameters)
        self.assertFalse(rearms_send())


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_a_close_and_not_a_send(self):
        blocked = admit_flag(name="quote_sent", intended="open")
        self.assertFalse(blocked.allowed)
        resumed = admit_flag(name="OFN_WIRE_OUTBOUND", intended="closed",
                             later_hold=True)
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(grants_send())
        self.assertFalse(rearms_send())

    def test_later_hold_still_refuses_open_after_recovery(self):
        d = admit_flag(name="auto_email", intended="open", later_hold=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "later_hold")
        self.assertFalse(d.grants_send)


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready = admit_flag(name="campaign_envelope_ready", intended="closed")
        sent = admit_flag(name="quote_sent", intended="closed")
        auth = admit_flag(name="send_authorized", intended="closed")
        for d in (ready, sent, auth):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual(ready.name, auth.name)


if __name__ == "__main__":
    unittest.main()
