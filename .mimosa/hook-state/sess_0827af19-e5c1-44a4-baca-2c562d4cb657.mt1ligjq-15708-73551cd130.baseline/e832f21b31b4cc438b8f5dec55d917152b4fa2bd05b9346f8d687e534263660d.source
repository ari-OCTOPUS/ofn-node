#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_patch.py — produce the FINAL minimal patch (comment-preserving, LF line endings)
addressing the patch-fidelity lens caveats, and re-verify byte-identical.

Minimal change: insert a batched IN(...) hydration before the out-loop and swap the single
per-candidate `self._conn.execute(...).fetchone()` for `row_by_id.get(mid)`. Docstring and
the `# FTS5 lenient` / `# رتبهٔ ترکیبی` comments are PRESERVED. Emits proposed_final.patch
(LF) + memory_store_final.py, then runs an original-vs-patched correctness battery.
"""
from __future__ import annotations

import difflib
import io
import sys
import types
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

_HERE = Path(__file__).resolve().parent
_WT = _HERE.parent.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_WT / "_ops" / "memory"))
sys.path.insert(0, str(_WT / "_ops" / "outcomes"))
import bench_common as bc  # noqa: E402
import memory_store as ms  # noqa: E402

SRC = (_WT / "_ops" / "memory" / "memory_store.py").read_text("utf-8").replace("\r\n", "\n")

_OLD = (
    '            out = []\n'
    '            for mid, score in ids:\n'
    '                r = self._conn.execute("SELECT " + ",".join(_COLS) + " FROM memory WHERE memory_id=? "\n'
    '                                       "AND (valid_to IS NULL OR valid_to>?)",\n'
    '                                       (mid, _utc_now_iso())).fetchone()\n'
)
_NEW = (
    '            # batched hydration (C6 evolution_v1): ONE IN(...) query for all candidates\n'
    '            # instead of a per-candidate round-trip (N+1). ranking/tie-break unchanged —\n'
    '            # candidate order is preserved and the validity/namespace/min_trust filters\n'
    '            # below are byte-identical. (for very large k on SQLite<3.32 the IN() list\n'
    '            # would exceed 999 params; k*4 candidates stays well under 32766 here.)\n'
    '            now = _utc_now_iso()\n'
    '            row_by_id = {}\n'
    '            if ids:\n'
    '                mids = [mid for mid, _ in ids]\n'
    '                ph = ",".join("?" * len(mids))\n'
    '                for hr in self._conn.execute(\n'
    '                        "SELECT " + ",".join(_COLS) + " FROM memory WHERE memory_id IN (" + ph + ") "\n'
    '                        "AND (valid_to IS NULL OR valid_to>?)", (*mids, now)).fetchall():\n'
    '                    row_by_id[hr[0]] = hr\n'
    '            out = []\n'
    '            for mid, score in ids:\n'
    '                r = row_by_id.get(mid)\n'
)

assert SRC.count(_OLD) == 1, f"anchor not unique: {SRC.count(_OLD)}"
patched = SRC.replace(_OLD, _NEW)
(_HERE / "memory_store_final.py").write_text(patched, "utf-8", newline="\n")
diff = "".join(difflib.unified_diff(
    SRC.splitlines(keepends=True), patched.splitlines(keepends=True),
    fromfile="a/_ops/memory/memory_store.py", tofile="b/_ops/memory/memory_store.py"))
(_HERE / "proposed_final.patch").write_text(diff, "utf-8", newline="\n")

mod = types.ModuleType("memory_store_final")
mod.__dict__["__file__"] = str(_HERE / "memory_store_final.py")
exec(compile(patched, "memory_store_final.py", "exec"), mod.__dict__)

added = sum(1 for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
removed = sum(1 for l in diff.splitlines() if l.startswith("-") and not l.startswith("---"))
print("proposed_final.patch written (LF).  diff scope:", f"+{added}/-{removed} lines, search() only")


def _sig(rows):
    return [(r["memory_id"], round(float(r.get("_rank", 0.0)), 9)) for r in rows]


seed, n = 2024, 4000
store = bc.fresh_store(f"final-patch-{seed}"); bc.make_corpus(store, n, seed=seed); db = store.path; store.close()
qs = bc.make_queries(seed, 40) + ["", "zzznope", "کلمهٔ فارسی", "of the", "lead-quote/x"]
filters = [{}, {"namespace": "semantic"}, {"namespace": "episodic"},
           {"min_trust": "GRADED"}, {"min_trust": "OWNER_CONFIRMED"}]
total = mism = 0
for force_like in (False, True):
    base = ms.MemoryStore(path=db); pat = mod.MemoryStore(path=db)
    if force_like:
        base._fts = False; pat._fts = False
    for q in qs:
        for k in (1, 5, 20, 300):
            for f in filters:
                total += 1
                if _sig(base.search(q, k=k, **f)) != _sig(pat.search(q, k=k, **f)):
                    mism += 1
    base.close(); pat.close()
print(f"correctness (original vs FINAL patch): {total} checks, {mism} mismatches ->",
      "IDENTICAL ✅" if mism == 0 else "MISMATCH ❌")
