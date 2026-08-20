#!/usr/bin/env python3
"""Decision-bound one-time nonce ledger for Mini App mutation fixtures/shadow.

No live route imports this module yet. It exists behind the security laboratory
boundary until an owner-approved canary explicitly wires it.

The raw nonce is never persisted. Atomic BEGIN IMMEDIATE transactions plus a
UNIQUE nonce_hash guarantee one concurrent winner across threads/processes.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from pathlib import Path

_SCHEMA = "miniapp-decision-ledger/1"
_LOCK = threading.RLock()


def _hash(value: str) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


class DecisionLedger:
    def __init__(self, path: Path | str, *, clock=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._clock = clock or time.time
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False,
                                     isolation_level=None, timeout=10.0)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.executescript(
            "CREATE TABLE IF NOT EXISTS decisions("
            "nonce_hash TEXT PRIMARY KEY, proposal_id TEXT NOT NULL, "
            "card_id TEXT NOT NULL, owner_ref_hash TEXT NOT NULL, "
            "scope_hash TEXT NOT NULL, expires_at REAL NOT NULL, "
            "state TEXT NOT NULL, created_at REAL NOT NULL, consumed_at REAL);"
            "CREATE TABLE IF NOT EXISTS transitions("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, nonce_hash TEXT NOT NULL, "
            "from_state TEXT, to_state TEXT NOT NULL, outcome TEXT NOT NULL, "
            "ts REAL NOT NULL, detail TEXT NOT NULL DEFAULT '{}');")

    def issue(self, *, proposal_id: str, card_id: str, nonce: str,
              owner_ref: str, scope_hash: str, expires_at: float) -> dict:
        fields = (proposal_id, card_id, nonce, owner_ref, scope_hash)
        if any(not str(value or "").strip() for value in fields):
            return {"ok": False, "status_code": 400, "state": "INVALID"}
        nonce_hash = _hash(nonce)
        now = float(self._clock())
        with _LOCK:
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                self._conn.execute(
                    "INSERT INTO decisions VALUES(?,?,?,?,?,?,?,?,NULL)",
                    (nonce_hash, proposal_id, card_id, _hash(owner_ref),
                     scope_hash, float(expires_at), "PENDING", now))
                self._conn.execute(
                    "INSERT INTO transitions(nonce_hash,from_state,to_state,outcome,ts) "
                    "VALUES(?,NULL,'PENDING','ok',?)", (nonce_hash, now))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                return {"ok": False, "status_code": 409,
                        "state": "REPLAY_REJECTED"}
        return {"ok": True, "status_code": 201, "state": "PENDING",
                "nonce_hash": nonce_hash}

    def consume(self, *, proposal_id: str, card_id: str, nonce: str,
                owner_ref: str, scope_hash: str) -> dict:
        nonce_hash = _hash(nonce)
        now = float(self._clock())
        with _LOCK:
            self._conn.execute("BEGIN IMMEDIATE")
            row = self._conn.execute(
                "SELECT proposal_id,card_id,owner_ref_hash,scope_hash,expires_at,state "
                "FROM decisions WHERE nonce_hash=?", (nonce_hash,)).fetchone()
            if row is None:
                self._conn.execute("ROLLBACK")
                return {"ok": False, "status_code": 409,
                        "state": "SCOPE_MISMATCH"}
            got_proposal, got_card, got_owner, got_scope, expires_at, state = row
            if state != "PENDING":
                self._append_transition(nonce_hash, state, "REPLAY_REJECTED",
                                        "rejected", now)
                self._conn.execute("COMMIT")
                return {"ok": False, "status_code": 409,
                        "state": "REPLAY_REJECTED"}
            if now > float(expires_at):
                self._conn.execute(
                    "UPDATE decisions SET state='EXPIRED' WHERE nonce_hash=?",
                    (nonce_hash,))
                self._append_transition(nonce_hash, state, "EXPIRED", "rejected", now)
                self._conn.execute("COMMIT")
                return {"ok": False, "status_code": 410, "state": "EXPIRED"}
            if (got_proposal != proposal_id or got_card != card_id
                    or got_owner != _hash(owner_ref) or got_scope != scope_hash):
                self._append_transition(nonce_hash, state, "SCOPE_MISMATCH",
                                        "rejected", now)
                self._conn.execute("COMMIT")
                return {"ok": False, "status_code": 409,
                        "state": "SCOPE_MISMATCH"}
            updated = self._conn.execute(
                "UPDATE decisions SET state='CONSUMED',consumed_at=? "
                "WHERE nonce_hash=? AND state='PENDING'", (now, nonce_hash)).rowcount
            if updated != 1:
                self._conn.execute("ROLLBACK")
                return {"ok": False, "status_code": 409,
                        "state": "REPLAY_REJECTED"}
            self._append_transition(nonce_hash, state, "RESERVED", "ok", now)
            self._append_transition(nonce_hash, "RESERVED", "CONSUMED", "ok", now)
            self._conn.execute("COMMIT")
        return {"ok": True, "status_code": 200, "state": "CONSUMED",
                "nonce_hash": nonce_hash}

    def _append_transition(self, nonce_hash: str, old: str | None,
                           new: str, outcome: str, ts: float,
                           detail: dict | None = None) -> None:
        self._conn.execute(
            "INSERT INTO transitions(nonce_hash,from_state,to_state,outcome,ts,detail) "
            "VALUES(?,?,?,?,?,?)",
            (nonce_hash, old, new, outcome, ts,
             json.dumps(detail or {}, sort_keys=True, separators=(",", ":"))))

    def transitions(self, nonce_hash: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT from_state,to_state,outcome,ts,detail FROM transitions "
            "WHERE nonce_hash=? ORDER BY id", (nonce_hash,)).fetchall()
        return [{"from": row[0], "to": row[1], "outcome": row[2],
                 "ts": row[3], "detail": json.loads(row[4])} for row in rows]

    def close(self) -> None:
        self._conn.close()
