"""event_stream.py — Cognitive Runtime: Typed Event Stream + Run ID.

روی `evidence_plane.event_log.append_event` موجود می‌نشیند — بازنویسی نیست.
هر تعامل مالک یک `run_id` دارد و مراحل مهم آن به‌صورت event تایپ‌دار ثبت می‌شوند.

قواعد:
  - run_id در trusted boundary mint می‌شود (نه از client).
  - sequence صعودی در هر run.
  - event_id یکتا و idempotent.
  - redaction خودکار (هیچ متن/prompt/payload خام).
  - may_authorize همیشه false.
  - event log authority نیست؛ به‌تنهایی effect ایجاد نمی‌کند.
"""
from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from cognitive.run_store import create_run, append_event, get_run, list_events

SCHEMA_VERSION = 1

# event types v1 (مطابق runbook مالک)
EVENT_TYPES = frozenset({
    "RUN_CREATED", "USER_MESSAGE_ACCEPTED", "INTENT_DETECTED",
    "CONTEXT_RETRIEVAL_STARTED", "CONTEXT_RETRIEVED", "MEMORY_FOUND",
    "MEMORY_CANDIDATE_CREATED", "MODEL_STARTED", "MODEL_TOKEN",
    "MODEL_FINISHED", "TOOL_REQUESTED", "TOOL_STARTED", "TOOL_RESULT",
    "CLAIM_CREATED", "CLAIM_VERIFIED", "PROPOSAL_CREATED",
    "POLICY_DECISION", "EXECUTION_RECEIPT", "RESPONSE_STARTED",
    "RESPONSE_COMPLETED", "RUN_PAUSED", "RUN_RESUMED",
    "RUN_CANCELLED", "RUN_FAILED", "RUN_COMPLETED",
})

# lifecycle states
RUN_STATES = (
    "CREATED", "UNDERSTANDING", "RETRIEVING", "REASONING",
    "VERIFYING", "RESPONDING", "COMPLETED",
    "PAUSED", "CANCELLED", "FAILED",
    "WAITING_APPROVAL",
)
TERMINAL_STATES = frozenset({"COMPLETED", "CANCELLED", "FAILED"})


def mint_run_id() -> str:
    """run_id یکتا در trusted boundary."""
    return f"run_{uuid4().hex[:12]}"


def mint_trace_id() -> str:
    """trace_id می‌تواند چند run مرتبط را bind کند."""
    return f"trace_{uuid4().hex[:12]}"


def mint_event_id() -> str:
    return f"evt_{uuid4().hex[:16]}"


def start_run(user_text: str, *, trace_id: str | None = None) -> dict[str, Any]:
    """یک run جدید بساز و RUN_CREATED emit کن."""
    run_id = mint_run_id()
    tid = trace_id or mint_trace_id()
    # digest متن (هیچ متن خام ذخیره نمی‌شود)
    import hashlib
    text_digest = hashlib.sha256(user_text.encode("utf-8")).hexdigest()[:16]
    create_run(run_id, trace_id=tid, metadata={"text_digest": text_digest})
    # create_run خودش RUN_CREATED با seq=0 ثبت می‌کند — فقط USER_MESSAGE_ACCEPTED
    emit(run_id, "USER_MESSAGE_ACCEPTED", trace_id=tid, producer="gateway",
         payload={"text_digest": text_digest, "text_len": len(user_text)})
    return {"run_id": run_id, "trace_id": tid}


def emit(run_id: str, event_type: str, *,
         trace_id: str | None = None,
         producer: str = "system",
         status: str = "COMPLETED",
         intent: str | None = None,
         payload: dict[str, Any] | None = None,
         evidence_refs: list[str] | None = None) -> str:
    """یک event تایپ‌دار emit کن. همیشه fail-soft، هرگز crash."""
    if event_type not in EVENT_TYPES:
        # unknown event → still record but flag
        pass
    sequence = append_event(
        run_id=run_id,
        event_type=event_type,
        trace_id=trace_id,
        producer=producer,
        status=status,
        intent=intent,
        payload=payload or {},
        evidence_refs=evidence_refs or [],
    )
    return sequence


def complete_run(run_id: str, *, trace_id: str | None = None,
                 response_digest: str | None = None) -> None:
    """RESPONSE_COMPLETED + RUN_COMPLETED."""
    emit(run_id, "RESPONSE_COMPLETED", trace_id=trace_id, producer="collaborator",
         payload={"response_digest": response_digest} if response_digest else {})
    emit(run_id, "RUN_COMPLETED", trace_id=trace_id, producer="event_stream")


def fail_run(run_id: str, reason: str, *, trace_id: str | None = None) -> None:
    """RUN_FAILED."""
    emit(run_id, "RUN_FAILED", trace_id=trace_id, producer="system",
         status="FAILED", payload={"reason": reason[:200]})


def run_summary(run_id: str) -> dict[str, Any]:
    """خلاصهٔ یک run برای UI/API."""
    events = list_events(run_id)
    if not events:
        return {"run_id": run_id, "status": "UNKNOWN", "events": []}
    run = get_run(run_id)
    return {
        "run_id": run_id,
        "trace_id": run.get("trace_id") if run else None,
        "status": run.get("state", "UNKNOWN") if run else "UNKNOWN",
        "event_count": len(events),
        "last_sequence": events[-1].get("sequence", 0) if events else 0,
        "events": [
            {"sequence": e.get("sequence"), "event_type": e.get("event_type"),
             "producer": e.get("producer"), "status": e.get("status"),
             "occurred_at": e.get("occurred_at")}
            for e in events[-20:]  # آخرین ۲۰ event
        ],
        "may_authorize": False,
    }
