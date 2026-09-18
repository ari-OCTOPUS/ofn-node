"""Owner-absent chaos — horizon-class + cutoff-pin (independent of #82).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the horizon/cutoff layer:
no fabricated witness, no store write, no run_id mint. HALT
stops STARTS only. One arm's timeout cannot mark another arm
SUSPECTED. Recovery is a classify/validate and is still not a send.
Equal is UNKNOWN, not closed-as-False.
"""

from __future__ import annotations

import unittest

from ofn.kernel.cutoff_pin import (
    grants_send as pin_grants_send,
    halt_blocks_pin,
    pin_cutoff,
    ready_is_authorized as pin_ready_is_authorized,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.horizon_class import (
    admit_horizon,
    classify_timeout,
    grants_send as horizon_grants_send,
    halt_blocks_classify,
    halt_blocks_inflight_admit,
    mints_run_id,
    ready_is_authorized as horizon_ready_is_authorized,
    timeout_proves_concurrent as horizon_timeout_proves,
)


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_horizon_kind_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_horizon(intended="admit", kind="DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_cutoff_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_cutoff(cutoff="DEAD_SOURCE", epoch_s=10)
        self.assertNotIn("FALSE", str(ctx.exception))


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_classify(self):
        timed = admit_horizon(
            intended="classify", kind="mint",
            now_epoch_s=10, horizon_epoch_s=20, timed_out=True)
        self.assertEqual(timed.status, "UNKNOWN")
        self.assertEqual(timed.position, "unknown")
        self.assertTrue(timed.allowed)
        sibling = admit_horizon(
            intended="classify", kind="validate",
            now_epoch_s=10, horizon_epoch_s=20)
        self.assertTrue(sibling.allowed)
        self.assertEqual(sibling.status, "VERIFIED")
        self.assertEqual(sibling.position, "inside")
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(horizon_timeout_proves())
        self.assertEqual(classify_timeout(), "UNKNOWN")
        d = admit_horizon(
            intended="admit", kind="validate",
            now_epoch_s=10, horizon_epoch_s=20,
            activity="concurrent", timed_out=True)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.reason, "unknown_horizon")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_classify_and_pin(self):
        horizons = [
            admit_horizon(
                intended="classify", kind=kind,
                now_epoch_s=10, horizon_epoch_s=20)
            for kind in ("validate", "replay", "receipt_bind")
        ]
        pins = [
            pin_cutoff(cutoff=name, epoch_s=20, now_epoch_s=10)
            for name in ("validate_cutoff", "replay_cutoff", "receipt_cutoff")
        ]
        self.assertEqual(len(horizons), 3)
        self.assertEqual(len(pins), 3)
        for d in horizons:
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)
        for p in pins:
            self.assertEqual(p.position, "before")
            self.assertFalse(p.grants_send)


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_admit_is_not_a_send(self):
        first = admit_horizon(
            intended="classify", kind="replay",
            now_epoch_s=10, horizon_epoch_s=20)
        second = admit_horizon(
            intended="classify", kind="replay",
            now_epoch_s=10, horizon_epoch_s=20)
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(first.grants_send)
        self.assertFalse(horizon_grants_send())
        self.assertFalse(pin_grants_send())
        a = pin_cutoff(cutoff="replay_cutoff", epoch_s=20, now_epoch_s=10)
        b = pin_cutoff(cutoff="replay_cutoff", epoch_s=20, now_epoch_s=10)
        self.assertEqual(a, b)
        self.assertFalse(a.grants_send)


class Scenario5SealedNameStopsThatRowOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_classify_continues(self):
        sealed = admit_horizon(intended="admit", kind="send_authorized")
        self.assertFalse(sealed.allowed)
        self.assertEqual(sealed.reason, "sealed_effect")
        sibling = admit_horizon(
            intended="classify", kind="validate",
            now_epoch_s=10, horizon_epoch_s=20)
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)


class Scenario6GlobalHaltIsStartOnly(unittest.TestCase):
    def test_halt_refuses_mint_admit_not_classify(self):
        mint = admit_horizon(
            intended="admit", kind="mint",
            now_epoch_s=10, horizon_epoch_s=20, halted=True)
        self.assertFalse(mint.allowed)
        self.assertEqual(mint.reason, "halt_active")
        classify = admit_horizon(
            intended="classify", kind="mint",
            now_epoch_s=10, horizon_epoch_s=20, halted=True)
        self.assertTrue(classify.allowed)
        validate = admit_horizon(
            intended="admit", kind="validate",
            now_epoch_s=10, horizon_epoch_s=20, halted=True)
        self.assertTrue(validate.allowed)
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_inflight_admit())
        self.assertFalse(halt_blocks_pin())
        pin = pin_cutoff(cutoff="mint_cutoff", epoch_s=20, now_epoch_s=10)
        self.assertEqual(pin.position, "before")
        self.assertFalse(pin.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        import inspect
        params = inspect.signature(admit_horizon).parameters
        self.assertNotIn("halt_raw", params)
        self.assertNotIn("send_authorized", params)
        self.assertNotIn("resend", params)
        pin_params = inspect.signature(pin_cutoff).parameters
        self.assertNotIn("halt", pin_params)
        self.assertNotIn("send_authorized", pin_params)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_a_classify_and_not_a_send(self):
        blocked = admit_horizon(
            intended="admit", kind="quote_sent")
        self.assertFalse(blocked.allowed)
        resumed = admit_horizon(
            intended="classify", kind="replay",
            now_epoch_s=10, horizon_epoch_s=20)
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(horizon_grants_send())
        self.assertFalse(mints_run_id())

    def test_at_edge_recovery_is_unknown_not_a_send(self):
        d = admit_horizon(
            intended="admit", kind="validate",
            now_epoch_s=20, horizon_epoch_s=20)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_horizon")
        self.assertEqual(d.position, "at_edge")
        self.assertFalse(d.grants_send)


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready_h = admit_horizon(
            intended="classify", kind="campaign_envelope_ready")
        sent_h = admit_horizon(intended="classify", kind="quote_sent")
        auth_h = admit_horizon(intended="classify", kind="send_authorized")
        for d in (ready_h, sent_h, auth_h):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        self.assertFalse(horizon_ready_is_authorized())
        self.assertFalse(pin_ready_is_authorized())
        self.assertNotEqual(ready_h.kind, auth_h.kind)
        with self.assertRaises(FailClosedError):
            pin_cutoff(cutoff="campaign_envelope_ready", epoch_s=10)
        with self.assertRaises(FailClosedError):
            pin_cutoff(cutoff="send_authorized", epoch_s=10)


if __name__ == "__main__":
    unittest.main()
