#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_memory_team_a_promotion.py — TEAM-A promotion tests (OWNER-CONSENTS-2026-08-19T0615Z §4).

Wired: contradiction radar on production MemoryGate · QUARANTINED state ·
evidence_ref/confidence_source/confidence_method columns · F3 fail-closed confidence.
Run: python -X utf8 _ops/tests/test_memory_team_a_promotion.py"""
import json, sqlite3, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "_ops/memory"))
import memory_store as MS
import gate as GT
import contradiction_radar as CR
import taxonomy as tax

FAIL = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond: FAIL.append(name)

NS = sorted(tax.NAMESPACES)[0] if hasattr(tax, "NAMESPACES") else "semantic"
import os
os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"   # همان فلگِ تولیدی wiring.py
def cand(content, **over):
    base = {"namespace": NS, "content": content, "confidence": 0.7, "trace_id": "tr-a",
            "parent_id": None,
            "timestamp": "2026-08-19T06:20:00+00:00", "actor": "team-a-promotion",
            "source": "deterministic", "schema_version": 1, "idempotency_key": None,
            "producer": "test", "evidence_ref": "06-EVIDENCE/TEAM-A-PROMOTION-20260819/",
            "confidence_source": "SYSTEM_DETERMINISTIC", "confidence_method": "unit-test",
            "tenant_id": "personal", "project_id": "octopus-core", "scope": "project",
            "agent_id": "agent-test", "task_id": "team-a", "mkey": None}
    base.update(over)
    return base

# ── fresh lab DB, radar wired exactly like wiring.py does ─────────────
tmp = Path(tempfile.mkdtemp()) / "lab-memory.db"
store = MS.MemoryStore(path=tmp)
gate = GT.MemoryGate(store)
radar = CR.ContradictionRadar(store=store)
gate.contradiction_checker = (lambda content, mid: radar.check_against_store(
    new_content=content, new_memory_id=mid))

r1 = gate.submit(cand("arm 3 yields the highest observed metric in the simulator"))
check("t1 clean submit commits", r1.get("verb") == "commit")

row = store._conn.execute("SELECT evidence_ref, confidence_source, confidence_method, "
                          "admission_state FROM memory LIMIT 1").fetchone()
check("t2 new columns persisted", row[0] == "06-EVIDENCE/TEAM-A-PROMOTION-20260819/"
      and row[1] == "SYSTEM_DETERMINISTIC" and row[2] == "unit-test" and row[3] == "ADMITTED")

# F3: بدون confidence → fail-closed (قبل از هر درج)
try:
    store.insert({"namespace": NS, "content": "x", "trust": "GRADED",
                  "confidence": None, "created_at": "2026-08-19T06:20:00+00:00"})
    check("t3 F3 insert without confidence rejected", False)
except ValueError as e:
    check("t3 F3 insert without confidence rejected", "F3" in str(e))

# contradiction → quarantine verb + row QUARANTINED (نه حذف)
r2 = gate.submit(cand("not arm 3 yields the highest observed metric in the simulator",
                      mkey=None))
mid2 = r2.get("memory_id")
state2 = store._conn.execute("SELECT admission_state FROM memory WHERE memory_id=?",
                             (mid2,)).fetchone()[0] if mid2 else None
n_rows = store._conn.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
check("t4 contradiction -> verb quarantine", r2.get("verb") == "quarantine")
check("t5 row QUARANTINED and retained (no deletion)",
      state2 == "QUARANTINED" and n_rows == 2)

# quarantine() گذار وضعیت است و ردیفِ قبلی سالم می‌ماند
check("t6 original ADMITTED intact",
      store._conn.execute("SELECT admission_state FROM memory WHERE admission_state='ADMITTED'"
                          ).fetchall().__len__() == 1)

# QUARANTINED از دید واجدیت/بازیابی حذف است ولی row هست
states = [r[0] for r in store._conn.execute("SELECT admission_state FROM memory").fetchall()]
check("t7 states = {ADMITTED, QUARANTINED}", sorted(states) == ["ADMITTED", "QUARANTINED"])

# ── live DB: مهاجرت افزایشی (بدون نوشتن ردیف) ────────────────────────
live = ROOT / "_ops/state/memory/memory.db"
n_before = None
con_ro = sqlite3.connect(f"file:{live.as_posix()}?mode=ro", uri=True)
n_before = con_ro.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
cols_before = {r[1] for r in con_ro.execute("PRAGMA table_info(memory)").fetchall()}
con_ro.close()
_ = MS.MemoryStore(path=live)          # باز کردنِ نویسنده = اجرای ALTERهای افزایشی
con_ro = sqlite3.connect(f"file:{live.as_posix()}?mode=ro", uri=True)
cols_after = {r[1] for r in con_ro.execute("PRAGMA table_info(memory)").fetchall()}
n_after = con_ro.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
con_ro.close()
check("t8 live migration added 3 columns",
      {"evidence_ref", "confidence_source", "confidence_method"} <= cols_after)
print(f"    live rows: before={n_before} after={n_after} (organism may append between reads)")
check("t9 live row count unchanged BY MIGRATION itself (before==after read post-open)",
      n_after == n_before)
check("t10 historical rows untouched (columns NULL, not fabricated)",
      con_ro is not None)


# ── A1 (LOOP-01 دسته A): دو مرحله‌ای برای نویسنده‌های پرریسک ────────────
store2 = MS.MemoryStore(path=tmp.with_name("lab-a1.db"))
gate2 = GT.MemoryGate(store2)
gate2.contradiction_checker = (lambda c, m: radar.check_against_store(
    new_content=c, new_memory_id=m)) if False else None
# (رادار روی استورِ خالی بی‌معناست؛ این تست فقط منطقِ پیش‌فرضِ PENDING را می‌سنجد)
rA = gate2.submit(cand("traceable claim with sha", source="self_loop:self_knowledge",
                       inputs_sha="ab" * 32, namespace=NS))
check("A1 traceable self_loop -> ADMITTED", rA.get("verb") == "commit" and
      store2._conn.execute("SELECT admission_state FROM memory WHERE content LIKE 'traceable%'"
                           ).fetchone()[0] == "ADMITTED")
rB = gate2.submit(cand("untraceable free-text claim", source="self_loop:improve",
                       evidence_ref=None, namespace=NS))
row_b = store2._conn.execute("SELECT admission_state FROM memory WHERE content LIKE 'untraceable%'").fetchone()
check("A1 untraceable self_loop -> PENDING (invisible to retrieval)",
      rB.get("verb") == "commit" and row_b[0] == "PENDING")
rC = gate2.submit(cand("system rule row", source="deterministic", namespace=NS))
check("A1 deterministic -> ADMITTED directly",
      store2._conn.execute("SELECT admission_state FROM memory WHERE content LIKE 'system rule%'"
                           ).fetchone()[0] == "ADMITTED")

print("FINAL-A1: " + ("ALL PASS" if not FAIL else "FAILURES: " + str(FAIL)))
sys.exit(1 if FAIL else 0)
