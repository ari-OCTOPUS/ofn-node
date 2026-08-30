#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""measure_fair.py — C6 authoritative latency: position-symmetric interleave.

Cancels the warm-cache position bias that inflated the naive A/B: in each iteration
every variant runs ONCE first and ONCE second, so neither is systematically favored.
Reports median over 2*iters samples, at several corpus sizes. This is the honest
number fed to the governed research loop (benchmark_gain).
"""
from __future__ import annotations

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


def fair(seed: int, n: int, iters: int = 500) -> dict:
    store = bc.fresh_store(f"fair-{seed}-{n}")
    bc.make_corpus(store, n, seed=seed)
    store.close()
    db = store.path
    qs = bc.make_queries(seed, 48)
    base = ms.MemoryStore(path=db)
    opt = OptMemoryStore(path=db)
    qi = {"i": 0}

    def _q():
        qi["i"] = (qi["i"] + 1) % len(qs)
        return qs[qi["i"]]

    for _ in range(40):                      # shared warmup
        base.search(_q(), k=5); opt.search(_q(), k=5)

    bs, os_ = [], []
    for _ in range(iters):
        q = _q()
        # pair 1: base first, opt second
        t = time.perf_counter(); base.search(q, k=5); bs.append(time.perf_counter() - t)
        t = time.perf_counter(); opt.search(q, k=5); os_.append(time.perf_counter() - t)
        # pair 2: opt first, base second  (positions cancel)
        t = time.perf_counter(); opt.search(q, k=5); os_.append(time.perf_counter() - t)
        t = time.perf_counter(); base.search(q, k=5); bs.append(time.perf_counter() - t)
    base.close(); opt.close()

    b = statistics.median(bs) * 1000.0
    o = statistics.median(os_) * 1000.0
    return {"corpus_n": n, "seed": seed, "samples_each": len(bs),
            "baseline_median_ms": round(b, 4), "opt_median_ms": round(o, 4),
            "speedup": round(b / o, 3) if o else 0.0,
            "improvement_frac": round(1 - o / b, 4) if b else 0.0}


def run():
    print("=" * 66)
    print("C6 authoritative — position-symmetric latency (bias-cancelled)")
    print("=" * 66)
    results = []
    for seed, n in [(1000, 1000), (3000, 3000), (1000, 5000), (424242, 3000)]:
        r = fair(seed, n)
        results.append(r)
        print(f"  n={r['corpus_n']:<5} seed={r['seed']:<7}  "
              f"base={r['baseline_median_ms']:.4f}ms  opt={r['opt_median_ms']:.4f}ms  "
              f"speedup={r['speedup']}x  improvement={r['improvement_frac']*100:.1f}%")
    imps = [r["improvement_frac"] for r in results]
    print(f"\n  improvement across sizes: min={min(imps)*100:.1f}%  "
          f"median={statistics.median(imps)*100:.1f}%  max={max(imps)*100:.1f}%")
    return results


if __name__ == "__main__":
    run()
