#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""c6_state_machine.py — unified reproduction (C6) lifecycle reconciler + recorder.

Reconciles the four scattered state vocabularies into ONE canonical lifecycle and
writes an append-only transition journal + a DecisionReceipt at every edge:

  research verdict (research_loop ResearchLedger, research_loop.py:35)
  memory admission_state (memory_store.py:29; PENDING invisible)
  hypothesis-queue status (c6_trigger.py PENDING/RUNNING/DONE)
  RFC card state (approval_channel merge/deny/edit)

Canonical lifecycle:
  PROPOSED -> RUNNING -> VERIFIED -> PENDING_ADMISSION -> ADMITTED -> TRANSPLANTED
  with leaves REJECTED / QUARANTINED / RETRACTED / VERIFIED_NOT_ADMITTED /
  TERMINATED / DENIED.

This module DERIVES state from artifacts run_experiment already produces; it holds
NO authority and can change no verdict. Owner-gate boundary is unchanged:
ADMITTED -> TRANSPLANTED is only ever an owner tap (merge_or_deploy stays FORBIDDEN,
governance.py:62). stdlib-only, fail-soft, append-only.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

STATES = ("PROPOSED", "RUNNING", "VERIFIED", "PENDING_ADMISSION", "ADMITTED",
          "TRANSPLANTED", "REJECTED", "QUARANTINED", "RETRACTED",
          "VERIFIED_NOT_ADMITTED", "TERMINATED", "DENIED")

# fail-closed edge table — illegal transitions are refused (same posture as
# memory_store.set_admission_state, memory_store.py:220-247).
_ALLOWED = {
    "PROPOSED": {"RUNNING", "TERMINATED"},
    "RUNNING": {"VERIFIED", "REJECTED", "QUARANTINED", "VERIFIED_NOT_ADMITTED",
                "TERMINATED"},
    "VERIFIED": {"PENDING_ADMISSION", "QUARANTINED", "VERIFIED_NOT_ADMITTED"},
    "PENDING_ADMISSION": {"ADMITTED", "VERIFIED_NOT_ADMITTED", "QUARANTINED",
                          "RETRACTED"},
    "ADMITTED": {"TRANSPLANTED", "DENIED", "RETRACTED"},
}

# run_experiment verdict (research_loop.py) -> unified state.
_VERDICT_MAP = {
    "accepted": "ADMITTED",
    "rejected": "REJECTED",
    "quarantined": "QUARANTINED",
    "verified-not-admitted": "VERIFIED_NOT_ADMITTED",
    "terminated": "TERMINATED",
}


def _journal_path(state_dir) -> Path:
    return Path(state_dir) / "c6" / "state-machine.jsonl"


def repro_id(contract_id) -> str:
    return "repro_" + hashlib.sha256(str(contract_id or "").encode("utf-8")).hexdigest()[:16]


def derive(result: dict) -> str:
    """Map a run_experiment result dict to a unified state (research_loop.py:202-203).
    An accepted row still carrying admission_state==PENDING (promotion crashed) is
    reported as PENDING_ADMISSION rather than ADMITTED."""
    verdict = str((result or {}).get("verdict", "")).strip()
    entry = (result or {}).get("ledger_entry") or {}
    if verdict == "accepted" and entry.get("admission_state") == "PENDING":
        return "PENDING_ADMISSION"
    return _VERDICT_MAP.get(verdict, "TERMINATED")


def _last_state(state_dir, rid: str) -> "str | None":
    p = _journal_path(state_dir)
    if not p.exists():
        return None
    last = None
    try:
        for ln in p.read_text("utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                d = json.loads(ln)
            except ValueError:
                continue
            if d.get("repro_id") == rid:
                last = d.get("to")
    except Exception:  # noqa: BLE001
        return None
    return last


def transition(*, state_dir, contract_id, to_state: str, result=None,
               receipt_store=None, from_state: str = None) -> dict:
    """Append one transition row + one DecisionReceipt (effect_class E0). Illegal
    edges are refused. Never raises; never applies anything external."""
    try:
        if to_state not in STATES:
            return {"ok": False, "reason": f"unknown state {to_state!r}"}
        rid = repro_id(contract_id)
        prev = from_state or _last_state(state_dir, rid)
        if prev is not None and to_state not in _ALLOWED.get(prev, set()) \
                and to_state != prev:
            return {"ok": False, "reason": f"illegal edge {prev}->{to_state}"}
        result = result or {}
        receipt_id = None
        if receipt_store is not None:
            try:
                receipt_id = receipt_store.record({
                    "receipt_id": "dr_" + hashlib.sha256(
                        f"{rid}|{prev}|{to_state}|{time.time()}".encode()).hexdigest()[:16],
                    "trace_id": str(contract_id or ""),
                    "mission_id": "c6-reproduction",
                    "objective": f"repro transition {prev}->{to_state}"[:290],
                    "alternatives": sorted(_ALLOWED.get(prev, {to_state})) or [to_state],
                    "selected_alternative": to_state,
                    "reason_codes": [f"STATE_{to_state}",
                                     f"VERDICT_{str(result.get('verdict','na')).upper()}"],
                    "assumptions": ["owner-gated transplant is the only path to birth"],
                    "memories_used": [], "predicted_outcome": {"memory_id":
                        str(result.get("memory_id") or "")[:120]},
                    "effect_class": "E0"})
            except Exception:  # noqa: BLE001
                receipt_id = None
        row = {"repro_id": rid, "contract_id": str(contract_id or ""),
               "from": prev, "to": to_state,
               "verdict": result.get("verdict"), "memory_id": result.get("memory_id"),
               "receipt_id": receipt_id,
               "evidence_sha": (result.get("ledger_entry") or {}).get("artifact_sha256"),
               "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        p = _journal_path(state_dir)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            f.flush()
        return {"ok": True, "row": row}
    except Exception as e:  # noqa: BLE001 — recorder never kills caller
        return {"ok": False, "reason": f"failsoft:{type(e).__name__}"}


def history(state_dir, contract_id) -> list:
    """Full ordered transition history for one reproduction lineage (read-only)."""
    rid = repro_id(contract_id)
    p = _journal_path(state_dir)
    if not p.exists():
        return []
    out = []
    for ln in p.read_text("utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("repro_id") == rid:
            out.append(d)
    return out
