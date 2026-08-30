"""Risk tiering: every mandatory escalation, and the ratchet that has no reverse."""

from __future__ import annotations

import unittest

from ofn.kernel.domain import Action, Confidence, PackSpec, RiskTier, TenantId, max_tier
from ofn.kernel.risk import assess, base_tier, explain

T = TenantId("alpha")


def pk(**kw) -> PackSpec:
    base = dict(tenant=T, capacity_units_per_week=6)
    base.update(kw)
    return PackSpec(**base)


def act(**kw) -> Action:
    base = dict(tenant=T, name="do_thing")
    base.update(kw)
    return Action(**base)


class TestTierOrdering(unittest.TestCase):
    def test_ordering(self):
        self.assertTrue(RiskTier.RED.at_least(RiskTier.YELLOW))
        self.assertTrue(RiskTier.YELLOW.at_least(RiskTier.GREEN))
        self.assertFalse(RiskTier.GREEN.at_least(RiskTier.YELLOW))
        self.assertTrue(RiskTier.GREEN.at_least(RiskTier.GREEN))

    def test_max_tier(self):
        self.assertIs(max_tier(RiskTier.GREEN, RiskTier.RED), RiskTier.RED)
        self.assertIs(max_tier(RiskTier.GREEN, RiskTier.YELLOW), RiskTier.YELLOW)
        self.assertIs(max_tier(), RiskTier.GREEN)


class TestBaseTier(unittest.TestCase):
    def test_internal_reversible_is_green(self):
        self.assertIs(base_tier(act()), RiskTier.GREEN)

    def test_leaving_the_node_is_yellow(self):
        self.assertIs(base_tier(act(leaves_node=True)), RiskTier.YELLOW)

    def test_irreversible_is_red(self):
        self.assertIs(base_tier(act(reversible=False)), RiskTier.RED)


class TestMandatoryEscalations(unittest.TestCase):
    def test_money_is_always_red(self):
        r = assess(act(touches_money=True), pk())
        self.assertIs(r.tier, RiskTier.RED)
        self.assertIn("money", [e.rule for e in r.escalations])

    def test_money_is_red_even_when_internal_and_reversible(self):
        r = assess(act(touches_money=True, leaves_node=False, reversible=True), pk())
        self.assertIs(r.tier, RiskTier.RED)

    def test_pii_is_always_red(self):
        r = assess(act(touches_pii=True), pk())
        self.assertIs(r.tier, RiskTier.RED)
        self.assertIn("pii", [e.rule for e in r.escalations])

    def test_recipient_from_observed_content_is_red(self):
        """Anti-injection: a destination proposed by scraped text is never trusted."""
        r = assess(act(leaves_node=True, recipient_from_observed_content=True), pk())
        self.assertIs(r.tier, RiskTier.RED)
        self.assertIn("untrusted-recipient", [e.rule for e in r.escalations])

    def test_weak_fact_is_red(self):
        p = pk(required_facts={"price": Confidence.OWNER_CONFIRMED})
        r = assess(act(leaves_node=True, evidence={"price": Confidence.GUESSED}), p)
        self.assertIs(r.tier, RiskTier.RED)
        self.assertIn("weak-fact", [e.rule for e in r.escalations])

    def test_sufficient_fact_does_not_escalate(self):
        p = pk(required_facts={"price": Confidence.MEASURED})
        r = assess(act(leaves_node=True,
                       evidence={"price": Confidence.OWNER_CONFIRMED}), p)
        self.assertIs(r.tier, RiskTier.YELLOW)

    def test_missing_fact_only_escalates_when_leaving_the_node(self):
        p = pk(required_facts={"price": Confidence.OWNER_CONFIRMED})
        self.assertIs(assess(act(), p).tier, RiskTier.GREEN)
        self.assertIs(assess(act(leaves_node=True), p).tier, RiskTier.RED)

    def test_over_capacity_is_red(self):
        r = assess(act(requested_units=3), pk(capacity_units_per_week=6),
                   units_used_this_week=4)
        self.assertIs(r.tier, RiskTier.RED)
        self.assertIn("over-capacity", [e.rule for e in r.escalations])

    def test_exactly_at_capacity_is_allowed(self):
        r = assess(act(requested_units=2), pk(capacity_units_per_week=6),
                   units_used_this_week=4)
        self.assertIs(r.tier, RiskTier.GREEN)

    def test_closed_gate_escalates_whole_pack(self):
        p = pk(gates=("budget", "secret_rotation"))
        r = assess(act(), p, closed_gates=["secret_rotation"])
        self.assertIs(r.tier, RiskTier.RED)
        self.assertIn("closed-gate", [e.rule for e in r.escalations])

    def test_closed_gate_the_pack_does_not_use_is_ignored(self):
        p = pk(gates=("budget",))
        r = assess(act(), p, closed_gates=["some_other_gate"])
        self.assertIs(r.tier, RiskTier.GREEN)


class TestRatchetIsOneDirectional(unittest.TestCase):
    def test_override_can_raise(self):
        p = pk(risk_overrides={"do_thing": RiskTier.RED})
        self.assertIs(assess(act(), p).tier, RiskTier.RED)

    def test_override_cannot_lower_a_red(self):
        """The critical property: no configuration turns RED into GREEN."""
        p = pk(risk_overrides={"do_thing": RiskTier.GREEN})
        r = assess(act(touches_money=True), p)
        self.assertIs(r.tier, RiskTier.RED)

    def test_override_cannot_lower_a_yellow(self):
        p = pk(risk_overrides={"do_thing": RiskTier.GREEN})
        r = assess(act(leaves_node=True), p)
        self.assertIs(r.tier, RiskTier.YELLOW)

    def test_no_combination_of_inputs_lowers_below_base(self):
        p = pk(risk_overrides={"do_thing": RiskTier.GREEN},
               required_facts={"f": Confidence.GUESSED})
        for money in (False, True):
            for pii in (False, True):
                for leaves in (False, True):
                    for rev in (False, True):
                        a = act(touches_money=money, touches_pii=pii,
                                leaves_node=leaves, reversible=rev,
                                evidence={"f": Confidence.OWNER_CONFIRMED})
                        with self.subTest(money=money, pii=pii, leaves=leaves,
                                          reversible=rev):
                            r = assess(a, p)
                            self.assertTrue(r.tier.at_least(base_tier(a)))


class TestDeterminism(unittest.TestCase):
    def test_same_inputs_same_tier(self):
        p = pk(required_facts={"price": Confidence.OWNER_CONFIRMED},
               gates=("budget",))
        a = act(leaves_node=True, evidence={"price": Confidence.MEASURED})
        first = assess(a, p, closed_gates=["budget"])
        for _ in range(20):
            self.assertEqual(assess(a, p, closed_gates=["budget"]).tier, first.tier)

    def test_explain_is_ledger_shaped(self):
        r = assess(act(touches_money=True), pk())
        d = explain(r)
        self.assertEqual(d["tier"], "red")
        self.assertEqual(d["base"], "green")
        self.assertTrue(any(e["rule"] == "money" for e in d["escalations"]))


if __name__ == "__main__":
    unittest.main()
