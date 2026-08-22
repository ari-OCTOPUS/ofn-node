#!/usr/bin/env python3
"""Delivery truth states + bounded reconciliation queue (never auto-resends).

Truth states (owner ruling 2026-08-21):
    QUEUED, ATTEMPTING, DELIVERY_CONFIRMED, DELIVERY_FAILED,
    UNCERTAIN_SEND_OUTCOME, OWNER_OBSERVED_UNCONFIRMED_API, DEAD_LETTERED.

Rules:
- UNCERTAIN_SEND_OUTCOME is never automatically resent and never counted as
  DELIVERY_CONFIRMED.
- It enters a bounded reconciliation queue.
- Reconciliation first searches existing send/outbox/transport evidence.
- Owner-confirmed visibility is recorded as immutable
  OWNER_OBSERVED_UNCONFIRMED_API evidence — it never invents a message_id.
- Only transport evidence with a message_id and successful readback becomes
  DELIVERY_CONFIRMED.
- Unresolved items are quarantined / dead-lettered after the bound.

The queue is append-only: every pass appends a resolution row and the
effective state of an item is its last row.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent

SCHEMA = "telegram-delivery-reconciliation/1"
MAX_ATTEMPTS = 3
# message_keys are 64-hex; event ids look like "tg:223883342". Anything else
# is refused before it can reach a filesystem path.
_SAFE_ID = re.compile(r"^[A-Za-z0-9_:.\-]{1,128}$")

TRUTH_QUEUED = "QUEUED"
TRUTH_ATTEMPTING = "ATTEMPTING"
TRUTH_CONFIRMED = "DELIVERY_CONFIRMED"
TRUTH_FAILED = "DELIVERY_FAILED"
TRUTH_UNCERTAIN = "UNCERTAIN_SEND_OUTCOME"
TRUTH_OWNER_OBSERVED = "OWNER_OBSERVED_UNCONFIRMED_API"
TRUTH_DEAD_LETTERED = "DEAD_LETTERED"
TRUTH_STATES = {
    TRUTH_QUEUED, TRUTH_ATTEMPTING, TRUTH_CONFIRMED, TRUTH_FAILED,
    TRUTH_UNCERTAIN, TRUTH_OWNER_OBSERVED, TRUTH_DEAD_LETTERED,
}


def _safe_component(value: str | None) -> str | None:
    """Normalize a stored id to a single path component.

    Path(value).name strips any directory components; we then require the
    stripped name to be identical to the input and free of '..', so an id
    can never escape the fixed state directories below.
    """
    if not isinstance(value, str) or not value:
        return None
    if ".." in value or "/" in value or "\\" in value:
        return None
    name = Path(value).name
    if name != value or name in ("", ".", ".."):
        return None
    if not _SAFE_ID.match(name):
        return None
    return name


def _root() -> Path:
    base = str(os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
    return Path(base) if base else (_OPS / "state")


def _queue_path() -> Path:
    return _root() / "telegram" / "loop" / "reconciliation-queue.jsonl"


def _evidence_path() -> Path:
    return _root() / "telegram" / "loop" / "owner-observed-evidence.jsonl"


def _append(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _read_rows(path: Path) -> list[dict]:
    out = []
    try:
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if isinstance(d, dict):
                    out.append(d)
    except OSError:
        pass
    return out


def _read_json(path: Path) -> dict | None:
    try:
        if path.is_file():
            d = json.loads(path.read_text(encoding="utf-8"))
            return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        pass
    return None



def _event_fs_name(event_id: str) -> str:
    """Canonical on-disk event filename stem (matches durable_loop._event_path).

    Logical event ids are built as ``tg:<update_id>`` (see durable_loop._normalize).
    durable_loop persists them under ``events/tg_<update_id>.json`` because ``:``
    is illegal in Windows filenames. Callers / queue rows may still carry the
    colon form; this helper is the single compare/lookup normalizer so both
    ``tg:223883344`` and ``tg_223883344`` resolve to the same file.
    """
    return str(event_id).replace(":", "_")


def _identity(row: dict) -> tuple[str, str]:
    return (str(row.get("event_id") or ""), str(row.get("message_key") or ""))


def enqueue_uncertain(*, event_id: str, message_key: str,
                      correlation_id: str | None = None,
                      reason: str = "UNCERTAIN_SEND_OUTCOME") -> dict:
    """Record an uncertain send outcome into the bounded reconciliation queue.

    Never resends. The row starts with truth=UNCERTAIN_SEND_OUTCOME and
    status=pending.
    """
    row = {
        "schema": SCHEMA,
        "event_id": str(event_id),
        "message_key": str(message_key),
        "correlation_id": correlation_id,
        "truth": TRUTH_UNCERTAIN,
        "status": "pending",
        "attempts": 0,
        "reason": reason,
        "enqueued_at": time.time(),
    }
    _append(_queue_path(), row)
    return row


def pending() -> list[dict]:
    """All items whose LAST row is still pending (append-only view)."""
    rows = _read_rows(_queue_path())
    last: dict[tuple[str, str], dict] = {}
    for r in rows:
        last[_identity(r)] = r
    return [r for r in last.values() if r.get("status") == "pending"]


def _search_transport_evidence(row: dict) -> dict | None:
    """Existing outbox/event evidence first; returns a truth when found."""
    key = _safe_component(row.get("message_key") or "")
    event_id = _safe_component(row.get("event_id") or "")
    if key is None and event_id is None:
        return None
    try:
        if key is not None:
            ob = _read_json(_root().joinpath("telegram", "loop", "outbox", key)
                            .with_suffix(".json"))
            if ob is not None and ob.get("state") == "CONFIRMED" \
                    and ob.get("message_id") is not None:
                return {"truth": TRUTH_CONFIRMED,
                        "evidence": "outbox CONFIRMED + message_id"}
        if event_id is not None:
            # Normalize tg: -> tg_ so queue event_id matches on-disk stem
            # (durable_loop._event_path). See OCTOPUS-OUTBOX-RECONCILE B5.
            d = _read_json(_root().joinpath(
                "telegram", "loop", "events", _event_fs_name(event_id))
                           .with_suffix(".json"))
            if d is not None and d.get("state") == "CLOSED" \
                    and d.get("readback_verified") is True \
                    and d.get("delivery_message_id") is not None:
                return {"truth": TRUTH_CONFIRMED,
                        "evidence": "event CLOSED + readback + delivery_message_id"}
    except (OSError, ValueError):
        pass
    return None


def _search_owner_evidence(row: dict) -> dict | None:
    """Immutable owner-observed evidence matches this item?"""
    event_id = row.get("event_id") or ""
    key = row.get("message_key") or ""
    for r in _read_rows(_evidence_path()):
        if r.get("kind") != "OWNER_OBSERVED_UNCONFIRMED_API":
            continue
        if r.get("event_id") == event_id or r.get("message_key") == key:
            return {"truth": TRUTH_OWNER_OBSERVED,
                    "evidence": "owner-observed-evidence.jsonl"}
    return None


def record_owner_observation(*, event_id: str, message_key: str,
                             observed_by: str,
                             note: str | None = None) -> dict:
    """Immutable evidence that the owner confirms visibility of the response.

    No message_id is invented here — this is explicitly NOT transport
    confirmation, only owner-side visibility.
    """
    rec = {
        "schema": SCHEMA,
        "kind": "OWNER_OBSERVED_UNCONFIRMED_API",
        "event_id": str(event_id),
        "message_key": str(message_key),
        "observed_by": str(observed_by),
        "note": note,
        "recorded_at": time.time(),
    }
    _append(_evidence_path(), rec)
    return rec


def reconcile(now: float | None = None) -> dict:
    """Bounded reconciliation pass over pending items (append-only).

    1) Search existing outbox/event transport evidence → DELIVERY_CONFIRMED.
    2) Search immutable owner-observed evidence → OWNER_OBSERVED_UNCONFIRMED_API.
    3) Otherwise append a row with attempts+1; past MAX_ATTEMPTS the item is
       dead-lettered (quarantined) — never resent, never confirmed.
    """
    now = float(now if now is not None else time.time())
    resolved = {"confirmed": 0, "owner_observed": 0, "dead_lettered": 0}
    for row in pending():
        found = _search_transport_evidence(row)
        if found is None:
            found = _search_owner_evidence(row)
        nxt = dict(row)
        nxt["updated_at"] = now
        if found is not None:
            nxt["truth"] = found["truth"]
            nxt["status"] = "resolved"
            nxt["resolution"] = found["evidence"]
            nxt["resolved_at"] = now
            if found["truth"] == TRUTH_CONFIRMED:
                resolved["confirmed"] += 1
            else:
                resolved["owner_observed"] += 1
        else:
            nxt["attempts"] = int(row.get("attempts") or 0) + 1
            if nxt["attempts"] >= MAX_ATTEMPTS:
                nxt["status"] = "dead_lettered"
                nxt["truth"] = TRUTH_DEAD_LETTERED
                nxt["resolved_at"] = now
                resolved["dead_lettered"] += 1
            else:
                nxt["status"] = "pending"
        _append(_queue_path(), nxt)
    return {"resolved": resolved, "still_pending": len(pending())}
