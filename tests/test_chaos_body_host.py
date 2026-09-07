"""Owner-absent chaos — body-class / host-pin composition.

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the body/host layer: no
store, no run_id mint, no fabricated second node. HALT is not a
classify or pin parameter. One arm's timeout cannot mark another
arm SUSPECTED. Recovery is observing a pin and is still not a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.body_class import (
    admit_body,
    classify_timeout as body_timeout,
    grants_send as body_grants_send,
    halt_blocks_classify,
    hashes_body,
    one_host_proves_missing,
    ready_is_authorized as body_ready_is_authorized,
    timeout_proves_concurrent as body_timeout_proves,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.host_pin import (
    classify_timeout as host_timeout,
    grants_send as host_grants_send,
    halt_blocks_pin,
    invents_second_node,
    pin_host,
    promotes_to_system_wide,
    ready_is_authorized as host_ready_is_authorized,
    timeout_proves_concurrent as host_timeout_proves,
)

NODE_A = "node-a"
NODE_B = "node-b"
NODE_C = "node-c"


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_missing_location_is_not_classified_false(self):
        d = admit_body(None)
        self.assertEqual(d.body_class, "UNKNOWN")
        self.assertIsNot(d.body_class, False)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)

    def test_unknown_present_string_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_body("DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("body", str(ctx.exception).lower())


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_pin(self):
        timed = pin_host("on_this_host", NODE_A, timed_out=True)
        self.assertEqual(timed.pin_class, "UNKNOWN")
        self.assertTrue(timed.allowed)
        sibling = pin_host("not_on_this_host", NODE_B)
        self.assertTrue(sibling.allowed)
        self.assertEqual(sibling.pin_class, "BOUND")
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(body_timeout_proves())
        self.assertFalse(host_timeout_proves())
        self.assertEqual(body_timeout(), "UNKNOWN")
        self.assertEqual(host_timeout(), "UNKNOWN")
        d = admit_body("on_this_host", timed_out=True)
        self.assertEqual(d.body_class, "UNKNOWN")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_body_and_pin(self):
        decisions = [
            admit_body(token)
            for token in ("on_this_host", "not_on_this_host", "absent_here")
        ]
        self.assertEqual(len(decisions), 3)
        for d in decisions:
            self.assertTrue(d.allowed)
            self.assertIn(d.body_class, {"ON_THIS_HOST", "NOT_ON_THIS_HOST"})
            self.assertFalse(d.grants_send)
        pins = [
            pin_host("on_this_host", NODE_A),
            pin_host("not_on_this_host", NODE_B),
            pin_host("body_not_on_this_host", NODE_C),
        ]
        for p in pins:
            self.assertTrue(p.allowed)
            self.assertEqual(p.pin_class, "BOUND")
            self.assertFalse(p.grants_send)
            self.assertFalse(invents_second_node())
            self.assertFalse(promotes_to_system_wide())


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_admit_is_not_a_send(self):
        first = admit_body("on_this_host")
        second = admit_body("on_this_host")
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(first.grants_send)
        restated = pin_host("on_this_host", NODE_A)
        again = pin_host("on_this_host", NODE_A)
        self.assertEqual(restated, again)
        self.assertEqual(restated.pin_class, "BOUND")
        self.assertFalse(restated.grants_send)
        self.assertFalse(body_grants_send())
        self.assertFalse(host_grants_send())


class Scenario5SealedNameStopsThatRowOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_classify_continues(self):
        sealed = admit_body("send_authorized")
        self.assertFalse(sealed.allowed)
        self.assertEqual(sealed.reason, "sealed_effect")
        sibling = admit_body("on_this_host")
        self.assertTrue(sibling.allowed)
        self.assertEqual(sibling.body_class, "ON_THIS_HOST")
        self.assertFalse(sibling.grants_send)
        sealed_pin = pin_host("quote_sent", NODE_A)
        self.assertFalse(sealed_pin.allowed)
        live = pin_host("on_this_host", NODE_B)
        self.assertTrue(live.allowed)


class Scenario6GlobalHaltIsNotAClassifyParameter(unittest.TestCase):
    def test_halt_does_not_block_body_or_host(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_pin())
        for token in ("on_this_host", "not_on_this_host", "absent_here"):
            d = admit_body(token)
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)
        p = pin_host("on_this_host", NODE_A)
        self.assertTrue(p.allowed)
        self.assertFalse(p.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        body_params = inspect.signature(admit_body).parameters
        host_params = inspect.signature(pin_host).parameters
        for params in (body_params, host_params):
            self.assertNotIn("halt", params)
            self.assertNotIn("halt_raw", params)
            self.assertNotIn("send_authorized", params)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_a_classify_and_not_a_send(self):
        blocked = pin_host("campaign_envelope_ready", "send_authorized")
        self.assertFalse(blocked.allowed)
        resumed = pin_host("on_this_host", NODE_A)
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(body_grants_send())
        self.assertFalse(host_grants_send())
        self.assertFalse(hashes_body())
        self.assertFalse(invents_second_node())
        self.assertFalse(one_host_proves_missing())

    def test_recovery_does_not_hash_a_body(self):
        d = admit_body("on_this_host")
        self.assertTrue(d.allowed)
        self.assertFalse(hashes_body())
        self.assertFalse(invents_second_node())


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready = admit_body("campaign_envelope_ready")
        sent = admit_body("quote_sent")
        auth = admit_body("send_authorized")
        for d in (ready, sent, auth):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        self.assertFalse(body_ready_is_authorized())
        self.assertFalse(host_ready_is_authorized())
        self.assertNotEqual(ready.location, auth.location)
        folded = pin_host("campaign_envelope_ready", "send_authorized")
        self.assertFalse(folded.allowed)
        self.assertEqual(folded.reason, "sealed_effect")
        missing = pin_host("body_missing", NODE_A)
        self.assertFalse(missing.allowed)
        self.assertEqual(missing.reason, "missing_claim")
        wide = pin_host("on_this_host", NODE_A, vantage="system_wide")
        self.assertFalse(wide.allowed)
        self.assertEqual(wide.reason, "promotion_refused")


if __name__ == "__main__":
    unittest.main()
