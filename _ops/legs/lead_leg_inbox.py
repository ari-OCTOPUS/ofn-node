#!/usr/bin/env python3
"""lead_leg_inbox.py - Lead record backend: inbox persistence for raw leads.

Additive module (INV-12 compliant). Provides register_lead, list_leads, get_lead.
Stores per-lead JSON files in _ops/state/legs/lead-inbox/<id>.json.
Dedup: identical normalized text within 24h returns existing lead (no duplicate).
Atomic write via tmp+os.replace. Fail-soft (never raises to caller).

Gate: OCTOPUS_WIRE_LEAD_INBOX must be "1" (default OFF).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Config: paths
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_STATE = _OPS / "state"
_LEAD_INBOX_DIR = _STATE / "legs" / "lead-inbox"

# ---------------------------------------------------------------------------
# Feature gate
# ---------------------------------------------------------------------------
def _is_enabled() -> bool:
    return os.environ.get("OCTOPUS_WIRE_LEAD_INBOX", "0") == "1"

# ---------------------------------------------------------------------------
# Normalization: lowercase, collapse whitespace, strip
# ---------------------------------------------------------------------------
_WS_RE = re.compile(r"\s+")

def _normalize(text: str) -> str:
    return _WS_RE.sub(" ", text.strip().lower())

# ---------------------------------------------------------------------------
# Dedup key: sha256 of normalized text (stable across calls)
# ---------------------------------------------------------------------------
def _dedup_key(text: str) -> str:
    return hashlib.sha256(_normalize(text).encode("utf-8")).hexdigest()

# ---------------------------------------------------------------------------
# Timestamp helper
# ---------------------------------------------------------------------------
def _now_ts() -> float:
    return time.time()

# ---------------------------------------------------------------------------
# UUID helper (deterministic-seeming but unique)
# ---------------------------------------------------------------------------
def _new_lead_id() -> str:
    return f"LD-{uuid.uuid4().hex[:12]}"

# ---------------------------------------------------------------------------
# Atomic write: write to tmp in same dir, then os.replace
# ---------------------------------------------------------------------------
def _atomic_write_json(path: Path, data: dict) -> None:
    """Write *data* as JSON to *path* atomically (tmp + os.replace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, str(path))
    except BaseException:
        # Best-effort cleanup of temp file
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def register_lead(text: str, source: str = "telegram") -> dict:
    """Register a new lead. Returns a dict with lead_id and status.

    Schema of the stored JSON:
        {lead_id, created_ts, source, raw_text, status:"new",
         contact:null, estimate:null, trace_id}

    Dedup: if the same normalized text was registered within the last 24h,
    returns the existing lead record with status "dup" instead of creating
    a new file.  Atomic write (tmp+os.replace).  Fail-soft on I/O errors.

    Gate: if OCTOPUS_WIRE_LEAD_INBOX != "1", returns {ok:false, reason:"gate_off"}.
    """
    if not _is_enabled():
        return {"ok": False, "reason": "gate_off"}

    raw = (text or "").strip()
    if not raw:
        return {"ok": False, "reason": "empty_text"}

    nkey = _dedup_key(raw)
    now = _now_ts()
    inbox = _LEAD_INBOX_DIR

    # --- dedup scan: check existing leads for same normalized text < 24h ---
    if inbox.is_dir():
        try:
            for fp in sorted(inbox.glob("LD-*.json"), key=lambda p: p.stat().st_mtime):
                try:
                    data = json.loads(fp.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue  # corrupt file — skip silently
                if data.get("status") == "new" and data.get("_nkey") == nkey:
                    age_h = (now - data.get("created_ts", 0)) / 3600.0
                    if age_h < 24.0:
                        return {
                            "ok": True,
                            "status": "dup",
                            "lead_id": data["lead_id"],
                            "reason": f"duplicate_within_24h ({age_h:.1f}h)",
                        }
        except OSError:
            pass  # fail-soft on directory scan

    # --- create new lead ---
    lead_id = _new_lead_id()
    record: dict[str, Any] = {
        "lead_id": lead_id,
        "created_ts": now,
        "source": source,
        "raw_text": raw,
        "status": "new",
        "contact": None,
        "estimate": None,
        "trace_id": None,
        "_nkey": nkey,  # internal dedup key (not part of public schema)
    }
    try:
        _atomic_write_json(inbox / f"{lead_id}.json", record)
    except OSError as exc:
        return {"ok": False, "reason": f"write_error:{exc}"}

    return {"ok": True, "status": "new", "lead_id": lead_id}


def list_leads(status: str | None = None) -> list[dict]:
    """List leads from the inbox directory.

    *status*: optional filter ("new", "dup", etc.).  None = all.
    Returns list of dicts (the stored JSON minus the internal _nkey).
    Sorted by created_ts descending (newest first).  Fail-soft.
    """
    if not _is_enabled():
        return []

    inbox = _LEAD_INBOX_DIR
    if not inbox.is_dir():
        return []

    results: list[dict] = []
    try:
        for fp in inbox.glob("LD-*.json"):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            # Apply status filter
            if status is not None and data.get("status") != status:
                continue
            # Strip internal key before returning
            data.pop("_nkey", None)
            results.append(data)
    except OSError:
        return []

    # Newest first
    results.sort(key=lambda d: d.get("created_ts", 0), reverse=True)
    return results


def get_lead(lead_id: str) -> dict | None:
    """Get a single lead by its lead_id.  Returns None if not found or on error."""
    if not _is_enabled():
        return None

    fp = _LEAD_INBOX_DIR / f"{lead_id}.json"
    if not fp.is_file():
        return None
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
        data.pop("_nkey", None)
        return data
    except (json.JSONDecodeError, OSError):
        return None
