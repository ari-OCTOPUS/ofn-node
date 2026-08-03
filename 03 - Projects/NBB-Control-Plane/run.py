"""Demo entrypoint: one shadow epoch end-to-end, then the KPI snapshot.

Usage: python run.py
Runs in shadow mode with in-memory stores — no keys, no network, no files.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from nbb_cp.app.bootstrap import build_service
from nbb_cp.app.config import AppConfig
from nbb_cp.kernel.domain import ProposalKind


def main() -> None:
    config = AppConfig.from_env()
    service = build_service(config, in_memory=True)

    print(f"NBB Control Plane v0.2 — mode={config.mode.value}, cap={config.global_cap_cents}c\n")

    # 1. Governor proposes a grant for a venture.
    proposal, decision = service.submit_proposal(
        "painting-leads", ProposalKind.GRANT, 500, "seed the lead pipeline for epoch 0"
    )
    print(f"proposal {proposal.proposal_id}: admitted={decision.allowed} ({decision.reason})")

    # 2. Execute through the effector gate (shadow: simulated, but budget is committed).
    result = service.execute(proposal.proposal_id)
    print(f"execute: allowed={result.decision.allowed} simulated={result.simulated}")

    # 3. Revenue arrives; only CONFIRMED will count toward fitness.
    service.record_revenue("painting-leads", "reported", 2000)
    service.record_revenue("painting-leads", "confirmed", 1500)
    fit = service.fitness("painting-leads")
    print(f"fitness painting-leads: confirmed={fit.confirmed_value_cents}c net={fit.net_cents}c")

    # 4. Spawn requires a human verdict — watch it deny without one.
    spawn, spawn_decision = service.submit_proposal(
        "painting-leads", ProposalKind.SPAWN, 1, "clone the outreach agent",
        parent_agent_id="agent-leads-01",
    )
    denied = service.execute(spawn.proposal_id)
    print(f"spawn without verdict: allowed={denied.decision.allowed} ({denied.decision.reason})")

    # 5. Audit + snapshot.
    violations = service.run_audit()
    print(f"\naudit violations: {len(violations)}")
    print(json.dumps(service.snapshot(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
