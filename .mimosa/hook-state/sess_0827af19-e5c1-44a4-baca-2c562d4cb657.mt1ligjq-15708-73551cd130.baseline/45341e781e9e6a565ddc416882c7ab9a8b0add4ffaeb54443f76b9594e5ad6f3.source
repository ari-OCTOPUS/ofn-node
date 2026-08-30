#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prediction_ledger.py — دفترِ پیش‌بینیِ append-only و ضد-backdating (CL01-P4).

قواعد (از verdict مالک):
  · فقط append؛ UPDATE و DELETE در سطحِ خودِ SQLite با تریگر ABORT می‌شوند.
  · prediction_id یکتا (PRIMARY KEY)؛ created_at پس از درج تغییرناپذیر.
  · outcome فقط بعد از prediction و فقط با زمانِ نه‌کوچک‌تر از created_at
    و نهدرآینده (skew مجاز ۳۰۰s) قابل‌ الصاق است — و هرگز ردیفِ پیش‌بینی را
    بازنویسی نمی‌کند (جدول جدا).
  · هر پیش‌بینی الزاماً: trace_id، source، model، confidence، eval_window.
"""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCHEMA_VERSION = "prediction-ledger.v1"
SKEW_SECONDS = 300


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(ts: str) -> datetime:
    dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class PredictionLedger:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(str(self.path), timeout=30)
        c.execute("PRAGMA foreign_keys=ON")
        return c

    def _init_db(self) -> None:
        with self._conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS predictions (
                prediction_id TEXT PRIMARY KEY,
                created_at    TEXT NOT NULL,
                content       TEXT NOT NULL,
                content_sha   TEXT NOT NULL,
                trace_id      TEXT NOT NULL,
                source        TEXT NOT NULL,
                model         TEXT NOT NULL,
                confidence    REAL NOT NULL,
                eval_window   TEXT NOT NULL,
                schema_version TEXT NOT NULL DEFAULT 'prediction-ledger.v1'
            );
            CREATE TABLE IF NOT EXISTS outcomes (
                outcome_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id TEXT NOT NULL REFERENCES predictions(prediction_id),
                outcome_at   TEXT NOT NULL,
                outcome      TEXT NOT NULL,
                outcome_sha  TEXT NOT NULL
            );
            CREATE TRIGGER IF NOT EXISTS trg_pred_no_update
            BEFORE UPDATE ON predictions
            BEGIN SELECT RAISE(ABORT, 'prediction-ledger: append-only (no UPDATE)'); END;
            CREATE TRIGGER IF NOT EXISTS trg_pred_no_delete
            BEFORE DELETE ON predictions
            BEGIN SELECT RAISE(ABORT, 'prediction-ledger: append-only (no DELETE)'); END;
            CREATE TRIGGER IF NOT EXISTS trg_outcome_no_update
            BEFORE UPDATE ON outcomes
            BEGIN SELECT RAISE(ABORT, 'prediction-ledger: append-only (no UPDATE)'); END;
            CREATE TRIGGER IF NOT EXISTS trg_outcome_no_delete
            BEFORE DELETE ON outcomes
            BEGIN SELECT RAISE(ABORT, 'prediction-ledger: append-only (no DELETE)'); END;
            """)

    # ── append ────────────────────────────────────────────────────────────
    def append_prediction(self, *, prediction_id: str, content: str, trace_id: str,
                          source: str, model: str, confidence: float,
                          eval_window: str, created_at: str | None = None) -> str:
        for field, val in (("prediction_id", prediction_id), ("content", content),
                           ("trace_id", trace_id), ("source", source), ("model", model),
                           ("eval_window", eval_window)):
            if not str(val or "").strip():
                raise ValueError(f"prediction_ledger: missing required field {field}")
        if not (0.0 <= float(confidence) <= 1.0):
            raise ValueError("prediction_ledger: confidence must be in [0,1]")
        ts = created_at or _now().isoformat(timespec="seconds")
        _parse(ts)  # باید ISO معتبر باشد
        sha = hashlib.sha256(str(content).encode("utf-8", "replace")).hexdigest()
        with self._conn() as c:
            c.execute("INSERT INTO predictions (prediction_id, created_at, content, content_sha,"
                      " trace_id, source, model, confidence, eval_window) VALUES (?,?,?,?,?,?,?,?,?)",
                      (prediction_id, ts, str(content), sha, trace_id, source, model,
                       float(confidence), eval_window))
        return prediction_id

    def prediction(self, prediction_id: str) -> dict | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM predictions WHERE prediction_id=?",
                            (prediction_id,)).fetchone()
            if row is None:
                return None
            cols = [d[0] for d in c.execute("SELECT * FROM predictions LIMIT 0").description]
            return dict(zip(cols, row))

    # ── outcome ───────────────────────────────────────────────────────────
    def attach_outcome(self, *, prediction_id: str, outcome: str,
                       outcome_at: str | None = None) -> int:
        pred = self.prediction(prediction_id)
        if pred is None:
            raise ValueError("prediction_ledger: outcome for unknown prediction (must exist first)")
        ts_out = _parse(outcome_at or _now().isoformat(timespec="seconds"))
        ts_cre = _parse(pred["created_at"])
        if ts_out < ts_cre:
            raise ValueError("prediction_ledger: outcome_at earlier than created_at (backdating)")
        if ts_out > _now() + timedelta(seconds=SKEW_SECONDS):
            raise ValueError("prediction_ledger: outcome_at in the future beyond skew")
        sha = hashlib.sha256(str(outcome).encode("utf-8", "replace")).hexdigest()
        with self._conn() as c:
            cur = c.execute("INSERT INTO outcomes (prediction_id, outcome_at, outcome, outcome_sha)"
                            " VALUES (?,?,?,?)", (prediction_id, ts_out.isoformat(timespec="seconds"),
                                                  str(outcome), sha))
            return int(cur.lastrowid)

    def outcomes(self, prediction_id: str) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT outcome_id, outcome_at, outcome FROM outcomes"
                             " WHERE prediction_id=? ORDER BY outcome_id", (prediction_id,)).fetchall()
            return [{"outcome_id": r[0], "outcome_at": r[1], "outcome": r[2]} for r in rows]

    def stats(self) -> dict:
        with self._conn() as c:
            n_pred = c.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
            n_out = c.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0]
            return {"predictions": n_pred, "outcomes": n_out, "schema": SCHEMA_VERSION}
