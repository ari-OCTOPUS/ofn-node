# _ops/conversation_hub/service.py — Conversation Hub service entry point
# ADR-039: Hub is a façade/orchestrator — NOT a replacement for collaborator.
# It rides on top of existing modules (ask_vault, ask_brain, collaborator, etc.).
#
# Phase 1: stub adapters return placeholder text.
# Phase 2: real adapters wire to vault/brain/collab/MCP/runtime/memory/epistemic.
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .router import classify_intent
from .schemas import (
    ChatReply,
    ChatRequest,
    ProvenanceEvent,
    RouteDecision,
    SourceRef,
)

FLAG = "OCTOPUS_UNIFIED_CHAT"
_STUB_LIMITATION = "Phase 1 stub — real adapter not yet wired"


def _enabled() -> bool:
    """Feature flag gate — default OFF for safety."""
    return os.environ.get(FLAG, "0") == "1"


def _now_iso() -> str:
    """Current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _make_provenance(
    *,
    message_id: str = "",
    conversation_id: str = "owner-main",
    idempotency_key: str = "",
) -> ProvenanceEvent:
    """Create a provenance event before any processing."""
    event_id = f"evt-{uuid.uuid4().hex[:12]}"
    return ProvenanceEvent(
        event_id=event_id,
        trigger_source="owner",
        initiator="telegram-miniapp",
        human_prompt_id=message_id or None,
        conversation_id=conversation_id,
        ts=_now_iso(),
    )


# ---------------------------------------------------------------------------
# Stub adapters (Phase 1 — replaced in Phase 2)
# ---------------------------------------------------------------------------

def _stub_ask(text: str, route: str) -> Dict[str, Any]:
    """Stub for ask/vault/brain/collab routes."""
    return {
        "answer": f"[stub:{route}] {text[:80]}",
        "sources": [],
    }


def _stub_runtime() -> Dict[str, Any]:
    """Stub for runtime snapshot."""
    return {
        "answer": "[stub:runtime] system status placeholder — cortex read-model not wired",
        "sources": [],
    }


def _stub_mcp(text: str) -> Dict[str, Any]:
    """Stub for MCP broker."""
    return {
        "answer": f"[stub:mcp] file search placeholder — MCP server not wired",
        "sources": [],
    }


def _stub_memory(text: str) -> Dict[str, Any]:
    """Stub for memory retrieval."""
    return {
        "answer": f"[stub:memory] recall placeholder — memory adapter not wired",
        "sources": [],
    }


def _stub_epistemic(text: str) -> Dict[str, Any]:
    """Stub for epistemic projection."""
    return {
        "answer": "[stub:epistemic] hypothesis projection not wired",
        "sources": [],
    }


def _stub_guide(text: str) -> Dict[str, Any]:
    """Stub for owner guidance."""
    return {
        "answer": f"[stub:guide] guidance placeholder — owner guidance not wired",
        "sources": [],
    }


def _stub_propose(text: str) -> Dict[str, Any]:
    """Stub for proposal queue."""
    return {
        "answer": "[stub:propose] proposal queued — queue adapter not wired",
        "sources": [],
        "proposals": [],
    }


# Route → stub adapter dispatch
_ADAPTERS = {
    "ask": lambda text, _rd: _stub_ask(text, "ask"),
    "vault": lambda text, _rd: _stub_ask(text, "vault"),
    "brain": lambda text, _rd: _stub_ask(text, "brain"),
    "collab": lambda text, _rd: _stub_ask(text, "collab"),
    "runtime": lambda _text, _rd: _stub_runtime(),
    "mcp": lambda text, _rd: _stub_mcp(text),
    "memory": lambda text, _rd: _stub_memory(text),
    "epistemic": lambda text, _rd: _stub_epistemic(text),
    "guide": lambda text, _rd: _stub_guide(text),
    "propose": lambda text, _rd: _stub_propose(text),
}


def _call_adapter(route: str, text: str, decision: RouteDecision) -> Dict[str, Any]:
    """Dispatch to the appropriate adapter (stub or real in Phase 2+)."""
    adapter = _ADAPTERS.get(route)
    if adapter is None:
        return _stub_ask(text, route)
    try:
        return adapter(text, decision)
    except Exception:
        return {"answer": f"[error:{route}] adapter raised an exception", "sources": []}


def handle(
    req: ChatRequest | dict,
    *,
    state_dir: Optional[str] = None,
) -> ChatReply:
    """Main entry point for the Conversation Hub.

    Accepts a ChatRequest (or raw dict that validates as one).
    Returns a ChatReply with unified schema.

    Steps:
      1. Validate request schema
      2. Create provenance event (before any processing)
      3. Route intent via deterministic router
      4. Call adapter (Phase 1 = stub)
      5. Compose unified reply
      6. Attach provenance + limitations
      7. Return ChatReply
    """
    # 1. Validate / coerce request
    if not isinstance(req, ChatRequest):
        req = ChatRequest(**req)  # may raise ValidationError

    # 2. Provenance event (created BEFORE processing — cannot retroactively
    #    claim a chat was self-initiated)
    prov = _make_provenance(
        message_id=req.message_id,
        conversation_id=req.conversation_id,
        idempotency_key=req.idempotency_key,
    )

    # 3. Route intent
    decision = classify_intent(req.text, mode=req.mode)

    # 4. Call adapter
    result = _call_adapter(decision.route, req.text, decision)

    # 5. Compose unified reply
    sources = [
        SourceRef(path=s) if isinstance(s, str) else s
        for s in result.get("sources", [])
    ]

    # Epistemic status: only meaningful for epistemic route.
    # All other routes → not_applicable (never fake "supported").
    if decision.route == "epistemic":
        epistemic = "inconclusive"  # stub cannot determine
    else:
        epistemic = "not_applicable"

    reply = ChatReply(
        ok=True,
        answer=result.get("answer", ""),
        route=decision.route,
        epistemic_status=epistemic,
        confidence=decision.confidence,
        sources=sources,
        provenance_event_id=prov.event_id,
        may_authorize=False,
        external_effect=False,
        limitations=[_STUB_LIMITATION],
    )

    return reply
