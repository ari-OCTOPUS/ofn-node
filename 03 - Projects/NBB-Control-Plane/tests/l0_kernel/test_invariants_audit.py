import dataclasses

import pytest

pytestmark = pytest.mark.l0

from nbb_cp.kernel.domain import BudgetState, Mode, Money, Organ
from nbb_cp.kernel.events import EventKind, next_event
from nbb_cp.kernel.invariants import INVARIANTS, SystemView, audit

ORGANS = {"a": Organ(organ_id="a", name="A")}


def view(**overrides):
    # committed must reconcile with the sum of GRANT events (INV-1 ledger check),
    # so a default view with no events has committed=0. Tests that need committed>0
    # override both budget and events together.
    defaults = dict(
        budget=BudgetState(cap=Money(1000), committed=Money(0), version=3),
        events=(),
        organs=ORGANS,
        mode=Mode.SHADOW,
        killed=False,
        sigma=0.5,
    )
    defaults.update(overrides)
    return SystemView(**defaults)


class TestRegistry:
    def test_exactly_twelve_invariants(self):
        assert len(INVARIANTS) == 12

    def test_ids_are_stable_and_sequential(self):
        numeric = sorted(INVARIANTS, key=lambda inv_id: int(inv_id.split("-")[1]))
        assert numeric == [f"INV-{i}" for i in range(1, 13)]

    def test_every_invariant_has_a_description(self):
        assert all(len(text) > 20 for text in INVARIANTS.values())


class TestAudit:
    def test_clean_view_passes(self):
        assert audit(view()) == []

    def test_broken_chain_flagged_inv5(self):
        e0 = next_event(None, "t0", EventKind.PROPOSAL, {"i": 0})
        e1 = next_event(e0, "t1", EventKind.PROPOSAL, {"i": 1})
        forged = dataclasses.replace(e1, payload={"i": 666})
        violations = audit(view(events=(e0, forged)))
        assert any(v.invariant == "INV-5" for v in violations)

    def test_sigma_over_limit_flagged_inv6(self):
        violations = audit(view(sigma=1.5))
        assert any(v.invariant == "INV-6" for v in violations)

    def test_ungated_extinction_flagged_inv2(self):
        event = next_event(None, "t0", EventKind.LIFECYCLE, {"organ_id": "a", "to": "extinct"})
        violations = audit(view(events=(event,)))
        assert any(v.invariant == "INV-2" for v in violations)

    def test_gated_extinction_passes(self):
        event = next_event(
            None, "t0", EventKind.LIFECYCLE, {"organ_id": "a", "to": "extinct", "verdict_by": "armin"}
        )
        assert audit(view(events=(event,))) == []

    def test_live_effect_in_shadow_flagged_inv4(self):
        violations = audit(view(live_effects_executed=2))
        assert any(v.invariant == "INV-4" for v in violations)

    def test_post_kill_execution_flagged_inv3(self):
        violations = audit(view(post_kill_executions=1))
        assert any(v.invariant == "INV-3" for v in violations)

    def test_unlabelled_revenue_flagged_inv7(self):
        event = next_event(None, "t0", EventKind.REVENUE, {"organ_id": "a", "amount_cents": 100})
        violations = audit(view(events=(event,)))
        assert any(v.invariant == "INV-7" for v in violations)

    def test_budget_ledger_divergence_flagged_inv1(self):
        # committed budget with no backing GRANT event: the silent divergence a
        # CAS-without-append (or append-without-CAS) leaves behind. Now caught.
        violations = audit(view(budget=BudgetState(cap=Money(1000), committed=Money(100))))
        assert any(v.invariant == "INV-1" and "divergence" in v.detail for v in violations)

    def test_committed_matching_grants_passes(self):
        grant = next_event(None, "t0", EventKind.GRANT, {"amount_cents": 100})
        clean = audit(view(budget=BudgetState(cap=Money(1000), committed=Money(100)), events=(grant,)))
        assert clean == []
