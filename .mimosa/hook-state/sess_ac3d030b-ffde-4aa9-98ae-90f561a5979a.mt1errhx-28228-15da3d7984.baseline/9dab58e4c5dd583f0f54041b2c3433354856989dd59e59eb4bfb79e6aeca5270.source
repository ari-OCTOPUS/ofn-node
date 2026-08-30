#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench_v2.py — latency + mechanism for the batched hydration on the LIVE c7 code.

Methodology fixed from the v1 lessons (an adversarial lens refuted the earlier numbers):
symmetric PAIRED design — each iteration draws ONE query, BOTH variants are timed on that
SAME query (identical multiset, no disjoint-subset skew), lead position alternates each
iteration (cancels warm-cache bias), and GC is disabled during timing. Median AND mean are
reported; their convergence is the clean-signal check.
"""
from __future__ import annotations

import gc
import io
import json
import statistics
import sys
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_v2 as C  # noqa: E402


class _Counting:
    def __init__(self, conn):
        self._c = conn; self.n = 0

    def execute(self, *a, **k):
        self.n += 1
        return self._c.execute(*a, **k)

    def __getattr__(self, name):
        return getattr(self._c, name)


def mechanism(seed=909, n=3000):
    db = C.fresh_db(f"v2-mech-{seed}")
    C.make_corpus(db, n, seed)
    q = C.make_queries(seed, 1)[0]
    b = C.BASE.MemoryStore(path=db); p = C.PATCHED.MemoryStore(path=db)
    b._conn = _Counting(b._conn); p._conn = _Counting(p._conn)
    b.search(q, k=5); p.search(q, k=5)
    bn, pn = b._conn.n, p._conn.n
    b.close(); p.close()
    return q, bn, pn


def paired(seed, n, iters=1200):
    db = C.fresh_db(f"v2-bench-{seed}-{n}")
    C.make_corpus(db, n, seed)
    qs = C.make_queries(seed, 64)
    base = C.BASE.MemoryStore(path=db); pat = C.PATCHED.MemoryStore(path=db)
    qi = [0]

    def q():
        qi[0] = (qi[0] + 1) % len(qs); return qs[qi[0]]
    for _ in range(80):
        base.search(q(), k=5); pat.search(q(), k=5)
    bs, ps = [], []
    lead_base = True
    gc.collect(); gc.disable()
    try:
        for _ in range(iters):
            x = q()
            if lead_base:
                t = time.perf_counter(); base.search(x, k=5); bs.append(time.perf_counter() - t)
                t = time.perf_counter(); pat.search(x, k=5); ps.append(time.perf_counter() - t)
            else:
                t = time.perf_counter(); pat.search(x, k=5); ps.append(time.perf_counter() - t)
                t = time.perf_counter(); base.search(x, k=5); bs.append(time.perf_counter() - t)
            lead_base = not lead_base
    finally:
        gc.enable()
    base.close(); pat.close()
    bm, pm = statistics.median(bs) * 1000, statistics.median(ps) * 1000
    bmu, pmu = statistics.fmean(bs) * 1000, statistics.fmean(ps) * 1000
    return {"seed": seed, "n": n, "base_median_ms": round(bm, 4), "opt_median_ms": round(pm, 4),
            "improvement_median": round(1 - pm / bm, 4), "improvement_mean": round(1 - pmu / bmu, 4),
            "speedup": round(bm / pm, 3), "samples_each": len(bs)}


if __name__ == "__main__":
    q, bn, pn = mechanism()
    print("=" * 72)
    print("C6 evolution_v2 — mechanism (exact) on LIVE c7 code")
    print("=" * 72)
    print(f"  query={q!r}")
    print(f"  baseline executes = {bn}  | patched executes = {pn}  "
          f"-> {round(bn / pn, 1)}x fewer SQL round-trips")

    print("\n" + "=" * 72)
    print("C6 evolution_v2 — latency (symmetric paired, GC off)")
    print("=" * 72)
    rows = [paired(s, n) for s, n in [(1000, 1000), (3000, 3000), (4242, 5000)]]
    for r in rows:
        print(f"  n={r['n']:<5} base={r['base_median_ms']:.4f}ms opt={r['opt_median_ms']:.4f}ms  "
              f"median={r['improvement_median']*100:5.1f}%  mean={r['improvement_mean']*100:5.1f}%  "
              f"({r['speedup']}x)")
    imps = [r["improvement_median"] for r in rows]
    n5 = min(r["improvement_median"] for r in rows if r["n"] == 5000)
    print(f"\n  improvement: min={min(imps)*100:.1f}%  median={statistics.median(imps)*100:.1f}%  "
          f"max={max(imps)*100:.1f}%")
    print(f"  conservative (n=5000): {n5*100:.1f}%")

    corr = json.loads((C.HERE / "correctness_v2.json").read_text("utf-8"))
    out = {"schema": "c6-evolution-v2-result",
           "mechanism": {"baseline_executes": bn, "patched_executes": pn,
                         "roundtrip_reduction_x": round(bn / pn, 1)},
           "latency_paired": rows, "conservative_improvement_frac": n5,
           "correctness": corr,
           "note": "measured against the LIVE c7 memory_store (schema v2, admission_state gate)"}
    (C.HERE / "result_v2.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
    print("\nwrote result_v2.json")
