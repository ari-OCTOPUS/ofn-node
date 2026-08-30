from __future__ import annotations
import sqlite3
SCHEMA_VERSION = "3"
_LOG_COLUMNS = [
    ("rmssd_quality", "TEXT"), ("rmssd_source", "TEXT"),
    ("measurement_duration_sec", "INTEGER"), ("measurement_posture", "TEXT"),
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
"""
def _columns(conn, table):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
def run_migrations(conn):
    existing = _columns(conn, "log")
    for name, decl in _LOG_COLUMNS:
        if name not in existing:
            conn.execute(f"ALTER TABLE log ADD COLUMN {name} {decl}")
    conn.executescript(_TABLES)
    conn.execute("INSERT INTO config(key, val) VALUES ('schema_version', ?) "
                 "ON CONFLICT(key) DO UPDATE SET val = excluded.val", (SCHEMA_VERSION,))
    return SCHEMA_VERSION
