"""ControlPlaneService — the one orchestration path.

Every action flows: proposal -> gate -> ledger -> (simulated|real) effect.
There is no second door. The in-memory proposal/verdict indexes are soma:
disposable projections rebuilt from the ledger (genome) at any time via
`rebuild_projections`.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Mapping, Sequence

from ..kernel import budget as budget_math
from ..kernel.domain import (
    BudgetState,
    EvidencePack,
    GateDecision,
    Mode,
    Money,
    Organ,
    Proposal,
    ProposalKind,
    Verdict,
)
from ..kernel.errors import ConcurrencyConflictError, FailClosedError, KernelError
from ..kernel.events import EventKind, LedgerEvent
from ..kernel.fitness import FitnessReport, compute_fitness
from ..kernel.gates import budget_gate, effector_gate, spawn_gate
from ..kernel.invariants import SystemView, Violation, audit
from ..kernel.ports import (
    BudgetStore,
    Clock,
    IdGen,
    KillSwitch,
    LedgerStore,
    LLMPort,
    Telemetry,
)
from ..kernel.sigma import prospective_sigma_from_events, sigma_from_events

MAX_CAS_RETRIES = 5


@dataclass(frozen=True)
class ExecutionResult:
    proposal_id: str
    decision: GateDecision
    event: LedgerEvent | None
    simulated: bool


class ControlPlaneService:
    def __init__(
        self,
        *,
        ledger: LedgerStore,
        budget: BudgetStore,
        llm: LLMPort,
        telemetry: Telemetry,
        clock: Clock,
        idgen: IdGen,
        kill: KillSwitch,
        organs: Sequence[Organ],
        mode: Mode = Mode.SHADOW,
        sigma_window_epochs: int = 5,
    ) -> None:
        self._ledger = ledger
        self._budget = budget
        self._llm = llm
        self._telemetry = telemetry
        self._clock = clock
        self._idgen = idgen
        self._kill = kill
        self._organs: dict[str, Organ] = {o.organ_id: o for o in organs}
        self._mode = mode
        self._sigma_window = sigma_window_epochs
        self._current_epoch = 0
        # Serializes the check-then-append windows (kill vs execute, spawn sigma
        # recheck vs append) that store-level CAS/locks do not span — the TOCTOU
        # lesson applied at the orchestration layer, not just the budget store.
        self._lock = threading.RLock()
        # Soma: projections over the genome. Rebuildable, never authoritative.
        self._proposals: dict[str, Proposal] = {}
        self._verdicts: dict[str, Verdict] = {}
        # Idempotency ledger: proposal_ids that already produced a terminal
        # execution event. Keyed on the genome (rebuilt below) so one admission +
        # one verdict authorize exactly one execution even across a restart.
        self._executed: set[str] = set()
        self.rebuild_projections()

    # ---------------------------------------------------------------- intake

    def submit_proposal(
        self,
        organ_id: str,
        kind: ProposalKind,
        amount_cents: int,
        rationale: str,
        *,
        irreversible: bool = False,
        parent_agent_id: str | None = None,
        spawn_depth: int = 0,
        approval_ttl_epochs: int | None = None,
        evidence: EvidencePack | None = None,
    ) -> tuple[Proposal, GateDecision]:
        """Admit a proposal through its gate and ledger it. Never executes anything."""
        proposal = Proposal(
            proposal_id=self._idgen.new_id("prop"),
            organ_id=organ_id,
            kind=kind,
            amount=Money(amount_cents),
            rationale=rationale,
            epoch=self._current_epoch,
            irreversible=irreversible,
            parent_agent_id=parent_agent_id,
            spawn_depth=spawn_depth,
            approval_ttl_epochs=approval_ttl_epochs,
            evidence=evidence,
        )
        if kind is ProposalKind.SPAWN:
            decision = spawn_gate(proposal, self._spawn_sigma())
        elif kind is ProposalKind.GRANT:
            decision = budget_gate(self._budget.get(), proposal, self._organs)
        else:  # EFFECT: admission is cheap; the effector gate is the real judge
            decision = (
                GateDecision(True, "effect admitted; effector gate decides at execution")
                if organ_id in self._organs
                else GateDecision(False, f"unknown organ {organ_id!r}", "INV-12")
            )
        self._append(
            EventKind.PROPOSAL,
            {
                "proposal_id": proposal.proposal_id,
                "organ_id": organ_id,
                "kind": kind.value,
                "amount_cents": amount_cents,
                "rationale": rationale,
                "epoch": proposal.epoch,
                "irreversible": irreversible,
                "parent_agent_id": parent_agent_id,
                "spawn_depth": spawn_depth,
                "approval_ttl_epochs": approval_ttl_epochs,
                "evidence": _evidence_payload(evidence),
                "admitted": decision.allowed,
                "reason": decision.reason,
                "invariant": decision.invariant,
            },
        )
        if decision.allowed:
            self._proposals[proposal.proposal_id] = proposal
        self._telemetry.emit(
            "nbb.proposal.admitted" if decision.allowed else "nbb.proposal.denied",
            1.0,
            {"kind": kind.value, "organ": organ_id},
        )
        return proposal, decision

    def record_verdict(self, proposal_id: str, approved: bool, by: str, note: str = "") -> Verdict:
        if proposal_id not in self._proposals:
            raise FailClosedError(f"verdict for unknown proposal {proposal_id!r}")
        verdict = Verdict(
            proposal_id=proposal_id,
            approved=approved,
            by=by,
            ts=self._clock.now_iso(),
            note=note,
            epoch=self._current_epoch,
        )
        self._append(
            EventKind.VERDICT,
            {
                "proposal_id": proposal_id,
                "approved": approved,
                "by": by,
                "note": note,
                "epoch": self._current_epoch,
                "organ_id": self._proposals[proposal_id].organ_id,
            },
        )
        self._verdicts[proposal_id] = verdict
        return verdict

    # ------------------------------------------------------------- execution

    def execute(self, proposal_id: str) -> ExecutionResult:
        """The single execution path. Everything passes the effector gate here.

        Held under the service lock: the kill sample below and the SPAWN sigma
        recheck in `_execute_spawn` must not interleave with a concurrent kill or
        another execution (both were race windows the store-level CAS cannot close).
        """
        with self._lock:
            proposal = self._proposals.get(proposal_id)
            if proposal is None:
                raise FailClosedError(f"execute of unknown or unadmitted proposal {proposal_id!r}")
            if proposal_id in self._executed:
                # One admission + one verdict authorize exactly ONE execution. A
                # replay (a network retry of POST .../execute, or a duplicate call)
                # is refused idempotently — keyed on the genome, so it holds across a
                # soma rebuild. This is the 2026 HITL norm: persist an idempotency
                # key and refuse duplicate/stale approved actions, never re-run.
                event = self._append(
                    EventKind.INCIDENT,
                    {
                        "proposal_id": proposal_id,
                        "organ_id": proposal.organ_id,
                        "reason": "proposal already executed; idempotent refusal",
                        "invariant": "INV-2",
                    },
                )
                self._telemetry.emit("nbb.execution.replay_refused", 1.0, {"organ": proposal.organ_id})
                denied = GateDecision(False, "already executed", "INV-2")
                return ExecutionResult(proposal_id, denied, event, simulated=False)
            verdict = self._verdicts.get(proposal_id)
            decision = effector_gate(proposal, verdict, self._mode, self._kill.engaged())
            if decision.allowed and self._approval_is_stale(proposal, verdict):
                # The gate approved, but the verdict has aged past the proposal's TTL.
                # Refuse the stale approval and require a fresh human verdict (INV-2):
                # an approval granted long ago must not authorize execution forever.
                decision = GateDecision(
                    False, "approval expired; a fresh human verdict is required", "INV-2"
                )
            if not decision.allowed:
                event = self._append(
                    EventKind.INCIDENT,
                    {
                        "proposal_id": proposal_id,
                        "organ_id": proposal.organ_id,
                        "reason": decision.reason,
                        "invariant": decision.invariant,
                        "killed": self._kill.engaged(),
                    },
                )
                self._telemetry.emit("nbb.execution.denied", 1.0, {"invariant": decision.invariant or "-"})
                return ExecutionResult(proposal_id, decision, event, simulated=False)

            if proposal.kind is ProposalKind.GRANT:
                result = self._execute_grant(proposal, decision)
            elif proposal.kind is ProposalKind.SPAWN:
                result = self._execute_spawn(proposal, decision)
            else:
                result = self._execute_effect(proposal, decision)
            # Mark executed only when a terminal event actually landed. A cap/sigma
            # re-check denial (allowed=False, no terminal event) stays retryable.
            if result.decision.allowed:
                self._executed.add(proposal_id)
            return result

    def _execute_grant(self, proposal: Proposal, decision: GateDecision) -> ExecutionResult:
        # Budget commitment is internal bookkeeping, so it is real in both
        # modes; only the outward effect is simulated in shadow. Reservation
        # re-checks the cap at execution time (admission headroom may be gone
        # by now — the TOCTOU lesson) and lands via compare-and-swap.
        for _ in range(MAX_CAS_RETRIES):
            state = self._budget.get()
            try:
                new_state = budget_math.reserve(state, proposal.amount)
            except KernelError as exc:  # CapExceeded / FailClosed -> incident, fail closed
                event = self._append(
                    EventKind.INCIDENT,
                    {
                        "proposal_id": proposal.proposal_id,
                        "organ_id": proposal.organ_id,
                        "reason": str(exc),
                        "invariant": getattr(exc, "invariant", None),
                    },
                )
                denied = GateDecision(False, str(exc), getattr(exc, "invariant", None))
                return ExecutionResult(proposal.proposal_id, denied, event, simulated=False)
            try:
                self._budget.compare_and_swap(state.version, new_state)
                break
            except ConcurrencyConflictError:
                continue  # re-read and retry
        else:
            raise ConcurrencyConflictError(
                f"grant {proposal.proposal_id} lost {MAX_CAS_RETRIES} CAS races; giving up"
            )
        try:
            event = self._append(
                EventKind.GRANT,
                {
                    "proposal_id": proposal.proposal_id,
                    "organ_id": proposal.organ_id,
                    "amount_cents": proposal.amount.cents,
                    "epoch": proposal.epoch,
                    "shadow": decision.shadow,
                },
            )
        except Exception as exc:  # noqa: BLE001 — second half of a two-store write
            # Saga compensation: the CAS already committed the reservation, but the
            # GRANT event failed to land. Release the reservation so committed budget
            # can never silently diverge from the genome (M2 / the INV-1 reconciliation
            # check). A retry then re-reserves cleanly instead of double-committing.
            self._compensate_release(proposal.amount)
            raise ConcurrencyConflictError(
                f"grant {proposal.proposal_id} committed but failed to ledger; "
                f"reservation released (no divergence): {exc}"
            ) from exc
        self._telemetry.emit("nbb.grant.executed", float(proposal.amount.cents), {"organ": proposal.organ_id})
        return ExecutionResult(proposal.proposal_id, decision, event, simulated=decision.shadow)

    def _execute_spawn(self, proposal: Proposal, decision: GateDecision) -> ExecutionResult:
        # Re-check sigma at execution time: approvals age, populations move.
        recheck = spawn_gate(proposal, self._spawn_sigma())
        if not recheck.allowed:
            event = self._append(
                EventKind.INCIDENT,
                {
                    "proposal_id": proposal.proposal_id,
                    "organ_id": proposal.organ_id,
                    "reason": f"stale approval: {recheck.reason}",
                    "invariant": recheck.invariant,
                },
            )
            return ExecutionResult(proposal.proposal_id, recheck, event, simulated=False)
        event = self._append(
            EventKind.SPAWN,
            {
                "proposal_id": proposal.proposal_id,
                "organ_id": proposal.organ_id,
                "parent_agent_id": proposal.parent_agent_id,
                "spawn_depth": proposal.spawn_depth,
                "epoch": proposal.epoch,
                "executed": True,
                "shadow": decision.shadow,
            },
        )
        return ExecutionResult(proposal.proposal_id, decision, event, simulated=decision.shadow)

    def _execute_effect(self, proposal: Proposal, decision: GateDecision) -> ExecutionResult:
        event = self._append(
            EventKind.SPEND,
            {
                "proposal_id": proposal.proposal_id,
                "organ_id": proposal.organ_id,
                "input_cents": proposal.amount.cents,
                "output_cents": 0,
                "orchestration_cents": 0,
                "epoch": proposal.epoch,
                "shadow": decision.shadow,
            },
        )
        return ExecutionResult(proposal.proposal_id, decision, event, simulated=decision.shadow)

    # ------------------------------------------------------------ accounting

    def record_revenue(self, organ_id: str, state: str, amount_cents: int, token: str | None = None) -> LedgerEvent:
        """Ledger a revenue observation with its five-state attribution label."""
        if organ_id not in self._organs:
            raise FailClosedError(f"revenue for unknown organ {organ_id!r}")
        from ..kernel.domain import RevenueState

        revenue_state = RevenueState(state)  # raises ValueError on junk: fail closed
        amount = Money(amount_cents)  # fail closed on negative / non-int amounts (INV-12)
        return self._append(
            EventKind.REVENUE,
            {
                "organ_id": organ_id,
                "state": revenue_state.value,
                "amount_cents": amount.cents,
                "carried_token": token,
                "epoch": self._current_epoch,
            },
        )

    def record_spend(
        self, organ_id: str, *, input_cents: int = 0, output_cents: int = 0, orchestration_cents: int = 0
    ) -> LedgerEvent:
        """Three-bucket cost accounting. The orchestration bucket is mandatory-aware."""
        if organ_id not in self._organs:
            raise FailClosedError(f"spend for unknown organ {organ_id!r}")
        # Route every bucket through Money: a negative (an adversarial LLM self-
        # reporting -tokens, INV-8) or a float fails closed here instead of
        # inflating fitness. No raw int() near the ledger.
        return self._append(
            EventKind.SPEND,
            {
                "organ_id": organ_id,
                "input_cents": Money(input_cents).cents,
                "output_cents": Money(output_cents).cents,
                "orchestration_cents": Money(orchestration_cents).cents,
                "epoch": self._current_epoch,
            },
        )

    def record_kill(self, by: str, reason: str = "") -> LedgerEvent:
        """Emergency stop. Engages the real switch *first* (safety over bookkeeping),
        then ledgers the KILL — so the API's only stop control actually halts every
        gate instead of writing an event the effector gate never reads."""
        with self._lock:
            self._kill.engage()
            return self._append(EventKind.KILL, {"by": by, "reason": reason})

    def resume(self, by: str) -> LedgerEvent:
        """Release a kill. Ledger the intent first, then un-halt: a failed release
        leaves the system safely stopped. A kill switch is reversible; extinction is not."""
        with self._lock:
            event = self._append(EventKind.RESUME, {"by": by})
            self._kill.release()
            return event

    def advance_epoch(self) -> int:
        """Advance the epoch and ledger it, so `rebuild_projections` restores the epoch
        from the genome instead of silently regressing it (and skewing sigma) on restart."""
        with self._lock:
            self._current_epoch += 1
            self._append(EventKind.EPOCH, {"epoch": self._current_epoch})
            return self._current_epoch

    # -------------------------------------------------------------- readouts

    def sigma(self) -> float:
        return sigma_from_events(
            self._ledger.read_all(),
            active_agents=max(1, len(self._organs)),
            window_epochs=self._sigma_window,
            current_epoch=self._current_epoch,
        )

    def _spawn_sigma(self) -> float:
        """Prospective sigma — the value the gate judges (what one more spawn costs)."""
        return prospective_sigma_from_events(
            self._ledger.read_all(),
            active_agents=max(1, len(self._organs)),
            window_epochs=self._sigma_window,
            current_epoch=self._current_epoch,
        )

    def fitness(self, organ_id: str) -> FitnessReport:
        return compute_fitness(self._ledger.read_all(), organ_id)

    def snapshot(self) -> dict:
        state = self._budget.get()
        head = self._ledger.head()
        return {
            "mode": self._mode.value,
            "killed": self._kill.engaged(),
            "epoch": self._current_epoch,
            "cap_cents": state.cap.cents,
            "committed_cents": state.committed.cents,
            "headroom_cents": budget_math.headroom(state).cents,
            "sigma": self.sigma(),
            "event_count": 0 if head is None else head.seq + 1,
            "head_hash": None if head is None else head.hash,
            "organs": {
                organ_id: {
                    "name": organ.name,
                    "vital": organ.vital,
                    "fitness_net_cents": self.fitness(organ_id).net_cents,
                }
                for organ_id, organ in self._organs.items()
            },
        }

    def run_audit(self) -> list[Violation]:
        events = self._ledger.read_all()
        # Single pass: an execution is a live effect if it carries shadow=False, and a
        # kill violation if it landed while the switch was engaged. Kill/resume toggle
        # the halted window, so a released kill stops condemning later legitimate work.
        live_effects = 0
        post_kill = 0
        killed = False
        for e in events:
            if e.kind is EventKind.KILL:
                killed = True
            elif e.kind is EventKind.RESUME:
                killed = False
            elif e.kind in (EventKind.GRANT, EventKind.SPAWN, EventKind.SPEND):
                if e.payload.get("shadow") is False:
                    live_effects += 1
                if killed:
                    post_kill += 1
        view = SystemView(
            budget=self._budget.get(),
            events=events,
            organs=self._organs,
            mode=self._mode,
            killed=self._kill.engaged(),
            sigma=self.sigma(),
            active_agents=max(1, len(self._organs)),
            live_effects_executed=live_effects if self._mode is Mode.SHADOW else 0,
            post_kill_executions=post_kill,
        )
        return audit(view)

    def trip_breaker_if_unsafe(self, by: str = "circuit-breaker") -> list[Violation]:
        """Opt-in safety circuit breaker (2026 pattern): if the audit finds any
        violation, engage the kill switch and ledger a KILL naming the invariant ids.
        Returns the violations found. NOT auto-wired to any path — a caller (e.g. the
        governor loop) invokes it, so normal operation is unchanged until something is
        actually wrong. Idempotent: does nothing extra once already killed."""
        with self._lock:
            violations = self.run_audit()
            if violations and not self._kill.engaged():
                ids = ",".join(sorted({v.invariant for v in violations}))
                self._kill.engage()
                self._append(EventKind.KILL, {"by": by, "reason": f"circuit breaker tripped: {ids}"})
            return violations

    # ------------------------------------------------------------ projection

    def rebuild_projections(self) -> None:
        """Recreate soma (indexes) from genome (ledger). Proves state is disposable."""
        self._proposals.clear()
        self._verdicts.clear()
        self._executed.clear()
        max_epoch = 0
        for event in self._ledger.read_all():
            max_epoch = max(max_epoch, int(event.payload.get("epoch", 0) or 0))
            if event.kind in (EventKind.GRANT, EventKind.SPAWN, EventKind.SPEND):
                pid = event.payload.get("proposal_id")
                if pid is not None:  # organ-level accounting SPENDs carry no proposal_id
                    self._executed.add(str(pid))
            if event.kind is EventKind.PROPOSAL and event.payload.get("admitted"):
                p = event.payload
                self._proposals[str(p["proposal_id"])] = Proposal(
                    proposal_id=str(p["proposal_id"]),
                    organ_id=str(p["organ_id"]),
                    kind=ProposalKind(str(p["kind"])),
                    amount=Money(int(p["amount_cents"])),
                    rationale=str(p["rationale"]),
                    epoch=int(p["epoch"]),
                    irreversible=bool(p["irreversible"]),
                    parent_agent_id=p.get("parent_agent_id"),
                    spawn_depth=int(p.get("spawn_depth", 0)),
                    approval_ttl_epochs=(
                        None if p.get("approval_ttl_epochs") is None else int(p["approval_ttl_epochs"])
                    ),
                    evidence=_evidence_from_payload(p.get("evidence")),
                )
            elif event.kind is EventKind.VERDICT:
                p = event.payload
                self._verdicts[str(p["proposal_id"])] = Verdict(
                    proposal_id=str(p["proposal_id"]),
                    approved=bool(p["approved"]),
                    by=str(p["by"]),
                    ts=event.ts,
                    note=str(p.get("note", "")),
                    epoch=int(p.get("epoch", 0) or 0),
                )
        self._current_epoch = max_epoch

    # --------------------------------------------------------------- private

    def _approval_is_stale(self, proposal: Proposal, verdict: Verdict | None) -> bool:
        """True when the proposal set a TTL and the verdict has aged past it. Proposals
        without a TTL (the default) are never stale, so prior behavior is preserved."""
        if proposal.approval_ttl_epochs is None or verdict is None:
            return False
        return (self._current_epoch - verdict.epoch) > proposal.approval_ttl_epochs

    def _compensate_release(self, amount: Money) -> None:
        """Undo a committed reservation whose GRANT event failed to land (saga
        compensation). Best-effort CAS-retry; if even compensation cannot land, the
        budget-reconciliation audit check surfaces the residual divergence."""
        for _ in range(MAX_CAS_RETRIES):
            state = self._budget.get()
            try:
                self._budget.compare_and_swap(state.version, budget_math.release(state, amount))
                return
            except ConcurrencyConflictError:
                continue

    def _append(self, kind: EventKind, payload: Mapping[str, object]) -> LedgerEvent:
        return self._ledger.append(self._clock.now_iso(), kind, payload)


def default_budget_state(cap_cents: int) -> BudgetState:
    return BudgetState(cap=Money(cap_cents))


def _evidence_payload(ev: EvidencePack | None) -> dict | None:
    """Serialize an EvidencePack to a JSON-safe dict for the ledger (None stays None)."""
    if ev is None:
        return None
    return {
        "expected_value_cents": ev.expected_value_cents,
        "reversibility": ev.reversibility,
        "alternatives": list(ev.alternatives),
        "rollback": ev.rollback,
    }


def _evidence_from_payload(d: object) -> EvidencePack | None:
    """Rebuild an EvidencePack from a ledger payload (missing/None -> None)."""
    if not isinstance(d, Mapping):
        return None
    return EvidencePack(
        expected_value_cents=int(d.get("expected_value_cents", 0)),
        reversibility=str(d.get("reversibility", "unknown")),
        alternatives=tuple(d.get("alternatives", ()) or ()),
        rollback=str(d.get("rollback", "")),
    )
