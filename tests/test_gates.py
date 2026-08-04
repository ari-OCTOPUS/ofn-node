"""The choke point: admission, ordering, and the two-step release for RED."""

from __future__ import annotations

import unittest

from ofn.kernel.domain import (
    Action, Confidence, PackSpec, RiskTier, TenantId, TokenSpend,
)
from ofn.kernel.gates import admit, executable
from ofn.kernel.quota import NodeQuota

T = TenantId("alpha")
NOW = 0


def pk(**kw) -> PackSpec:
    base = dict(tenant=T, capacity_units_per_week=6, quota_share=1.0)
    base.update(kw)
    return PackSpec(**base)


def act(**kw) -> Action:
    base = dict(tenant=T, name="do_thing")
    base.update(kw)
    return Action(**base)


def q(capacity=10_000_000, utilisation=1.0, mult=1.0) -> NodeQuota:
    return NodeQuota(estimated_capacity_tokens=capacity, utilisation=utilisation,
                     shares={"alpha": 1.0}, orchestration_multiplier=mult)


class TestAdmission(unittest.TestCase):
    def test_green_runs_unattended(self):
        d = admit(act(), pk(), q(), now_epoch_s=NOW)
        self.assertTrue(d.allowed)
        self.assertIs(d.tier, RiskTier.GREEN)
        self.assertFalse(d.needs_human)

    def test_yellow_is_allowed_but_needs_a_human(self):
        d = admit(act(leaves_node=True), pk(), q(), now_epoch_s=NOW)
        self.assertTrue(d.allowed)
        self.assertTrue(d.needs_human)
        self.assertFalse(d.needs_double_confirm)

    def test_red_needs_two_steps(self):
        d = admit(act(touches_money=True), pk(), q(), now_epoch_s=NOW)
        self.assertTrue(d.allowed)
        self.assertTrue(d.needs_double_confirm)

    def test_allowed_does_not_mean_execute_now(self):
        """`admit` answers a policy question; it must never be read as a go-ahead."""
        d = admit(act(touches_money=True), pk(), q(), now_epoch_s=NOW)
        self.assertTrue(d.allowed)
        self.assertFalse(executable(d).allowed)


class TestOrdering(unittest.TestCase):
    def test_kill_switch_wins_over_everything(self):
        d = admit(act(), pk(), q(), now_epoch_s=NOW, killed=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule, "gate:kill-switch")

    def test_quota_is_checked_before_risk(self):
        """A RED action that would sit in a queue must not reserve budget first."""
        quota = q(capacity=100, utilisation=1.0)
        quota.record("alpha", TokenSpend(visible=100), NOW)
        d = admit(act(touches_money=True, estimated_tokens=50), pk(), quota,
                  now_epoch_s=NOW)
        self.assertFalse(d.allowed)
        self.assertTrue(d.rule.startswith("quota:"))

    def test_zero_token_actions_skip_the_quota_check(self):
        quota = q(capacity=100, utilisation=1.0)
        quota.record("alpha", TokenSpend(visible=100), NOW)
        d = admit(act(estimated_tokens=0), pk(), quota, now_epoch_s=NOW)
        self.assertTrue(d.allowed)


class TestTenantBinding(unittest.TestCase):
    def test_action_for_another_tenant_is_refused(self):
        other = Action(tenant=TenantId("bravo"), name="do_thing")
        d = admit(other, pk(), q(), now_epoch_s=NOW)
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule, "gate:tenant-mismatch")


class TestClosedGates(unittest.TestCase):
    def test_closed_gate_forces_red_even_for_internal_work(self):
        p = pk(gates=("secret_rotation",))
        d = admit(act(), p, q(), now_epoch_s=NOW, closed_gates=["secret_rotation"])
        self.assertTrue(d.allowed)
        self.assertIs(d.tier, RiskTier.RED)
        self.assertIn("secret_rotation", d.reason)


class TestExecutable(unittest.TestCase):
    def setUp(self):
        self.green = admit(act(), pk(), q(), now_epoch_s=NOW)
        self.yellow = admit(act(leaves_node=True), pk(), q(), now_epoch_s=NOW)
        self.red = admit(act(touches_money=True), pk(), q(), now_epoch_s=NOW)

    def test_green_executes_without_approval(self):
        self.assertTrue(executable(self.green).allowed)

    def test_yellow_blocked_without_approval(self):
        r = executable(self.yellow)
        self.assertFalse(r.allowed)
        self.assertEqual(r.rule, "exec:awaiting-approval")

    def test_yellow_runs_with_one_approval(self):
        self.assertTrue(executable(self.yellow, human_approved=True).allowed)

    def test_red_needs_the_second_confirmation(self):
        once = executable(self.red, human_approved=True)
        self.assertFalse(once.allowed)
        self.assertEqual(once.rule, "exec:awaiting-second-confirm")
        twice = executable(self.red, human_approved=True, confirmed_twice=True)
        self.assertTrue(twice.allowed)

    def test_second_confirm_alone_is_not_enough(self):
        r = executable(self.red, human_approved=False, confirmed_twice=True)
        self.assertFalse(r.allowed)

    def test_a_denied_decision_stays_denied(self):
        denied = admit(act(), pk(), q(), now_epoch_s=NOW, killed=True)
        r = executable(denied, human_approved=True, confirmed_twice=True)
        self.assertFalse(r.allowed)


class TestEndToEndShapes(unittest.TestCase):
    def test_price_without_confirmed_cost_is_red(self):
        p = pk(required_facts={"cost": Confidence.OWNER_CONFIRMED},
               risk_overrides={"publish_price": RiskTier.RED})
        a = act(name="publish_price", leaves_node=True,
                evidence={"cost": Confidence.GUESSED})
        d = admit(a, p, q(), now_epoch_s=NOW)
        self.assertIs(d.tier, RiskTier.RED)

    def test_price_with_confirmed_cost_is_still_red_by_override(self):
        """Confirming the cost unblocks the *fact*, not the irreversibility."""
        p = pk(required_facts={"cost": Confidence.OWNER_CONFIRMED},
               risk_overrides={"publish_price": RiskTier.RED})
        a = act(name="publish_price", leaves_node=True,
                evidence={"cost": Confidence.OWNER_CONFIRMED})
        d = admit(a, p, q(), now_epoch_s=NOW)
        self.assertIs(d.tier, RiskTier.RED)

    def test_internal_classification_stays_green_and_free(self):
        a = act(name="classify_inbound", estimated_tokens=0)
        d = admit(a, pk(), q(), now_epoch_s=NOW)
        self.assertIs(d.tier, RiskTier.GREEN)
        self.assertTrue(executable(d).allowed)


if __name__ == "__main__":
    unittest.main()
