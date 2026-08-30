#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""octopus_reader.py — bridge read-only از Architect/Seed Agent به state واقعی Octopus.

قرارداد (Seed Agent v1 — قدمِ ۵، ۲۰۲۶-۰۸-۰۸):
  · read-only مطلق. هیچ write. هیچ credential.
  · Scope-limited: فقط فایل‌های state، نه secrets/credentials.
  · fail-soft همه‌جا: شکست → None/[]، نه crash.
  · این ماژول مشترک است — هم Architect هم context_assembler می‌توانند import کنند.

منابع:
  · live_snapshot.snapshot() — ۸ بخش state با cache TTL 5s
  · retrieval_router.route() — facts با citation از memory.db + vault_rag
  · semantic_memory.jsonl — episodic خلاصه‌شده
  · effect-shadow.jsonl — trace اعمال
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))

try:
    import opslib
    STATE_DIR = opslib.STATE_DIR
except Exception:  # noqa: BLE001
    opslib = None  # type: ignore
    STATE_DIR = _OPS / "state"

FLAG = "OCTOPUS_WIRE_SEED_ASSEMBLER"


def _flag_on() -> bool:
    return str(os.environ.get(FLAG, "0")).strip().lower() in ("1", "true", "yes", "on")


def _read_jsonl_tail(path: Path, n: int = 10) -> list[dict]:
    """آخرین N خطِ یک فایل JSONL را بخوان (fail-soft)."""
    try:
        if not path.exists():
            return []
        lines = path.read_text("utf-8", errors="replace").splitlines()
        out: list[dict] = []
        for line in lines[-n:]:
            line = line.strip()
            if not line or "\x00" in line:
                continue
            try:
                out.append(json.loads(line))
            except (ValueError, TypeError):
                continue
        return out
    except OSError:
        return []


# ─── public API ─────────────────────────────────────────────────────────────

def read_snapshot() -> dict:
    """خواندن live_snapshot — ۸ بخش state زنده (cache TTL 5s).
    fail-soft: شکست → {"status":"error","reason":"..."}"""
    if not _flag_on():
        return {"status": "disabled", "reason": f"{FLAG}=0"}
    try:
        from control_plane import live_snapshot as ls
        return ls.snapshot(use_cache=True)
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(e).__name__}: {e!s:.120}"}


def read_semantic(n: int = 5) -> list[dict]:
    """آخرین N ورودیِ semantic_memory (episodic خلاصه‌شده).
    فیلدها: ts, kind, gist, salience, recency, importance, source_agent."""
    if not _flag_on():
        return []
    path = STATE_DIR / "semantic_memory.jsonl"
    records = _read_jsonl_tail(path, n)
    # معکوس کن تا جدیدترین اول بیاید
    records.reverse()
    return records


def read_trace(n: int = 10) -> list[dict]:
    """آخرین N ورودیِ effect-shadow (trace اعمال).
    فیلدها: ts, beat, would_throttle_brain, applied, signals, confidence_adjustment."""
    if not _flag_on():
        return []
    path = STATE_DIR / "neural" / "effect-shadow.jsonl"
    records = _read_jsonl_tail(path, n)
    records.reverse()
    # فقط applied=True را برگردان (اعمالِ واقعی)
    return [r for r in records if r.get("applied")]


def read_retrieval(goal_key: str, k: int = 6) -> list[dict]:
    """Wrapper حول retrieval_router.route() — facts با citation.
    خروجی: list of {source, title, relevance, snippet, memory_id}."""
    if not _flag_on() or not goal_key.strip():
        return []
    try:
        from memory import vault_bridge
        return vault_bridge.search_vault_evidence(goal_key, k=k)
    except Exception:  # noqa: BLE001
        # fail-soft: اگر vault_bridge در دسترس نبود، semantic را به‌عنوان fallback بده
        try:
            from memory import retrieval_router
            result = retrieval_router.route(goal_key, k=k)
            return result.get("memories_used", [])
        except Exception:  # noqa: BLE001
            return []


def read_doctor_self_model() -> dict:
    """خواندن self-model و self-knowledge doctor (fail-soft)."""
    if not _flag_on():
        return {"status": "disabled"}
    out: dict[str, Any] = {}
    try:
        sm = json.loads((STATE_DIR / "cortex" / "self-model.json").read_text("utf-8"))
        out["self_model"] = {
            "modules": sm.get("n_modules"),
            "self_awareness_pct": sm.get("self_awareness_pct"),
            "total_lines": sm.get("total_lines"),
            "n_tests": sm.get("n_tests"),
        }
    except (OSError, ValueError):
        out["self_model"] = {"error": True}
    try:
        sk = json.loads((STATE_DIR / "doctor" / "self-knowledge-latest.json").read_text("utf-8"))
        sa = sk.get("self_accuracy", {})
        if isinstance(sa, dict):
            sa = sa.get("accuracy")
        out["doctor"] = {
            "version": sk.get("version"),
            "stable_cycles": sk.get("stable_cycles"),
            "self_accuracy": sa,
        }
    except (OSError, ValueError):
        out["doctor"] = {"error": True}
    return out
