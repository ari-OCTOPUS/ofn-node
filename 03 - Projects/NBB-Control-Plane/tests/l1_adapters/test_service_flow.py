"""Service orchestration against in-memory adapters: the one execution path."""

import pytest

pytestmark = pytest.mark.l1

from nbb_cp.kernel.domain import EvidencePack, ProposalKind
from nbb_cp.kernel.errors import ConcurrencyConflictError, FailClosedError
from nbb_cp.kernel.events import EventKind
from nbb_cp.adapters.storage.memory import MemoryLedgerStore


class TestGrantFlow:
    def test_grant_admit_execute_commits_budget(self, service, budget_store):
        proposal, decision = service.submit_proposal(
            "painting-leads", ProposalKind.GRANT, 500, "seed"
        )
        assert decision.allowed
        result = service.execute(proposal.proposal_id)
        assert result.decision.allowed
        assert result.simulated  # shadow mode
        assert budget_store.get().committed.cents == 500

    def test_grant_past_cap_denied_at_admission(self, service):
        _, decision = service.submit_proposal("ziman", ProposalKind.GRANT, 999999, "greed")
        assert not decision.allowed
        assert decision.invariant == "INV-1"

    def test_denied_proposal_cannot_execute(self, service):
        proposal, decision = service.submit_proposal("ziman", ProposalKind.GRANT, 999999, "greed")
        assert not decision.allowed
        with pytest.raises(FailClosedError):
            service.execute(proposal.proposal_id)

    def test_headroom_rechecked_at_execution(self, service, budget_store):
        # Admission passes for both, but the second execution must fail: the
        # first one consumed the headroom in between (TOCTOU discipline).
        p1, _ = service.submit_proposal("painting-leads", ProposalKind.GRANT, 2000, "a")
        p2, _ = service.submit_proposal("ziman", ProposalKind.GRANT, 2000, "b")
        assert service.execute(p1.proposal_id).decision.allowed
        result = service.execute(p2.proposal_id)
        assert not result.decision.allowed
        assert result.decision.invariant == "INV-1"
        assert budget_store.get().committed.cents == 2000

    def test_unknown_organ_denied_fail_closed(self, service):
        _, decision = service.submit_proposal("ghost", ProposalKind.GRANT, 10, "?")
        assert not decision.allowed
        assert decision.invariant == "INV-12"


class TestExecuteIdempotency:
    """One admission + one verdict authorize exactly one execution (INV-2/INV-4)."""

    def test_replay_of_grant_is_refused_not_recommitted(self, service, budget_store):
        p, _ = service.submit_proposal("painting-leads", ProposalKind.GRANT, 500, "seed")
        first = service.execute(p.proposal_id)
        assert first.decision.allowed
        assert budget_store.get().committed.cents == 500
        # A network retry / duplicate execute must be refused, not double-committed.
        second = service.execute(p.proposal_id)
        assert not second.decision.allowed
        assert second.decision.invariant == "INV-2"
        assert budget_store.get().committed.cents == 500

    def test_replay_of_irreversible_effect_is_refused(self, service):
        p, _ = service.submit_proposal(
            "ziman", ProposalKind.EFFECT, 50, "publish", irreversible=True
        )
        service.record_verdict(p.proposal_id, True, "armin")
        assert service.execute(p.proposal_id).decision.allowed
        replay = service.execute(p.proposal_id)  # one verdict must not authorize a second effect
        assert not replay.decision.allowed
        assert replay.decision.invariant == "INV-2"

    def test_idempotency_survives_soma_rebuild(self, service, ledger, budget_store, service_factory):
        p, _ = service.submit_proposal("painting-leads", ProposalKind.GRANT, 500, "seed")
        service.execute(p.proposal_id)
        # The executed set is rebuilt from the genome, so a reborn service still refuses replay.
        reborn = service_factory(ledger, budget_store)
        assert not reborn.execute(p.proposal_id).decision.allowed
        assert budget_store.get().committed.cents == 500


class TestGrantSagaCompensation:
    """A GRANT whose ledger append fails after the CAS must not diverge the budget (M2)."""

    def test_append_failure_releases_reservation_no_divergence(self, budget_store, service_factory):
        class FailOnGrantLedger(MemoryLedgerStore):
            def append(self, ts, kind, payload):
                if kind is EventKind.GRANT:
                    raise RuntimeError("ledger write failed mid-saga")
                return super().append(ts, kind, payload)

        svc = service_factory(FailOnGrantLedger(), budget_store)
        p, _ = svc.submit_proposal("painting-leads", ProposalKind.GRANT, 500, "seed")
        with pytest.raises(ConcurrencyConflictError):
            svc.execute(p.proposal_id)
        # Saga compensation released the committed reservation: committed == 0 == sum of
        # GRANT events, so the reconciliation audit stays clean and a retry is safe.
        assert budget_store.get().committed.cents == 0
        assert svc.run_audit() == []


class TestSpawnFlow:
    def test_spawn_without_verdict_denied_inv2(self, service):
        proposal, decision = service.submit_proposal(
            "painting-leads", ProposalKind.SPAWN, 1, "clone", parent_agent_id="agent-1"
        )
        assert decision.allowed  # admissible, pending human verdict
        result = service.execute(proposal.proposal_id)
        assert not result.decision.allowed
        assert result.decision.invariant == "INV-2"

    def test_spawn_with_approval_executes(self, service):
        proposal, _ = service.submit_proposal(
            "painting-leads", ProposalKind.SPAWN, 1, "clone", parent_agent_id="agent-1"
        )
        service.record_verdict(proposal.proposal_id, True, "armin")
        result = service.execute(proposal.proposal_id)
        assert result.decision.allowed
        assert result.event.kind is EventKind.SPAWN

    def test_spawn_depth_one_denied_at_admission(self, service):
        _, decision = service.submit_proposal(
            "painting-leads", ProposalKind.SPAWN, 1, "grandchild",
            parent_agent_id="agent-1", spawn_depth=1,
        )
        assert not decision.allowed
        assert decision.invariant == "INV-6"

    def test_sigma_freeze_blocks_execution_of_stale_approval(self, service):
        # Approve three spawns while sigma is calm, execute all: the last must
        # freeze because executed spawns pushed sigma to the limit.
        ids = []
        for i in range(4):
            p, d = service.submit_proposal(
                "painting-leads", ProposalKind.SPAWN, 1, f"clone {i}", parent_agent_id=f"agent-{i}"
            )
            if d.allowed:
                service.record_verdict(p.proposal_id, True, "armin")
                ids.append(p.proposal_id)
        outcomes = [service.execute(pid) for pid in ids]
        executed = [o for o in outcomes if o.decision.allowed]
        frozen = [o for o in outcomes if not o.decision.allowed]
        assert len(executed) == 3  # 3 spawns / 3 agents = sigma 1.0
        assert frozen and frozen[0].decision.invariant == "INV-6"


class TestKill:
    def test_kill_denies_all_execution(self, service, kill):
        proposal, _ = service.submit_proposal("painting-leads", ProposalKind.GRANT, 100, "x")
        kill.engage()
        result = service.execute(proposal.proposal_id)
        assert not result.decision.allowed
        assert result.decision.invariant == "INV-3"

    def test_kill_release_restores_operation(self, service, kill):
        proposal, _ = service.submit_proposal("painting-leads", ProposalKind.GRANT, 100, "x")
        kill.engage()
        kill.release()
        assert service.execute(proposal.proposal_id).decision.allowed

    def test_record_kill_actually_halts_execution(self, service):
        # The in-band API path (POST /kill -> record_kill) must engage the real switch,
        # not merely ledger a KILL event the effector gate never reads. Before the fix,
        # this execution was allowed and the "emergency stop" stopped nothing.
        proposal, _ = service.submit_proposal("painting-leads", ProposalKind.GRANT, 100, "x")
        service.record_kill(by="armin")
        result = service.execute(proposal.proposal_id)
        assert not result.decision.allowed
        assert result.decision.invariant == "INV-3"

    def test_resume_restores_and_leaves_audit_clean(self, service):
        proposal, _ = service.submit_proposal("painting-leads", ProposalKind.GRANT, 100, "x")
        service.record_kill(by="armin")
        service.resume(by="armin")
        assert service.execute(proposal.proposal_id).decision.allowed
        # A released kill must not condemn later legitimate work forever.
        assert service.run_audit() == []


class TestRevenueAndFitness:
    def test_reported_revenue_never_moves_fitness(self, service):
        service.record_revenue("ziman", "reported", 100000)
        assert service.fitness("ziman").confirmed_value_cents == 0

    def test_confirmed_revenue_counts(self, service):
        service.record_revenue("ziman", "confirmed", 700)
        assert service.fitness("ziman").confirmed_value_cents == 700

    def test_junk_state_rejected_fail_closed(self, service):
        with pytest.raises(ValueError):
            service.record_revenue("ziman", "vibes", 100)

    def test_unknown_organ_rejected(self, service):
        with pytest.raises(FailClosedError):
            service.record_revenue("ghost", "confirmed", 100)

    def test_negative_revenue_rejected_fail_closed(self, service):
        # A negative confirmed-revenue would fabricate fitness. It must fail closed
        # (INV-12) like every other money value, not slip in as a raw int().
        with pytest.raises(FailClosedError):
            service.record_revenue("ziman", "confirmed", -5000)

    def test_negative_spend_rejected_fail_closed(self, service):
        # An adversarial/buggy LLM self-reporting -tokens (INV-8) must not become
        # positive fitness via record_spend. Route through Money -> fail closed.
        with pytest.raises(FailClosedError):
            service.record_spend("accounting", input_cents=-100000)

    def test_negative_spend_does_not_poison_fitness(self, service):
        service.record_spend("ziman", input_cents=100)  # a normal, real cost
        with pytest.raises(FailClosedError):
            service.record_spend("ziman", output_cents=-999999)
        # The rejected poison never landed; fitness reflects only the real spend.
        assert service.fitness("ziman").net_cents == -100


class TestProjectionRebuild:
    def test_soma_rebuilds_from_genome(self, service, ledger, budget_store, service_factory):
        p1, _ = service.submit_proposal("painting-leads", ProposalKind.GRANT, 300, "seed")
        service.record_verdict(p1.proposal_id, True, "armin")
        service.advance_epoch()
        service.advance_epoch()  # epoch is now 2 and must survive a rebuild
        # A fresh service over the same ledger must see the same world — epoch included.
        # (Before advance_epoch was ledgered, the rebuilt epoch silently regressed to 0,
        # and this test passed anyway because it never advanced the epoch.)
        reborn = service_factory(ledger, budget_store)
        assert reborn.snapshot()["epoch"] == 2
        result = reborn.execute(p1.proposal_id)
        assert result.decision.allowed
        assert budget_store.get().committed.cents == 300

    def test_audit_clean_after_normal_flow(self, service):
        p, _ = service.submit_proposal("painting-leads", ProposalKind.GRANT, 100, "seed")
        service.execute(p.proposal_id)
        service.record_revenue("painting-leads", "confirmed", 50)
        assert service.run_audit() == []

    def test_snapshot_shape(self, service):
        snap = service.snapshot()
        assert snap["cap_cents"] == 3000
        assert snap["mode"] == "shadow"
        assert set(snap["organs"]) == {"accounting", "painting-leads", "ziman"}


class TestRuntimeAudit:
    """run_audit must actually *find* things — not just be asserted == [] everywhere."""

    def test_flags_execution_inside_kill_window(self, service, ledger):
        # Write a violating genome straight to the ledger: a GRANT that landed while
        # the switch was engaged, with no intervening RESUME. If the audit wiring
        # (kill window -> post_kill count -> INV-3) were a no-op, this would return [].
        ledger.append("t0", EventKind.KILL, {"by": "armin"})
        ledger.append("t1", EventKind.GRANT, {"organ_id": "ziman", "amount_cents": 0, "shadow": True})
        violations = service.run_audit()
        assert any(v.invariant == "INV-3" for v in violations)

    def test_resume_closes_the_kill_window(self, service, ledger):
        # Same shape, but a RESUME precedes the GRANT: the execution is no longer
        # inside a killed window, so INV-3 must NOT fire.
        ledger.append("t0", EventKind.KILL, {"by": "armin"})
        ledger.append("t1", EventKind.RESUME, {"by": "armin"})
        ledger.append("t2", EventKind.GRANT, {"organ_id": "ziman", "amount_cents": 0, "shadow": True})
        assert not any(v.invariant == "INV-3" for v in service.run_audit())


class TestApprovalTTL:
    """A verdict older than the proposal's TTL is stale — one approval must not
    authorize execution forever (the 2026 HITL 'approval deadline')."""

    def test_verdict_within_ttl_executes(self, service):
        p, _ = service.submit_proposal(
            "ziman", ProposalKind.EFFECT, 50, "publish",
            irreversible=True, approval_ttl_epochs=2,
        )
        service.record_verdict(p.proposal_id, True, "armin")
        assert service.execute(p.proposal_id).decision.allowed

    def test_verdict_past_ttl_refused_as_stale(self, service):
        p, _ = service.submit_proposal(
            "ziman", ProposalKind.EFFECT, 50, "publish",
            irreversible=True, approval_ttl_epochs=1,
        )
        service.record_verdict(p.proposal_id, True, "armin")  # verdict issued at epoch 0
        service.advance_epoch()
        service.advance_epoch()  # epoch 2: verdict is 2 epochs old, past the TTL of 1
        result = service.execute(p.proposal_id)
        assert not result.decision.allowed
        assert result.decision.invariant == "INV-2"
        assert "expired" in result.decision.reason

    def test_absent_ttl_never_expires(self, service):
        p, _ = service.submit_proposal(
            "ziman", ProposalKind.EFFECT, 50, "publish", irreversible=True,  # no TTL
        )
        service.record_verdict(p.proposal_id, True, "armin")
        for _ in range(10):
            service.advance_epoch()
        assert service.execute(p.proposal_id).decision.allowed


class TestEvidencePack:
    """Structured evidence a proposal carries for the reviewer, preserved in the genome."""

    def test_evidence_round_trips_through_rebuild(self, service, ledger, budget_store, service_factory):
        ev = EvidencePack(
            expected_value_cents=5000,
            reversibility="reversible",
            alternatives=("do nothing", "smaller grant"),
            rollback="release the grant",
        )
        p, _ = service.submit_proposal(
            "painting-leads", ProposalKind.GRANT, 300, "seed", evidence=ev
        )
        reborn = service_factory(ledger, budget_store)
        assert reborn._proposals[p.proposal_id].evidence == ev

    def test_absent_evidence_is_none(self, service, ledger, budget_store, service_factory):
        p, _ = service.submit_proposal("painting-leads", ProposalKind.GRANT, 300, "seed")
        reborn = service_factory(ledger, budget_store)
        assert reborn._proposals[p.proposal_id].evidence is None
