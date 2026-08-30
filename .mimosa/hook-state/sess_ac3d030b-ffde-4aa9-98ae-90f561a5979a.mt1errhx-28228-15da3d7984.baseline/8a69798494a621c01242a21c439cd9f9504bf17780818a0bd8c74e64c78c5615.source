#!/usr/bin/env python3
"""test_c5_cas_execution — C5: CAS execution state machine (no TOCTOU in the money path).

Proves (hermetic, fixture-only, no live DB):
  * migration v4: fresh → user_version 4; idempotent; execution columns exist; the C3
    UNIQUE idempotency index SURVIVES the table rebuild; genuine v3 data preserved.
  * rollback: an induced failure inside the 3→4 step rolls back atomically —
    user_version stays 3, data intact, no half-migrated table; retry then succeeds.
  * future version (5) → ChronoSchemaError (fail-closed, no auto-downgrade).
  * state machine: pending → releasable → EXECUTING → settled; NO direct
    pending→settled, NO pending→EXECUTING; claim requires the LANGAR release_ref.
  * two executors, one winner (atomic claim); duplicate claim → None.
  * wrong/stale execution_id can never finalize; duplicate completion idempotent.
  * halt-before-claim → refused; halt-during-execution → RECONCILE_REQUIRED
    (external effect may have happened — never silently refused), receipt kept.
  * settle() is now a single guarded atomic UPDATE (one winner; second call False).

Run: python -X utf8 test_c5_cas_execution.py
"""
import sqlite3
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
import harness   # noqa: E402
ENV = harness.setup("c5-cas-execution")
import chrono    # noqa: E402
import opslib    # noqa: E402

_FAILED = 0


def check(name, cond):
    global _FAILED
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        _FAILED += 1


def _db(tag):
    return chrono.ChronoDB(path=opslib.STATE_DIR / f"c5-{tag}.db")


def _appr(db, eid, aid):
    r = db.q("SELECT content_hash, action_kind, target_ref FROM gated_effect "
             "WHERE effect_id=?", (eid,))[0]
    return {"effect_id": eid, "approval_id": aid, "content_hash": r[0],
            "action_kind": r[1], "target_ref": r[2], "expires_at": None,
            "release_ref": "ref-" + str(aid)}


def _released_pay(gate, db, tag):
    """یک effectِ پول را از مسیرِ رسمیِ C4 (release_effect دقیق) به releasable می‌رساند."""
    e = gate.request("pay", f"order-{tag}", target_ref=f"acct-{tag}")
    assert gate.release_effect(e, _appr(db, e, f"A-{tag}")) is True
    return e


def _uv(path):
    c = sqlite3.connect(path)
    v = c.execute("PRAGMA user_version").fetchone()[0]
    c.close()
    return v


def _tmp():
    return str(Path(tempfile.mkdtemp(prefix="chrono-c5-")) / "c.db")


# v3 fixture: exact v2 table shape (C2 rebuild) + C3 UNIQUE index + user_version=3
_V3_DDL = """CREATE TABLE gated_effect (
  effect_id    TEXT PRIMARY KEY,
  kind         TEXT NOT NULL,
  payload_ref  TEXT NOT NULL,
  created_beat INTEGER,
  created_ts   INTEGER NOT NULL,
  release_ref  TEXT,
  status       TEXT NOT NULL DEFAULT 'pending'
               CHECK (status IN ('pending','releasable','settled','refused',
                                 'NEEDS_OWNER_REVIEW','LEGACY_UNBOUND')),
  content_hash    TEXT,
  action_kind     TEXT,
  target_ref      TEXT,
  idempotency_key TEXT,
  proposal_id     TEXT,
  mission_id      TEXT,
  approval_id     TEXT,
  approved_by     TEXT,
  approved_at     INTEGER,
  expires_at      INTEGER
);
CREATE UNIQUE INDEX ux_gated_effect_idem ON gated_effect(idempotency_key);
PRAGMA user_version=3;"""


# ── 1) migration v4: fresh, idempotent, columns, index survives rebuild ─────────
p1 = _tmp()
chrono.ChronoDB(p1).close()
check("fresh DB migrates to v4", _uv(p1) == 4 and chrono.CHRONO_SCHEMA_TARGET == 4)
chrono.ChronoDB(p1).close()
check("second open is a no-op (still v4)", _uv(p1) == 4)
c = sqlite3.connect(p1)
cols = {r[1] for r in c.execute("PRAGMA table_info(gated_effect)")}
need = {"execution_id", "execution_started_at", "execution_finished_at",
        "execution_worker_ref", "external_receipt_ref", "failure_reason"}
check("v4 execution columns all present", need <= cols)
try:
    c.execute("INSERT INTO gated_effect(effect_id,kind,payload_ref,created_ts,"
              "idempotency_key) VALUES('X1','send','a',1,'K')")
    c.execute("INSERT INTO gated_effect(effect_id,kind,payload_ref,created_ts,"
              "idempotency_key) VALUES('X2','send','b',2,'K')")
    c.commit()
    _idem_ok = False
except sqlite3.IntegrityError:
    _idem_ok = True
c.close()
check("C3 UNIQUE idempotency index SURVIVES the v4 rebuild", _idem_ok)

# ── 2) genuine v3 DB: data preserved, releasable row still works end-to-end ─────
p2 = _tmp()
c = sqlite3.connect(p2)
c.executescript(_V3_DDL)
c.execute("INSERT INTO gated_effect(effect_id,kind,payload_ref,created_ts,release_ref,"
          "status,content_hash,action_kind,target_ref,approval_id) "
          "VALUES('L-REL','pay','legacy-order',1,'ref-legacy','releasable','ch','pay','acct','AP-L')")
c.execute("INSERT INTO gated_effect(effect_id,kind,payload_ref,created_ts,status) "
          "VALUES('L-SET','send','legacy-done',1,'settled')")
c.commit()
c.close()
db2 = chrono.ChronoDB(p2)
check("v3→v4: user_version now 4", _uv(p2) == 4)
rows = dict((r[0], r[1]) for r in db2.q("SELECT effect_id, status FROM gated_effect"))
check("v3→v4: rows and statuses preserved (additive, zero status rewrites)",
      rows == {"L-REL": "releasable", "L-SET": "settled"})
g2 = chrono.EffectorGate(db2)
xidL = g2.begin_execution("L-REL", worker_ref="w-legacy")
check("legacy releasable row claimable after migration", isinstance(xidL, str))
check("legacy row completes with receipt → settled",
      g2.complete_execution("L-REL", xidL, "RCPT-L") is True
      and g2.status_of("L-REL") == "settled")
db2.close()

# ── 3) induced failure in 3→4 rolls back atomically; retry succeeds ─────────────
p3 = _tmp()
c = sqlite3.connect(p3)
c.executescript(_V3_DDL)
c.execute("INSERT INTO gated_effect(effect_id,kind,payload_ref,created_ts) "
          "VALUES('R1','send','keep-me',1)")
c.commit()
c.close()
_orig = chrono.ChronoDB._migrate_3_to_4


def _boom(self):
    self._con.execute("CREATE TABLE gated_effect_v4 (x TEXT)")   # نیمه‌کاره
    raise RuntimeError("induced 3->4 failure")


chrono.ChronoDB._migrate_3_to_4 = _boom
try:
    try:
        chrono.ChronoDB(p3)
        _raised = False
    except RuntimeError:
        _raised = True
finally:
    chrono.ChronoDB._migrate_3_to_4 = _orig
c = sqlite3.connect(p3)
_v = c.execute("PRAGMA user_version").fetchone()[0]
_row = c.execute("SELECT payload_ref FROM gated_effect WHERE effect_id='R1'").fetchone()
_leftover = c.execute("SELECT name FROM sqlite_master WHERE name='gated_effect_v4'").fetchone()
c.close()
check("failed 3→4 step raises and stays v3 (no half-migration)", _raised and _v == 3)
check("failed step: data intact, no leftover v4 table",
      _row == ("keep-me",) and _leftover is None)
chrono.ChronoDB(p3).close()
check("retry after restored migration → v4", _uv(p3) == 4)

# ── 4) future version fails closed ──────────────────────────────────────────────
p4 = _tmp()
c = sqlite3.connect(p4)
c.execute("PRAGMA user_version=5")
c.commit()
c.close()
try:
    chrono.ChronoDB(p4)
    check("user_version=5 (future) → ChronoSchemaError", False)
except chrono.ChronoSchemaError:
    check("user_version=5 (future) → ChronoSchemaError", True)

# ── 5) happy path: pay → exact release → claim → complete(receipt) → settled ────
db = _db("sm")
gate = chrono.EffectorGate(db)
e = _released_pay(gate, db, "hp")
xid = gate.begin_execution(e, worker_ref="worker-1")
check("claim: releasable → EXECUTING with execution_id",
      isinstance(xid, str) and len(xid) == 32 and gate.status_of(e) == "EXECUTING")
check("complete with external receipt → settled",
      gate.complete_execution(e, xid, "RCPT-1") is True and gate.status_of(e) == "settled")
r = db.q("SELECT external_receipt_ref, execution_worker_ref FROM gated_effect "
         "WHERE effect_id=?", (e,))[0]
check("receipt + worker_ref durably recorded", r == ("RCPT-1", "worker-1"))

# ── 6) two executors, one winner; duplicate claim → None ────────────────────────
e6 = _released_pay(gate, db, "race")
x1 = gate.begin_execution(e6, worker_ref="A")
x2 = gate.begin_execution(e6, worker_ref="B")
check("two executors: exactly one winner", isinstance(x1, str) and x2 is None)
check("loser did not disturb state (still EXECUTING, winner's claim)",
      gate.status_of(e6) == "EXECUTING")

# ── 7) wrong execution_id cannot finalize; right one still can ──────────────────
check("wrong execution_id → False, stays EXECUTING",
      gate.complete_execution(e6, "bogus-xid", "RCPT-X") is False
      and gate.status_of(e6) == "EXECUTING")
check("correct execution_id then completes", gate.complete_execution(e6, x1, "RCPT-6") is True)

# ── 8) duplicate completion idempotent; different receipt refused ───────────────
check("duplicate completion (same xid+receipt) → True, idempotent",
      gate.complete_execution(e6, x1, "RCPT-6") is True and gate.status_of(e6) == "settled")
check("same xid but DIFFERENT receipt → False (no silent receipt rewrite)",
      gate.complete_execution(e6, x1, "RCPT-OTHER") is False)

# ── 9) stale worker can never finalize a FAILED_SAFE row ────────────────────────
e9 = _released_pay(gate, db, "stale")
x9 = gate.begin_execution(e9, worker_ref="C")
check("fail_execution: EXECUTING → FAILED_SAFE",
      gate.fail_execution(e9, x9, "network down") is True
      and gate.status_of(e9) == "FAILED_SAFE")
check("stale worker complete after FAILED_SAFE → False, state unchanged",
      gate.complete_execution(e9, x9, "RCPT-9") is False
      and gate.status_of(e9) == "FAILED_SAFE")
check("second fail_execution → False (terminal)", gate.fail_execution(e9, x9, "again") is False)

# ── 10) no direct pending→settled / pending→EXECUTING ───────────────────────────
e10 = gate.request("pay", "order-pend", target_ref="acct-pend")
check("settle(pending) → False", gate.settle(e10) is False and gate.status_of(e10) == "pending")
check("begin_execution(pending) → None",
      gate.begin_execution(e10) is None and gate.status_of(e10) == "pending")
check("complete_execution(pending) → False",
      gate.complete_execution(e10, "whatever-xid", "R") is False
      and gate.status_of(e10) == "pending")

# ── 11) claim requires the LANGAR release_ref (TINV-7 holds in the new path) ────
e11 = gate.request("pay", "order-noref", target_ref="acct-noref")
db.ex("UPDATE gated_effect SET status='releasable', release_ref='' WHERE effect_id=?", (e11,))
check("releasable WITHOUT release_ref cannot be claimed", gate.begin_execution(e11) is None)

# ── 12) halt-before-claim → refused ─────────────────────────────────────────────
e12 = _released_pay(gate, db, "halt-b")
opslib.STOP_ORGANISM.write_text("test", "utf-8")
try:
    check("STOP before claim → None + refused",
          gate.begin_execution(e12) is None and gate.status_of(e12) == "refused")
finally:
    opslib.STOP_ORGANISM.unlink(missing_ok=True)

# ── 13) halt-during-execution → RECONCILE_REQUIRED (never a fake refuse) ────────
e13 = _released_pay(gate, db, "halt-d")
x13 = gate.begin_execution(e13, worker_ref="D")
opslib.STOP_ORGANISM.write_text("test", "utf-8")
try:
    r13 = gate.complete_execution(e13, x13, "RCPT-13")
    row13 = db.q("SELECT status, failure_reason, external_receipt_ref FROM gated_effect "
                 "WHERE effect_id=?", (e13,))[0]
    check("STOP during execution → False + RECONCILE_REQUIRED",
          r13 is False and row13[0] == "RECONCILE_REQUIRED")
    check("  reconcile row keeps halt reason + the external receipt",
          "halt during execution" in (row13[1] or "") and row13[2] == "RCPT-13")
finally:
    opslib.STOP_ORGANISM.unlink(missing_ok=True)

# ── 14) settle(): atomic single winner (TOCTOU closed behaviorally) ─────────────
e14 = _released_pay(gate, db, "settle")
check("settle first call wins", gate.settle(e14) is True and gate.status_of(e14) == "settled")
check("settle second call → False (single winner, no blind re-update)",
      gate.settle(e14) is False)


if __name__ == "__main__":
    print(f"\n== {_FAILED} failure(s) ==")
    print("OK test_c5_cas_execution" if _FAILED == 0 else "FAIL test_c5_cas_execution")
    sys.exit(1 if _FAILED else 0)
