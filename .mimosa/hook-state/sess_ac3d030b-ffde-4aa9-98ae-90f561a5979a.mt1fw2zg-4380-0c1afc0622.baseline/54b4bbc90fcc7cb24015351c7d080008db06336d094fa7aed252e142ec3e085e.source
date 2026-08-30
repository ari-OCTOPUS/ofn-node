#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_final_patch.py — hardening from the correctness-schema adversarial lens:
wrap the index DDL in try/except sqlite3.OperationalError (fail-soft, like the FTS DDL).
If another process holds a long write txn during first open, the indexes simply don't
build that open (queries stay correct, just slow) and the next open retries. Also fixes
the contrived table-name-collision case. Re-verifies correctness + mechanism + the two
lens scenarios on the final patched module.
"""
from __future__ import annotations

import difflib
import io
import sqlite3
import sys
import types
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import experiment_v3 as ex  # noqa: E402

_OLD = (
    '            self._conn.execute(\n'
    '                "CREATE INDEX IF NOT EXISTS idx_memory_ns_mkey "\n'
    '                "ON memory(namespace, mkey, created_at DESC)")\n'
    '            self._conn.execute(\n'
    '                "CREATE INDEX IF NOT EXISTS idx_memory_ns_sha "\n'
    '                "ON memory(namespace, content_sha256)")\n'
)
_NEW = (
    '            try:\n'
    '                self._conn.execute(\n'
    '                    "CREATE INDEX IF NOT EXISTS idx_memory_ns_mkey "\n'
    '                    "ON memory(namespace, mkey, created_at DESC)")\n'
    '                self._conn.execute(\n'
    '                    "CREATE INDEX IF NOT EXISTS idx_memory_ns_sha "\n'
    '                    "ON memory(namespace, content_sha256)")\n'
    '            except sqlite3.OperationalError:\n'
    '                pass   # fail-soft (busy writer / name collision): slow-but-correct;\n'
    '                       # next open retries — same posture as the FTS DDL below.\n'
)
assert ex.PATCHED_SRC.count(_OLD) == 1
FINAL_SRC = ex.PATCHED_SRC.replace(_OLD, _NEW)
(HERE / "memory_store_v3_final.py").write_text(FINAL_SRC, "utf-8", newline="\n")
diff = "".join(difflib.unified_diff(
    ex.SRC.splitlines(keepends=True), FINAL_SRC.splitlines(keepends=True),
    fromfile="a/_ops/memory/memory_store.py", tofile="b/_ops/memory/memory_store.py"))
(HERE / "proposed_v3_final.patch").write_text(diff, "utf-8", newline="\n")
add = sum(1 for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
rem = sum(1 for l in diff.splitlines() if l.startswith("-") and not l.startswith("---"))
print(f"final patch: +{add}/-{rem} lines")

FINAL = types.ModuleType("ms_v3_final")
FINAL.__dict__["__file__"] = str(HERE / "memory_store_v3_final.py")
exec(compile(FINAL_SRC, "memory_store_v3_final.py", "exec"), FINAL.__dict__)
ex.PATCHED = FINAL   # re-point the battery at the final module

# 1) full correctness battery on a fresh seed
c = ex.correctness(n=2500, seed=424243)
print(f"correctness(final): checks={c['checks']} mismatches={c['mismatches']} "
      f"leaks={c['admission_leaks']} replay={c['replay_ops_equal']} metrics={c['metrics_equal']}")

# 2) mechanism unchanged
m = ex.mechanism()
ok_get = "SEARCH" in m["get"] and "idx_memory_ns_mkey" in m["get"]
ok_dd = "idx_memory_ns_sha" in m["dedupe"]
print(f"mechanism(final): get uses index={ok_get}  dedupe uses index={ok_dd}")

# 3) lens scenario A: table named like the index -> must open fail-soft now
p = ex.fresh("collide")
con = sqlite3.connect(str(p)); con.execute("CREATE TABLE idx_memory_ns_mkey(x)"); con.commit(); con.close()
try:
    st = FINAL.MemoryStore(path=p)
    st.insert({"namespace": "semantic", "mkey": "c1", "content": "collision probe",
               "trust": "GRADED", "privacy": "scrubbed"})
    r = st.get("semantic", "c1")
    st.close()
    print(f"name-collision open: OK (fail-soft), get works={r is not None}")
except Exception as e:  # noqa: BLE001
    print(f"name-collision open: STILL RAISES ({type(e).__name__}) ❌")

# 4) lens scenario B: busy writer during first open -> fail-soft, correct, retry next open
p2 = ex.fresh("busy")
base = ex.BASE.MemoryStore(path=p2)
ex.seed_corpus(base, 300, 8)
base.close()
w = sqlite3.connect(str(p2), timeout=1)
w.execute("BEGIN IMMEDIATE"); w.execute("INSERT INTO memory(memory_id,namespace,content,content_sha256,"
    "trust,valid_from,privacy,admission_state,schema_version,created_at) VALUES('busyrow','semantic','x','h',"
    "'GRADED','2026','scrubbed','ADMITTED',2,'2026')")
try:
    st = FINAL.MemoryStore(path=p2)          # writer holds txn -> DDL fails soft
    got = st.get("semantic", "k-8-1")
    idx1 = [r[0] for r in st._conn.execute(
        "SELECT name FROM sqlite_master WHERE name LIKE 'idx_memory%'").fetchall()]
    st.close()
    w.rollback(); w.close()
    st2 = FINAL.MemoryStore(path=p2)         # retry after writer gone
    idx2 = [r[0] for r in st2._conn.execute(
        "SELECT name FROM sqlite_master WHERE name LIKE 'idx_memory%'").fetchall()]
    st2.close()
    print(f"busy-writer open: fail-soft OK, get-during={got is not None}, "
          f"indexes during={idx1}, after retry={sorted(idx2)}")
except Exception as e:  # noqa: BLE001
    try:
        w.rollback(); w.close()
    except Exception:
        pass
    print(f"busy-writer open: STILL RAISES ({type(e).__name__}) ❌")
