#!/usr/bin/env python3
"""test_gate_sweep.py — تستِ sweep_stale_effects در chrono.py (EffectorGate).

$0 آفلاین: ChronoDB با in-memory sqlite تزریق می‌شود.
"""
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import harness
ENV = harness.setup("gate-sweep")   # ایزولاسیون — alert/state به vault موقت، نه واقعی

import chrono


def _make_db():
    """ChronoDB روی tmpdir."""
    import os
    td = tempfile.mkdtemp()
    dbfile = os.path.join(td, "chrono.db")
    return chrono.ChronoDB(dbfile), td


def _utc_ms_ago(hours: float) -> int:
    """millisecond timestamp از hours ساعت پیش."""
    return int((time.time() - hours * 3600) * 1000)


def t_sweep_refuses_old_pending():
    """gated_effect با age > 72h و status=pending → refused."""
    db, _ = _make_db()
    gate = chrono.EffectorGate(db=db)
    # یک effect قدیمی بساز
    db.ex("INSERT INTO gated_effect(effect_id,kind,payload_ref,created_beat,"
         "created_ts,status) VALUES (?,?,?,?,?,'pending')",
         ("old1", "test", "ref1", 0, _utc_ms_ago(100)))
    result = gate.sweep_stale_effects(max_age_hours=72)
    assert result["refused"] == 1
    assert "old1" in result["ids"]
    # وضعیت در DB باید refused باشد
    row = db.q("SELECT status FROM gated_effect WHERE effect_id='old1'")
    assert row[0][0] == "refused"


def t_sweep_keeps_fresh_pending():
    """gated_effect با age < 72h → بدون تغییر."""
    db, _ = _make_db()
    gate = chrono.EffectorGate(db=db)
    db.ex("INSERT INTO gated_effect(effect_id,kind,payload_ref,created_beat,"
         "created_ts,status) VALUES (?,?,?,?,?,'pending')",
         ("fresh1", "test", "ref2", 0, _utc_ms_ago(10)))
    result = gate.sweep_stale_effects(max_age_hours=72)
    assert result["refused"] == 0
    row = db.q("SELECT status FROM gated_effect WHERE effect_id='fresh1'")
    assert row[0][0] == "pending"


def t_sweep_off_when_zero():
    """max_age_hours=0 → sweep خاموش."""
    db, _ = _make_db()
    gate = chrono.EffectorGate(db=db)
    db.ex("INSERT INTO gated_effect(effect_id,kind,payload_ref,created_beat,"
         "created_ts,status) VALUES (?,?,?,?,?,'pending')",
         ("old2", "test", "ref3", 0, _utc_ms_ago(200)))
    result = gate.sweep_stale_effects(max_age_hours=0)
    assert result["refused"] == 0
    row = db.q("SELECT status FROM gated_effect WHERE effect_id='old2'")
    assert row[0][0] == "pending"


def t_sweep_skips_non_pending():
    """gated_effect با status=releasable/settled/refused → بدون تغییر."""
    db, _ = _make_db()
    gate = chrono.EffectorGate(db=db)
    for st in ("releasable", "settled", "refused"):
        db.ex("INSERT INTO gated_effect(effect_id,kind,payload_ref,created_beat,"
             "created_ts,status) VALUES (?,?,?,?,?,?)",
             (f"eff_{st}", "test", "ref", 0, _utc_ms_ago(200), st))
    result = gate.sweep_stale_effects(max_age_hours=72)
    assert result["refused"] == 0
    for st in ("releasable", "settled", "refused"):
        row = db.q("SELECT status FROM gated_effect WHERE effect_id=?", (f"eff_{st}",))
        assert row[0][0] == st


def t_sweep_mixed():
    """ترکیب fresh + old + non-pending → فقط old pending refused."""
    db, _ = _make_db()
    gate = chrono.EffectorGate(db=db)
    db.ex("INSERT INTO gated_effect(effect_id,kind,payload_ref,created_beat,"
         "created_ts,status) VALUES (?,?,?,?,?,'pending')",
         ("mix_old", "test", "r", 0, _utc_ms_ago(100)))
    db.ex("INSERT INTO gated_effect(effect_id,kind,payload_ref,created_beat,"
         "created_ts,status) VALUES (?,?,?,?,?,'pending')",
         ("mix_fresh", "test", "r", 0, _utc_ms_ago(5)))
    db.ex("INSERT INTO gated_effect(effect_id,kind,payload_ref,created_beat,"
         "created_ts,status) VALUES (?,?,?,?,?,'releasable')",
         ("mix_rel", "test", "r", 0, _utc_ms_ago(200)))
    result = gate.sweep_stale_effects(max_age_hours=72)
    assert result["refused"] == 1
    assert result["ids"] == ["mix_old"]


def t_sweep_returns_structure():
    """خروجی ساختار معتبر دارد."""
    db, _ = _make_db()
    gate = chrono.EffectorGate(db=db)
    result = gate.sweep_stale_effects(max_age_hours=72)
    assert isinstance(result, dict)
    assert "refused" in result
    assert "ids" in result
    assert isinstance(result["refused"], int)
    assert isinstance(result["ids"], list)


if __name__ == "__main__":
    failed = harness.run([
        ("refuse old pending", t_sweep_refuses_old_pending),
        ("keep fresh pending", t_sweep_keeps_fresh_pending),
        ("sweep خاموش (max_age=0)", t_sweep_off_when_zero),
        ("skip non-pending", t_sweep_skips_non_pending),
        ("ترکیب mixed", t_sweep_mixed),
        ("ساختار خروجی معتبر", t_sweep_returns_structure),
    ])
    sys.exit(1 if failed else 0)
