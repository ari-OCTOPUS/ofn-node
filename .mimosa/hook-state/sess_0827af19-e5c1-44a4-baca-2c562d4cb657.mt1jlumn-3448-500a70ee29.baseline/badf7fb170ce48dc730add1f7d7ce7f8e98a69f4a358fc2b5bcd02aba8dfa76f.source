#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""db.py — WP3: SQLite schema برای لاگ‌های ارکستراسیون + audit ledger.

قرارداد (Owner-Cockpit WP3، ۲۰۲۶-۰۸-۰۸):
  · ۴ جدول: provider_usage, otel_spans, audit_ledger, owner_sessions.
  · provider_usage: هر call به Fugu با token/cost/model/status.
  · otel_spans: mirrorِ traces.jsonl در SQLite (برای query سریع).
  · audit_ledger: hash-chained (tamper-proof) — هر رکورد hash قبلی را دارد.
  · owner_sessions: session token + owner_id + created_at + expires_at.
  · migration idempotent (CREATE TABLE IF NOT EXISTS).
  · پشت فلگ OCTOPUS_WIRE_OWNER_DB (default OFF).

Schema design:
  · audit_ledger: chain hash = sha256(prev_hash + record_json). tamper → break.
  · provider_usage: برای dashboard و budget tracking.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

FLAG = "OCTOPUS_WIRE_OWNER_DB"
DB_PATH = _OPS / "state" / "owner_cockpit.db"


def _flag_on() -> bool:
    return str(os.environ.get(FLAG, "0")).strip().lower() in ("1", "true", "yes", "on")


SCHEMA_SQL = """
-- WP1: provider_usage — هر call به Fugu
CREATE TABLE IF NOT EXISTS provider_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    model TEXT NOT NULL DEFAULT '',
    task TEXT NOT NULL DEFAULT '',
    tier TEXT NOT NULL DEFAULT '',
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cached_tokens INTEGER DEFAULT 0,
    orchestration_input_tokens INTEGER DEFAULT 0,
    orchestration_output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    latency_ms INTEGER DEFAULT 0,
    status TEXT DEFAULT 'ok',
    error TEXT DEFAULT '',
    trace_id TEXT DEFAULT ''
);

-- WP2: otel_spans — mirror traces.jsonl
CREATE TABLE IF NOT EXISTS otel_spans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT NOT NULL,
    span_id TEXT NOT NULL,
    parent_id TEXT,
    name TEXT NOT NULL,
    start_ms INTEGER NOT NULL,
    end_ms INTEGER,
    duration_ms INTEGER,
    status TEXT DEFAULT 'ok',
    error TEXT DEFAULT '',
    attributes_json TEXT DEFAULT '{}'
);

-- WP3: audit_ledger — hash-chained (tamper-proof)
CREATE TABLE IF NOT EXISTS audit_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    action TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT 'owner',
    target TEXT DEFAULT '',
    payload_hash TEXT NOT NULL,
    prev_hash TEXT NOT NULL DEFAULT '',
    this_hash TEXT NOT NULL,
    status TEXT DEFAULT 'applied'
);

-- WP4: owner_sessions — session tokens
CREATE TABLE IF NOT EXISTS owner_sessions (
    token_hash TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    expires_at TEXT NOT NULL,
    revoked INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_provider_usage_ts ON provider_usage(ts);
CREATE INDEX IF NOT EXISTS idx_audit_ledger_ts ON audit_ledger(ts);
CREATE INDEX IF NOT EXISTS idx_otel_spans_trace ON otel_spans(trace_id);
"""


def get_db() -> sqlite3.Connection:
    """دسترسی به DB (migration idempotent)."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


# ─── provider_usage ─────────────────────────────────────────────────────────

def log_provider_usage(model: str, task: str = "", tier: str = "",
                       usage: dict | None = None, latency_ms: int = 0,
                       status: str = "ok", error: str = "",
                       trace_id: str = "") -> int | None:
    """ثبتِ یک call در provider_usage."""
    if not _flag_on():
        return None
    usage = usage or {}
    try:
        conn = get_db()
        conn.execute("""
            INSERT INTO provider_usage
                (model, task, tier, input_tokens, output_tokens, cached_tokens,
                 orchestration_input_tokens, orchestration_output_tokens,
                 total_tokens, cost_usd, latency_ms, status, error, trace_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            model, task, tier,
            usage.get("input_tokens", 0),
            usage.get("output_tokens", 0),
            usage.get("cached_tokens", 0),
            usage.get("orchestration_input_tokens", 0),
            usage.get("orchestration_output_tokens", 0),
            usage.get("total_tokens", 0),
            usage.get("total_cost_usd", 0.0),
            latency_ms, status, error, trace_id,
        ))
        conn.commit()
        rowid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return rowid
    except sqlite3.Error:
        return None


# ─── audit_ledger (hash-chained) ────────────────────────────────────────────

def _compute_hash(prev_hash: str, record: dict) -> str:
    """chain hash: sha256(prev_hash + canonical_json(record))."""
    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256((prev_hash + canonical).encode("utf-8")).hexdigest()


def audit_append(action: str, actor: str = "owner", target: str = "",
                 payload: dict | None = None, status: str = "applied") -> str | None:
    """ثبتِ یک رکورد در audit_ledger (hash-chained).
    payload_hash = sha256(payload_json). this_hash = chain hash."""
    if not _flag_on():
        return None
    payload = payload or {}
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    try:
        conn = get_db()
        # آخرین hash را بخوان
        row = conn.execute(
            "SELECT this_hash FROM audit_ledger ORDER BY id DESC LIMIT 1"
        ).fetchone()
        prev_hash = row[0] if row else ""
        this_hash = _compute_hash(prev_hash, {
            "action": action, "actor": actor, "target": target,
            "payload_hash": payload_hash, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        conn.execute("""
            INSERT INTO audit_ledger (action, actor, target, payload_hash, prev_hash, this_hash, status)
            VALUES (?,?,?,?,?,?,?)
        """, (action, actor, target, payload_hash, prev_hash, this_hash, status))
        conn.commit()
        conn.close()
        return this_hash
    except sqlite3.Error:
        return None


def verify_chain() -> tuple[bool, int]:
    """verify hash chain — tamper detection.
    خروجی: (valid, broken_at_id)."""
    try:
        conn = get_db()
        rows = conn.execute(
            "SELECT id, prev_hash, this_hash, action, actor, target, payload_hash, ts FROM audit_ledger ORDER BY id"
        ).fetchall()
        conn.close()
        prev = ""
        for row in rows:
            if row["prev_hash"] != prev:
                return False, row["id"]
            expected = _compute_hash(prev, {
                "action": row["action"], "actor": row["actor"],
                "target": row["target"], "payload_hash": row["payload_hash"],
                "ts": row["ts"],
            })
            if row["this_hash"] != expected:
                return False, row["id"]
            prev = row["this_hash"]
        return True, 0
    except sqlite3.Error:
        return False, -1


# ─── owner_sessions ─────────────────────────────────────────────────────────

def create_session(token_hash: str, owner_id: str, expires_at: str) -> bool:
    if not _flag_on():
        return False
    try:
        conn = get_db()
        conn.execute("""
            INSERT OR REPLACE INTO owner_sessions (token_hash, owner_id, expires_at)
            VALUES (?,?,?)
        """, (token_hash, owner_id, expires_at))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        return False


def verify_session(token_hash: str) -> tuple[bool, str]:
    """verify: (valid, owner_id). revoked یا expired → invalid."""
    if not _flag_on():
        return False, ""
    try:
        conn = get_db()
        row = conn.execute(
            "SELECT owner_id, expires_at, revoked FROM owner_sessions WHERE token_hash=?",
            (token_hash,)
        ).fetchone()
        conn.close()
        if not row or row["revoked"]:
            return False, ""
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if row["expires_at"] < now:
            return False, ""
        return True, row["owner_id"]
    except sqlite3.Error:
        return False, ""


def revoke_session(token_hash: str) -> bool:
    if not _flag_on():
        return False
    try:
        conn = get_db()
        conn.execute("UPDATE owner_sessions SET revoked=1 WHERE token_hash=?", (token_hash,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        return False
