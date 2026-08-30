"""
PHASE 0 GATE TEST — Brushline
DoD (ROADMAP فاز ۰): scaffold complete + DB separate from LANGAR + no hard dependency

Tests:
  T1 — DB path separate from LANGAR                  (Phase 0 invariant)
  T2 — All required tables exist after init_db()     (schema)
  T3 — brushline_meta identifies this as Brushline   (identity)
  T4 — Can JOIN with mock LANGAR DB (compatible but not coupled)
  T5 — No 'import langar' in any Brushline src file  (no hard dependency)
  T6 — Audit chain appends + verifies correctly      (KB-06)
  T7 — Audit chain detects tampering                 (KB-06)
  T8 — Spend cap blocks action above per-action cap  (INV-3)
  T9 — Spend cap blocks when daily cap would exceed  (INV-3)
  T10 — Kill switch blocks all actions when active   (INV-3)
  T11 — Kill switch can be toggled and unblocks      (INV-3)
  T12 — PII auto-sanitised from audit payload        (INV-2)

Run: python -m pytest tests/test_phase0_gate.py -v
  or: python tests/test_phase0_gate.py
"""
import os
import sqlite3
import tempfile
import sys
from pathlib import Path

# ── Bootstrap: temp DB + governance paths ────────────────────────────────────
_tmp = tempfile.mkdtemp(prefix="brushline_test_")
os.environ["BRUSHLINE_DB_PATH"] = str(Path(_tmp) / "brushline_test.db")
os.environ["KILL_SWITCH_FILE"] = str(Path(_tmp) / "KILL_SWITCH")
os.environ["SPEND_CAP_PER_ACTION_AUD"] = "5.00"
os.environ["SPEND_CAP_PER_DAY_AUD"] = "20.00"
os.environ["ANTHROPIC_API_KEY"] = "test-key-not-used-in-phase-0"

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Helpers ──────────────────────────────────────────────────────────────────

def _pass(msg: str):
    print(f"  ✅ {msg}")

def _fail(msg: str):
    print(f"  ❌ {msg}")
    raise AssertionError(msg)


# ── Tests ────────────────────────────────────────────────────────────────────

def test_t1_db_separate_from_langar():
    """T1: Brushline DB path must differ from LANGAR's."""
    from src.config import config

    hypothetical_langar_paths = [
        "langar/data/langar.db",
        "/srv/langar/data/langar.db",
        "data/langar.db",
    ]
    for langar_path in hypothetical_langar_paths:
        if config.DB_PATH == langar_path:
            _fail(f"DB path collision with LANGAR: {config.DB_PATH}")

    _pass(f"DB separation confirmed: Brushline={config.DB_PATH}")


def test_t2_schema_initialises():
    """T2: All required tables exist after init_db()."""
    from src.database import init_db, get_connection
    init_db()

    conn = get_connection()
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    conn.close()

    required = {
        "leads", "consent_records", "drafts", "gate_results",
        "approval_actions", "audit_entries", "sync_jobs",
        "cost_events", "brushline_meta"
    }
    missing = required - tables
    if missing:
        _fail(f"Missing tables: {sorted(missing)}")
    _pass(f"All {len(required)} required tables present")


def test_t3_meta_identity():
    """T3: brushline_meta identifies this DB as Brushline's."""
    from src.database import get_connection
    conn = get_connection()
    row = conn.execute(
        "SELECT value FROM brushline_meta WHERE key='system'"
    ).fetchone()
    conn.close()

    if not row or row["value"] != "brushline":
        _fail("brushline_meta does not identify system as 'brushline'")
    _pass("brushline_meta identity verified")


def test_t4_join_with_mock_langar():
    """
    T4: Brushline CAN cross-reference LANGAR data via shared IDs,
    but does NOT require LANGAR (no hard foreign key, no shared DB file).
    """
    from src.database import get_connection, init_db

    init_db()
    shared_id = "shared-entity-001"

    # Insert into Brushline
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO leads VALUES "
        "(?, 'Test', '0412000000', NULL, 'Newtown', 'interior', 'gbp', 'express', '', '2026-06-30T00:00:00')",
        (shared_id,)
    )
    conn.commit()
    conn.close()

    # Create a mock LANGAR DB (totally separate, no shared file)
    langar_conn = sqlite3.connect(":memory:")
    langar_conn.executescript("""
        CREATE TABLE langar_entities (id TEXT PRIMARY KEY, name TEXT);
        INSERT INTO langar_entities VALUES ('shared-entity-001', 'LANGAR User');
    """)

    # Cross-reference via Python (simulates application-level JOIN)
    bl_conn = get_connection()
    bl_ids = {r[0] for r in bl_conn.execute("SELECT id FROM leads").fetchall()}
    lg_ids = {r[0] for r in langar_conn.execute("SELECT id FROM langar_entities").fetchall()}
    bl_conn.close()
    langar_conn.close()

    shared = bl_ids & lg_ids
    if shared_id not in shared:
        _fail("Application-level JOIN failed — shared ID not found in both systems")
    _pass(f"Cross-system JOIN works: {len(shared)} shared entities (no DB coupling)")


def test_t5_no_langar_import():
    """T5: No Brushline source file imports from LANGAR."""
    src_dir = Path(__file__).parent.parent / "src"
    violations = []
    import re
    # Match actual import statements, not comments or string mentions
    import_pattern = re.compile(r"^\s*(import langar|from langar)", re.MULTILINE | re.IGNORECASE)
    for py_file in src_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        if import_pattern.search(content):
            violations.append(py_file.name)

    if violations:
        _fail(f"LANGAR imports found in: {violations}")
    _pass("No LANGAR imports: Brushline is fully standalone")


def test_t6_audit_chain_basic():
    """T6: Hash chain appends entries and verifies correctly."""
    from src.database import init_db
    from src import audit

    init_db()

    id1 = audit.append("GATE_CHECK", "draft-001", {"status": "pass", "round": 1})
    id2 = audit.append("APPROVAL_DECISION", "draft-001", {"decision": "approved"})
    id3 = audit.append("SYNC", "lead-001", {"target": "servicem8"})

    is_valid, msg = audit.verify_chain()
    if not is_valid:
        _fail(f"Chain verification failed: {msg}")
    _pass(f"Audit chain verified: {msg}")


def test_t7_tamper_detection():
    """T7: Chain detects payload tampering."""
    from src.database import init_db, get_connection
    from src import audit

    init_db()
    entry_id = audit.append("GATE_CHECK", "draft-tamper", {"status": "pass"})

    # Tamper with the payload
    conn = get_connection()
    conn.execute(
        "UPDATE audit_entries SET payload = '{\"tampered\": true}' WHERE id = ?",
        (entry_id,)
    )
    conn.commit()
    conn.close()

    is_valid, msg = audit.verify_chain()
    if is_valid:
        _fail("Tamper detection failed — chain should be broken but reported as valid")
    _pass(f"Tamper detected correctly: {msg[:80]}")


def test_t8_spend_cap_per_action():
    """T8: Per-action spend cap rejects actions above threshold."""
    from src.database import init_db
    from src.governance import check_and_enforce, SpendCapExceeded

    init_db()

    # Small action: allowed
    check_and_enforce(0.10, "agent_C")
    _pass("AUD $0.10 action approved (below $5.00 cap)")

    # Large action: blocked
    try:
        check_and_enforce(100.0, "agent_C")
        _fail("Should have raised SpendCapExceeded for AUD $100")
    except SpendCapExceeded as e:
        _pass(f"AUD $100 action blocked by per-action cap: {str(e)[:60]}")


def test_t9_spend_cap_daily():
    """T9: Daily spend cap blocks when cumulative total would exceed it."""
    from src.database import init_db
    from src.governance import log_cost, check_and_enforce, SpendCapExceeded

    init_db()

    # Log enough cost to fill the daily cap (AUD $20)
    log_cost("llm_call", "agent_C", "claude-haiku", cost_usd=13.00, tokens_in=1000)
    # AUD $13 × 1.45 = $18.85 → remaining ~$1.15

    try:
        check_and_enforce(2.0, "agent_C")  # $2 would push over $20
        _fail("Should have raised SpendCapExceeded for daily cap")
    except SpendCapExceeded as e:
        _pass(f"Daily cap enforced: {str(e)[:80]}")


def test_t10_kill_switch_blocks():
    """T10: Kill switch blocks ALL actions when active."""
    from src.database import init_db
    from src.governance import (
        activate_kill_switch, check_and_enforce, KillSwitchActivated,
        is_kill_switch_active
    )

    init_db()

    # Ensure clean state
    ks_file = Path(os.environ["KILL_SWITCH_FILE"])
    if ks_file.exists():
        ks_file.unlink()

    # Normal: allowed
    check_and_enforce(0.001, "agent_A")
    _pass("Pre-kill: action allowed")

    # Activate
    activate_kill_switch(99999, "Phase 0 gate test")
    assert is_kill_switch_active(), "Kill switch should be active"

    # Should block
    try:
        check_and_enforce(0.001, "agent_A")
        _fail("Kill switch active but action was not blocked")
    except KillSwitchActivated as e:
        _pass(f"Kill switch blocks action: {str(e)[:60]}")


def test_t11_kill_switch_toggle():
    """T11: Kill switch can be deactivated and system resumes."""
    from src.database import init_db
    from src.governance import (
        deactivate_kill_switch, check_and_enforce, is_kill_switch_active
    )

    init_db()

    # Kill switch may still be active from T10 — deactivate it
    deactivate_kill_switch(99999)
    assert not is_kill_switch_active(), "Kill switch should be inactive"

    # Should work again
    check_and_enforce(0.001, "agent_A")
    _pass("Kill switch deactivated — actions resume normally")


def test_t12_pii_sanitised_in_audit():
    """T12: phone/email never appears in raw form in audit log (INV-2)."""
    from src.database import init_db, get_connection
    from src import audit

    init_db()

    # Attempt to log PII in audit payload
    audit.append("TEST_PII", "lead-pii-test", {
        "phone": "0412345678",   # PII — should be sanitised
        "email": "test@example.com",  # PII — should be sanitised
        "suburb": "Newtown",     # non-PII — should pass through
    })

    conn = get_connection()
    row = conn.execute(
        "SELECT payload FROM audit_entries WHERE entity_id='lead-pii-test'"
    ).fetchone()
    conn.close()

    import json
    payload = json.loads(row["payload"])

    if "phone" in payload:
        _fail(f"Raw 'phone' found in audit payload: {payload}")
    if "email" in payload:
        _fail(f"Raw 'email' found in audit payload: {payload}")
    if payload.get("suburb") != "Newtown":
        _fail("Non-PII field 'suburb' was incorrectly stripped")

    _pass(f"PII sanitised in audit. Payload keys: {list(payload.keys())}")


# ── Runner ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_t1_db_separate_from_langar,
        test_t2_schema_initialises,
        test_t3_meta_identity,
        test_t4_join_with_mock_langar,
        test_t5_no_langar_import,
        test_t6_audit_chain_basic,
        test_t7_tamper_detection,
        test_t8_spend_cap_per_action,
        test_t9_spend_cap_daily,
        test_t10_kill_switch_blocks,
        test_t11_kill_switch_toggle,
        test_t12_pii_sanitised_in_audit,
    ]

    print("\n" + "=" * 60)
    print("  PHASE 0 GATE TEST — Brushline")
    print("  DoD: scaffold + DB isolation + governance")
    print("=" * 60)

    passed = failed = 0
    for test in tests:
        name = test.__name__.replace("test_", "").upper()
        print(f"\n[{name}] {test.__doc__.strip().splitlines()[0]}")
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1

    print("\n" + "=" * 60)
    if failed == 0:
        status = "GATE PASSED [ALL GREEN]"
    if failed == 0:
        status = 'GATE PASSED [ALL GREEN]'
    else:
        status = 'GATE FAILED [' + str(failed) + ' test(s) failed]'
    print('  ' + status + ' -- ' + str(passed) + '/' + str(len(tests)) + ' passed')
    print('=' * 60)
    import sys as _sys
    _sys.exit(0 if failed == 0 else 1)
