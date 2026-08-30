#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench_ab.py — C6 Phase-2 EXPERIMENT: baseline vs batched-hydration search().

Design for an airtight correctness gate: ONE corpus DB, opened by BOTH the baseline
MemoryStore and the candidate OptMemoryStore. Identical rows / identical memory_ids,
so any output difference is purely the algorithm. Measures:
  - CORRECTNESS (hard gate): identical (memory_id, _rank) sequence for every query,
    across k ∈ {1,5,20} and filters {none, namespace, min_trust}. ANY mismatch → falsify.
  - LATENCY: median/p95 full-search, baseline vs opt, → speedup.
  - HELD-OUT: repeat on an independently-seeded corpus + different queries (anti-overfit).
Returns a structured dict for the governed research loop. Offline, $0, sandbox-only.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_common as bc  # noqa: E402
import memory_store as ms  # noqa: E402
from memory_store_opt import OptMemoryStore  # noqa: E402

_FILTERS = [
    {},
    {"namespace": "semantic"},
    {"namespace": "episodic"},
    {"min_trust": "GRADED"},
    {"min_trust": "OWNER_CONFIRMED"},   # nothing qualifies → both must return []
]
_KS = [1, 5, 20]


def _sig(rows):
    """Comparable signature of a search result: ordered (memory_id, rank)."""
    return [(r["memory_id"], round(float(r.get("_rank", 0.0)), 9)) for r in rows]


def _corpus_db(seed: int, n: int) -> Path:
    store = bc.fresh_store(f"ab-{seed}-{n}")
    bc.make_corpus(store, n, seed=seed)
    store.close()          # flush WAL
    return store.path


def _correctness(db: Path, queries: list) -> dict:
    base = ms.MemoryStore(path=db)
    opt = OptMemoryStore(path=db)
    checks = mismatches = 0
    first_bad = None
    try:
        for q in queries:
            for k in _KS:
                for filt in _FILTERS:
                    checks += 1
                    a = _sig(base.search(q, k=k, **filt))
                    b = _sig(opt.search(q, k=k, **filt))
                    if a != b:
                        mismatches += 1
                        if first_bad is None:
                            first_bad = {"query": q, "k": k, "filter": filt,
                                         "baseline": a[:6], "opt": b[:6]}
    finally:
        base.close(); opt.close()
    return {"checks": checks, "mismatches": mismatches, "first_bad": first_bad,
            "correctness_ok": mismatches == 0}


def _latency(db: Path, queries: list, iters: int, rounds: int) -> dict:
    base = ms.MemoryStore(path=db)
    opt = OptMemoryStore(path=db)
    qi = {"i": 0}

    def _q():
        qi["i"] = (qi["i"] + 1) % len(queries)
        return queries[qi["i"]]

    try:
        b_meds, o_meds = [], []
        for _ in range(rounds):        # interleave rounds to dampen systematic drift
            b_meds.append(bc.timed(lambda: base.search(_q(), k=5), iters=iters)["median_ms"])
            o_meds.append(bc.timed(lambda: opt.search(_q(), k=5), iters=iters)["median_ms"])
        b = sorted(b_meds)[len(b_meds) // 2]
        o = sorted(o_meds)[len(o_meds) // 2]
        # p95 from one representative measure each
        bp = bc.timed(lambda: base.search(_q(), k=5), iters=iters)["p95_ms"]
        op = bc.timed(lambda: opt.search(_q(), k=5), iters=iters)["p95_ms"]
    finally:
        base.close(); opt.close()
    speedup = (b / o) if o else 0.0
    improvement = (1.0 - o / b) if b else 0.0
    return {"baseline_median_ms": round(b, 4), "opt_median_ms": round(o, 4),
            "baseline_p95_ms": round(bp, 4), "opt_p95_ms": round(op, 4),
            "speedup": round(speedup, 3), "improvement_frac": round(improvement, 4),
            "rounds_baseline": [round(x, 4) for x in b_meds],
            "rounds_opt": [round(x, 4) for x in o_meds]}


def run_ab(main_seed=1000, main_n=5000, heldout_seed=424242, heldout_n=3000,
           iters=300, rounds=3) -> dict:
    main_db = _corpus_db(main_seed, main_n)
    main_q = bc.make_queries(main_seed, 48)
    ho_db = _corpus_db(heldout_seed, heldout_n)
    ho_q = bc.make_queries(heldout_seed, 48)

    main = {"corpus_n": main_n, **_correctness(main_db, main_q),
            **_latency(main_db, main_q, iters, rounds)}
    held = {"corpus_n": heldout_n, **_correctness(ho_db, ho_q),
            **_latency(ho_db, ho_q, iters, rounds)}
    return {"main": main, "heldout": held,
            "correctness_ok": main["correctness_ok"] and held["correctness_ok"]}


def _print(tag, r):
    print(f"\n[{tag}] corpus_n={r['corpus_n']}")
    print(f"  correctness: {r['checks']} checks, {r['mismatches']} mismatches "
          f"-> {'IDENTICAL ✅' if r['correctness_ok'] else 'MISMATCH ❌'}")
    if r["first_bad"]:
        print(f"    first mismatch: {r['first_bad']}")
    print(f"  latency: baseline median={r['baseline_median_ms']}ms  "
          f"opt median={r['opt_median_ms']}ms")
    print(f"           baseline p95={r['baseline_p95_ms']}ms  opt p95={r['opt_p95_ms']}ms")
    print(f"  speedup={r['speedup']}x  improvement={r['improvement_frac']*100:.1f}%")
    print(f"  rounds baseline={r['rounds_baseline']}  opt={r['rounds_opt']}")


if __name__ == "__main__":
    res = run_ab()
    print("=" * 70)
    print("C6 Phase-2 A/B — baseline vs batched-hydration search()")
    print("=" * 70)
    _print("MAIN", res["main"])
    _print("HELD-OUT", res["heldout"])
    print("\nOVERALL correctness_ok:", res["correctness_ok"])
