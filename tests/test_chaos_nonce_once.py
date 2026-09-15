"""Owner-absent chaos — nonce/once composition (independent of #82 chaos).

``tests/test_chaos_owner_absent.py`` is owned by another change. These
scenarios lock the same seven rules at the one-shot-token layer: no
store, no run_id mint, no fabricated witness. HALT refuses admit
only. One arm's timeout cannot refuse another arm's in-flight
replay_check or consume. Recovery is peek/consume and is still not
a send.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.nonce_class import (
    admit_nonce,
    grants_send as nonce_grants_send,
    halt_blocks_replay_check,
    ready_is_authorized as nonce_ready,
)
from ofn.kernel.once_pin import (
    OnceIndex,
    grants_send as once_grants_send,
    halt_blocks_consume,
    pin_once,
    ready_is_authorized as once_ready,
)

_RUN = "run-1780000000-abcdefghij"
_NCE_A = "nce-aaaaaaaaaaaaaaaa"
_NCE_B = "nce-bbbbbbbbbbbbbbbb"
_NCE_C = "nce-cccccccccccccccc"


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_intent_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_nonce(intended="DEAD_SOURCE", nonce=_NCE_A, run_id=_RUN)
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_once_intent_is_not_classified_false(self):
        idx = OnceIndex()
        with self.assertRaises(FailClosedError) as ctx:
            pin_once(idx, intended="DEAD_SOURCE", nonce=_NCE_A, run_id=_RUN)
        self.assertNotIn("FALSE", str(ctx.exception))


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_siblings(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("arm A fetch timed out")
        sibling = admit_nonce(
            intended="replay_check", nonce=_NCE_B, run_id=_RUN)
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("lock wait timed out")
        d = admit_nonce(intended="replay_check", nonce=_NCE_A, run_id=_RUN)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)
        idx = OnceIndex()
        c = pin_once(idx, intended="consume", nonce=_NCE_A, run_id=_RUN)
        self.assertTrue(c.allowed)
        self.assertFalse(c.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_distinct_nonces(self):
        decisions = [
            admit_nonce(intended="admit", nonce=nce, run_id=_RUN)
            for nce in (_NCE_A, _NCE_B, _NCE_C)
        ]
        self.assertEqual(len(decisions), 3)
        for d in decisions:
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)
        idx = OnceIndex()
        for nce in (_NCE_A, _NCE_B, _NCE_C):
            c = pin_once(idx, intended="consume", nonce=nce, run_id=_RUN)
            self.assertTrue(c.allowed)
            self.assertFalse(c.grants_send)
        self.assertEqual(len(idx), 3)


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_consume_is_not_a_send(self):
        idx = OnceIndex()
        first = pin_once(idx, intended="consume", nonce=_NCE_A, run_id=_RUN)
        second = pin_once(idx, intended="consume", nonce=_NCE_A, run_id=_RUN)
        self.assertTrue(first.allowed)
        self.assertFalse(second.allowed)
        self.assertEqual(second.reason, "already_consumed")
        self.assertFalse(first.grants_send)
        self.assertFalse(second.grants_send)
        self.assertFalse(once_grants_send())
        self.assertFalse(nonce_grants_send())


class Scenario5SealedNameStopsThatWriteOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_continues(self):
        sealed = admit_nonce(
            intended="admit", nonce="send_authorized", run_id=_RUN)
        self.assertFalse(sealed.allowed)
        sibling = admit_nonce(intended="admit", nonce=_NCE_B, run_id=_RUN)
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)
        idx = OnceIndex()
        blocked = pin_once(
            idx, intended="consume", nonce="quote_sent", run_id=_RUN)
        self.assertFalse(blocked.allowed)
        ok = pin_once(idx, intended="consume", nonce=_NCE_B, run_id=_RUN)
        self.assertTrue(ok.allowed)
        self.assertFalse(ok.grants_send)


class Scenario6GlobalHaltIsNotAConsumeParameter(unittest.TestCase):
    def test_halt_does_not_block_replay_or_consume(self):
        self.assertFalse(halt_blocks_replay_check())
        self.assertFalse(halt_blocks_consume())
        idx = OnceIndex()
        for nce in (_NCE_A, _NCE_B, _NCE_C):
            d = admit_nonce(
                intended="replay_check", nonce=nce, run_id=_RUN, halted=True)
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)
            c = pin_once(idx, intended="consume", nonce=nce, run_id=_RUN)
            self.assertTrue(c.allowed)
            self.assertFalse(c.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        import inspect
        self.assertNotIn("halt", inspect.signature(pin_once).parameters)
        self.assertNotIn("halt_raw", inspect.signature(pin_once).parameters)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_a_peek_and_not_a_send(self):
        blocked = admit_nonce(
            intended="admit", nonce="quote_sent", run_id=_RUN)
        self.assertFalse(blocked.allowed)
        idx = OnceIndex()
        resumed = pin_once(idx, intended="peek", nonce=_NCE_A, run_id=_RUN)
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.seen)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(once_grants_send())
        self.assertEqual(len(idx), 0)

    def test_halt_refuses_new_admit_not_in_flight_consume(self):
        refused = admit_nonce(
            intended="admit", nonce=_NCE_A, run_id=_RUN, halted=True)
        self.assertFalse(refused.allowed)
        self.assertEqual(refused.reason, "halt_active")
        idx = OnceIndex()
        inflight = pin_once(idx, intended="consume", nonce=_NCE_A, run_id=_RUN)
        self.assertTrue(inflight.allowed)
        self.assertFalse(inflight.grants_send)


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready = admit_nonce(
            intended="admit", nonce="campaign_envelope_ready", run_id=_RUN)
        sent = admit_nonce(
            intended="admit", nonce="quote_sent", run_id=_RUN)
        auth = admit_nonce(
            intended="admit", nonce="send_authorized", run_id=_RUN)
        for d in (ready, sent, auth):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        self.assertFalse(nonce_ready())
        self.assertFalse(once_ready())
        idx = OnceIndex()
        for sealed in (
            "campaign_envelope_ready",
            "quote_sent",
            "send_authorized",
        ):
            p = pin_once(idx, intended="consume", nonce=sealed, run_id=_RUN)
            self.assertFalse(p.allowed)
            self.assertEqual(p.reason, "sealed_effect")
        self.assertEqual(len(idx), 0)
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
