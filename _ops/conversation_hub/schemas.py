# _ops/conversation_hub/schemas.py — unified chat schemas (v1)
# ADR-039: Conversation Hub — single chat endpoint for Octopus.
# All models are Pydantic v2, strict, frozen — no mutation after creation.
#
# Hard constraints baked into schema:
#   - epistemic_status: only 5 values; retrieval answers → "not_applicable"
#   - confidence: only 4 precise levels; never free-form
#   - external_effect: always False (chat endpoint NEVER executes)
#   - may_authorize: always False (approval is a separate endpoint)
#   - source paths: logical only, never filesystem absolute paths
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SourceRef(BaseModel, frozen=True, strict=True, extra="forbid"):
    """A reference to a source file or artifact.

    path is LOGICAL only — e.g. "cortex/cortex.py", never "F:\\backup\\...".
    The UI must never see the host filesystem layout.
    """
    path: str = Field(min_length=1)
    line: Optional[int] = None
    sha256: Optional[str] = None
    content_hash: Optional[str] = None


# ---------------------------------------------------------------------------
# Enum-like constants (plain strings, validated at usage sites)
# ---------------------------------------------------------------------------

VALID_MODES = frozenset({"auto", "ask", "research", "guide", "propose"})
VALID_DEPTHS = frozenset({"normal", "deep", "brief"})
VALID_ROUTES = frozenset({
    "ask", "vault", "brain", "collab", "runtime", "mcp",
    "epistemic", "guide", "propose", "memory",
})
VALID_EPISTEMIC = frozenset({
    "supported", "refuted", "inconclusive", "blocked", "not_applicable",
})
VALID_CONFIDENCE = frozenset({"evidenced", "derived", "inferred", "unknown"})


class ChatRequest(BaseModel, frozen=True, strict=True, extra="forbid"):
    """Inbound chat request — the only schema the Hub accepts.

    Fields from GPT-5.6 Terra review (idempotency_key, client_sent_at)
    are included for replay safety and anti-confusion.
    """
    schema_version: str = "octopus.chat.request.v1"
    message_id: str = Field(min_length=1)
    conversation_id: str = "owner-main"
    text: str = Field(min_length=1)
    mode: str = "auto"                   # auto|ask|research|guide|propose
    requested_depth: str = "normal"       # normal|deep|brief
    client: str = "telegram-miniapp"
    init_data_verified: bool = True
    idempotency_key: str = ""
    client_sent_at: Optional[str] = None


class RouteDecision(BaseModel, frozen=True, strict=True, extra="forbid"):
    """Output of the deterministic intent router.

    confidence reflects HOW the route was decided:
      - evidenced: explicit mode override (research/guide/propose)
      - derived: keyword matching with >= 2 hits or high-signal keyword
      - inferred: single keyword hit
      - unknown: no keyword matched (fallback to 'ask')
    """
    route: str
    confidence: str   # evidenced|derived|inferred|unknown
    reason: str
    keywords: List[str] = Field(default_factory=list)


class ProvenanceEvent(BaseModel, frozen=True, strict=True, extra="forbid"):
    """Per-interaction provenance record.

    Separates owner-initiated from self-initiated telemetry triggers.
    This is the record the system MUST produce before any processing —
    so it can never retroactively claim a chat was self-initiated.
    """
    event_id: str = Field(min_length=1)
    trigger_source: str = "owner"          # owner|telemetry
    initiator: str = "telegram-miniapp"
    human_prompt_id: Optional[str] = None
    conversation_id: str = "owner-main"
    goal_id: Optional[str] = None
    tool_calls: List[dict] = Field(default_factory=list)
    side_effects: List[str] = Field(default_factory=list)
    may_authorize: bool = False
    ts: str = ""                          # ISO-8601


class ChatReply(BaseModel, frozen=True, strict=True, extra="forbid"):
    """Unified reply — the ONLY response schema from POST /api/octopus/chat.

    Invariant: external_effect is always False. may_authorize is always False.
    Approval and execution happen on separate endpoints with nonce + payload-hash.
    """
    schema_version: str = "octopus.chat.reply.v1"
    ok: bool = True
    answer: str = ""
    route: str = ""
    epistemic_status: str = "not_applicable"
    confidence: str = "unknown"
    sources: List[SourceRef] = Field(default_factory=list)
    run_id: Optional[str] = None
    trace_id: Optional[str] = None
    receipt_ids: List[str] = Field(default_factory=list)
    proposals: List[dict] = Field(default_factory=list)
    provenance_event_id: Optional[str] = None
    may_authorize: bool = False
    external_effect: bool = False
    limitations: List[str] = Field(default_factory=list)
