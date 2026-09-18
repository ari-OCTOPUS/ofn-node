"""Owner-absent chaos — mint-fence + append-class composition.

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the mint and append layer:
no store, no fabricated witness. HALT is not a parameter. One
arm's timeout cannot refuse another arm's mint or append.
Recovery is admitting a fresh mint / spine append and is still
not a send.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import RUN_CREATED, RUN_REJECTED, TOOL_INVOKED
from ofn.kernel.append_class import (
    admit_append,
    grants_send as append_grants_send,
    halt_blocks_append,
    ready_is_authorized as append_ready_is_authorized,
)
from ofn.kernel.mint_fence import (
    admit_mint,
    grants_send as mint_grants_send,
    halt_blocks_mint,
    ready_is_authorized as mint_ready_is_authorized,
)

_A = "run-1756857700-aaaaaaaaaa"
_B = "run-1756857701-bbbbbbbbbb"
_C = "run-1756857702-cccccccccc"


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_boundary_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_mint(boundary="DEAD_SOURCE", proposed_id=_A,
                       existing_ids=set())
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_mode_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_append(mode="DEAD_MODE", kind=RUN_CREATED)
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_missing_registry_is_unknown_not_empty(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_mint(boundary="trusted_boundary", proposed_id=_A,
                       existing_ids=None)
        self.assertIn("UNKNOWN", str(ctx.exception))


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_mint(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("arm A fetch timed out")
        sibling = admit_mint(boundary="trusted_boundary",
                             proposed_id=_B, existing_ids={_A})
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("lock wait timed out")
        d = admit_append(mode="append", kind=TOOL_INVOKED)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_mint_distinct_ids(self):
        registry: set[str] = set()
        decisions = []
        for proposed in (_A, _B, _C):
            d = admit_mint(boundary="trusted_boundary",
                           proposed_id=proposed, existing_ids=registry)
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)
            registry.add(proposed)
            decisions.append(d)
        self.assertEqual(len(decisions), 3)
        self.assertEqual(len(registry), 3)

    def test_three_arms_append_tool_invoked(self):
        decisions = [
            admit_append(mode="append", kind=TOOL_INVOKED)
            for _arm in ("a", "b", "c")
        ]
        self.assertEqual(len(decisions), 3)
        for d in decisions:
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_mint_is_collision_not_a_send(self):
        first = admit_mint(boundary="trusted_boundary",
                           proposed_id=_A, existing_ids=set())
        second = admit_mint(boundary="trusted_boundary",
                            proposed_id=_A, existing_ids={_A})
        self.assertTrue(first.allowed)
        self.assertFalse(second.allowed)
        self.assertEqual(second.reason, "id_collision")
        self.assertFalse(first.grants_send)
        self.assertFalse(second.grants_send)
        self.assertFalse(mint_grants_send())

    def test_second_identical_append_is_not_a_send(self):
        first = admit_append(mode="append", kind="EXECUTION_RECEIPT")
        second = admit_append(mode="append", kind="EXECUTION_RECEIPT")
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(append_grants_send())


class Scenario5SealedNameStopsThatWriteOnly(unittest.TestCase):
    def test_sealed_mint_refused_sibling_continues(self):
        sealed = admit_mint(boundary="trusted_boundary",
                            proposed_id="send_authorized",
                            existing_ids=set())
        self.assertFalse(sealed.allowed)
        sibling = admit_mint(boundary="trusted_boundary",
                             proposed_id=_A, existing_ids=set())
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)

    def test_sealed_append_refused_sibling_continues(self):
        sealed = admit_append(mode="append", kind="quote_sent")
        self.assertFalse(sealed.allowed)
        sibling = admit_append(mode="append", kind=TOOL_INVOKED)
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)


class Scenario6GlobalHaltIsNotAParameter(unittest.TestCase):
    def test_halt_does_not_block_in_flight_mint_or_append(self):
        self.assertFalse(halt_blocks_mint())
        self.assertFalse(halt_blocks_append())
        for proposed in (_A, _B, _C):
            m = admit_mint(boundary="trusted_boundary",
                           proposed_id=proposed, existing_ids=set())
            self.assertTrue(m.allowed)
            self.assertFalse(m.grants_send)
            a = admit_append(mode="append", kind=TOOL_INVOKED)
            self.assertTrue(a.allowed)
            self.assertFalse(a.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        import inspect
        self.assertNotIn("halt", inspect.signature(admit_mint).parameters)
        self.assertNotIn("halt", inspect.signature(admit_append).parameters)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_a_fresh_mint_and_not_a_send(self):
        blocked = admit_mint(boundary="trusted_boundary",
                             proposed_id="quote_sent", existing_ids=set())
        self.assertFalse(blocked.allowed)
        resumed = admit_mint(boundary="trusted_boundary",
                             proposed_id=_A, existing_ids=set())
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(mint_grants_send())

    def test_resume_append_is_not_a_send(self):
        blocked = admit_append(mode="rewrite", kind=RUN_CREATED)
        self.assertFalse(blocked.allowed)
        resumed = admit_append(mode="append", kind=RUN_CREATED)
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)

    def test_refusal_witness_is_still_an_append(self):
        d = admit_append(mode="append", kind=RUN_REJECTED)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready_m = admit_mint(boundary="trusted_boundary",
                             proposed_id="campaign_envelope_ready",
                             existing_ids=set())
        sent_m = admit_mint(boundary="trusted_boundary",
                            proposed_id="quote_sent",
                            existing_ids=set())
        auth_m = admit_mint(boundary="trusted_boundary",
                            proposed_id="send_authorized",
                            existing_ids=set())
        for d in (ready_m, sent_m, auth_m):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        self.assertFalse(mint_ready_is_authorized())
        self.assertNotEqual(ready_m.proposed_id, auth_m.proposed_id)

        ready_a = admit_append(mode="append",
                               kind="campaign_envelope_ready")
        auth_a = admit_append(mode="append", kind="send_authorized")
        for d in (ready_a, auth_a):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
        self.assertFalse(append_ready_is_authorized())
        self.assertNotEqual(ready_a.kind, auth_a.kind)


if __name__ == "__main__":
    unittest.main()
