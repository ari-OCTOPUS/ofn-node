"""Stub Governor — deterministic allocation planner behind an LLM port.

Phase 1 replaces the stub's decision rule with a real LangGraph agent, but the
call surface stays exactly this: snapshot in, plan out, all LLM traffic through
LLMPort (so cassettes capture it and L2 replays it byte-for-byte).

The Governor only proposes (INV-4). Token usage comes back in the plan so the
caller can ledger three-bucket costs — the stub prices 1 token = 1 cent.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..kernel.ports import LLMPort, LLMRequest
from ..kernel.domain import ProposalKind
from .service import ControlPlaneService

MAX_GRANT_CENTS = 500


@dataclass(frozen=True)
class Allocation:
    organ_id: str
    amount_cents: int
    rationale: str


@dataclass(frozen=True)
class GovernorPlan:
    allocations: tuple[Allocation, ...]
    llm_text: str
    input_tokens: int
    output_tokens: int
    orchestration_tokens: int


class StubGovernor:
    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    def plan(self, snapshot: dict) -> GovernorPlan:
        organs = sorted(snapshot["organs"])
        prompt = (
            f"NBB govern epoch {snapshot['epoch']}: "
            f"cap={snapshot['cap_cents']}c committed={snapshot['committed_cents']}c "
            f"headroom={snapshot['headroom_cents']}c sigma={snapshot['sigma']:.2f} "
            f"organs={','.join(organs)}"
        )
        response = self._llm.complete(LLMRequest(task="govern", prompt=prompt))
        per_organ = min(MAX_GRANT_CENTS, snapshot["headroom_cents"] // (2 * max(1, len(organs))))
        allocations = tuple(
            Allocation(
                organ_id=organ_id,
                amount_cents=per_organ,
                rationale=f"epoch {snapshot['epoch']} baseline allocation | {response.text}",
            )
            for organ_id in organs
            if per_organ > 0
        )
        return GovernorPlan(
            allocations=allocations,
            llm_text=response.text,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            orchestration_tokens=response.orchestration_tokens,
        )


def run_demo_epoch(service: ControlPlaneService, llm: LLMPort) -> dict:
    """One scripted governance epoch: plan -> propose -> execute -> account -> advance.

    Deterministic given deterministic ports (FixedClock, SequentialIdGen,
    memory stores, cassette/mock LLM) — the property L2 replay tests pin down.
    """
    plan = StubGovernor(llm).plan(service.snapshot())
    executed = 0
    for allocation in plan.allocations:
        proposal, decision = service.submit_proposal(
            allocation.organ_id, ProposalKind.GRANT, allocation.amount_cents, allocation.rationale
        )
        if decision.allowed and service.execute(proposal.proposal_id).decision.allowed:
            executed += 1
    # Governor's own metabolism, three buckets, stub-priced 1 token = 1 cent.
    service.record_spend(
        "accounting",
        input_cents=plan.input_tokens,
        output_cents=plan.output_tokens,
        orchestration_cents=plan.orchestration_tokens,
    )
    epoch = service.advance_epoch()
    head = service.snapshot()
    return {
        "epoch_completed": epoch - 1,
        "grants_executed": executed,
        "committed_cents": head["committed_cents"],
        "head_hash": head["head_hash"],
        "audit_violations": len(service.run_audit()),
    }
