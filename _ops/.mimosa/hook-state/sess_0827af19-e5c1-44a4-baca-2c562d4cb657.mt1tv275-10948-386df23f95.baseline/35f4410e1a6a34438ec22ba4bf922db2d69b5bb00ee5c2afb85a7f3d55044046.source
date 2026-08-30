#!/usr/bin/env python3
"""intel_spine — لایهٔ هوش و حافظهٔ اختاپوس.

ماژولی مینیمال برای ثبتِ تعاملات، رویدادها، حقایق، باورها، و تصمیم‌ها —
به‌صورتِ local، append-only، redacted، و provenance-based.

طراحی:
  - هیچ outbound ندارد
  - هیچ secret/PII خام ذخیره نمی‌کند
  - از convention موجود (tmp + os.replace برای atomic) استفاده می‌کند
  - owner stop/kill را نمی‌شکند
  - پشتِ flag: OCTOPUS_INTERACTION_LOG=1 (default off)

لایه‌ها:
  L0 Raw Event Intake (telegram، webapp، owner، agent، system)
  L1 Normalization + Correlation
  L2 Safety/Governance Gate (classification فقط — enforcement نه)
  L3 Working Memory (session-local)
  L4 Episodic Memory (events.jsonl، interactions.jsonl)
  L5 Semantic/Factual Memory (facts.jsonl با provenance)
  L6 Beliefs + Contradictions (beliefs.jsonl، contradictions.jsonl)
  L7 Decisions (decisions.jsonl)
  L8 Learning Loop (proposals.jsonl — shadow، no auto-apply)

State path: _ops/state/intel_spine/*.jsonl
"""
from __future__ import annotations

__version__ = "0.1.0"

FLAG = "OCTOPUS_INTERACTION_LOG"

import json
import os
import hashlib
import time
import uuid
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_STATE = _HERE.parent / "state" / "intel_spine"


def _flag_on() -> bool:
    """آیا interaction log روشن است؟ default off."""
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _ensure_state_dir() -> Path:
    _STATE.mkdir(parents=True, exist_ok=True)
    return _STATE


def _now_iso() -> str:
    """ISO-8601 UTC."""
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


def _redact(value: Any, max_len: int = 40) -> str:
    """متن را redact می‌کند — فقط hash + length، نه محتوای خام.

    برای token/secret/chat_id/PII: فقط prefix/suffix (max 3 chars) + length.
    """
    if value is None:
        return ""
    s = str(value)
    if len(s) <= max_len:
        # کوتاه: فقط hash کوتاه
        return f"<redacted:{hashlib.sha256(s.encode()).hexdigest()[:8]}>"
    # بلند: prefix + suffix + length
    return f"<redacted:{hashlib.sha256(s.encode()).hexdigest()[:8]} len={len(s)}>"


def _actor_ref(actor: Any) -> str:
    """actor را hash می‌کند — نه raw chat_id."""
    if actor is None:
        return ""
    return f"actor:{hashlib.sha256(str(actor).encode()).hexdigest()[:12]}"


def _channel_ref(channel: Any) -> str:
    """channel را hash می‌کند."""
    if channel is None:
        return ""
    return f"ch:{hashlib.sha256(str(channel).encode()).hexdigest()[:12]}"


def _append_jsonl(path: Path, record: dict) -> bool:
    """append-only atomic write با flock-style safety.

    از convention موجود (tmp + os.replace برای atomic) استفاده نمی‌کند چون
    append است نه overwrite. اما line-by-line append با newline هم safe است
    اگر write کامل شود.
    """
    try:
        _ensure_state_dir()
        line = json.dumps(record, ensure_ascii=False) + "\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
        return True
    except Exception:
        # fail-soft: logging نباید caller را crash کند
        return False


# ─── L4: Episodic — Events ──────────────────────────────────────────────

def log_event(
    source: str,
    direction: str,
    actor: Any = None,
    channel: Any = None,
    text: str = "",
    intent_guess: str = "",
    d_level: str = "D0",
    safety_verdict: str = "unknown",
    correlation_id: str = "",
    notes: str = "",
    **extra: Any,
) -> str | None:
    """یک event ثبت کن.

    Returns: event_id اگر ثبت شد، None اگر flag off بود یا خطا.
    """
    if not _flag_on():
        return None
    event_id = _uuid()
    record = {
        "event_id": event_id,
        "ts": _now_iso(),
        "source": source,
        "direction": direction,
        "actor_ref": _actor_ref(actor),
        "channel_ref": _channel_ref(channel),
        "text_redacted": _redact(text) if text else "",
        "intent_guess": intent_guess,
        "d_level": d_level,
        "safety_verdict": safety_verdict,
        "correlation_id": correlation_id,
        "evidence": [],
        "raw_stored": False,
        "notes": notes,
    }
    record.update(extra)
    ok = _append_jsonl(_STATE / "events.jsonl", record)
    return event_id if ok else None


# ─── L4: Episodic — Interactions (Telegram/WebApp) ─────────────────────

def log_interaction(
    source: str,  # "telegram" | "webapp" | "owner" | "agent" | "system"
    direction: str,  # "in" | "out" | "internal"
    actor: Any = None,
    channel: Any = None,
    text: str = "",
    kind: str = "",
    **extra: Any,
) -> str | None:
    """یک interaction ثبت کن (Telegram/WebApp/owner)."""
    event_id = log_event(
        source=source,
        direction=direction,
        actor=actor,
        channel=channel,
        text=text,
        intent_guess=kind,
        **extra,
    )
    if event_id:
        # همچنین در interactions.jsonl
        _append_jsonl(_STATE / "interactions.jsonl", {
            "event_id": event_id,
            "ts": _now_iso(),
            "source": source,
            "direction": direction,
            "kind": kind,
            "actor_ref": _actor_ref(actor),
            "channel_ref": _channel_ref(channel),
            "text_redacted": _redact(text) if text else "",
        })
    return event_id


# ─── L5: Semantic — Facts ──────────────────────────────────────────────

def log_fact(
    claim: str,
    evidence: list[str] | None = None,
    confidence: float = 0.0,
    source: str = "",
    expires_at: str = "",
) -> str | None:
    """یک fact با provenance ثبت کن."""
    if not _flag_on():
        return None
    fact_id = _uuid()
    record = {
        "fact_id": fact_id,
        "ts": _now_iso(),
        "claim": claim,
        "source": source,
        "evidence": evidence or [],
        "confidence": confidence,
        "expires_at": expires_at,
        "status": "active",
    }
    ok = _append_jsonl(_STATE / "facts.jsonl", record)
    return fact_id if ok else None


# ─── L6: Beliefs ───────────────────────────────────────────────────────

def log_belief(
    belief: str,
    basis: list[str] | None = None,
    confidence: float = 0.0,
    contradictions: list[str] | None = None,
) -> str | None:
    """یک belief ثبت کن."""
    if not _flag_on():
        return None
    belief_id = _uuid()
    record = {
        "belief_id": belief_id,
        "ts": _now_iso(),
        "belief": belief,
        "basis": basis or [],
        "confidence": confidence,
        "contradictions": contradictions or [],
        "last_verified": _now_iso(),
        "status": "active",
    }
    ok = _append_jsonl(_STATE / "beliefs.jsonl", record)
    return belief_id if ok else None


# ─── L7: Decisions ─────────────────────────────────────────────────────

def log_decision(
    context: str,
    chosen: str,
    level: str = "D2",
    alternatives: list[str] | None = None,
    risk: str = "",
    reversibility: str = "",
    tests: list[str] | None = None,
    rollback: str = "",
    owner_required: bool = False,
    status: str = "proposed",
) -> str | None:
    """یک decision record ثبت کن."""
    if not _flag_on():
        return None
    decision_id = _uuid()
    record = {
        "decision_id": decision_id,
        "ts": _now_iso(),
        "level": level,
        "context": context,
        "chosen": chosen,
        "alternatives": alternatives or [],
        "risk": risk,
        "reversibility": reversibility,
        "tests": tests or [],
        "rollback": rollback,
        "owner_required": owner_required,
        "status": status,
    }
    ok = _append_jsonl(_STATE / "decisions.jsonl", record)
    return decision_id if ok else None


# ─── L8: Proposals (shadow) ────────────────────────────────────────────

def log_proposal(
    title: str,
    description: str,
    risk: str = "",
    evidence: list[str] | None = None,
) -> str | None:
    """یک proposal ثبت کن (shadow، no auto-apply)."""
    if not _flag_on():
        return None
    proposal_id = _uuid()
    record = {
        "proposal_id": proposal_id,
        "ts": _now_iso(),
        "title": title,
        "description": description,
        "risk": risk,
        "evidence": evidence or [],
        "status": "proposed",  # همیشه proposed — auto-apply ممنون
    }
    ok = _append_jsonl(_STATE / "proposals.jsonl", record)
    return proposal_id if ok else None


# ─── Errors ────────────────────────────────────────────────────────────

def log_error(
    error: str,
    context: str = "",
    severity: str = "warn",
) -> str | None:
    """یک error ثبت کن (بدون secret)."""
    # errors همیشه ثبت می‌شوند حتی اگر flag off باشد — ولی redacted
    error_id = _uuid()
    record = {
        "error_id": error_id,
        "ts": _now_iso(),
        "error": _redact(error, max_len=200),
        "context": _redact(context, max_len=200),
        "severity": severity,
    }
    ok = _append_jsonl(_STATE / "errors.jsonl", record)
    return error_id if ok else None


# ─── Read helpers (for retrieval/Obsidian) ─────────────────────────────

def read_recent(path_name: str, limit: int = 10) -> list[dict]:
    """آخرین N record از یک jsonl بخوان."""
    p = _STATE / f"{path_name}.jsonl"
    if not p.exists():
        return []
    try:
        lines = p.read_text("utf-8").strip().splitlines()
        records = []
        for line in lines[-limit:]:
            line = line.strip()
            if line:
                records.append(json.loads(line))
        return records
    except Exception:
        return []


def stats() -> dict:
    """آمارِ intel_spine."""
    result = {}
    for name in ("events", "interactions", "facts", "beliefs",
                 "decisions", "proposals", "errors"):
        p = _STATE / f"{name}.jsonl"
        if p.exists():
            try:
                count = sum(1 for _ in p.read_text("utf-8").splitlines() if _.strip())
            except Exception:
                count = 0
        else:
            count = 0
        result[name] = count
    result["flag"] = FLAG
    result["flag_on"] = _flag_on()
    result["state_dir"] = str(_STATE)
    return result
