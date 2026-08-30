# -*- coding: utf-8 -*-
"""Afferent event contract — bitemporal, no fabricated occurred_at."""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any

SCHEMA = "organ-afferent-event/1"
INELIGIBLE = "INELIGIBLE_TEMPORAL_METADATA"


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def event_id(path: str, occurred_at: float, content_hash: str) -> str:
    raw = f"{path}|{occurred_at:.3f}|{content_hash}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def make_event(
    *,
    source: str,
    path: str,
    occurred_at: float | None,
    ingested_at: float | None = None,
    content_hash: str = "",
    note_type: str = "",
    tags: list[str] | None = None,
    extra: dict[str, Any] | None = None,
    now: float | None = None,
) -> dict:
    """Build one afferent event. Missing/future occurred_at → ineligible, not fake."""
    now = time.time() if now is None else now
    ingested_at = now if ingested_at is None else ingested_at
    rec: dict[str, Any] = {
        "schema": SCHEMA,
        "source": source,
        "path": path,
        "ingested_at": _iso(ingested_at),
        "ingested_at_unix": ingested_at,
        "content_hash": content_hash,
        "note_type": note_type,
        "tags": list(tags or []),
        "executable": False,
        "paid": False,
        "future_use": False,
        "fabricated_occurred_at": False,
    }
    if occurred_at is None:
        rec["status"] = INELIGIBLE
        rec["occurred_at"] = None
        rec["event_id"] = event_id(path, 0.0, content_hash)
        rec["reason"] = "no real source timestamp"
        return rec
    if occurred_at > now + 60:
        rec["status"] = INELIGIBLE
        rec["occurred_at"] = None
        rec["future_use"] = True
        rec["event_id"] = event_id(path, occurred_at, content_hash)
        rec["reason"] = "source timestamp in the future — not used"
        return rec
    rec["status"] = "ok"
    rec["occurred_at"] = _iso(occurred_at)
    rec["occurred_at_unix"] = occurred_at
    rec["event_id"] = event_id(path, occurred_at, content_hash)
    if extra:
        rec["extra"] = extra
    return rec


def dumps(rec: dict) -> str:
    return json.dumps(rec, ensure_ascii=False, sort_keys=True)
