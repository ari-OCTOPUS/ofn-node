"""Owner-absent chaos — revoke-class + withdraw-pin (independent of #82).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the revoke/withdraw layer:
no fabricated witness, no store write, no run_id mint. HALT
stops STARTS only. One arm's timeout cannot mark another arm
withdrawn. Recovery is a revoke of a held ready and is still
not a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.revoke_class import (
    HELD,
    READY,
    REVOKE,
    UNKNOWN,
    admit_revoke,
    bind_revoke,
    classify_family,
    classify_intent,
    classify_subject,
    classify_timeout,
    grants_send as revoke_grants_send,
    halt_blocks_issue,
    halt_blocks_revoke,
    later_withdraw_supersedes,
    mints_run_id,
    ready_is_authorized as revoke_ready_is_authorized,
    timeout_proves_concurrent_write as revoke_timeout_proves,
    try_bind,
)
from ofn.kernel.withdraw_pin import (
    grants_send as pin_grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_withdraw,
    pin_allows_send,
    pin_withdraw,
    ready_is_authorized as pin_ready_is_authorized,
    timeout_proves_concurrent_write as pin_timeout_proves,
    try_pin,
)

_RUN_A = "run-1780000000-armaaaaaaa"
_RUN_B = "run-1780000000-armbbbbbbb"
_RUN_C = "run-1780000000-armccccccc"


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_intent_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_intent("DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_missing_is_unknown_not_false(self):
        self.assertEqual(classify_intent(None), UNKNOWN)
        self.assertIsNone(classify_subject(None))
        self.assertIsNone(classify_family(None))
        self.assertNotEqual(classify_intent(None), "FALSE")


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_revoke(self):
        timed = admit_revoke(
            REVOKE, READY, withdrawn=False, timeout=True)
        self.assertIsNone(timed)
        sibling = admit_revoke(
            REVOKE, _RUN_B, withdrawn=False)
        self.assertIs(sibling, True)
        self.assertFalse(revoke_grants_send())

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(revoke_timeout_proves())
        self.assertFalse(pin_timeout_proves())
        self.assertEqual(classify_timeout(), UNKNOWN)
        table: dict[str, str] = {}
        self.assertIsNone(try_pin(
            table, REVOKE, READY, withdrawn=False, slot="a",
            timeout=True))
        self.assertEqual(table, {})


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_classify_and_revoke_held(self):
        admits = [
            admit_revoke("classify", rid, withdrawn=False)
            for rid in (_RUN_A, _RUN_B, _RUN_C)
        ]
        revokes = [
            admit_revoke(REVOKE, rid, withdrawn=False)
            for rid in (_RUN_A, _RUN_B, _RUN_C)
        ]
        self.assertEqual(len(admits), 3)
        self.assertEqual(len(revokes), 3)
        for d in admits + revokes:
            self.assertIs(d, True)
        self.assertFalse(revoke_grants_send())
        self.assertFalse(pin_grants_send())


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_bind_is_not_a_send(self):
        first = try_bind(
            REVOKE, READY, withdrawn=False, slot="slot-a")
        second = try_bind(
            REVOKE, READY, withdrawn=False, slot="slot-a")
        self.assertEqual(first, second)
        self.assertFalse(revoke_grants_send())
        table: dict[str, str] = {}
        pin_withdraw(table, first)
        pin_withdraw(table, second)
        self.assertFalse(pin_allows_send(first))


class Scenario5SealedNameStopsThatRowOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_revoke_continues(self):
        with self.assertRaises(FailClosedError):
            admit_revoke(REVOKE, "send_authorized", withdrawn=False)
        sibling = admit_revoke(REVOKE, _RUN_B, withdrawn=False)
        self.assertIs(sibling, True)
        self.assertFalse(revoke_grants_send())


class Scenario6GlobalHaltIsStartOnly(unittest.TestCase):
    def test_halt_refuses_issue_not_revoke_or_classify(self):
        self.assertTrue(is_halted("???"))
        self.assertTrue(halt_blocks_issue())
        self.assertFalse(halt_blocks_revoke())
        self.assertFalse(halt_blocks_pin())
        issued = admit_revoke(
            "issue", _RUN_A, withdrawn=False, halted=True)
        self.assertIs(issued, False)
        revoked = admit_revoke(
            REVOKE, READY, withdrawn=False, halted=True)
        self.assertIs(revoked, True)
        classified = admit_revoke(
            "classify", _RUN_B, withdrawn=False, halted=True)
        self.assertIs(classified, True)
        self.assertFalse(revoke_grants_send())

    def test_no_halt_knob_to_rearm_send(self):
        for fn in (admit_revoke, bind_revoke, pin_withdraw):
            params = inspect.signature(fn).parameters
            self.assertNotIn("halt_raw", params)
            self.assertNotIn("send_authorized", params)
            self.assertNotIn("resend", params)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_a_revoke_of_held_ready_and_not_a_send(self):
        with self.assertRaises(FailClosedError):
            admit_revoke(REVOKE, "quote_sent", withdrawn=False)
        resumed = admit_revoke(
            REVOKE, "campaign_envelope_ready", withdrawn=False)
        self.assertIs(resumed, True)
        self.assertFalse(revoke_grants_send())
        self.assertFalse(mints_run_id())
        self.assertTrue(later_withdraw_supersedes())
        self.assertTrue(later_disarm_supersedes())

    def test_already_withdrawn_is_not_a_send(self):
        d = admit_revoke(REVOKE, READY, withdrawn=True)
        self.assertIs(d, False)
        self.assertFalse(revoke_ready_is_authorized())
        self.assertFalse(pin_ready_is_authorized())
        self.assertIsNone(peek_withdraw({}, "missing"))


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_is_a_subject_send_is_sealed(self):
        self.assertEqual(
            classify_subject("campaign_envelope_ready"), READY)
        self.assertEqual(classify_family(False), HELD)
        with self.assertRaises(FailClosedError):
            classify_subject("send_authorized")
        with self.assertRaises(FailClosedError):
            classify_subject("quote_sent")
        self.assertFalse(revoke_ready_is_authorized())
        self.assertFalse(pin_ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
