"""Owner-absent chaos — slot-class + occupy-pin (independent of #82).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the slot/occupy layer:
no fabricated witness, no store write, no steal. HALT stops
STARTS only. One arm's timeout cannot mark another arm
SUSPECTED. Recovery is a release/inspect/unpin and is still
not a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.occupy_pin import (
    classify_timeout,
    grants_send as pin_grants_send,
    halt_blocks_unpin,
    occupy_is_persist,
    occupy_is_send,
    occupy_is_write,
    pin_occupy,
    ready_is_authorized as pin_ready_is_authorized,
    timeout_proves_concurrent as pin_timeout_proves,
)
from ofn.kernel.slot_class import (
    admit_slot,
    grants_send as slot_grants_send,
    halt_blocks_release,
    occupy_is_persist as slot_occupy_is_persist,
    ready_is_authorized as slot_ready_is_authorized,
    steals_slot,
    timeout_proves_concurrent as slot_timeout_proves,
)

_RUN_A = "run-1780000000-armaaaaaaa"
_RUN_B = "run-1780000000-armbbbbbbb"
_RUN_C = "run-1780000000-armccccccc"


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_slot_activity_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_slot(
                intended="occupy", run_id=_RUN_A, activity="DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_pin_activity_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_occupy(
                intended="pin", run_id=_RUN_A, activity="DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_inspect(self):
        timed = admit_slot(
            intended="inspect", run_id=_RUN_A, timed_out=True)
        self.assertEqual(timed.status, "UNKNOWN")
        self.assertTrue(timed.allowed)
        sibling = admit_slot(intended="inspect", run_id=_RUN_B)
        self.assertTrue(sibling.allowed)
        self.assertEqual(sibling.status, "VERIFIED")
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(slot_timeout_proves())
        self.assertFalse(pin_timeout_proves())
        self.assertEqual(classify_timeout(), "UNKNOWN")
        d = pin_occupy(
            intended="pin", run_id=_RUN_A,
            activity="concurrent", timed_out=True)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.reason, "unknown_activity")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_inspect_and_unpin(self):
        slots = [
            admit_slot(intended="inspect", run_id=rid, occupancy="held")
            for rid in (_RUN_A, _RUN_B, _RUN_C)
        ]
        pins = [
            pin_occupy(intended="inspect", run_id=rid, pin_state="held")
            for rid in (_RUN_A, _RUN_B, _RUN_C)
        ]
        self.assertEqual(len(slots), 3)
        self.assertEqual(len(pins), 3)
        for d in slots + pins:
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_inspect_is_not_a_send(self):
        first = admit_slot(intended="inspect", run_id=_RUN_A, occupancy="held")
        second = admit_slot(intended="inspect", run_id=_RUN_A, occupancy="held")
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(first.grants_send)
        self.assertFalse(slot_grants_send())
        self.assertFalse(pin_grants_send())
        self.assertFalse(occupy_is_send())
        self.assertFalse(occupy_is_write())
        self.assertFalse(occupy_is_persist())
        self.assertFalse(slot_occupy_is_persist())


class Scenario5SealedNameStopsThatRowOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_inspect_continues(self):
        sealed = admit_slot(intended="occupy", run_id="send_authorized")
        self.assertFalse(sealed.allowed)
        self.assertEqual(sealed.reason, "sealed_effect")
        sibling = admit_slot(intended="inspect", run_id=_RUN_B)
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)


class Scenario6GlobalHaltIsStartOnly(unittest.TestCase):
    def test_halt_refuses_occupy_and_pin_not_release(self):
        occupy = admit_slot(
            intended="occupy", run_id=_RUN_A, halted=True)
        self.assertFalse(occupy.allowed)
        self.assertEqual(occupy.reason, "halt_start")
        pinned = pin_occupy(
            intended="pin", run_id=_RUN_A, halted=True)
        self.assertFalse(pinned.allowed)
        self.assertEqual(pinned.reason, "halt_start")
        release = admit_slot(
            intended="release", run_id=_RUN_B, occupancy="held", halted=True)
        self.assertTrue(release.allowed)
        unpin = pin_occupy(
            intended="unpin", run_id=_RUN_B, pin_state="held", halted=True)
        self.assertTrue(unpin.allowed)
        self.assertFalse(halt_blocks_release())
        self.assertFalse(halt_blocks_unpin())
        self.assertFalse(release.grants_send)
        self.assertFalse(unpin.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        for fn in (admit_slot, pin_occupy):
            params = inspect.signature(fn).parameters
            self.assertNotIn("halt_raw", params)
            self.assertNotIn("send_authorized", params)
            self.assertNotIn("resend", params)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_a_release_or_inspect_and_not_a_send(self):
        blocked = admit_slot(intended="inspect", run_id="quote_sent")
        self.assertFalse(blocked.allowed)
        resumed = admit_slot(
            intended="inspect", run_id=_RUN_C, occupancy="held")
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(slot_grants_send())
        self.assertFalse(steals_slot())

    def test_steal_is_never_recovery(self):
        d = admit_slot(intended="steal", run_id=_RUN_C, occupancy="held")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "steal_forbidden")
        self.assertFalse(steals_slot())


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready_s = admit_slot(
            intended="inspect", run_id="campaign_envelope_ready")
        sent_s = admit_slot(intended="inspect", run_id="quote_sent")
        auth_s = admit_slot(intended="inspect", run_id="send_authorized")
        ready_p = pin_occupy(
            intended="inspect", run_id="campaign_envelope_ready")
        sent_p = pin_occupy(intended="inspect", run_id="quote_sent")
        auth_p = pin_occupy(intended="inspect", run_id="send_authorized")
        for d in (ready_s, sent_s, auth_s, ready_p, sent_p, auth_p):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        self.assertFalse(slot_ready_is_authorized())
        self.assertFalse(pin_ready_is_authorized())
        self.assertNotEqual(ready_s.run_id, auth_s.run_id)
        self.assertNotEqual(ready_p.run_id, auth_p.run_id)


if __name__ == "__main__":
    unittest.main()
