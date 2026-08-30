#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_edges.py — adversarial: prove the ACTUAL in-file patch (not just the subclass)
is byte-identical, INCLUDING the paths my A/B never exercised.

1. Build the proposed patched module by splicing the batched-hydration search() into a
   copy of the real memory_store.py source; save it + emit a unified diff for the owner.
2. Run correctness (original vs patched) over: FTS path, LIKE-fallback path (fts forced
   off), large-k IN(...), unicode/special-char queries, empty query, filter combos.
   ANY mismatch => the patch is NOT safe.
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

_SRC = (_WT / "_ops" / "memory" / "memory_store.py").read_text("utf-8")

# new search() body — identical logic to memory_store_opt, as an in-file method
_NEW_SEARCH = '''    def search(self, query: str, namespace: str = None, k: int = 5, min_trust: str = None) -> list:
        """Batched-hydration recall (C6 evolution_v1): one IN(...) query instead of the
        per-candidate N+1 loop. Ranking/tie-break byte-identical to the prior version."""
        q = str(query or "").strip()
        import re as _re
        terms = [t for t in _re.findall(r"[^\\W_]{3,}", q, _re.UNICODE)][:12]
        fts_q = " OR ".join(terms) if terms else ""
        with _LOCK:
            ids = []
            if self._fts and fts_q:
                try:
                    frows = self._conn.execute(
                        "SELECT memory_id, bm25(memory_fts) AS score FROM memory_fts "
                        "WHERE memory_fts MATCH ? ORDER BY score LIMIT ?", (fts_q, max(k * 4, 20))).fetchall()
                    ids = [(r[0], r[1]) for r in frows]
                except sqlite3.OperationalError:
                    ids = []
            if not ids:
                like = f"%{q}%"
                lrows = self._conn.execute(
                    "SELECT memory_id, 0.0 FROM memory WHERE content LIKE ? OR mkey LIKE ? LIMIT ?",
                    (like, like, max(k * 4, 20))).fetchall()
                ids = [(r[0], 0.0) for r in lrows]
            now = _utc_now_iso()
            score_by_id = {}
            for mid, score in ids:
                if mid not in score_by_id:
                    score_by_id[mid] = score
            row_by_id = {}
            if score_by_id:
                mids = list(score_by_id.keys())
                ph = ",".join("?" * len(mids))
                for r in self._conn.execute(
                        "SELECT " + ",".join(_COLS) + " FROM memory WHERE memory_id IN (" + ph + ") "
                        "AND (valid_to IS NULL OR valid_to>?)", (*mids, now)).fetchall():
                    d = dict(zip(_COLS, r))
                    row_by_id[d["memory_id"]] = d
            out = []
            for mid, score in ids:
                d = row_by_id.get(mid)
                if not d:
                    continue
                if namespace and d["namespace"] != namespace:
                    continue
                if min_trust and not tax.trust_at_least(d["trust"], min_trust):
                    continue
                sal = d.get("salience") or 0.0
                d = dict(d)
                d["_rank"] = float(score) - float(sal)
                out.append(d)
        out.sort(key=lambda x: x["_rank"])
        return out[:k]
'''


def _splice():
    start = _SRC.index("    def search(self, query")
    end = _SRC.index("    def as_memories_used(self", start)
    patched = _SRC[:start] + _NEW_SEARCH + "\n" + _SRC[end:]
    (_HERE / "memory_store_patched.py").write_text(patched, "utf-8")
    diff = "".join(difflib.unified_diff(
        _SRC.splitlines(keepends=True), patched.splitlines(keepends=True),
        fromfile="a/_ops/memory/memory_store.py", tofile="b/_ops/memory/memory_store.py"))
    (_HERE / "proposed.patch").write_text(diff, "utf-8")
    # import the patched source as a distinct module sharing the same globals
    mod = types.ModuleType("memory_store_patched")
    mod.__dict__["__file__"] = str(_HERE / "memory_store_patched.py")
    exec(compile(patched, "memory_store_patched.py", "exec"), mod.__dict__)
    return mod, diff


def _sig(rows):
    return [(r["memory_id"], round(float(r.get("_rank", 0.0)), 9)) for r in rows]


def main():
    patched_mod, diff = _splice()
    print("=" * 70)
    print("proposed patch (unified diff) — surgical, search() only:")
    print("=" * 70)
    print(diff)
    added = sum(1 for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff.splitlines() if l.startswith("-") and not l.startswith("---"))
    print(f"[diff scope: +{added} / -{removed} lines, single method]")

    seed, n = 2024, 4000
    store = bc.fresh_store(f"edge-{seed}")
    bc.make_corpus(store, n, seed=seed)
    db = store.path
    store.close()
    qs = bc.make_queries(seed, 40)
    edge_qs = qs + ["", "  ", "zzznomatch999", "sydney!!! @@ painting", "کلمهٔ فارسی",
                    "a", "of the", "lead-painting/quote"]
    filters = [{}, {"namespace": "semantic"}, {"namespace": "episodic"},
               {"min_trust": "GRADED"}, {"min_trust": "OWNER_CONFIRMED"}]
    ks = [1, 5, 20, 300]

    def _battery(force_like: bool, tag: str):
        base = ms.MemoryStore(path=db)
        pat = patched_mod.MemoryStore(path=db)
        if force_like:                    # exercise the LIKE fallback path
            base._fts = False; pat._fts = False
        checks = mism = 0
        bad = None
        try:
            for q in edge_qs:
                for k in ks:
                    for f in filters:
                        checks += 1
                        a = _sig(base.search(q, k=k, **f))
                        b = _sig(pat.search(q, k=k, **f))
                        if a != b:
                            mism += 1
                            if bad is None:
                                bad = {"q": q, "k": k, "f": f, "a": a[:4], "b": b[:4]}
        finally:
            base.close(); pat.close()
        print(f"  [{tag}] {checks} checks, {mism} mismatches "
              f"-> {'IDENTICAL ✅' if mism == 0 else 'MISMATCH ❌ ' + str(bad)}")
        return mism

    print("\nedge correctness (original vs PATCHED FILE):")
    m1 = _battery(False, "FTS path")
    m2 = _battery(True, "LIKE fallback")
    print("\nOVERALL edge mismatches:", m1 + m2)


if __name__ == "__main__":
    main()
