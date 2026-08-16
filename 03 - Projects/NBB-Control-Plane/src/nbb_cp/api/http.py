"""HTTP API skeleton (contract-first). Phase 4 completes validation + status codes.

Contract (v0.2 + owner-gate v0.3):
    GET  /health              -> 200 {"status": "ok", "mode": ...}
    GET  /state               -> 200 KPI snapshot
    GET  /audit               -> 200 {"violations": [...]}  (never 500s on findings)
    POST /proposals           -> 201 admitted | 409 gate-denied | 422 invalid body
    POST /proposals/{id}/verdict -> 200 | 404 unknown proposal | 422 invalid body
    POST /proposals/{id}/execute -> 200 executed/simulated | 409 gate-denied | 404 unknown
    POST /kill                -> 200 (engages the kill switch AND records KILL; halts every gate)
    POST /resume              -> 200 (releases the kill switch AND records RESUME)
    POST /taps                -> 200 {tap_id} (owner-only: درخواست کارت تپ — v0.3)

Owner-gate v0.3 (رأی‌های NBB-V2/V4، پیش‌فرض خاموش = byte-parity):
    وقتی NBB_CP_OWNER_GATE=1 است، همهٔ POSTهای بالا به امضای Ed25519 مالک
    (X-Owner-Sig/Nonce/Ts) نیاز دارند؛ execute و kill علاوه بر آن به کارت تپ
    (X-Owner-Tap + X-Owner) که از POST /taps گرفته شده — یک‌بارمصرف.
    fail-closed: نبود/کهنگی/بازپخش = 401.

FastAPI is an optional extra: `pip install -e .[api]`. Import of this module
without FastAPI installed raises a clear error; nothing else in the package
depends on it.
"""

from __future__ import annotations

from ..app.service import ControlPlaneService
from ..kernel.domain import ProposalKind
from ..kernel.errors import FailClosedError
from .owner_gate import OwnerSignatureGate, OwnerTapGate

try:
    from fastapi import FastAPI, HTTPException, Request
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


class TapIn(BaseModel):
    action: str = Field(pattern="^(execute|kill|resume)$")
    target: str = ""


def create_app(service: ControlPlaneService) -> "FastAPI":
    app = FastAPI(title="NBB Control Plane", version="0.3.0")

    # fail-closed در بوت: اگر فلگ روشن باشد ولی کلید عمومی نباشد، ازEnvError می‌گیریم.
    sig_gate = OwnerSignatureGate.from_env()
    tap_gate = OwnerTapGate()

    async def _guard(request: Request, *, action: str | None = None, target: str = "") -> None:
        """V4 (امضا) همیشه روی POSTها؛ V2 (تپ) فقط برای عمل‌های تپ‌پذیر."""
        body = await request.body()
        headers = {k.lower(): v for k, v in request.headers.items()}
        sig = sig_gate.check(headers, body)
        if not sig.allowed:
            raise HTTPException(status_code=401, detail={"reason": sig.reason})
        if action is not None and sig_gate.enabled:
            tap = tap_gate.check(headers, action, target)
            if not tap.allowed:
                raise HTTPException(status_code=401, detail={"reason": tap.reason})

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
    async def create_proposal(body: ProposalIn, request: Request) -> dict:
        await _guard(request)
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
    async def record_verdict(proposal_id: str, body: VerdictIn, request: Request) -> dict:
        await _guard(request)
        try:
            verdict = service.record_verdict(proposal_id, body.approved, body.by, body.note)
        except FailClosedError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"proposal_id": proposal_id, "approved": verdict.approved}

    @app.post("/proposals/{proposal_id}/execute")
    async def execute(proposal_id: str, request: Request) -> dict:
        await _guard(request, action="execute", target=proposal_id)
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
    async def kill(request: Request, by: str = "operator") -> dict:
        await _guard(request, action="kill", target="")
        service.record_kill(by=by)
        return {"recorded": True}

    @app.post("/resume")
    async def resume(request: Request, by: str = "operator") -> dict:
        await _guard(request)
        service.resume(by=by)
        return {"resumed": True}

    @app.post("/taps")
    async def request_tap(body: TapIn, request: Request) -> dict:
        """کارت تپ مالک — خودش امضاخواه است (فقط مالک می‌تواند کارت بسازد)."""
        await _guard(request)
        card = tap_gate.request_tap(body.action, body.target)
        return {"tap_id": card.tap_id, "action": card.action, "target": card.target}

    return app
