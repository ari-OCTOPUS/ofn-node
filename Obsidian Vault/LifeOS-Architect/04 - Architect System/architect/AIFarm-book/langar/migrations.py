"""
migrations.py — مهاجرتِ schema برای LANGAR (idempotent، غیرمخرب، فقط stdlib).
"""

from __future__ import annotations

import sqlite3

#   v2: ستون‌های کیفیتِ اندازه‌گیری + daily_state
#   v3: habit, habit_log, review, experiment, experiment_day, measurement_import
#   v4: mental_model_snapshot, question_quality, improvement_report, agent_weights (CORE)
#   v5: research, event_log, patch_suggestion (Researcher + observability + safety)
#   v6: verdict_log (append-only) — verdictِ نسخه‌بندی‌شده
#   v7: ailab_* — دادهٔ AI-Lab، جدا از دادهٔ شخصی
#   v8: ai_usage — ردیابیِ مصرف و هزینه (BudgetManager)
SCHEMA_VERSION = "8"

_LOG_COLUMNS: list[tuple[str, str]] = [
    ("rmssd_quality", "TEXT"),
    ("rmssd_source", "TEXT"),
    ("measurement_duration_sec", "INTEGER"),
    ("measurement_posture", "TEXT"),
]

_TABLES = """
CREATE TABLE IF NOT EXISTS daily_state (
    date TEXT PRIMARY KEY, mood INTEGER, energy INTEGER, stress INTEGER, soreness INTEGER,
    exercise INTEGER, caffeine_time TEXT, screen_late INTEGER, social INTEGER,
    deep_work_min INTEGER, meditation_min INTEGER, wake_time TEXT, bedtime TEXT,
    weight REAL, tags TEXT, updated_at TEXT DEFAULT (datetime('now','localtime')));

CREATE TABLE IF NOT EXISTS habit (
    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, cue TEXT, action TEXT,
    min_version TEXT, frequency TEXT DEFAULT 'daily', active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now','localtime')));

CREATE TABLE IF NOT EXISTS habit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT, habit_id INTEGER NOT NULL, date TEXT NOT NULL,
    status TEXT, note TEXT, UNIQUE(habit_id, date));

CREATE TABLE IF NOT EXISTS review (
    id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, period_start TEXT, period_end TEXT,
    created_at TEXT DEFAULT (datetime('now','localtime')), answers_json TEXT, summary TEXT);

CREATE TABLE IF NOT EXISTS experiment (
    id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT DEFAULT (datetime('now','localtime')),
    status TEXT DEFAULT 'active', title TEXT, hypothesis TEXT, metric_primary TEXT DEFAULT 'rmssd',
    metric_secondary TEXT, intervention TEXT, start_date TEXT, end_date TEXT, design TEXT, notes TEXT);

CREATE TABLE IF NOT EXISTS experiment_day (
    id INTEGER PRIMARY KEY AUTOINCREMENT, experiment_id INTEGER NOT NULL, date TEXT NOT NULL,
    intervention_done TEXT, adherence_note TEXT, outcome_note TEXT, UNIQUE(experiment_id, date));

CREATE TABLE IF NOT EXISTS measurement_import (
    id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT DEFAULT (datetime('now','localtime')),
    file_name TEXT, source TEXT, detected_columns TEXT, sample_rate REAL, duration_sec REAL,
    rmssd REAL, mean_hr REAL, beat_count INTEGER, quality TEXT, artifact_ratio REAL,
    used_in_log_id INTEGER, notes TEXT);

CREATE TABLE IF NOT EXISTS mental_model_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT (datetime('now','localtime')),
    traits_json TEXT);

CREATE TABLE IF NOT EXISTS question_quality (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT (datetime('now','localtime')),
    agent TEXT, domain TEXT, provider TEXT, question TEXT,
    answered INTEGER DEFAULT 0, response_time_sec REAL, led_to_log INTEGER DEFAULT 0);

CREATE TABLE IF NOT EXISTS improvement_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT DEFAULT (datetime('now','localtime')),
    metrics_json TEXT, suggestions_json TEXT, status TEXT DEFAULT 'pending');

CREATE TABLE IF NOT EXISTS agent_weights (
    domain TEXT PRIMARY KEY, weight REAL DEFAULT 1.0,
    updated_at TEXT DEFAULT (datetime('now','localtime')));

CREATE TABLE IF NOT EXISTS research (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT (datetime('now','localtime')),
    question TEXT, target TEXT, brief TEXT, sources_json TEXT, tag TEXT,
    status TEXT DEFAULT 'open', verdict TEXT DEFAULT 'pending');

CREATE TABLE IF NOT EXISTS event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT (datetime('now','localtime')),
    type TEXT, data_json TEXT);

CREATE TABLE IF NOT EXISTS patch_suggestion (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT (datetime('now','localtime')),
    issue TEXT, path TEXT, status TEXT DEFAULT 'generated');

CREATE TABLE IF NOT EXISTS verdict_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT (datetime('now','localtime')),
    subject_type TEXT, subject_id INTEGER, verdict TEXT, note TEXT);

-- AI-Lab (جدا از دادهٔ شخصی)
CREATE TABLE IF NOT EXISTS ailab_entry (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT (datetime('now','localtime')),
    kind TEXT, topic TEXT, content TEXT, sources_json TEXT);
CREATE TABLE IF NOT EXISTS ailab_idea (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT (datetime('now','localtime')),
    text TEXT, status TEXT DEFAULT 'open');
CREATE TABLE IF NOT EXISTS ailab_proposal (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT (datetime('now','localtime')),
    target TEXT, issue TEXT, path TEXT, status TEXT DEFAULT 'proposed');

CREATE TABLE IF NOT EXISTS ai_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT (datetime('now','localtime')),
    command TEXT, provider TEXT, model TEXT,
    input_tokens INTEGER, output_tokens INTEGER, estimated_cost_usd REAL);
"""


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def run_migrations(conn: sqlite3.Connection) -> str:
    existing = _columns(conn, "log")
    for name, decl in _LOG_COLUMNS:
        if name not in existing:
            conn.execute(f"ALTER TABLE log ADD COLUMN {name} {decl}")
    conn.executescript(_TABLES)
    conn.execute(
        "INSERT INTO config(key, val) VALUES ('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET val = excluded.val",
        (SCHEMA_VERSION,),
    )
    return SCHEMA_VERSION
