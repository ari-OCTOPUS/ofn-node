#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""quarantine.py — ContextQuarantine: provenance + trust for untrusted inputs.

QUARANTINED context is inspectable only — no operational consume / write / action.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from hashlib import sha256
from typing import Any, Literal
from uuid import uuid4

TrustLevel = Literal["verified", "derived", "untrusted", "unknown"]


class QuarantineStatus(str, Enum):
    OPEN = "open"
    QUARANTINED = "quarantined"
    RELEASED = "released"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass(frozen=True)
class ContextEnvelope:
    provenance_id: str
    source_kind: str  # user | tool | rag | agent_handoff
    trust_level: TrustLevel
    content_digest: str
    captured_at: str
    status: QuarantineStatus
    reason: str | None = None
    ttl_hours: int | None = 24

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


def digest_text(text: str) -> str:
    return sha256((text or "").encode("utf-8")).hexdigest()


def admit(
    *,
    text: str,
    source_kind: str,
    trust_level: TrustLevel = "untrusted",
    injection_signals: bool = False,
    provenance_id: str | None = None,
) -> ContextEnvelope:
    """Create envelope. Injection / missing trust → QUARANTINED."""
    dig = digest_text(text)
    pid = provenance_id or f"ctx-{uuid4().hex[:12]}"
    now = datetime.now(UTC).isoformat()

    if injection_signals:
        env = ContextEnvelope(
            provenance_id=pid,
            source_kind=source_kind,
            trust_level="untrusted",
            content_digest=dig,
            captured_at=now,
            status=QuarantineStatus.QUARANTINED,
            reason="prompt_injection_signal",
        )
        _log(env, red_team=True)
        return env

    if trust_level in ("untrusted", "unknown") or not pid:
        env = ContextEnvelope(
            provenance_id=pid,
            source_kind=source_kind,
            trust_level=trust_level,
            content_digest=dig,
            captured_at=now,
            status=QuarantineStatus.QUARANTINED,
            reason="untrusted_or_unknown",
        )
        _log(env)
        return env

    return ContextEnvelope(
        provenance_id=pid,
        source_kind=source_kind,
        trust_level=trust_level,
        content_digest=dig,
        captured_at=now,
        status=QuarantineStatus.OPEN,
        reason=None,
    )


def may_consume_operationally(env: ContextEnvelope) -> bool:
    """Operational consume forbidden while quarantined."""
    return env.status == QuarantineStatus.OPEN and env.trust_level in (
        "verified", "derived"
    )


def may_draft_reply(env: ContextEnvelope) -> bool:
    """Talk Discovery may draft from quarantined user input (read-only path)."""
    return env.status in (
        QuarantineStatus.OPEN,
        QuarantineStatus.QUARANTINED,
    ) and env.status not in (QuarantineStatus.REJECTED, QuarantineStatus.EXPIRED)


def _log(env: ContextEnvelope, *, red_team: bool = False) -> None:
    try:
        from evidence_plane.event_log import append_event
        append_event(
            event_type="context.quarantine" + (".red_team" if red_team else ""),
            run_id=f"ctx-{env.provenance_id[:12]}",
            actor="context_quarantine",
            action="admit",
            decision="quarantine",
            reason_code=env.reason or "quarantined",
            payload_digest="sha256:" + env.content_digest[:16],
            extra={"source_kind": env.source_kind, "trust_level": env.trust_level},
        )
    except Exception:  # noqa: BLE001
        pass
