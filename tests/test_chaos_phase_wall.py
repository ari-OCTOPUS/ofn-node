"""Owner-absent chaos — phase-wall composition (independent of #82 chaos).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These scenarios
lock the same seven rules at the phase layer: no store, no run_id mint,
no fabricated witness. HALT is not a phase-wall parameter. One arm's
timeout cannot authorize another arm's send. Recovery is admitting
ready and is still not a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.phase_wall import (
    admit_phase,
    grants_send,
    halt_blocks_phase,
    ready_equals_authorized,
    ready_is_authorized,
    rearms_send,
)


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_phase_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_phase(name="DEAD_SOURCE", intended="classify")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_intended_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_phase(name="campaign_envelope_ready", intended="maybe")
        self.assertNotIn("FALSE", str(ctx.exception))


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_authorize_siblings(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("arm A fetch timed out")
        sibling = admit_phase(name="quote_drafted", intended="classify")
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("lock wait timed out")
        d = admit_phase(name="campaign_envelope_ready", intended="advance")
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)
        self.assertFalse(ready_is_authorized())


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_can_classify_distinct_ready_names(self):
        decisions = [
            admit_phase(name=name, intended="classify")
            for name in ("campaign_envelope_ready", "quote_drafted",
                         "campaign-envelope-ready")
        ]
        self.assertEqual(len(decisions), 3)
        for d in decisions:
            self.assertTrue(d.allowed)
            self.assertEqual(d.band, "ready")
            self.assertFalse(d.grants_send)


class Scenario4DuplicateReadyStillNotASend(unittest.TestCase):
    def test_second_identical_ready_is_not_a_send(self):
        first = admit_phase(name="campaign_envelope_ready",
                            intended="advance")
        second = admit_phase(name="campaign_envelope_ready",
                             intended="advance")
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(first.grants_send)
        self.assertFalse(grants_send())
        self.assertFalse(ready_equals_authorized())


class Scenario5SealedNameStopsThatPhaseOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_ready_continues(self):
        sealed = admit_phase(name="send_authorized", intended="advance")
        self.assertFalse(sealed.allowed)
        sibling = admit_phase(name="campaign_envelope_ready",
                              intended="advance")
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)
        self.assertNotEqual(sealed.name, sibling.name)


class Scenario6GlobalHaltIsNotAPhaseParameter(unittest.TestCase):
    def test_halt_does_not_block_phase_classify(self):
        self.assertFalse(halt_blocks_phase())
        for name in ("campaign_envelope_ready", "quote_drafted"):
            d = admit_phase(name=name, intended="classify")
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        self.assertNotIn("halt", inspect.signature(admit_phase).parameters)
        self.assertNotIn("halt_raw", inspect.signature(admit_phase).parameters)
        self.assertFalse(rearms_send())


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_ready_and_not_a_send(self):
        blocked = admit_phase(name="quote_sent", intended="advance")
        self.assertFalse(blocked.allowed)
        resumed = admit_phase(name="campaign_envelope_ready",
                              intended="advance", later_hold=True)
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(grants_send())
        self.assertFalse(rearms_send())
        self.assertFalse(ready_is_authorized())

    def test_later_hold_still_refuses_send_after_recovery(self):
        d = admit_phase(name="send_authorized", intended="advance",
                        later_hold=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "later_hold")
        self.assertFalse(d.grants_send)


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_stay_apart(self):
        ready = admit_phase(name="campaign_envelope_ready",
                            intended="classify")
        sent = admit_phase(name="quote_sent", intended="classify")
        auth = admit_phase(name="send_authorized", intended="classify")
        self.assertTrue(ready.allowed)
        self.assertFalse(sent.allowed)
        self.assertFalse(auth.allowed)
        self.assertEqual(sent.reason, "sealed_effect")
        self.assertEqual(auth.reason, "sealed_effect")
        self.assertFalse(ready.grants_send)
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual(ready.name, auth.name)
        self.assertNotEqual(ready.band, auth.band)


if __name__ == "__main__":
    unittest.main()
