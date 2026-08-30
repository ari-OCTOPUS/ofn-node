#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""attack_measure.py — adversarial measurement-validity probe (lean, cached corpora)."""
from __future__ import annotations

import io
import statistics
import sys
import time
import gc
import re as _re
from collections import Counter
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

_DBCACHE = {}


def corpus(seed, n):
    key = (seed, n)
    if key not in _DBCACHE:
        st = bc.fresh_store(f"atk-{seed}-{n}")
        bc.make_corpus(st, n, seed=seed)
        _DBCACHE[key] = st.path
        st.close()
    return _DBCACHE[key]


def _med(xs):
    return statistics.median(xs) * 1000


def prove_disjoint():
    qs = bc.make_queries(1000, 64)
    qi = {"i": 0}

    def _q():
        qi["i"] = (qi["i"] + 1) % len(qs)
        return qi["i"]

    for _ in range(60):
        _q(); _q()
    base_idx, opt_idx = set(), set()
    for it in range(2 * 1000):
        idx = _q()
        (base_idx if it % 2 == 0 else opt_idx).add(idx)
    return sorted(base_idx), sorted(opt_idx), sorted(base_idx & opt_idx)


def subset_cost(db, seed, idx_set, iters=2500):
    """Baseline algo only, over a specific query-index subset."""
    qs = bc.make_queries(seed, 64)
    store = ms.MemoryStore(path=db)
    sub = [qs[i] for i in idx_set]
    for i in range(150):
        store.search(sub[i % len(sub)], k=5)
    samples = []
    gc.collect(); gc.disable()
    try:
        for it in range(iters):
            t = time.perf_counter(); store.search(sub[it % len(sub)], k=5); samples.append(time.perf_counter() - t)
    finally:
        gc.enable()
    store.close()
    return _med(samples)


def paired(db, seed, n, iters=1200):
    qs = bc.make_queries(seed, 64)
    base = ms.MemoryStore(path=db)
    opt = OptMemoryStore(path=db)
    for i in range(150):
        base.search(qs[i % 64], k=5); opt.search(qs[i % 64], k=5)
    bs, os_ = [], []
    gc.collect(); gc.disable()
    try:
        for it in range(iters):
            q = qs[it % 64]
            if it % 2 == 0:
                t = time.perf_counter(); base.search(q, k=5); bs.append(time.perf_counter() - t)
                t = time.perf_counter(); opt.search(q, k=5); os_.append(time.perf_counter() - t)
            else:
                t = time.perf_counter(); opt.search(q, k=5); os_.append(time.perf_counter() - t)
                t = time.perf_counter(); base.search(q, k=5); bs.append(time.perf_counter() - t)
    finally:
        gc.enable()
    base.close(); opt.close()
    b_med, o_med = _med(bs), _med(os_)
    return {"n": n, "seed": seed, "b_med": b_med, "o_med": o_med, "imp_med": 1 - o_med / b_med}


def candidate_counts(db, seed):
    base = ms.MemoryStore(path=db)
    qs = bc.make_queries(seed, 64)
    counts = []
    for q in qs:
        terms = [t for t in _re.findall(r"[^\W_]{3,}", str(q).strip(), _re.UNICODE)][:12]
        fts_q = " OR ".join(terms) if terms else ""
        rows = base._conn.execute(
            "SELECT memory_id FROM memory_fts WHERE memory_fts MATCH ? ORDER BY bm25(memory_fts) LIMIT ?",
            (fts_q, 20)).fetchall()
        counts.append(len(rows))
    base.close()
    return counts


if __name__ == "__main__":
    print("=" * 72)
    print("(A) QUERY-SUBSET CONFOUND")
    print("=" * 72)
    b_idx, o_idx, ov = prove_disjoint()
    print(f"  base query indices n={len(b_idx)}: {b_idx[:10]}")
    print(f"  opt  query indices n={len(o_idx)}: {o_idx[:10]}")
    print(f"  OVERLAP: {len(ov)} -> {ov[:10]}")
    for seed, n in [(1000, 1000), (1000, 5000)]:
        db = corpus(seed, n)
        cb = subset_cost(db, seed, b_idx)
        co = subset_cost(db, seed, o_idx)
        print(f"  n={n:<5} SAME baseline-algo: base-subset(odd)={cb:.4f}ms opt-subset(even)={co:.4f}ms"
              f"  -> skew {(cb/co-1)*100:+.1f}%")

    print("\n" + "=" * 72)
    print("(B) PAIRED (identical queries, order-balanced, GC-off)")
    print("=" * 72)
    imps = []
    for seed, n in [(1000, 1000), (3000, 3000), (1000, 5000), (7, 5000), (2024, 4000)]:
        r = paired(corpus(seed, n), seed, n)
        imps.append(r["imp_med"])
        print(f"  seed={r['seed']:<5} n={r['n']:<5} base={r['b_med']:.4f} opt={r['o_med']:.4f}"
              f" -> median {r['imp_med']*100:5.1f}%")
    print(f"\n  PAIRED improvement: min={min(imps)*100:.1f}% median={statistics.median(imps)*100:.1f}%"
          f" max={max(imps)*100:.1f}%")

    print("\n" + "=" * 72)
    print("(C) MECHANISM candidate-count spread")
    print("=" * 72)
    for seed, n in [(1000, 3000), (1000, 1000), (5000, 500), (5000, 200)]:
        cc = candidate_counts(corpus(seed, n), seed)
        print(f"  seed={seed} n={n}: dist={dict(sorted(Counter(cc).items()))}"
              f"  max_baseline_executes={max(cc)+1}")
