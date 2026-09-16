# -*- coding: utf-8 -*-
"""R1–R5 loop breakers. Own state under state/organs — never telegram paths."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .paths import ORGANS_STATE, assert_not_telegram

UNKNOWN = "UNKNOWN"
RENDER_UNKNOWN = "نامعلوم"
QUARANTINED = "TOOL_REQUEST_QUARANTINED"
DENY_BY_POLICY = "DENY_BY_POLICY"
DENY_ALREADY_ALLOWED = "DENY_ALREADY_ALLOWED"
MAX_ATTEMPTS = 2
COOLDOWN_S = 24 * 3600
OPEN_RFC_CAP = 8
POLICY_DENY_CAPS = frozenset({"shell.full", "shell.raw", "shell.full_access"})


def metric_count(raw: Any) -> dict:
    """Non-negative counts only. Sentinel -1 → UNKNOWN / نامعلوم. Never publish negatives."""
    try:
        if raw is None or (isinstance(raw, str) and not str(raw).strip()):
            raise ValueError("empty")
        v = int(raw)
    except (TypeError, ValueError):
        return {"value": None, "semantic": UNKNOWN, "render": RENDER_UNKNOWN, "raw_discarded": True}
    if v < 0:
        return {"value": None, "semantic": UNKNOWN, "render": RENDER_UNKNOWN,
                "raw_discarded": True, "sentinel": v}
    return {"value": v, "semantic": "MEASURED", "render": str(v), "raw_discarded": False}


def request_key(need: str, target: str, capability: str) -> str:
    blob = f"{need.strip()}|{target.strip()}|{capability.strip()}".encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:20]


def _qpath(root: Path | None = None) -> Path:
    base = Path(root) if root is not None else ORGANS_STATE
    p = base / "tool-request-quarantine.json"
    assert_not_telegram(p)
    return p


def _load_q(root: Path | None = None) -> dict:
    p = _qpath(root)
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {"items": {}}


def _save_q(d: dict, root: Path | None = None) -> None:
    p = _qpath(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def gate_tool_request(
    need: str,
    target: str,
    capability: str,
    *,
    allowed_registry: set[str] | None = None,
    now: float | None = None,
    reason_from_reject: str = "",
    state_root: Path | None = None,
) -> dict:
    """Max 2 attempts then 24h quarantine. Rejection reason returns to generator."""
    now = time.time() if now is None else now
    cap = capability.strip()
    key = request_key(need, target, cap)
    if cap in POLICY_DENY_CAPS:
        return {"status": DENY_BY_POLICY, "key": key, "reason": "capability denied by policy (no shell.full)",
                "attempts": 0, "feedback_to_generator": "DENY_BY_POLICY: shell.full/raw is not grantable"}
    if allowed_registry and cap in allowed_registry:
        return {"status": DENY_ALREADY_ALLOWED, "key": key,
                "reason": "capability already in registry — do not mint a card",
                "attempts": 0, "feedback_to_generator": "read registry; no new card"}
    store = _load_q(state_root)
    items = store.setdefault("items", {})
    row = items.get(key) or {"attempts": 0, "last_ts": 0.0, "status": "open", "reasons": []}
    if row.get("status") == QUARANTINED:
        until = float(row.get("cooldown_until") or 0)
        if now < until:
            return {"status": QUARANTINED, "key": key, "attempts": row["attempts"],
                    "cooldown_until": until,
                    "feedback_to_generator": row.get("last_reason") or "quarantined"}
        row = {"attempts": 0, "last_ts": 0.0, "status": "open", "reasons": []}
    attempts = int(row.get("attempts") or 0) + 1
    row["attempts"] = attempts
    row["last_ts"] = now
    if reason_from_reject:
        row.setdefault("reasons", []).append(reason_from_reject[:240])
        row["last_reason"] = reason_from_reject[:240]
    if attempts > MAX_ATTEMPTS:
        row["status"] = QUARANTINED
        row["cooldown_until"] = now + COOLDOWN_S
        items[key] = row
        _save_q(store, state_root)
        return {"status": QUARANTINED, "key": key, "attempts": attempts,
                "cooldown_until": row["cooldown_until"],
                "feedback_to_generator": row.get("last_reason") or "max attempts; 24h cooldown"}
    row["status"] = "open"
    items[key] = row
    _save_q(store, state_root)
    return {"status": "ALLOW_RECORD", "key": key, "attempts": attempts,
            "feedback_to_generator": reason_from_reject or ""}


def merge_rfcs(rfcs: list[dict], *, open_cap: int = OPEN_RFC_CAP) -> dict:
    """Cluster similar open RFCs by bottleneck prefix; cap open set. No file delete."""
    open_st = {"draft", "drafted", "sandboxed", "sandbox-skip", "submitted", "open", "pending"}
    open_rows = [r for r in rfcs if str(r.get("status") or "").lower() in open_st]
    clusters: dict[str, list[dict]] = {}
    for r in open_rows:
        bn = str(r.get("bottleneck") or r.get("title") or "")[:80].strip().lower()
        key = bn[:48] or str(r.get("rfc_id") or "")
        clusters.setdefault(key, []).append(r)
    merged = []
    kept = []
    for key, group in clusters.items():
        if len(group) == 1:
            kept.append(group[0])
            continue
        primary = group[0]
        merged.append({
            "cluster": key,
            "primary_id": primary.get("rfc_id"),
            "duplicate_ids": [g.get("rfc_id") for g in group[1:]],
            "count": len(group),
        })
        kept.append({**primary, "merged_from": [g.get("rfc_id") for g in group[1:]],
                     "evidence_required": True, "rollback_required": True})
    kept.sort(key=lambda r: str(r.get("rfc_id") or ""))
    overflow = kept[open_cap:]
    kept = kept[:open_cap]
    return {
        "open_before": len(open_rows),
        "clusters_merged": merged,
        "open_kept": kept,
        "open_overflow_parked": [r.get("rfc_id") for r in overflow],
        "cap": open_cap,
        "rfc_duplicates_merged": bool(merged) or len(open_rows) <= open_cap,
    }


def autotune_card_gate(incident_id: str, evidence: float, *,
                       threshold: float = 0.7, store: dict | None = None,
                       now: float | None = None) -> dict:
    """One incident → one card until evidence changes. evidence=0 never re-fires."""
    now = time.time() if now is None else now
    store = store if store is not None else {}
    prev = store.get(incident_id) or {}
    ev = float(evidence)
    if ev <= 0.0:
        if prev.get("card_emitted"):
            return {"emit": False, "reason": "zero-evidence-repeat-suppressed",
                    "incident_id": incident_id, "evidence": ev}
        store[incident_id] = {"card_emitted": True, "evidence": ev, "ts": now}
        return {"emit": True, "reason": "first-zero-evidence-notice-only",
                "incident_id": incident_id, "evidence": ev, "store": store}
    if ev < threshold:
        return {"emit": False, "reason": "below-threshold", "incident_id": incident_id, "evidence": ev}
    if prev.get("card_emitted") and float(prev.get("evidence") or 0) == ev:
        return {"emit": False, "reason": "same-evidence-suppressed",
                "incident_id": incident_id, "evidence": ev}
    store[incident_id] = {"card_emitted": True, "evidence": ev, "ts": now}
    return {"emit": True, "reason": "evidence-changed-or-first",
            "incident_id": incident_id, "evidence": ev, "store": store}


def halt_record(cause_machine: str, *, extra: dict | None = None,
                now: float | None = None, log_path: Path | None = None) -> dict:
    """Every protective halt gets a machine cause, repeat counter, and root RFC id."""
    now = time.time() if now is None else now
    p = log_path or (ORGANS_STATE / "protective-halts.jsonl")
    assert_not_telegram(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            c = str(rec.get("cause_machine") or "")
            if c:
                counts[c] = counts.get(c, 0) + 1
    n = counts.get(cause_machine, 0) + 1
    rfc_id = "RFC-halt-" + hashlib.sha256(cause_machine.encode("utf-8")).hexdigest()[:8]
    row = {
        "schema": "protective-halt-record/1",
        "ts": now,
        "cause_machine": cause_machine,
        "repeat_count": n,
        "root_rfc_id": rfc_id,
        "executable": False,
        **(extra or {}),
    }
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row
