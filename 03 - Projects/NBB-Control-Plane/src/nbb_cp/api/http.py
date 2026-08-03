"""HTTP API skeleton (contract-first). Phase 4 completes validation + status codes.

Contract (v0.2):
    GET  /health              -> 200 {"status": "ok", "mode": ...}
    GET  /state               -> 200 KPI snapshot
    GET  /audit               -> 200 {"violations": [...]}  (never 500s on findings)
    POST /proposals           -> 201 admitted | 409 gate-denied | 422 invalid body
    POST /proposals/{id}/verdict -> 200 | 404 unknown proposal | 422 invalid body
    POST /proposals/{id}/execute -> 200 executed/simulated | 409 gate-denied | 404 unknown
    POST /kill                -> 200 (engages the kill switch AND records KILL; halts every gate)
    POST /resume              -> 200 (releases the kill switch AND records RESUME)

FastAPI is an optional extra: `pip install -e .[api]`. Import of this module
without FastAPI installed raises a clear error; nothing else in the package
depends on it.
"""

from __future__ import annotations

from ..app.service import ControlPlaneService
from ..kernel.domain import ProposalKind
from ..kernel.errors import FailClosedError

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover - exercised only without the extra
    raise ImportError(
        "The HTTP API needs the 'api' extra: pip install -e .[api]"
    ) from exc


class ProposalIn(BaseModel):
    organ_id: str = Field(min_length=1)
    kind: str = Field(pattern="^(grant|effect|spawn)$")
    amount_cents: int = Field(gt=0)
    rationale: str = ""
    irreversible: bool = False
    parent_agent_id: str | None = None
    spawn_depth: int = Field(default=0, ge=0)


class VerdictIn(BaseModel):
    approved: bool
    by: str = Field(min_length=1)
    note: str = ""


def create_app(service: ControlPlaneService) -> "FastAPI":
    app = FastAPI(title="NBB Control Plane", version="0.2.0")

    @app.get("/health")
    def health() -> dict:
        snap = service.snapshot()
        return {"status": "ok", "mode": snap["mode"], "killed": snap["killed"]}

    @app.get("/state")
    def state() -> dict:
        return service.snapshot()

    @app.get("/audit")
    def audit() -> dict:
        return {
            "violations": [
                {"invariant": v.invariant, "detail": v.detail} for v in service.run_audit()
            ]
        }

    @app.post("/proposals", status_code=201)
    def create_proposal(body: ProposalIn) -> dict:
        try:
            proposal, decision = service.submit_proposal(
                body.organ_id,
                ProposalKind(body.kind),
                body.amount_cents,
                body.rationale,
                irreversible=body.irreversible,
                parent_agent_id=body.parent_agent_id,
                spawn_depth=body.spawn_depth,
            )
        except FailClosedError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if not decision.allowed:
            raise HTTPException(
                status_code=409,
                detail={"reason": decision.reason, "invariant": decision.invariant},
            )
        return {"proposal_id": proposal.proposal_id, "admitted": True}

    @app.post("/proposals/{proposal_id}/verdict")
    def record_verdict(proposal_id: str, body: VerdictIn) -> dict:
        try:
            verdict = service.record_verdict(proposal_id, body.approved, body.by, body.note)
        except FailClosedError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"proposal_id": proposal_id, "approved": verdict.approved}

    @app.post("/proposals/{proposal_id}/execute")
    def execute(proposal_id: str) -> dict:
        try:
            result = service.execute(proposal_id)
        except FailClosedError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if not result.decision.allowed:
            raise HTTPException(
                status_code=409,
                detail={"reason": result.decision.reason, "invariant": result.decision.invariant},
            )
        return {
            "proposal_id": proposal_id,
            "executed": True,
            "simulated": result.simulated,
        }

    @app.post("/kill")
    def kill(by: str = "operator") -> dict:
        service.record_kill(by=by)
        return {"recorded": True}

    @app.post("/resume")
    def resume(by: str = "operator") -> dict:
        service.resume(by=by)
        return {"resumed": True}

    return app
