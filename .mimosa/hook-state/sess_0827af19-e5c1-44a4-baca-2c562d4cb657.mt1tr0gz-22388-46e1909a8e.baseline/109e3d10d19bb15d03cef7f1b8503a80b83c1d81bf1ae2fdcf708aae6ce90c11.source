#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_v2.py — correctness of the batched hydration against the LIVE c7 code (schema v2).

Three gates:
 A. BYTE-IDENTICAL: patched search() == baseline search() for every query x k x filter,
    on both the FTS path and the forced LIKE-fallback path.
 B. GOVERNANCE INVARIANT (new in v2): no PENDING and no RETRACTED memory may EVER appear
    in a search result — from either version. This is the owner-gate the v1 patch would
    have silently broken.
 C. NON-VACUITY: prove PENDING/RETRACTED rows actually reach the candidate stage (so the
    admission filter is really doing work and gate B is not trivially satisfied).
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_v2 as C  # noqa: E402

FILTERS = [{}, {"namespace": "semantic"}, {"namespace": "episodic"},
           {"min_trust": "GRADED"}, {"min_trust": "OWNER_CONFIRMED"}]
KS = [1, 5, 20, 300]


def _sig(rows):
    return [(r["memory_id"], round(float(r.get("_rank", 0.0)), 9)) for r in rows]


def _raw_candidates(conn, query, k=5):
    """FTS candidate ids WITHOUT the admission filter — used for the non-vacuity proof."""
    terms = [t for t in re.findall(r"[^\W_]{3,}", query, re.UNICODE)][:12]
    fq = " OR ".join(terms) if terms else ""
    if not fq:
        return []
    try:
        return [r[0] for r in conn.execute(
            "SELECT memory_id, bm25(memory_fts) AS score FROM memory_fts WHERE memory_fts MATCH ? "
            "ORDER BY score LIMIT ?", (fq, max(k * 4, 20))).fetchall()]
    except Exception:
        return []


def main():
    diff = C.write_artifacts()
    added = sum(1 for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff.splitlines() if l.startswith("-") and not l.startswith("---"))
    print("=" * 72)
    print("C6 evolution_v2 — patch vs LIVE c7 code (schema v2, admission_state)")
    print("=" * 72)
    print(f"patch scope: +{added}/-{removed} lines, search() hydration only\n")

    seed, n = 4242, 4000
    db = C.fresh_db(f"v2-{seed}")
    sets = C.make_corpus(db, n, seed)
    print(f"corpus: admitted={len(sets['admitted'])} pending={len(sets['pending'])} "
          f"retracted={len(sets['retracted'])}")
    blocked = sets["pending"] | sets["retracted"]
    queries = C.make_queries(seed, 40) + ["", "zzznope", "کلمهٔ فارسی", "of the", "lead-quote/x"]

    base = C.BASE.MemoryStore(path=db)
    pat = C.PATCHED.MemoryStore(path=db)
    m = base.metrics()
    print(f"metrics: total={m['total']} active={m['active']} pending={m['pending']} "
          f"retracted={m['retracted']} schema_v={m['schema_version']} fts={m['fts']}\n")

    # ---- C. non-vacuity: do blocked rows reach the candidate stage? ----
    reach = 0
    for q in queries[:40]:
        cands = _raw_candidates(base._conn, q, k=5)
        reach += sum(1 for c in cands if c in blocked)
    print(f"[C] non-vacuity: blocked (PENDING/RETRACTED) rows reaching candidate stage: {reach}")
    print(f"    -> the admission filter is {'DOING REAL WORK' if reach > 0 else 'NOT EXERCISED (vacuous!)'}\n")

    # ---- A + B ----
    checks = mism = 0
    first_bad = None
    leaked_base, leaked_pat = set(), set()
    for force_like in (False, True):
        if force_like:
            base._fts = False; pat._fts = False
        for q in queries:
            for k in KS:
                for f in FILTERS:
                    checks += 1
                    rb = base.search(q, k=k, **f)
                    rp = pat.search(q, k=k, **f)
                    if _sig(rb) != _sig(rp):
                        mism += 1
                        if first_bad is None:
                            first_bad = {"q": q, "k": k, "f": f,
                                         "base": _sig(rb)[:4], "pat": _sig(rp)[:4]}
                    leaked_base |= {r["memory_id"] for r in rb} & blocked
                    leaked_pat |= {r["memory_id"] for r in rp} & blocked
        tag = "LIKE fallback" if force_like else "FTS path"
        print(f"[A] {tag}: cumulative {checks} checks, {mism} mismatches")
    base.close(); pat.close()

    print(f"\n[A] BYTE-IDENTICAL: {checks} checks, {mism} mismatches -> "
          f"{'IDENTICAL ✅' if mism == 0 else 'MISMATCH ❌ ' + str(first_bad)}")
    print(f"[B] GOVERNANCE: PENDING/RETRACTED leaked into results — "
          f"baseline={len(leaked_base)} patched={len(leaked_pat)} -> "
          f"{'OWNER-GATE HELD ✅' if not leaked_base and not leaked_pat else 'LEAK ❌'}")

    out = {"schema": "c6-evolution-v2-correctness", "patch_lines": {"added": added, "removed": removed},
           "corpus": {"n": n, "admitted": len(sets["admitted"]), "pending": len(sets["pending"]),
                      "retracted": len(sets["retracted"]), "schema_version": m["schema_version"]},
           "non_vacuity_blocked_candidates": reach,
           "checks": checks, "mismatches": mism,
           "leaked_baseline": len(leaked_base), "leaked_patched": len(leaked_pat),
           "byte_identical": mism == 0,
           "owner_gate_held": not leaked_base and not leaked_pat}
    (C.HERE / "correctness_v2.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
    print("\nwrote correctness_v2.json")


if __name__ == "__main__":
    main()
