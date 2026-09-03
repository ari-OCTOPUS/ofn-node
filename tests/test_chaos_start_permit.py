"""Owner-absent chaos — start-permit composition (independent of #82 chaos).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These scenarios
lock the same seven rules at the pre-mint layer: no store, no run_id,
no fabricated witness. One arm's halt decision cannot mint a run for
another arm. Recovery is ``halt_raw=None`` and is still not a send.
"""

from __future__ import annotations

import unittest

from ofn.kernel.events import RUN_CREATED
from ofn.kernel.start_permit import decide_start, grants_send


class Scenario6GlobalHaltStopsNewStarts(unittest.TestCase):
    def test_three_arms_refused_with_no_run_id(self):
        decisions = [
            decide_start(halt_raw="1", proposed_kind=RUN_CREATED)
            for _ in ("a", "b", "c")
        ]
        self.assertEqual(len(decisions), 3)
        for d in decisions:
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "halt_active")
            self.assertFalse(d.grants_send)

    def test_unparsable_flag_halts_every_arm(self):
        for raw in ("", "garbage", "2"):
            for _arm in ("d", "e", "f"):
                d = decide_start(halt_raw=raw)
                self.assertFalse(d.allowed)


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_halt_siblings(self):
        # A timeout is UNKNOWN, not a halt. Sibling starts still decide.
        with self.assertRaises(TimeoutError):
            raise TimeoutError("arm A fetch timed out")
        sibling = decide_start(halt_raw=None, proposed_kind=RUN_CREATED)
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_absent_flag_and_not_a_send(self):
        blocked = decide_start(halt_raw="1", proposed_kind=RUN_CREATED)
        self.assertFalse(blocked.allowed)
        # Resume = deliberate absence. No owner knob. Not a send grant.
        resumed = decide_start(halt_raw=None, proposed_kind=RUN_CREATED)
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(grants_send())


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready = decide_start(halt_raw=None,
                             proposed_tool="campaign_envelope_ready")
        sent = decide_start(halt_raw=None, proposed_tool="quote_sent")
        auth = decide_start(halt_raw=None, proposed_tool="send_authorized")
        for d in (ready, sent, auth):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)


if __name__ == "__main__":
    unittest.main()
