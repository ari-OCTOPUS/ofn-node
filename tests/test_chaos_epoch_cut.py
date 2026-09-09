"""Owner-absent chaos — epoch-class + cut-pin composition.

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the epoch and cut layer:
no store, no fabricated witness. HALT is not a parameter. One
arm's timeout cannot refuse another arm's epoch or cut.
Recovery is admitting a fresh open epoch / cut of an open
window and is still not a send.
"""

from __future__ import annotations

import unittest

from ofn.kernel.cut_pin import (
    grants_send as cut_grants_send,
    halt_blocks_cut,
    pin_cut,
    ready_is_authorized as cut_ready_is_authorized,
)
from ofn.kernel.epoch_class import (
    admit_epoch,
    grants_send as epoch_grants_send,
    halt_blocks_epoch,
    ready_is_authorized as epoch_ready_is_authorized,
)
from ofn.kernel.errors import FailClosedError

_A = "epoch-1756857700-aaaaaaaaaa"
_B = "epoch-1756857701-bbbbbbbbbb"
_C = "epoch-1756857702-cccccccccc"


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_state_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_epoch(state="DEAD_STATE", epoch_id=_A)
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_prior_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_cut(epoch_id=_A, prior_state="DEAD_PRIOR")
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_missing_prior_is_unknown_not_open(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_cut(epoch_id=_A, prior_state=None)
        self.assertIn("UNKNOWN", str(ctx.exception))


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_epoch(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("arm A fetch timed out")
        sibling = admit_epoch(state="open", epoch_id=_B)
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("lock wait timed out")
        d = pin_cut(epoch_id=_B, prior_state="open")
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_distinct_epochs(self):
        decisions = []
        for epoch_id in (_A, _B, _C):
            d = admit_epoch(state="open", epoch_id=epoch_id)
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)
            decisions.append(d)
        self.assertEqual(len(decisions), 3)
        self.assertEqual({d.epoch_id for d in decisions}, {_A, _B, _C})

    def test_three_arms_cut_open_windows(self):
        decisions = [
            pin_cut(epoch_id=epoch_id, prior_state="open")
            for epoch_id in (_A, _B, _C)
        ]
        self.assertEqual(len(decisions), 3)
        for d in decisions:
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_open_is_still_not_a_send(self):
        first = admit_epoch(state="open", epoch_id=_A)
        second = admit_epoch(state="open", epoch_id=_A)
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(first.grants_send)
        self.assertFalse(epoch_grants_send())

    def test_second_cut_is_already_cut_not_a_send(self):
        first = pin_cut(epoch_id=_A, prior_state="open")
        second = pin_cut(epoch_id=_A, prior_state="cut")
        self.assertTrue(first.allowed)
        self.assertFalse(second.allowed)
        self.assertEqual(second.reason, "already_cut")
        self.assertFalse(first.grants_send)
        self.assertFalse(second.grants_send)
        self.assertFalse(cut_grants_send())


class Scenario5SealedNameStopsThatWriteOnly(unittest.TestCase):
    def test_sealed_epoch_refused_sibling_continues(self):
        sealed = admit_epoch(state="open", epoch_id="send_authorized")
        self.assertFalse(sealed.allowed)
        sibling = admit_epoch(state="open", epoch_id=_A)
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)

    def test_sealed_cut_refused_sibling_continues(self):
        sealed = pin_cut(epoch_id="quote_sent", prior_state="open")
        self.assertFalse(sealed.allowed)
        sibling = pin_cut(epoch_id=_A, prior_state="open")
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)


class Scenario6GlobalHaltIsNotAParameter(unittest.TestCase):
    def test_halt_does_not_block_in_flight_epoch_or_cut(self):
        self.assertFalse(halt_blocks_epoch())
        self.assertFalse(halt_blocks_cut())
        for epoch_id in (_A, _B, _C):
            e = admit_epoch(state="open", epoch_id=epoch_id)
            self.assertTrue(e.allowed)
            self.assertFalse(e.grants_send)
            c = pin_cut(epoch_id=epoch_id, prior_state="open")
            self.assertTrue(c.allowed)
            self.assertFalse(c.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        import inspect
        self.assertNotIn("halt", inspect.signature(admit_epoch).parameters)
        self.assertNotIn("halt", inspect.signature(pin_cut).parameters)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_a_fresh_open_epoch_and_not_a_send(self):
        blocked = admit_epoch(state="open", epoch_id="quote_sent")
        self.assertFalse(blocked.allowed)
        resumed = admit_epoch(state="open", epoch_id=_A)
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(epoch_grants_send())

    def test_resume_cut_is_not_a_send(self):
        blocked = pin_cut(epoch_id=_A, prior_state="rewrite")
        self.assertFalse(blocked.allowed)
        resumed = pin_cut(epoch_id=_A, prior_state="open")
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)

    def test_cut_of_already_cut_is_not_truncate(self):
        d = pin_cut(epoch_id=_A, prior_state="cut")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "already_cut")
        self.assertNotEqual(d.reason, "truncate")
        self.assertFalse(d.grants_send)


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready_e = admit_epoch(state="open",
                              epoch_id="campaign_envelope_ready")
        sent_e = admit_epoch(state="open", epoch_id="quote_sent")
        auth_e = admit_epoch(state="open", epoch_id="send_authorized")
        for d in (ready_e, sent_e, auth_e):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        self.assertFalse(epoch_ready_is_authorized())
        self.assertNotEqual(ready_e.epoch_id, auth_e.epoch_id)

        ready_c = pin_cut(epoch_id="campaign_envelope_ready",
                          prior_state="open")
        auth_c = pin_cut(epoch_id="send_authorized", prior_state="open")
        for d in (ready_c, auth_c):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
        self.assertFalse(cut_ready_is_authorized())
        self.assertNotEqual(ready_c.epoch_id, auth_c.epoch_id)


if __name__ == "__main__":
    unittest.main()
