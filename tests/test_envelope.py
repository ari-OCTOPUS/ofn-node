"""Contract tests for TaskEnvelope v1 (P1 skeleton).

Every test is a rule that must hold forever. The negative controls are
the point: a boundary that only accepts good input has never been tested.
"""

from __future__ import annotations

import unittest

from ofn.kernel.callbudget import CallBudget
from ofn.kernel.envelope import (
    AUTHORITY_LEVELS, RISK_TIERS, TaskEnvelope, create_envelope, mint_run_id,
    rung_for_authority,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.routing import Rung

import hashlib

_GOAL = "score three OCP leads for the renewal radar"
_DEADLINE = "2026-09-09T12:00:00Z"
_AC = hashlib.sha256(b"acceptance: reply rate >= 1/6 by 2026-09-09").hexdigest()
_NOW = 1780000000
_RAND = "a1b2c3d4e5f6a7b8"


def _envelope(**overrides):
    kwargs = dict(
        goal=_GOAL, risk_tier="YELLOW", authority_level="A2",
        idempotency_key="idem-1", acceptance_criteria_hash=_AC,
        now_epoch_s=_NOW, rand=_RAND, deadline_iso=_DEADLINE,
    )
    kwargs.update(overrides)
    return create_envelope(**kwargs)


class MintingBoundary(unittest.TestCase):
    def test_factory_mints_strict_run_ids(self):
        env = _envelope()
        self.assertTrue(env.run_id.startswith("run-"))
        self.assertIn(env.run_id, {env.run_id})  # str, non-empty by construction

    def test_two_calls_different_rand_give_different_run_ids(self):
        a = _envelope(rand="a1b2c3d4e5f6a7b8")
        b = _envelope(rand="b1b2c3d4e5f6a7b8")
        self.assertNotEqual(a.run_id, b.run_id)

    def test_short_rand_refused(self):
        with self.assertRaises(FailClosedError):
            mint_run_id(_NOW, "abc")

    def test_run_id_cannot_be_injected_via_dataclass(self):
        # The dataclass itself enforces the format, so an arm cannot smuggle
        # a hand-made run_id like "run-1-myrun" past the boundary regex.
        with self.assertRaises(FailClosedError):
            TaskEnvelope(
                version=1, run_id="run-1-myrun", goal=_GOAL, risk_tier="GREEN",
                authority_level="A1", idempotency_key="idem-x",
                acceptance_criteria_hash=_AC, budget_tokens=0,
                budget_aud_cents=0, deadline_iso=_DEADLINE,
                allowed_tools=(), parent_evidence=())


class ValidationNegativeControls(unittest.TestCase):
    def test_empty_goal_refused(self):
        with self.assertRaises(FailClosedError):
            _envelope(goal="   ")

    def test_unknown_risk_tier_refused(self):
        with self.assertRaises(FailClosedError):
            _envelope(risk_tier="ORANGE-TUESDAY")

    def test_unknown_authority_refused(self):
        with self.assertRaises(FailClosedError):
            _envelope(authority_level="A9")

    def test_missing_idempotency_key_refused(self):
        with self.assertRaises(FailClosedError):
            _envelope(idempotency_key="")

    def test_post_hoc_looking_acceptance_hash_refused(self):
        # not a sha256 hex digest — e.g. a human pasted a sentence
        with self.assertRaises(FailClosedError):
            _envelope(acceptance_criteria_hash="looks-fine-to-me")

    def test_bad_deadline_refused(self):
        with self.assertRaises(FailClosedError):
            _envelope(deadline_iso="next tuesday-ish")

    def test_a3_without_rollback_plan_refused(self):
        with self.assertRaises(FailClosedError):
            _envelope(authority_level="A3")

    def test_a3_with_plan_but_no_rollback_ref_refused(self):
        with self.assertRaises(FailClosedError):
            _envelope(authority_level="A3", rollback_plan="delete drafts")

    def test_a3_with_plan_and_ref_accepted(self):
        env = _envelope(authority_level="A3", rollback_plan="delete drafts",
                        rollback_ref="rb-20260902-001")
        self.assertEqual(env.rollback_ref, "rb-20260902-001")

    def test_a3_with_rollback_plan_accepted(self):
        env = _envelope(authority_level="A3", rollback_plan="delete drafts, no external effect existed",
                         rollback_ref="rb-fixture-1")
        self.assertEqual(env.authority_level, "A3")

    def test_negative_budget_refused(self):
        with self.assertRaises(FailClosedError):
            _envelope(budget_aud_cents=-1)


class BudgetWiring(unittest.TestCase):
    def test_authority_maps_conservatively_to_rungs(self):
        self.assertEqual(rung_for_authority("A3"), Rung.REMOTE_DEEP)
        self.assertEqual(rung_for_authority("A2"), Rung.REMOTE)

    def test_a3_runs_hit_the_deep_cap(self):
        env = _envelope(authority_level="A3", rollback_plan="none needed, dry run",
                         rollback_ref="rb-fixture-2")
        budget = CallBudget()  # DEFAULT_CAPS: REMOTE_DEEP == 5
        now = 1780000000
        allowed = 0
        while budget.allows(env.rung(), now):
            budget.record(env.rung(), now)
            allowed += 1
            self.assertTrue(allowed <= 5)
        self.assertEqual(allowed, 5)  # the cap is a cap, not a suggestion


class PerRunTokenCeiling(unittest.TestCase):
    def test_zero_budget_authorizes_no_spend(self):
        env = _envelope()  # default budget_tokens == 0
        self.assertTrue(env.may_consume_tokens(0, 0))
        self.assertFalse(env.may_consume_tokens(0, 1))

    def test_ceiling_is_a_ceiling(self):
        env = _envelope(budget_tokens=10)
        self.assertTrue(env.may_consume_tokens(8, 2))
        self.assertFalse(env.may_consume_tokens(8, 3))

    def test_negative_request_refused(self):
        env = _envelope(budget_tokens=10)
        with self.assertRaises(FailClosedError):
            env.may_consume_tokens(0, -1)


class AllowedToolsAreAClosedSet(unittest.TestCase):
    def test_empty_allowlist_permits_ordinary_tools(self):
        env = _envelope()
        self.assertTrue(env.tool_allowed("score"))

    def test_nonempty_allowlist_refuses_unnamed_tool(self):
        env = _envelope(allowed_tools=("score", "draft"))
        self.assertTrue(env.tool_allowed("score"))
        self.assertFalse(env.tool_allowed("smtp"))

    def test_sealed_effect_name_is_never_a_tool(self):
        env = _envelope()
        self.assertFalse(env.tool_allowed("send_authorized"))
        self.assertFalse(env.tool_allowed("quote_sent"))
        self.assertFalse(env.tool_allowed("campaign_envelope_ready"))

    def test_allowlist_cannot_name_a_sealed_effect(self):
        with self.assertRaises(FailClosedError):
            _envelope(allowed_tools=("score", "send_authorized"))

    def test_blank_tool_name_fails_closed(self):
        env = _envelope()
        with self.assertRaises(FailClosedError):
            env.tool_allowed("   ")


if __name__ == "__main__":
    unittest.main()
