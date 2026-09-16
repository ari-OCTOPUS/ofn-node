import pytest

pytestmark = pytest.mark.l0

from nbb_cp.kernel.domain import (
    BudgetState,
    Mode,
    Money,
    Organ,
    Proposal,
    ProposalKind,
    Verdict,
)
from nbb_cp.kernel.gates import budget_gate, effector_gate, spawn_gate

ORGANS = {"leads": Organ(organ_id="leads", name="Leads")}
STATE = BudgetState(cap=Money(1000))


def grant(amount=100, **kw):
    return Proposal(
        proposal_id=kw.pop("proposal_id", "p1"), organ_id=kw.pop("organ_id", "leads"),
        kind=ProposalKind.GRANT, amount=Money(amount), rationale="r", epoch=0, **kw,
    )


def spawn(depth=0, **kw):
    return Proposal(
        proposal_id="s1", organ_id="leads", kind=ProposalKind.SPAWN,
        amount=Money(1), rationale="r", epoch=0,
        parent_agent_id="agent-1", spawn_depth=depth, **kw,
    )


def effect(irreversible=False):
    return Proposal(
        proposal_id="e1", organ_id="leads", kind=ProposalKind.EFFECT,
        amount=Money(10), rationale="r", epoch=0, irreversible=irreversible,
    )


def approved(proposal_id="p1"):
    return Verdict(proposal_id=proposal_id, approved=True, by="armin", ts="t")


def denied(proposal_id="p1"):
    return Verdict(proposal_id=proposal_id, approved=False, by="armin", ts="t")


class TestBudgetGate:
    def test_grant_within_cap_admitted(self):
        assert budget_gate(STATE, grant(500), ORGANS).allowed

    def test_grant_past_cap_denied_inv1(self):
        decision = budget_gate(STATE, grant(1001), ORGANS)
        assert not decision.allowed
        assert decision.invariant == "INV-1"

    def test_unknown_organ_denied_inv12(self):
        decision = budget_gate(STATE, grant(organ_id="ghost"), ORGANS)
        assert not decision.allowed
        assert decision.invariant == "INV-12"


class TestSpawnGate:
    def test_depth_zero_under_calm_sigma_admitted(self):
        assert spawn_gate(spawn(), sigma=0.5).allowed

    def test_depth_at_limit_denied_inv6(self):
        decision = spawn_gate(spawn(depth=1), sigma=0.0)
        assert not decision.allowed
        assert decision.invariant == "INV-6"

    def test_sigma_over_one_freezes_replication(self):
        decision = spawn_gate(spawn(), sigma=1.01)
        assert not decision.allowed
        assert decision.invariant == "INV-6"

    def test_sigma_exactly_one_still_admits(self):
        assert spawn_gate(spawn(), sigma=1.0).allowed

    def test_non_spawn_proposal_rejected(self):
        assert not spawn_gate(grant(), sigma=0.0).allowed


class TestEffectorGate:
    def test_kill_denies_everything_first(self):
        decision = effector_gate(effect(), approved("e1"), Mode.LIVE, killed=True)
        assert not decision.allowed
        assert decision.invariant == "INV-3"

    def test_irreversible_without_verdict_denied_inv2(self):
        decision = effector_gate(effect(irreversible=True), None, Mode.LIVE, killed=False)
        assert not decision.allowed
        assert decision.invariant == "INV-2"

    def test_irreversible_with_denied_verdict_denied(self):
        decision = effector_gate(effect(irreversible=True), denied("e1"), Mode.LIVE, killed=False)
        assert not decision.allowed

    def test_irreversible_with_approval_allowed_live(self):
        decision = effector_gate(effect(irreversible=True), approved("e1"), Mode.LIVE, killed=False)
        assert decision.allowed and not decision.shadow

    def test_mismatched_verdict_denied_inv12(self):
        decision = effector_gate(effect(irreversible=True), approved("other"), Mode.LIVE, killed=False)
        assert not decision.allowed
        assert decision.invariant == "INV-12"

    def test_spawn_always_needs_human(self):
        decision = effector_gate(spawn(), None, Mode.LIVE, killed=False)
        assert not decision.allowed
        assert decision.invariant == "INV-2"

    def test_shadow_mode_allows_but_flags_simulation(self):
        decision = effector_gate(effect(), None, Mode.SHADOW, killed=False)
        assert decision.allowed and decision.shadow

    def test_reversible_effect_live_no_verdict_needed(self):
        decision = effector_gate(effect(), None, Mode.LIVE, killed=False)
        assert decision.allowed and not decision.shadow
