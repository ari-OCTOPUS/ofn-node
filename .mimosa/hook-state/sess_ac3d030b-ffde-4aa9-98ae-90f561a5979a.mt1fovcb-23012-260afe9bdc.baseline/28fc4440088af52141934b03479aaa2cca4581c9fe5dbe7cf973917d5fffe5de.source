#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""semantic_trace.py — trace instrumentation for Rich Think cycles (WP-C).

هدف: عبور از `context-wired` به یک verdict علمی برای semantic_memory.

این ماژول برای هر Rich Think cycle یک trace record ثبت می‌کند — بدون کپیِ
prompt خام یا gist یا هر PII. فقط hash/reference و boolean و bucket.

قرارداد (PII safety):
  - محتوای gist یا prompt هرگز در trace کپی نمی‌شود.
  - فقط `gist_hash` (SHA256 اولین ۱۲ کاراکتر) و `gist_length_bucket`.
  - هیچ متنِ مالک، هیچ محتوای semantic، هیچ raw prompt.

Schema: SemanticTrace.v1

Fields:
  trace_id           — UUID-like unique id
  ts                 — UTC ISO timestamp
  cycle              — cortex cycle number (if available)
  semantic_memory_attempted — bool: did the code try to read semantic_memory?
  semantic_memory_read_ok    — bool: was the read successful?
  memory_record_id   — reference to the record read (hash prefix), never content
  gist_injected      — bool: was a gist actually appended to the prompt?
  gist_length_bucket — bucket: "empty" | "short" | "medium" | "long"
  router_called      — bool: was model_router.ask() called?
  router_status      — "ok" | "fail" | "skipped"
  output_fingerprint — SHA256 prefix of the model output (for ablation diffing)

Default OFF. Activated only by OCTOPUS_WIRE_SEMANTIC_TRACE=1.
Trace file: _ops/state/cortex/semantic-trace.jsonl (append-only).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
STATE = _HERE.parent / "state"
TRACE_PATH = STATE / "cortex" / "semantic-trace.jsonl"

SCHEMA = "SemanticTrace.v1"


def _is_enabled() -> bool:
    """Only active when explicitly armed. Default OFF."""
    return os.environ.get("OCTOPUS_WIRE_SEMANTIC_TRACE", "0") == "1"


def _hash_prefix(text: str, length: int = 12) -> str:
    """SHA256 prefix of text — for reference/fingerprinting, never content storage."""
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def _bucket(length: int) -> str:
    if length == 0:
        return "empty"
    if length < 50:
        return "short"
    if length < 200:
        return "medium"
    return "long"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append(record: dict) -> None:
    """Append-only write with torn-write protection (tmp+replace pattern)."""
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
    try:
        with open(TRACE_PATH, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
    except OSError:
        pass  # trace must never kill the think path


def record_cycle(
    *,
    cycle: int | None = None,
    semantic_memory_attempted: bool = False,
    semantic_memory_read_ok: bool = False,
    memory_record_id: str = "",
    gist_text: str = "",
    gist_injected: bool = False,
    router_called: bool = False,
    router_status: str = "skipped",
    output_text: str = "",
) -> str | None:
    """Record a Rich Think cycle trace. Returns trace_id if recorded, None if disabled.

    SECURITY: gist_text and output_text are NEVER stored — only their hashes/buckets.
    The caller passes them for fingerprinting only; this function discards the content.
    """
    if not _is_enabled():
        return None

    trace_id = hashlib.sha256(
        f"{_utc_iso()}-{cycle}-{time.time_ns()}".encode()
    ).hexdigest()[:16]

    record = {
        "schema": SCHEMA,
        "trace_id": trace_id,
        "ts": _utc_iso(),
        "cycle": cycle,
        "semantic_memory_attempted": semantic_memory_attempted,
        "semantic_memory_read_ok": semantic_memory_read_ok,
        "memory_record_id": _hash_prefix(memory_record_id) if memory_record_id else "",
        "gist_injected": gist_injected,
        "gist_length_bucket": _bucket(len(gist_text)) if gist_text else "empty",
        "gist_hash": _hash_prefix(gist_text) if gist_text else "",
        "router_called": router_called,
        "router_status": router_status,
        "output_fingerprint": _hash_prefix(output_text) if output_text else "",
    }

    _append(record)
    return trace_id


def summary(limit: int = 100) -> dict:
    """Read recent traces and return a summary (for observability/reporting)."""
    if not TRACE_PATH.exists():
        return {"n": 0, "injected_rate": None}
    try:
        lines = TRACE_PATH.read_text("utf-8").splitlines()
    except OSError:
        return {"n": 0, "injected_rate": None}
    records = []
    for line in lines[-limit:]:
        try:
            records.append(json.loads(line))
        except ValueError:
            continue
    if not records:
        return {"n": 0, "injected_rate": None}
    injected = sum(1 for r in records if r.get("gist_injected"))
    read_ok = sum(1 for r in records if r.get("semantic_memory_read_ok"))
    router_ok = sum(1 for r in records if r.get("router_status") == "ok")
    return {
        "n": len(records),
        "injected_rate": injected / len(records),
        "read_ok_rate": read_ok / len(records),
        "router_ok_rate": router_ok / len(records),
        "ts_range": [records[0].get("ts"), records[-1].get("ts")],
    }
