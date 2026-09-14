"""lead_effect_gate — the per-effect settle gate for outbound effects.

This is the module outbound_worker.py has lazily imported since the cap
reordering review (2026-07-31) but which was never committed — making the
whole arc fail-closed-by-absence (ImportError → worker_error). It now
exists with the real contract send_one expects:

  release_and_settle(effect_id, candidate, gate, now_ms=None)
      -> {"settled": bool, "reason": str}

Semantics (A08/A09):
  · gate=None is REFUSED ("gate:missing"). A release without a real
    per-effect gate object is a bug by construction — never a pass.
  · The effect row is consumed ATOMICALLY (INSERT OR IGNORE on a PRIMARY
    KEY effect_id) the moment the gate allows. A retry with the same
    effect_id can never reserve twice: it gets settled=False and
    "idempotency:duplicate".
  · A gate DENY consumes nothing — the effect stays releasable (same
    shape as the worker's cap belt: denied-then-retried-tomorrow).
  · Crash windows are honest: after settle and before the transport
    outcome lands, the row stays "settled" and appears in
    unknown_outcomes() until reconciliation marks it sent/failed/unknown.

Store: state/legs/lead-effects.sqlite3 (WAL). One writer class (this
module) per the state-ownership contract; the legacy
ofn/agi2027_runtime/outbound-effects.sqlite3 is READ-ONLY here via
legacy_sent_ids() for P08 reconciliation so old effect_ids cannot be
silently reused.

The ``gate`` object contract (implemented in release_pipeline as
EffectGate): gate.release(effect_id, candidate) -> (ok: bool, reason: str).
It carries the real per-item checks that need pipeline context (caps from
the worker constants are already enforced as a belt in send_one; the gate
re-derives policy, suppression and payload binding).
"""

from __future__ import annotations

import json
import sqlite3
import sys
import threading
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

SCHEMA = "octopus.lead-effect-gate.v1"
DB_PATH = opslib.STATE_DIR / "legs" / "lead-effects.sqlite3"
LEGACY_DB_PATH = _HERE.parent / "agi2027_runtime" / "outbound-effects.sqlite3"

_STATUSES = ("reserved", "settled", "sent", "failed", "unknown")

_LOCK = threading.Lock()


def _connect(path: Path | None = None) -> sqlite3.Connection:
    p = path or DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    _ddl(conn)
    return conn


def _ddl(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS lead_effects(
             effect_id     TEXT PRIMARY KEY,
             lead_id       TEXT NOT NULL,
             status        TEXT NOT NULL CHECK(status IN
                 ('reserved','settled','sent','failed','unknown')),
             draft_sha256  TEXT NOT NULL,
             candidate_json TEXT NOT NULL,
             created_at    TEXT NOT NULL,
             settled_at    TEXT,
             outcome_at    TEXT,
             provider_status TEXT
           )""")


def status(effect_id: str, conn: sqlite3.Connection | None = None) -> dict | None:
    """Row for effect_id or None. Read-only."""
    own = conn is None
    c = conn or _connect()
    try:
        row = c.execute(
            "SELECT effect_id, lead_id, status, draft_sha256, candidate_json, "
            "created_at, settled_at, outcome_at, provider_status "
            "FROM lead_effects WHERE effect_id=?", (str(effect_id),)).fetchone()
    finally:
        if own:
            c.close()
    if not row:
        return None
    return {"effect_id": row[0], "lead_id": row[1], "status": row[2],
            "draft_sha256": row[3], "candidate": json.loads(row[4]),
            "created_at": row[5], "settled_at": row[6],
            "outcome_at": row[7], "provider_status": row[8]}


def ledger_ready(conn: sqlite3.Connection | None = None) -> bool:
    """The effect ledger must be openable AND writable before any release."""
    try:
        c = conn or _connect()
    except Exception:  # noqa: BLE001
        return False
    try:
        if conn is None:
            c.close()
        return True
    except Exception:  # noqa: BLE001
        return False


def release_and_settle(effect_id: str, candidate: dict, *, gate: Any,
                       now_ms: int | None = None,
                       conn: sqlite3.Connection | None = None) -> dict:
    """Consume the effect exactly once if the gate allows; never on deny."""
    eid = str(effect_id or "").strip()
    if not eid:
        return {"settled": False, "reason": "effect:empty-id"}
    if gate is None:
        # Regression lock: the M5 bridge used to pass gate=None here.
        return {"settled": False, "reason": "gate:missing"}
    # Accept a gate object (release method) or a plain callable gate —
    # both must return (ok, reason).
    if hasattr(gate, "release"):
        ok, reason = gate.release(eid, candidate)
    elif callable(gate):
        ok, reason = gate(eid, candidate)
    else:
        return {"settled": False, "reason": "gate:invalid"}
    if not ok:
        # no consumption — the effect stays releasable
        return {"settled": False, "reason": str(reason)}
    own = conn is None
    c = conn or _connect()
    try:
        now_iso = opslib.now_iso()
        with _LOCK:
            cur = c.execute(
                "INSERT OR IGNORE INTO lead_effects(effect_id, lead_id, status,"
                " draft_sha256, candidate_json, created_at, settled_at)"
                " VALUES(?,?,?,?,?,?,?)",
                (eid, str((candidate or {}).get("lead_id") or ""), "settled",
                 str((candidate or {}).get("draft_sha256") or ""),
                 json.dumps(candidate or {}, ensure_ascii=False, sort_keys=True),
                 now_iso, now_iso))
            c.commit()
            if cur.rowcount != 1:
                return {"settled": False, "reason": "idempotency:duplicate"}
        return {"settled": True, "reason": reason}
    finally:
        if own:
            c.close()


def mark_outcome(effect_id: str, sent: bool | None, provider_status: str,
                 conn: sqlite3.Connection | None = None) -> bool:
    """Post-transport reconciliation: sent=True/False, or None → unknown."""
    own = conn is None
    c = conn or _connect()
    try:
        new_status = {True: "sent", False: "failed", None: "unknown"}[sent]
        with _LOCK:
            cur = c.execute(
                "UPDATE lead_effects SET status=?, outcome_at=?, provider_status=?"
                " WHERE effect_id=? AND status='settled'",
                (new_status, opslib.now_iso(), str(provider_status)[:200],
                 str(effect_id)))
            c.commit()
            return cur.rowcount == 1
    finally:
        if own:
            c.close()


def unknown_outcomes(conn: sqlite3.Connection | None = None) -> list[dict]:
    """Effects settled but never reconciled — the crash-after-effect window
    (A09): re-sending these requires provider reconciliation first."""
    own = conn is None
    c = conn or _connect()
    try:
        rows = c.execute(
            "SELECT effect_id, lead_id, settled_at FROM lead_effects"
            " WHERE status='settled' ORDER BY settled_at").fetchall()
        return [{"effect_id": r[0], "lead_id": r[1], "settled_at": r[2]}
                for r in rows]
    finally:
        if own:
            c.close()


def legacy_sent_ids(path: Path | None = None) -> set[str]:
    """Read-only peek at the legacy WAL-mint ledger (P08 reconciliation).
    A legacy db that cannot be opened yields an empty set — never an error,
    never a write."""
    p = path or LEGACY_DB_PATH
    try:
        c = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=5)
    except Exception:  # noqa: BLE001
        return set()
    try:
        rows = c.execute("SELECT name FROM sqlite_master WHERE type='table'"
                         ).fetchall()
        ids: set[str] = set()
        for (tbl,) in rows:
            try:
                cols = [r[1] for r in c.execute(f"PRAGMA table_info({tbl})")]
                id_col = next((x for x in ("effect_id", "eid", "id")
                               if x in cols), None)
                if id_col is None:
                    continue
                for r in c.execute(f"SELECT {id_col} FROM {tbl}"):
                    if r[0]:
                        ids.add(str(r[0]))
            except sqlite3.Error:
                continue
        return ids
    except sqlite3.Error:
        return set()
    finally:
        c.close()
