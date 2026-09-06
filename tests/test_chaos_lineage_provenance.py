"""Owner-absent chaos — lineage-class + provenance-pin (independent of #82).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the lineage/provenance layer:
no fabricated witness, no store write, no run_id mint. HALT
stops STARTS only. One arm's timeout cannot mark another arm
SUSPECTED. Recovery is an observe and is still not a send.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.lineage_class import (
    admit_lineage,
    classify_timeout,
    grants_send as lineage_grants_send,
    halt_blocks_succeed,
    missing_prior_is_empty,
    mints_run_id,
    ready_is_authorized as lineage_ready_is_authorized,
    timeout_proves_concurrent as lineage_timeout_proves,
)
from ofn.kernel.provenance_pin import (
    grants_send as pin_grants_send,
    halt_blocks_pin,
    orphan_is_contained,
    pin_provenance,
    ready_is_authorized as pin_ready_is_authorized,
    timeout_proves_concurrent as pin_timeout_proves,
    unknown_is_contained,
)

_RUN_A = "run-1780000000-armaaaaaaa"
_RUN_B = "run-1780000000-armbbbbbbb"
_RUN_C = "run-1780000000-armccccccc"


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_lineage_activity_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_lineage(
                intended="mint", node_id=_RUN_A, activity="DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_missing_prior_is_unknown_not_empty(self):
        d = admit_lineage(
            intended="succeed", node_id=_RUN_B, parent_id=_RUN_A)
        self.assertEqual(d.reason, "unknown_prior")
        self.assertEqual(d.role, "unknown")
        self.assertFalse(missing_prior_is_empty())
        self.assertFalse(d.grants_send)


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_observe(self):
        timed = admit_lineage(
            intended="observe", node_id=_RUN_A, timed_out=True)
        self.assertEqual(timed.status, "UNKNOWN")
        self.assertTrue(timed.allowed)
        sibling = admit_lineage(intended="observe", node_id=_RUN_B)
        self.assertTrue(sibling.allowed)
        self.assertEqual(sibling.status, "VERIFIED")
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(lineage_timeout_proves())
        self.assertFalse(pin_timeout_proves())
        self.assertEqual(classify_timeout(), "UNKNOWN")
        d = admit_lineage(
            intended="succeed", node_id=_RUN_B, parent_id=_RUN_A,
            prior=frozenset({_RUN_A}), activity="concurrent",
            timed_out=True)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.reason, "unknown_activity")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_observe_and_contained_succeed(self):
        observes = [
            admit_lineage(intended="observe", node_id=rid)
            for rid in (_RUN_A, _RUN_B, _RUN_C)
        ]
        root = admit_lineage(intended="mint", node_id=_RUN_A)
        children = [
            admit_lineage(
                intended="succeed", node_id=rid, parent_id=_RUN_A,
                prior=frozenset({_RUN_A}))
            for rid in (_RUN_B, _RUN_C)
        ]
        self.assertEqual(len(observes), 3)
        self.assertTrue(root.allowed)
        self.assertEqual(root.role, "root")
        for d in observes + children:
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)
        pins = [
            pin_provenance(role="root", intended="mint", node_id=_RUN_A),
            pin_provenance(
                role="successor", intended="succeed",
                node_id=_RUN_B, parent_id=_RUN_A),
            pin_provenance(
                role="successor", intended="succeed",
                node_id=_RUN_C, parent_id=_RUN_A),
        ]
        for pin in pins:
            self.assertTrue(pin.allowed)
            self.assertFalse(pin.grants_send)


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_observe_is_not_a_send(self):
        first = admit_lineage(intended="observe", node_id=_RUN_A)
        second = admit_lineage(intended="observe", node_id=_RUN_A)
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(first.grants_send)
        self.assertFalse(lineage_grants_send())
        self.assertFalse(pin_grants_send())


class Scenario5SealedNameStopsThatRowOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_observe_continues(self):
        sealed = admit_lineage(intended="mint", node_id="send_authorized")
        self.assertFalse(sealed.allowed)
        self.assertEqual(sealed.reason, "sealed_effect")
        sibling = admit_lineage(intended="observe", node_id=_RUN_B)
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)


class Scenario6GlobalHaltIsStartOnly(unittest.TestCase):
    def test_halt_refuses_mint_not_succeed_or_observe(self):
        mint = admit_lineage(intended="mint", node_id=_RUN_A, halted=True)
        self.assertFalse(mint.allowed)
        self.assertEqual(mint.reason, "halt_start")
        succeed = admit_lineage(
            intended="succeed", node_id=_RUN_B, parent_id=_RUN_A,
            prior=frozenset({_RUN_A}), halted=True)
        self.assertTrue(succeed.allowed)
        observe = admit_lineage(
            intended="observe", node_id=_RUN_C, halted=True)
        self.assertTrue(observe.allowed)
        self.assertFalse(halt_blocks_succeed())
        self.assertFalse(halt_blocks_pin())
        self.assertFalse(succeed.grants_send)
        self.assertFalse(observe.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        import inspect
        for fn in (admit_lineage, pin_provenance):
            params = inspect.signature(fn).parameters
            self.assertNotIn("halt_raw", params)
            self.assertNotIn("send_authorized", params)
            self.assertNotIn("resend", params)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_an_observe_and_not_a_send(self):
        blocked = admit_lineage(intended="observe", node_id="quote_sent")
        self.assertFalse(blocked.allowed)
        resumed = admit_lineage(intended="observe", node_id=_RUN_C)
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(lineage_grants_send())
        self.assertFalse(mints_run_id())

    def test_orphan_is_never_recovery(self):
        d = admit_lineage(
            intended="succeed", node_id=_RUN_B, parent_id=_RUN_C,
            prior=frozenset({_RUN_A}))
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "orphan_parent")
        pin = pin_provenance(
            role="orphan", intended="succeed",
            node_id=_RUN_B, parent_id=_RUN_C)
        self.assertFalse(pin.allowed)
        self.assertEqual(pin.reason, "unbound_orphan")
        self.assertFalse(orphan_is_contained())
        self.assertFalse(unknown_is_contained())


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready_l = admit_lineage(
            intended="observe", node_id="campaign_envelope_ready")
        sent_l = admit_lineage(intended="observe", node_id="quote_sent")
        auth_l = admit_lineage(intended="observe", node_id="send_authorized")
        ready_p = pin_provenance(
            role="root", intended="mint",
            node_id="campaign_envelope_ready")
        sent_p = pin_provenance(
            role="root", intended="mint", node_id="quote_sent")
        auth_p = pin_provenance(
            role="root", intended="mint", node_id="send_authorized")
        for d in (ready_l, sent_l, auth_l, ready_p, sent_p, auth_p):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        self.assertFalse(lineage_ready_is_authorized())
        self.assertFalse(pin_ready_is_authorized())
        self.assertNotEqual(ready_l.node_id, auth_l.node_id)
        self.assertNotEqual(ready_p.node_id, auth_p.node_id)


if __name__ == "__main__":
    unittest.main()
