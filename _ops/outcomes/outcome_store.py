#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""outcome_store.py — spineِ durable و replayableِ outcome (پیرو Stage-1، دلتا-اسکن Q20).

هدف: زنجیرهٔ Proposal → Delivery → Verdict → Outcome را با IDهای مشترک، پایدار (SQLite/WAL)
و بازسازی‌پذیر ثبت کند تا یک مأموریت end-to-end trace شود و metrics قطعی از خودِ store
بازساخته شود. **صریحاً بیرونِ مسیرِ اثر:**
  - stdlib فقط (sqlite3). صفر import از settle/EffectorGate/money `app:`/approval_channel.
  - صفر شبکه/Telegram. صفر side-effectِ بیرونی.
  - `accepted-measurement` = سنجش، **نه** تأییدِ رسمیِ I7؛ vocabulary عمداً جدا نگه داشته شده.
  - `value_aud_claimed` = قیمتِ درخواستی (claim)، **نه** درآمدِ تأییدشده (بدونِ reconcile اینجا).

پایداری: idempotency (کلیدِ UNIQUE)، replay (metrics از rows بازساخته می‌شود)، restart-safe
(دیسک)، UTC-aware، schema-versioned، قفلِ single-writer برای concurrency.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
EVENT_TYPES = ("delivered", "deferred", "accepted-measurement", "rejected", "failed")
_ET_SET = set(EVENT_TYPES)
_LOCK = threading.RLock()   # single-writer روی همهٔ read-modify-writeها (intra-process)

_COLS = ("event_id", "idempotency_key", "correlation_id", "mission_id", "proposal_id",
         "leg_id", "lead_id", "event_type", "verdict", "value_aud_claimed",
         "occurred_at", "recorded_at", "schema_version", "payload_json")


def _utc_now_iso() -> str:
    """UTC-aware ISO-8601 (هرگز naive)."""
    return datetime.now(timezone.utc).isoformat()


def _f(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _sha(obj) -> str:
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _derive_idem(ev: dict) -> str:
    """کلیدِ idempotencyِ قطعی از tupleِ هویتیِ رویداد (اگر داده نشده)."""
    return _sha({"c": ev.get("correlation_id"), "p": ev.get("proposal_id"),
                 "t": ev.get("event_type"), "v": ev.get("verdict")})


def _default_path() -> Path:
    base = os.environ.get("OCTOPUS_STATE_DIR", "").strip()
    root = Path(base) if base else (Path(__file__).resolve().parent.parent / "state")
    return root / "outcomes" / "outcomes.db"


class OutcomeStore:
    """store پایدارِ outcome. path صریح در تست (temp)؛ پیش‌فرض state/outcomes/outcomes.db."""

    def __init__(self, path=None):
        self.path = Path(path) if path else _default_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        with _LOCK:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS outcomes("
                "event_id TEXT PRIMARY KEY,"
                "idempotency_key TEXT UNIQUE NOT NULL,"
                "correlation_id TEXT, mission_id TEXT, proposal_id TEXT,"
                "leg_id TEXT, lead_id TEXT,"
                "event_type TEXT NOT NULL, verdict TEXT,"
                "value_aud_claimed REAL,"
                "occurred_at TEXT NOT NULL, recorded_at TEXT NOT NULL,"
                "schema_version INTEGER NOT NULL, payload_json TEXT)")
            self._conn.commit()

    def record(self, ev: dict) -> bool:
        """درجِ idempotentِ پایدار. True = ردیفِ نو نوشته شد؛ False = idempotency_key از قبل بود.
        event_type نامعتبر → ValueError (fail-fastِ برنامه‌نویسی، نه side-effect)."""
        et = str(ev.get("event_type", ""))
        if et not in _ET_SET:
            raise ValueError(f"unknown event_type: {et!r} (allowed: {EVENT_TYPES})")
        idem = str(ev.get("idempotency_key") or "").strip() or _derive_idem(ev)
        event_id = str(ev.get("event_id") or ("evt_" + hashlib.sha256(idem.encode()).hexdigest()[:16]))
        row = (event_id, idem, ev.get("correlation_id"), ev.get("mission_id"),
               ev.get("proposal_id"), ev.get("leg_id"), ev.get("lead_id"),
               et, ev.get("verdict"), _f(ev.get("value_aud_claimed")),
               str(ev.get("occurred_at") or _utc_now_iso()), _utc_now_iso(),
               SCHEMA_VERSION, json.dumps(ev.get("payload") or {}, ensure_ascii=False, sort_keys=True))
        with _LOCK:
            cur = self._conn.execute(
                "INSERT OR IGNORE INTO outcomes("
                "event_id,idempotency_key,correlation_id,mission_id,proposal_id,leg_id,lead_id,"
                "event_type,verdict,value_aud_claimed,occurred_at,recorded_at,schema_version,payload_json)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", row)
            self._conn.commit()
            return cur.rowcount == 1

    def events(self, *, proposal_id=None, correlation_id=None, mission_id=None) -> list:
        conds, args = [], []
        for col, val in (("proposal_id", proposal_id), ("correlation_id", correlation_id),
                         ("mission_id", mission_id)):
            if val is not None:
                conds.append(f"{col}=?")
                args.append(val)
        q = ("SELECT event_id,idempotency_key,correlation_id,mission_id,proposal_id,leg_id,"
             "lead_id,event_type,verdict,value_aud_claimed,occurred_at,recorded_at,"
             "schema_version,payload_json FROM outcomes")
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY recorded_at, event_id"
        with _LOCK:
            rows = self._conn.execute(q, args).fetchall()
        return [dict(zip(_COLS, r)) for r in rows]

    def metrics(self) -> dict:
        """metricsِ materializedِ قطعی — همیشه از rowsِ durable بازساخته می‌شود (replay)."""
        with _LOCK:
            rows = self._conn.execute(
                "SELECT event_type, value_aud_claimed FROM outcomes").fetchall()
        m = {"delivered": 0, "deferred": 0, "accepted_measurement": 0, "rejected": 0,
             "failed": 0, "value_aud_claimed": 0.0, "total_events": len(rows)}
        for et, val in rows:
            key = str(et).replace("-", "_")
            if key in m:
                m[key] += 1
            if val:
                m["value_aud_claimed"] += float(val)
        decided = m["accepted_measurement"] + m["rejected"]
        m["accept_rate"] = round(m["accepted_measurement"] / decided, 4) if decided else 0.0
        m["value_aud_claimed"] = round(m["value_aud_claimed"], 2)
        # ناوردی: value_aud_claimed یک CLAIM است؛ درآمدِ تأییدشده تا reconcile = 0 (اینجا نداریم).
        m["confirmed_revenue_aud"] = 0.0
        m["schema_version"] = SCHEMA_VERSION
        return m

    def close(self):
        with _LOCK:
            try:
                self._conn.close()
            except Exception:  # noqa: BLE001
                pass
