#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collab_memory.py — PII-safe episodic memory for Collaborator (WP-E2).

default OFF (OCTOPUS_WIRE_COLLAB_MEMORY=0). Append-only JSONL.
UTC timestamps. Idempotency. Secret/PII scrub before persistence.
Malformed input = fail-closed.

Security model:
  - Only summary/intent/ref scrubbed, never raw sensitive text.
  - Secret/PII detection before write.
  - Injectable state dir (for test isolation).
  - Flag-off = no-op.

Schema: CollabMemory.v1
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_STATE_DIR = HERE.parent / "state"
SCHEMA = "CollabMemory.v1"

# PII/secret patterns to scrub/reject
_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password|credential)\s*[=:]\s*\S+", re.I),
    re.compile(r"(?i)sk-[a-zA-Z0-9]{20,}"),  # OpenAI-style keys
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),  # emails
    re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),  # credit card-like
    re.compile(r"(?i)(bearer|authorization)\s*[:=]\s*\S+", re.I),
]


def _is_enabled() -> bool:
    return os.environ.get("OCTOPUS_WIRE_COLLAB_MEMORY", "0") == "1"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _contains_secret(text: str) -> bool:
    """Check if text contains patterns that look like secrets/PII."""
    if not text:
        return False
    for pat in _SECRET_PATTERNS:
        if pat.search(text):
            return True
    return False


def _hash_ref(text: str) -> str:
    """Hash a reference (for dedup/idempotency), never store the text."""
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def append(
    *,
    turn_id: str,
    role: str,
    intent: str,
    summary: str,
    state_dir: Path | None = None,
) -> dict:
    """Append a scrubbed episodic memory entry.

    Args:
        turn_id: unique turn identifier (from caller).
        role: "owner" or "collaborator".
        intent: one-word intent tag (e.g. "ask", "clarify", "propose").
        summary: scrubbed summary (caller must scrub; we double-check).
        state_dir: injectable for test isolation.

    Returns:
        dict with ok/status. Never raises (fail-soft).
    """
    if not _is_enabled():
        return {"ok": False, "status": "disabled", "reason": "OCTOPUS_WIRE_COLLAB_MEMORY=0"}

    # Input validation: reject empty, non-string, or oversized inputs (fail-closed)
    if not turn_id or not isinstance(turn_id, str) or len(turn_id) > 128:
        return {"ok": False, "status": "rejected", "reason": "invalid turn_id"}
    if not role or not isinstance(role, str) or role not in ("owner", "collaborator"):
        return {"ok": False, "status": "rejected", "reason": "invalid role"}
    if not intent or not isinstance(intent, str):
        return {"ok": False, "status": "rejected", "reason": "invalid intent"}
    if not summary or not isinstance(summary, str) or len(summary) > 2000:
        return {"ok": False, "status": "rejected", "reason": "invalid summary"}

    # Fail-closed on secret/PII in summary
    if _contains_secret(summary) or _contains_secret(intent):
        return {"ok": False, "status": "rejected",
                "reason": "secret/PII detected in summary — refused"}

    sd = state_dir or DEFAULT_STATE_DIR
    # Path traversal protection: resolve to canonical form
    try:
        sd = sd.resolve()
    except (OSError, ValueError):
        return {"ok": False, "status": "rejected", "reason": "invalid state_dir"}
    mem_path = sd / "collab-memory.jsonl"

    # Idempotency: check if this turn_id already exists
    existing = _read_existing(mem_path)
    for row in existing:
        if row.get("turn_id") == turn_id:
            return {"ok": True, "status": "duplicate", "turn_id": turn_id,
                    "note": "idempotent — already recorded"}

    record = {
        "schema": SCHEMA,
        "ts": _utc_iso(),
        "turn_id": turn_id,
        "role": role,
        "intent": str(intent)[:100],
        "summary": str(summary)[:500],
        "summary_hash": _hash_ref(summary),
    }

    try:
        mem_path.parent.mkdir(parents=True, exist_ok=True)
        with open(mem_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except OSError as e:
        return {"ok": False, "status": "write_error", "error": str(e)}

    return {"ok": True, "status": "appended", "turn_id": turn_id, "ts": record["ts"]}


def _read_existing(path: Path) -> list[dict]:
    """Read existing entries (for idempotency check)."""
    if not path.exists():
        return []
    rows = []
    try:
        for line in path.read_text("utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue  # skip corrupt lines
    except OSError:
        pass
    return rows


def recent(limit: int = 20, state_dir: Path | None = None) -> list[dict]:
    """Read recent memory entries (for context injection)."""
    if not _is_enabled():
        return []
    sd = state_dir or DEFAULT_STATE_DIR
    return _read_existing(sd / "collab-memory.jsonl")[-limit:]
