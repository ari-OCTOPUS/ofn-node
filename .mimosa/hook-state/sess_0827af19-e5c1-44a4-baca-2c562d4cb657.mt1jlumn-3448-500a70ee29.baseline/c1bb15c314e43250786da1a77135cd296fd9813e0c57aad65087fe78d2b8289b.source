#!/usr/bin/env python3
"""test_chrono_schema_migration.py — C1: chrono.db schema migration framework.

Proves (hermetic, no live DB):
  * fresh DB -> user_version 1
  * legacy-unversioned v1 (user_version=0, has data) -> v1, DATA PRESERVED
  * already-v1 -> no-op
  * malformed gated_effect (wrong columns) -> ChronoSchemaError (fail-closed)
  * unknown higher version -> ChronoSchemaError (no auto-downgrade)
  * init twice -> idempotent; user_version never decreases

Run: python -X utf8 test_chrono_schema_migration.py
"""
import sqlite3
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
import harness  # noqa: E402
harness.setup("chrono-schema-migration")
import chrono  # noqa: E402

_V1_DDL = """CREATE TABLE gated_effect (
  effect_id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload_ref TEXT NOT NULL,
  created_beat INTEGER, created_ts INTEGER NOT NULL, release_ref TEXT,
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending','releasable','settled','refused')));"""


def _uv(path):
    c = sqlite3.connect(path)
    v = c.execute("PRAGMA user_version").fetchone()[0]
    c.close()
    return v


def _tmp():
    return str(Path(tempfile.mkdtemp(prefix="chrono-mig-")) / "c.db")


def t_a_fresh_db_migrates_to_v1():
    p = _tmp()
    chrono.ChronoDB(p).close()
    assert _uv(p) == chrono.CHRONO_SCHEMA_TARGET


def t_b_legacy_unversioned_v1_preserved():
    p = _tmp()
    c = sqlite3.connect(p)
    c.executescript(_V1_DDL)
    c.execute("INSERT INTO gated_effect(effect_id,kind,payload_ref,created_ts) "
              "VALUES('L1','send','x',1)")
    c.execute("PRAGMA user_version=0")
    c.commit()
    c.close()
    chrono.ChronoDB(p).close()
    assert _uv(p) == chrono.CHRONO_SCHEMA_TARGET
    c = sqlite3.connect(p)
    row = c.execute("SELECT status FROM gated_effect WHERE effect_id='L1'").fetchone()
    c.close()
    assert row is not None, "legacy data must survive migration"
    # C2: a legacy pending row has no per-effect binding -> quarantined, never auto-authorizable
    assert row[0] == 'NEEDS_OWNER_REVIEW', f"legacy unbound pending must be quarantined, got {row[0]}"


def t_c_already_v1_is_noop():
    p = _tmp()
    chrono.ChronoDB(p).close()
    assert _uv(p) == chrono.CHRONO_SCHEMA_TARGET
    chrono.ChronoDB(p).close()   # second open
    assert _uv(p) == chrono.CHRONO_SCHEMA_TARGET


def t_d_malformed_gated_effect_fail_closed():
    p = _tmp()
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE gated_effect (effect_id TEXT PRIMARY KEY, wrong_col TEXT)")
    c.execute("PRAGMA user_version=0")
    c.commit()
    c.close()
    try:
        chrono.ChronoDB(p)
        assert False, "expected ChronoSchemaError on malformed schema"
    except chrono.ChronoSchemaError:
        pass


def t_e_higher_unknown_version_fail_closed():
    p = _tmp()
    c = sqlite3.connect(p)
    c.execute("PRAGMA user_version=99")
    c.commit()
    c.close()
    try:
        chrono.ChronoDB(p)
        assert False, "expected ChronoSchemaError (no auto-downgrade)"
    except chrono.ChronoSchemaError:
        pass


def t_f_version_never_decreases():
    p = _tmp()
    chrono.ChronoDB(p).close()
    v1 = _uv(p)
    chrono.ChronoDB(p).close()
    v2 = _uv(p)
    assert v1 == chrono.CHRONO_SCHEMA_TARGET and v2 >= v1


def t_g_v2_binding_columns_exist():
    """C2: the per-effect authorization-binding columns are present after migration."""
    p = _tmp()
    chrono.ChronoDB(p).close()
    c = sqlite3.connect(p)
    cols = {r[1] for r in c.execute("PRAGMA table_info(gated_effect)")}
    c.close()
    for col in ("content_hash", "action_kind", "target_ref", "idempotency_key",
                "proposal_id", "mission_id", "approval_id", "approved_by",
                "approved_at", "expires_at"):
        assert col in cols, f"v2 binding column {col} missing after migration"


if __name__ == "__main__":
    _checks = [t_a_fresh_db_migrates_to_v1, t_b_legacy_unversioned_v1_preserved,
               t_c_already_v1_is_noop, t_d_malformed_gated_effect_fail_closed,
               t_e_higher_unknown_version_fail_closed, t_f_version_never_decreases,
               t_g_v2_binding_columns_exist]
    failed = 0
    for fn in _checks:
        try:
            fn()
            print(f"  ✅ {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  💥 {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n=== {len(_checks) - failed}/{len(_checks)} C1 schema-migration checks ===")
    sys.exit(1 if failed else 0)
