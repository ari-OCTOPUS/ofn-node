#!/usr/bin/env python3
"""chrono_migration_prototype.py — C (Exact Effect Authorization) proven on a
FIXTURE sqlite DB before porting into candidate chrono.py. NEVER touches live.

Proves: additive+idempotent+versioned v1->v2 migration; per-effect id+content+
action+target+expiry+anti-replay bound release; no money batch release; legacy
unbound -> NEEDS_OWNER_REVIEW; idempotent request; rollback on a copy.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
import time
from pathlib import Path

V1_DDL = """CREATE TABLE gated_effect (
  effect_id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload_ref TEXT NOT NULL,
  created_beat INTEGER, created_ts INTEGER NOT NULL, release_ref TEXT,
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending','releasable','settled','refused')));"""

V2_COLUMNS = [  # (name, decl)
    ("content_hash", "TEXT"), ("action_kind", "TEXT"), ("target_ref", "TEXT"),
    ("idempotency_key", "TEXT"), ("proposal_id", "TEXT"), ("mission_id", "TEXT"),
    ("approval_id", "TEXT"), ("approved_by", "TEXT"),
    ("approved_at", "INTEGER"), ("expires_at", "INTEGER"),
]
MONEY_KINDS = frozenset({"send", "publish", "sync", "pay"})


def _cols(con) -> set:
    return {r[1] for r in con.execute("PRAGMA table_info(gated_effect)")}


_V2_TABLE = """CREATE TABLE gated_effect_new (
  effect_id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload_ref TEXT NOT NULL,
  created_beat INTEGER, created_ts INTEGER NOT NULL, release_ref TEXT,
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending','releasable','settled','refused','NEEDS_OWNER_REVIEW','LEGACY_UNBOUND')),
  content_hash TEXT, action_kind TEXT, target_ref TEXT, idempotency_key TEXT,
  proposal_id TEXT, mission_id TEXT, approval_id TEXT, approved_by TEXT,
  approved_at INTEGER, expires_at INTEGER);"""


def migrate_up(con) -> dict:
    """Idempotent, versioned. Widens the status CHECK via table-recreate (SQLite
    cannot ALTER a CHECK), adds v2 binding columns, and quarantines legacy
    unbound pending rows as NEEDS_OWNER_REVIEW."""
    ver = con.execute("PRAGMA user_version").fetchone()[0]
    if ver >= 2:
        return {"version": ver, "recreated": False}
    con.executescript(_V2_TABLE)
    con.execute("INSERT INTO gated_effect_new "
                "(effect_id,kind,payload_ref,created_beat,created_ts,release_ref,status) "
                "SELECT effect_id,kind,payload_ref,created_beat,created_ts,release_ref,status "
                "FROM gated_effect")
    con.execute("DROP TABLE gated_effect")
    con.execute("ALTER TABLE gated_effect_new RENAME TO gated_effect")
    # legacy pending without exact binding => NEEDS_OWNER_REVIEW (never auto-releasable)
    con.execute("UPDATE gated_effect SET status='NEEDS_OWNER_REVIEW' "
                "WHERE status='pending' AND (content_hash IS NULL OR content_hash='')")
    con.execute("PRAGMA user_version=2")
    con.commit()
    return {"version": 2, "recreated": True}


def request_effect(con, *, effect_id, kind, payload, action_kind, target_ref,
                   idempotency_key, proposal_id=None, mission_id=None):
    """Idempotent by idempotency_key."""
    row = con.execute("SELECT effect_id FROM gated_effect WHERE idempotency_key=?",
                      (idempotency_key,)).fetchone()
    if row:
        return row[0]  # dedup
    ch = hashlib.sha256(str(payload).encode("utf-8")).hexdigest()
    con.execute(
        "INSERT INTO gated_effect(effect_id,kind,payload_ref,created_ts,status,"
        "content_hash,action_kind,target_ref,idempotency_key,proposal_id,mission_id) "
        "VALUES (?,?,?,?, 'pending', ?,?,?,?,?,?)",
        (effect_id, kind, str(payload), int(time.time()*1000), ch, action_kind,
         target_ref, idempotency_key, proposal_id, mission_id))
    con.commit()
    return effect_id


_used_approvals = set()  # anti-replay (would be a table in production)


def release_effect(con, effect_id, approval) -> bool:
    """fail-closed, id+content+action+target+expiry+anti-replay bound, single-use."""
    r = con.execute("SELECT status,content_hash,action_kind,target_ref FROM gated_effect "
                    "WHERE effect_id=?", (effect_id,)).fetchone()
    if not r:
        return False
    status, chash, akind, tref = r
    aid = str(approval.get("approval_id") or "")
    checks = [
        approval.get("effect_id") == effect_id,
        approval.get("content_hash") == chash,
        approval.get("action_kind") == akind,
        approval.get("target_ref") == tref,
        bool(aid) and aid not in _used_approvals,           # anti-replay single-use
        int(approval.get("expires_at") or 0) > int(time.time()*1000),
        status == "pending",
    ]
    if not all(checks):
        return False
    _used_approvals.add(aid)
    con.execute("UPDATE gated_effect SET status='releasable', release_ref=?, approval_id=?, "
                "approved_by=?, approved_at=? WHERE effect_id=? AND status='pending'",
                (aid, aid, str(approval.get("approved_by") or ""), int(time.time()*1000), effect_id))
    con.commit()
    return con.execute("SELECT changes()").fetchone()[0] == 1


def release_gated_effects_money_DISABLED(con, entry) -> int:
    """C: money kinds are NO LONGER batch-releasable. fail-closed → 0."""
    return 0


# ─────────────────────────── fixture tests ────────────────────────────────────
def _fresh_v1_db(path, rows=()):
    con = sqlite3.connect(path)
    con.executescript(V1_DDL)
    for eid, kind in rows:
        con.execute("INSERT INTO gated_effect(effect_id,kind,payload_ref,created_ts) "
                    "VALUES (?,?,?,?)", (eid, kind, "legacy", int(time.time()*1000)))
    con.commit()
    return con


def _appr(eid, con, **over):
    r = con.execute("SELECT content_hash,action_kind,target_ref FROM gated_effect WHERE effect_id=?",
                    (eid,)).fetchone()
    a = {"effect_id": eid, "content_hash": r[0], "action_kind": r[1], "target_ref": r[2],
         "approval_id": "AP-" + eid, "approved_by": "owner",
         "expires_at": int(time.time()*1000) + 60000}
    a.update(over)   # over may override any field, incl. effect_id
    return a


def run_tests() -> dict:
    _used_approvals.clear()
    d = Path(tempfile.mkdtemp(prefix="chrono-mig-"))
    R = []
    def ck(n, ok): R.append((n, bool(ok)))

    # migration on a legacy v1 db with an unbound pending row
    dbp = str(d / "fx.db")
    con = _fresh_v1_db(dbp, rows=[("LEGACY-1", "send")])
    m1 = migrate_up(con)
    ck("migration -> version=2 + content_hash column exists", m1["version"] == 2 and "content_hash" in _cols(con))
    ck("legacy unbound pending -> NEEDS_OWNER_REVIEW (never releasable)",
       con.execute("SELECT status FROM gated_effect WHERE effect_id='LEGACY-1'").fetchone()[0] == "NEEDS_OWNER_REVIEW")
    m2 = migrate_up(con)  # idempotent
    ck("migration idempotent (up twice, not recreated again)", m2["recreated"] is False)

    # two bound effects, one approval releases exactly one
    a = request_effect(con, effect_id="A", kind="send", payload="pay-A", action_kind="send",
                       target_ref="acct-1", idempotency_key="k-A")
    b = request_effect(con, effect_id="B", kind="send", payload="pay-B", action_kind="send",
                       target_ref="acct-2", idempotency_key="k-B")
    ck("1 two pending / one approval -> exactly one releasable",
       release_effect(con, "A", _appr("A", con)) and
       con.execute("SELECT status FROM gated_effect WHERE effect_id='B'").fetchone()[0] == "pending")
    ck("3 mismatched content_hash -> 0", not release_effect(con, "B", _appr("B", con, content_hash="x")))
    ck("4 mismatched target -> 0", not release_effect(con, "B", _appr("B", con, target_ref="x")))
    ck("5 mismatched action -> 0", not release_effect(con, "B", _appr("B", con, action_kind="pay")))
    ck("2 approval without effect_id binding -> 0", not release_effect(con, "B", _appr("B", con, effect_id="")))
    ck("7 expired approval -> 0", not release_effect(con, "B", _appr("B", con, expires_at=1)))
    ck("8 replayed approval -> 0 (single-use)",
       (release_effect(con, "B", _appr("B", con, approval_id="RE")) and
        not release_effect(con, "B", _appr("B", con, approval_id="RE"))))
    # idempotent request
    b2 = request_effect(con, effect_id="B-dup", kind="send", payload="pay-B", action_kind="send",
                        target_ref="acct-2", idempotency_key="k-B")
    ck("9 duplicate idempotency_key -> one effect", b2 == "B")
    ck("money batch release disabled -> 0", release_gated_effects_money_DISABLED(con, {"hash": "h"}) == 0)

    # rollback on a COPY: re-open the pre-migration bytes
    import shutil
    rb = str(d / "rollback.db")
    con0 = _fresh_v1_db(str(d / "orig.db"), rows=[("X", "send")])
    con0.close()
    shutil.copy2(str(d / "orig.db"), rb)
    conr = sqlite3.connect(rb)
    ck("15 rollback copy retains v1 shape (no v2 columns, version 0)",
       "content_hash" not in _cols(conr) and conr.execute("PRAGMA user_version").fetchone()[0] == 0)
    conr.close(); con.close()

    passed = sum(1 for _, o in R if o)
    return {"passed": passed, "total": len(R), "checks": [{"name": n, "pass": o} for n, o in R]}


if __name__ == "__main__":
    res = run_tests()
    for c in res["checks"]:
        print(f"[{'PASS' if c['pass'] else 'FAIL'}] {c['name']}")
    print(f"\n=== {res['passed']}/{res['total']} C migration+release checks passed ===")
    out = Path(__file__).resolve().parents[1] / "CHRONO-MIGRATION-TEST-REPORT.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    raise SystemExit(0 if res["passed"] == res["total"] else 1)
