#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""measure_paired.py — CORRECTED authoritative latency (fixes the disjoint-subset artifact
that the adversarial 'measurement-validity' lens refuted).

Correct paired design: each iteration draws ONE query; BOTH variants are timed on that SAME
query (identical query multiset — no subset skew), and the lead position alternates each
iteration (cancels within-pair warm-cache bias). GC disabled during timing. Median over
samples. This supersedes measure_final.py / finalize_result._gc_latency for the latency %.
"""
from __future__ import annotations

import gc
import io
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
import bench_common as bc  # noqa: E402
import memory_store as ms  # noqa: E402
from memory_store_opt import OptMemoryStore  # noqa: E402


def paired(seed, n, iters=1500):
    st = bc.fresh_store(f"paired-{seed}-{n}"); bc.make_corpus(st, n, seed=seed); db = st.path; st.close()
    qs = bc.make_queries(seed, 64)
    base = ms.MemoryStore(path=db); opt = OptMemoryStore(path=db)
    qi = [0]

    def q():
        qi[0] = (qi[0] + 1) % len(qs); return qs[qi[0]]
    for _ in range(80):
        base.search(q(), k=5); opt.search(q(), k=5)
    bs, os_ = [], []
    lead_base = True
    gc.collect(); gc.disable()
    try:
        for _ in range(iters):
            x = q()                       # SAME query for both this iteration
            if lead_base:
                t = time.perf_counter(); base.search(x, k=5); bs.append(time.perf_counter() - t)
                t = time.perf_counter(); opt.search(x, k=5); os_.append(time.perf_counter() - t)
            else:
                t = time.perf_counter(); opt.search(x, k=5); os_.append(time.perf_counter() - t)
                t = time.perf_counter(); base.search(x, k=5); bs.append(time.perf_counter() - t)
            lead_base = not lead_base
    finally:
        gc.enable()
    base.close(); opt.close()
    b = statistics.median(bs) * 1000; o = statistics.median(os_) * 1000
    bm = statistics.fmean(bs) * 1000; om = statistics.fmean(os_) * 1000
    return {"seed": seed, "n": n, "baseline_median_ms": round(b, 4), "opt_median_ms": round(o, 4),
            "improvement_frac_median": round(1 - o / b, 4), "improvement_frac_mean": round(1 - om / bm, 4),
            "speedup": round(b / o, 3), "samples_each": len(bs)}


if __name__ == "__main__":
    print("=" * 74)
    print("C6 CORRECTED latency — symmetric paired (same query both variants, lead alternated)")
    print("=" * 74)
    rows = [paired(s, n) for s, n in [(1000, 1000), (3000, 3000), (1000, 5000),
                                      (424242, 3000), (2024, 4000)]]
    for r in rows:
        print(f"  seed={r['seed']:<7} n={r['n']:<5}  base={r['baseline_median_ms']:.4f}ms "
              f"opt={r['opt_median_ms']:.4f}ms  median-imp={r['improvement_frac_median']*100:5.1f}%  "
              f"mean-imp={r['improvement_frac_mean']*100:5.1f}%  ({r['speedup']}x)")
    imps = [r["improvement_frac_median"] for r in rows]
    n5 = [r["improvement_frac_median"] for r in rows if r["n"] == 5000]
    print(f"\n  median improvement: min={min(imps)*100:.1f}%  median={statistics.median(imps)*100:.1f}%  "
          f"max={max(imps)*100:.1f}%")
    print(f"  n=5000 (conservative/forward-looking): {min(n5)*100:.1f}%")
