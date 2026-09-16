#!/usr/bin/env python3
"""heart/store.py — Heart v2 Gate 1:HeartStore ترابزنشی روی همان chrono.db.

قراردادها (طرح مصوب 2026-08-24 + اصلاحات بازبینی):
  · جداول heart_* در همان chrono.db؛ user_version دست‌نخورده (heart_schema_meta مستقل).
  · نویسنده فقط با BEGIN IMMEDIATE؛ خواننده با PRAGMA query_only=1؛ ATTACH ممنوع؛
    هیچ network/file I/O داخل تراکنش.
  · مدل زمان چهارگانه: boot_id + run_id + mono_ns + wall_utc + seq — ترتیب فقط با seq؛
    mono_ns تنها در همان boot/run قابل مقایسه است.
  · Genesis beat 0: یک‌بار، idempotent — snapshot وضعیت فعلی را import می‌کند،
    تاریخ گذشته جعل نمی‌شود.
  · effectively-once: خواندن/نوشتن رفت‌وبرگشت با idempotency_key یکتا.
$0 · stdlib · fail-closed روی نویسنده، fail-soft روی خواننده.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS / "budget"), str(_OPS)):
    if _p not in os.sys.path:
        os.sys.path.insert(0, _p)
import opslib  # noqa: E402

HEART_SCHEMA_VERSION = 1
SCHEMA = """
CREATE TABLE IF NOT EXISTS heart_schema_meta(
  key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS heart_run(
  run_id TEXT PRIMARY KEY, boot_id TEXT NOT NULL, started_wall TEXT NOT NULL,
  ended_wall TEXT, status TEXT NOT NULL DEFAULT 'OPEN');
CREATE TABLE IF NOT EXISTS heart_beat(
  seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, beat INTEGER NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('RESERVED','RUNNING','COMMITTED','DEGRADED')),
  mode TEXT, period_advisory_s REAL, report_json TEXT,
  mono_ns INTEGER, wall_utc TEXT NOT NULL, UNIQUE (run_id, beat));
CREATE TABLE IF NOT EXISTS heart_event(
  seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, beat INTEGER NOT NULL,
  type TEXT NOT NULL, payload_json TEXT, correlation TEXT, causation TEXT,
  idempotency_key TEXT UNIQUE, mono_ns INTEGER, wall_utc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS heart_outbox(
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, type TEXT NOT NULL,
  payload_json TEXT, status TEXT NOT NULL DEFAULT 'QUEUED'
  CHECK (status IN ('QUEUED','CLAIMED','CONFIRMED','FAILED','DLQ')),
  attempts INTEGER NOT NULL DEFAULT 0, lease_until REAL,
  mono_ns INTEGER, wall_utc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS heart_anchor(
  beat INTEGER NOT NULL, ledger_tip_hash TEXT, kind TEXT NOT NULL,
  wall_utc TEXT NOT NULL, PRIMARY KEY (beat, kind));
"""
_LOCK = threading.RLock()
_STORE = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _boot_id() -> str:
    try:
        return f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
    except Exception:  # noqa: BLE001
        return uuid.uuid4().hex[:12]


class HeartStore:
    """نویسندهٔ واحدِ قلب. هر تراکنش BEGIN IMMEDIATE + busy_timeout."""

    def __init__(self, path=None, *, run_id=None, boot_id=None):
        self.path = Path(path) if path else (opslib.STATE_DIR / "chrono.db")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id or f"run-{uuid.uuid4().hex[:12]}"
        self.boot_id = boot_id or _boot_id()
        self._con = sqlite3.connect(str(self.path), check_same_thread=False,
                                    timeout=10.0, isolation_level=None)
        self._con.execute("PRAGMA journal_mode=WAL")
        self._con.execute("PRAGMA synchronous=FULL")
        self._con.execute("PRAGMA busy_timeout=8000")
        self._init_schema()
        self._open_run()
        self.genesis()

    # ── init ────────────────────────────────────────────────────────────────
    def _init_schema(self) -> None:
        # executescript خودش commit می‌کند — بیرونِ تراکنشِ صریح اجرا شود.
        with _LOCK:
            self._con.executescript(SCHEMA)
            with self._txn():
                self._con.execute(
                    "INSERT OR IGNORE INTO heart_schema_meta(key,value) VALUES('version',?)",
                    (str(HEART_SCHEMA_VERSION),))

    @staticmethod
    def _ctx_txn(con):
        class _T:
            def __enter__(self):
                con.execute("BEGIN IMMEDIATE")
            def __exit__(self, *exc):
                if exc and exc[0] is not None:
                    try:
                        con.execute("ROLLBACK")
                    except sqlite3.Error:
                        pass
                else:
                    con.execute("COMMIT")
        return _T()

    def _txn(self):
        return self._ctx_txn(self._con)

    def _open_run(self) -> None:
        with _LOCK, self._txn():
            self._con.execute(
                "INSERT OR IGNORE INTO heart_run(run_id,boot_id,started_wall,status) "
                "VALUES(?,?,?,'OPEN')", (self.run_id, self.boot_id, _now_iso()))

    # ── Genesis beat 0 ──────────────────────────────────────────────────────
    def genesis(self) -> dict:
        """یک‌بار: beat 0 با snapshot زندهٔ فعلی (نه جعل تاریخ)."""
        anchor_period = None
        try:
            arb = json.loads((opslib.STATE_DIR / "pulse" / "arbiter-latest.json")
                             .read_text("utf-8-sig"))
            anchor_period = arb.get("effective_period_s")
        except Exception:  # noqa: BLE001
            anchor_period = None
        tip_hash = None
        try:
            tip = json.loads((opslib.GENOME_DIR / "ledger" / "ledger.jsonl.tip.json")
                             .read_text("utf-8-sig"))
            tip_hash = tip.get("tip_hash")
        except Exception:  # noqa: BLE001
            tip_hash = None
        with _LOCK, self._txn():
            cur = self._con.execute(
                "INSERT OR IGNORE INTO heart_beat(run_id,beat,status,mode,"
                "period_advisory_s,report_json,mono_ns,wall_utc) "
                "VALUES(?,0,'COMMITTED','GENESIS',?,?,?,?)",
                (self.run_id, anchor_period, json.dumps({
                    "kind": "genesis", "imported_period_s": anchor_period,
                    "ledger_tip_hash": tip_hash}, ensure_ascii=False),
                 time.monotonic_ns(), _now_iso()))
            if cur.rowcount == 1:
                self._con.execute(
                    "INSERT OR IGNORE INTO heart_event(run_id,beat,type,payload_json,"
                    "idempotency_key,mono_ns,wall_utc) VALUES(?,0,'genesis',?, 'genesis',?,?)",
                    (self.run_id, json.dumps({"imported_period_s": anchor_period,
                                              "ledger_tip_hash": tip_hash},
                                             ensure_ascii=False),
                     time.monotonic_ns(), _now_iso()))
                return {"genesis": True, "imported_period_s": anchor_period}
            return {"genesis": False, "already_present": True}

    # ── beat lifecycle ──────────────────────────────────────────────────────
    def begin_beat(self, beat: int, *, mode=None, period_advisory_s=None) -> bool:
        with _LOCK, self._txn():
            cur = self._con.execute(
                "INSERT OR IGNORE INTO heart_beat(run_id,beat,status,mode,"
                "period_advisory_s,mono_ns,wall_utc) VALUES(?,?, 'RESERVED',?,?,?,?)",
                (self.run_id, int(beat), mode, period_advisory_s,
                 time.monotonic_ns(), _now_iso()))
            if cur.rowcount != 1:
                return False
            self._con.execute(
                "UPDATE heart_beat SET status='RUNNING' "
                "WHERE run_id=? AND beat=? AND status='RESERVED'",
                (self.run_id, int(beat)))
            return True

    def commit_beat(self, beat: int, *, mode=None, period_advisory_s=None,
                    report=None, degraded: bool = False) -> bool:
        status = "DEGRADED" if degraded else "COMMITTED"
        with _LOCK, self._txn():
            cur = self._con.execute(
                "UPDATE heart_beat SET status=?, mode=?, period_advisory_s=?, "
                "report_json=?, wall_utc=? WHERE run_id=? AND beat=? "
                "AND status IN ('RESERVED','RUNNING','DEGRADED')",
                (status, mode, period_advisory_s,
                 json.dumps(report or {}, ensure_ascii=False), _now_iso(),
                 self.run_id, int(beat)))
            return cur.rowcount == 1

    # ── events / outbox (idempotent) ────────────────────────────────────────
    def emit(self, beat: int, type_: str, payload: dict, *,
             correlation: str = "", causation: str = "",
             idempotency_key: str = "") -> "int | None":
        key = idempotency_key or f"{type_}:{beat}:{uuid.uuid4().hex[:8]}"
        with _LOCK, self._txn():
            cur = self._con.execute(
                "INSERT OR IGNORE INTO heart_event(run_id,beat,type,payload_json,"
                "correlation,causation,idempotency_key,mono_ns,wall_utc) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (self.run_id, int(beat), type_,
                 json.dumps(payload or {}, ensure_ascii=False),
                 correlation, causation, key, time.monotonic_ns(), _now_iso()))
            return cur.lastrowid if cur.rowcount == 1 else None

    def enqueue(self, beat: int, type_: str, payload: dict) -> "int | None":
        with _LOCK, self._txn():
            cur = self._con.execute(
                "INSERT INTO heart_outbox(run_id,type,payload_json,mono_ns,wall_utc) "
                "VALUES(?,?,?,?,?)",
                (self.run_id, type_, json.dumps(payload or {}, ensure_ascii=False),
                 time.monotonic_ns(), _now_iso()))
            return cur.lastrowid

    def claim_outbox(self, *, limit: int = 8, lease_s: float = 120.0) -> list:
        now = time.time()
        with _LOCK, self._txn():
            rows = self._con.execute(
                "SELECT id,type,payload_json FROM heart_outbox "
                "WHERE status='QUEUED' OR (status='CLAIMED' AND lease_until<?) "
                "ORDER BY id LIMIT ?", (now, int(limit))).fetchall()
            out = []
            for rid, type_, payload in rows:
                self._con.execute(
                    "UPDATE heart_outbox SET status='CLAIMED', attempts=attempts+1, "
                    "lease_until=? WHERE id=?", (now + lease_s, rid))
                out.append({"id": rid, "type": type_, "payload": payload})
            return out

    def confirm_outbox(self, outbox_id: int, *, failed: bool = False,
                       dlq: bool = False) -> None:
        status = ("DLQ" if dlq else "FAILED" if failed else "CONFIRMED")
        with _LOCK, self._txn():
            self._con.execute(
                "UPDATE heart_outbox SET status=?, lease_until=NULL WHERE id=?",
                (status, int(outbox_id)))

    # ── anchors ─────────────────────────────────────────────────────────────
    def anchor(self, beat: int, ledger_tip_hash: str, kind: str = "daily") -> None:
        with _LOCK, self._txn():
            self._con.execute(
                "INSERT OR REPLACE INTO heart_anchor(beat,ledger_tip_hash,kind,wall_utc) "
                "VALUES(?,?,?,?)", (int(beat), ledger_tip_hash, kind, _now_iso()))

    # ── read-side (query_only جدا) ──────────────────────────────────────────
    def reader(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.path), check_same_thread=False, timeout=5.0)
        con.execute("PRAGMA query_only=1")
        con.execute("PRAGMA busy_timeout=5000")
        return con

    def latest_mode(self) -> "tuple[int, str]":
        con = self.reader()
        try:
            row = con.execute(
                "SELECT beat, mode FROM heart_beat "
                "WHERE status IN ('COMMITTED','DEGRADED') AND mode IS NOT NULL "
                "ORDER BY beat DESC LIMIT 1").fetchone()
            return (row[0], row[1]) if row else (0, "GENESIS")
        finally:
            con.close()

    def counts(self) -> dict:
        con = self.reader()
        try:
            beats = con.execute("SELECT COUNT(*), MAX(beat) FROM heart_beat").fetchone()
            evs = con.execute("SELECT COUNT(*) FROM heart_event").fetchone()[0]
            ob = dict(con.execute(
                "SELECT status, COUNT(*) FROM heart_outbox GROUP BY status").fetchall())
            return {"beats": beats[0], "max_beat": beats[1],
                    "events": evs, "outbox": ob}
        finally:
            con.close()

    def close(self) -> None:
        with _LOCK:
            try:
                self._con.execute(
                    "UPDATE heart_run SET status='CLOSED', ended_wall=? "
                    "WHERE run_id=?", (_now_iso(), self.run_id))
                self._con.close()
            except sqlite3.Error:
                pass


def get_store() -> "HeartStore | None":
    """singleton lazy — fail-soft: نبودش tick را نمی‌کشد (caller باید None را بپذیرد)."""
    global _STORE
    try:
        if _STORE is None:
            _STORE = HeartStore()
        return _STORE
    except Exception:  # noqa: BLE001
        return None


if __name__ == "__main__":
    s = HeartStore()
    print(json.dumps({"run": s.run_id, "genesis": s.genesis(), "counts": s.counts()},
                     ensure_ascii=False, indent=2))
    s.close()
