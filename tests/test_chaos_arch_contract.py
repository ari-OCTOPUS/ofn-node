"""Owner-absent chaos — arch-bind + contract-pin (independent of #82).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the architecture-contract
layer: no store, no run_id mint, no fabricated witness. HALT is
not a bind or pin parameter. One arm's timeout cannot mark
another arm as a race. Recovery is observing a contract and is
still not a send.
"""

from __future__ import annotations

import unittest

from ofn.kernel.arch_bind import (
    bind_arch,
    classify_timeout,
    grants_send,
    halt_blocks_bind,
    ready_is_authorized,
    timeout_proves_concurrent,
)
from ofn.kernel.contract_pin import (
    halt_blocks_pin,
    pin_contract,
)
from ofn.kernel.errors import FailClosedError

_DIGEST = "c" * 64


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_contract_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            bind_arch(
                contract="DEAD_SOURCE", surface="kernel", intended="observe")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_pin_contract_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_contract(
                contract="DEAD_SOURCE", sha256=_DIGEST, byte_size=1,
                evidence_level="B")
        self.assertNotIn("FALSE", str(ctx.exception))


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_observe(self):
        timed = bind_arch(
            contract="task_envelope", surface="kernel", intended="observe",
            timed_out=True)
        self.assertTrue(timed.timed_out)
        self.assertTrue(timed.allowed)
        self.assertEqual(classify_timeout(), "UNKNOWN")
        sibling = bind_arch(
            contract="typed_event", surface="adapter", intended="observe")
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.timed_out)
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(timeout_proves_concurrent())
        self.assertEqual(classify_timeout(), "UNKNOWN")
        d = bind_arch(
            contract="run_store", surface="kernel", intended="bind",
            timed_out=True)
        self.assertTrue(d.allowed)
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_observe(self):
        decisions = [
            bind_arch(
                contract=name, surface="test", intended="observe")
            for name in ("task_envelope", "dedup", "receipt")
        ]
        self.assertEqual(len(decisions), 3)
        for d in decisions:
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_bind_is_not_a_send(self):
        first = bind_arch(
            contract="halt", surface="kernel", intended="bind")
        second = bind_arch(
            contract="halt", surface="kernel", intended="bind")
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(first.grants_send)
        self.assertFalse(grants_send())

    def test_second_identical_pin_is_not_a_send(self):
        first = pin_contract(
            contract="receipt", sha256=_DIGEST, byte_size=8,
            evidence_level="B")
        second = pin_contract(
            contract="receipt", sha256=_DIGEST, byte_size=8,
            evidence_level="B")
        self.assertEqual(first, second)
        self.assertFalse(first.grants_send)


class Scenario5SealedNameStopsThatRowOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_observe_continues(self):
        sealed = bind_arch(
            contract="send_authorized", surface="kernel", intended="bind")
        self.assertFalse(sealed.allowed)
        self.assertEqual(sealed.reason, "sealed_effect")
        sibling = bind_arch(
            contract="worktree_inventory", surface="doc", intended="observe")
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)


class Scenario6GlobalHaltIsNotABindParameter(unittest.TestCase):
    def test_halt_does_not_block_bind_or_pin(self):
        self.assertFalse(halt_blocks_bind())
        self.assertFalse(halt_blocks_pin())
        for name in ("task_envelope", "otel_map", "token_budget"):
            d = bind_arch(
                contract=name, surface="kernel", intended="observe")
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        import inspect
        self.assertNotIn("halt", inspect.signature(bind_arch).parameters)
        self.assertNotIn("halt", inspect.signature(pin_contract).parameters)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_an_observe_and_not_a_send(self):
        blocked = bind_arch(
            contract="quote_sent", surface="kernel", intended="bind")
        self.assertFalse(blocked.allowed)
        resumed = bind_arch(
            contract="task_envelope", surface="kernel", intended="observe")
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(grants_send())

    def test_mutate_is_never_recovery(self):
        d = bind_arch(
            contract="receipt", surface="doc", intended="mutate")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "mutate_forbidden")


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready = bind_arch(
            contract="campaign_envelope_ready", surface="kernel",
            intended="observe")
        sent = bind_arch(
            contract="quote_sent", surface="kernel", intended="observe")
        auth = bind_arch(
            contract="send_authorized", surface="kernel", intended="observe")
        for d in (ready, sent, auth):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual(ready.contract, auth.contract)

    def test_pin_refuses_both_ready_and_authorized(self):
        with self.assertRaises(FailClosedError):
            pin_contract(
                contract="campaign_envelope_ready", sha256=_DIGEST,
                byte_size=1, evidence_level="B")
        with self.assertRaises(FailClosedError):
            pin_contract(
                contract="send_authorized", sha256=_DIGEST,
                byte_size=1, evidence_level="B")


if __name__ == "__main__":
    unittest.main()
