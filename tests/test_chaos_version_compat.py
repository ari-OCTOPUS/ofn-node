"""Owner-absent chaos — version-class + compat-pin (independent of #82).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the version layer: no
store write, no run_id mint, no fabricated witness. HALT stops
STARTS only. One arm's timeout cannot mark another arm
SUSPECTED. Recovery is a classify/pin and is still not a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.compat_pin import (
    grants_send as pin_grants_send,
    halt_blocks_pin,
    pin_compat,
    ready_is_authorized as pin_ready_is_authorized,
    timeout_proves_concurrent as pin_timeout_proves,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.version_class import (
    admit_version,
    classify_timeout,
    grants_send as version_grants_send,
    halt_blocks_classify,
    mints_run_id,
    ready_is_authorized as version_ready_is_authorized,
    timeout_proves_concurrent as version_timeout_proves,
)


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_intent_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_version(intended="DEAD_SOURCE", version=1)
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_version_class_is_not_false(self):
        d = admit_version(intended="classify", version=99)
        self.assertEqual(d.version_class, "UNKNOWN_VERSION")
        self.assertNotEqual(d.version_class, "FALSE")
        self.assertTrue(d.allowed)


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_classify(self):
        timed = admit_version(intended="classify", version=1, timed_out=True)
        self.assertEqual(timed.status, "UNKNOWN")
        self.assertTrue(timed.allowed)
        sibling = admit_version(intended="classify", version=1)
        self.assertTrue(sibling.allowed)
        self.assertEqual(sibling.status, "VERIFIED")
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(version_timeout_proves())
        self.assertFalse(pin_timeout_proves())
        self.assertEqual(classify_timeout(), "UNKNOWN")
        d = admit_version(
            intended="admit", version=1, activity="concurrent",
            timed_out=True)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.reason, "unknown_activity")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_classify_and_pin(self):
        versions = [
            admit_version(intended="classify", version=1)
            for _ in range(3)
        ]
        pins = [pin_compat(left=1, right=1) for _ in range(3)]
        self.assertEqual(len(versions), 3)
        self.assertEqual(len(pins), 3)
        for d in versions:
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)
        for p in pins:
            self.assertTrue(p.compatible)
            self.assertFalse(p.grants_send)


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_admit_is_not_a_send(self):
        first = admit_version(intended="classify", version=1)
        second = admit_version(intended="classify", version=1)
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(first.grants_send)
        self.assertFalse(version_grants_send())
        self.assertFalse(pin_grants_send())
        pin_a = pin_compat(left=1, right=1)
        pin_b = pin_compat(left=1, right=1)
        self.assertEqual(pin_a, pin_b)
        self.assertFalse(pin_a.grants_send)


class Scenario5SealedNameStopsThatRowOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_classify_continues(self):
        sealed = admit_version(intended="send_authorized", version=1)
        self.assertFalse(sealed.allowed)
        self.assertEqual(sealed.reason, "sealed_effect")
        sibling = admit_version(intended="classify", version=1)
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)


class Scenario6GlobalHaltIsStartOnly(unittest.TestCase):
    def test_halt_refuses_admit_not_classify_or_pin(self):
        blocked = admit_version(intended="admit", version=1, halted=True)
        self.assertFalse(blocked.allowed)
        self.assertEqual(blocked.reason, "halt_active")
        classify = admit_version(
            intended="classify", version=1, halted=True)
        self.assertTrue(classify.allowed)
        pin = pin_compat(left=1, right=1)
        self.assertTrue(pin.compatible)
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_pin())
        self.assertFalse(classify.grants_send)
        self.assertFalse(pin.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        for fn in (admit_version, pin_compat):
            params = inspect.signature(fn).parameters
            self.assertNotIn("halt_raw", params)
            self.assertNotIn("send_authorized", params)
            self.assertNotIn("resend", params)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_a_classify_or_pin_and_not_a_send(self):
        blocked = admit_version(intended="classify", version="quote_sent")
        self.assertFalse(blocked.allowed)
        resumed = admit_version(intended="classify", version=1)
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(version_grants_send())
        self.assertFalse(mints_run_id())
        pin = pin_compat(left=1, right=1)
        self.assertTrue(pin.compatible)
        self.assertFalse(pin.grants_send)

    def test_unknown_version_is_not_recovery_to_v2(self):
        d = admit_version(intended="admit", version=2)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_version")
        pin = pin_compat(left=2, right=2)
        self.assertIs(pin.compatible, False)


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready_v = admit_version(
            intended="classify", version="campaign_envelope_ready")
        sent_v = admit_version(intended="classify", version="quote_sent")
        auth_v = admit_version(intended="classify", version="send_authorized")
        for d in (ready_v, sent_v, auth_v):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        with self.assertRaises(FailClosedError):
            pin_compat(left="campaign_envelope_ready", right=1)
        with self.assertRaises(FailClosedError):
            pin_compat(left=1, right="send_authorized")
        self.assertFalse(version_ready_is_authorized())
        self.assertFalse(pin_ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
