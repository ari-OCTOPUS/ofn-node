#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""measure_final.py — C6 authoritative & cache-agnostic evidence.

(1) MECHANISM (exact, hardware-independent): count sqlite execute() calls per search.
    Proves baseline = 1 FTS + N point-queries; opt = 1 FTS + 1 batched. This is the
    durable claim; latency % is only its noisy consequence on this box.
(2) LATENCY (bias-controlled): single interleaved stream, fresh query every call,
    variant alternated call-by-call, so neither variant systematically gets a cold
    or warm cache position. Median + trimmed-mean + p90 over the stream.
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


class _CountingConn:
    """Transparent wrapper counting execute() calls."""
    def __init__(self, conn):
        self._c = conn
        self.n = 0

    def execute(self, *a, **k):
        self.n += 1
        return self._c.execute(*a, **k)

    def __getattr__(self, name):
        return getattr(self._c, name)


def mechanism(seed=1000, n=3000):
    store = bc.fresh_store(f"mech-{seed}")
    bc.make_corpus(store, n, seed=seed)
    db = store.path
    store.close()
    q = bc.make_queries(seed, 1)[0]
    base = ms.MemoryStore(path=db)
    opt = OptMemoryStore(path=db)
    base._conn = _CountingConn(base._conn)
    opt._conn = _CountingConn(opt._conn)
    base.search(q, k=5); opt.search(q, k=5)
    b_n, o_n = base._conn.n, opt._conn.n
    base.close(); opt.close()
    return q, b_n, o_n


def _trimmed_mean(xs, trim=0.1):
    xs = sorted(xs)
    c = int(len(xs) * trim)
    core = xs[c:len(xs) - c] or xs
    return statistics.fmean(core)


def latency(seed, n, iters=1000):
    store = bc.fresh_store(f"final-{seed}-{n}")
    bc.make_corpus(store, n, seed=seed)
    db = store.path
    store.close()
    qs = bc.make_queries(seed, 64)
    base = ms.MemoryStore(path=db)
    opt = OptMemoryStore(path=db)
    qi = {"i": 0}

    def _q():
        qi["i"] = (qi["i"] + 1) % len(qs)
        return qs[qi["i"]]

    for _ in range(60):
        base.search(_q(), k=5); opt.search(_q(), k=5)

    bs, os_ = [], []
    for it in range(2 * iters):          # single stream, alternate variant per call
        q = _q()
        if it % 2 == 0:
            t = time.perf_counter(); base.search(q, k=5); bs.append(time.perf_counter() - t)
        else:
            t = time.perf_counter(); opt.search(q, k=5); os_.append(time.perf_counter() - t)
    base.close(); opt.close()

    b_med = statistics.median(bs) * 1000
    o_med = statistics.median(os_) * 1000
    b_tm = _trimmed_mean(bs) * 1000
    o_tm = _trimmed_mean(os_) * 1000
    b_p90 = sorted(bs)[int(len(bs) * 0.9)] * 1000
    o_p90 = sorted(os_)[int(len(os_) * 0.9)] * 1000
    return {"n": n, "b_med": b_med, "o_med": o_med, "b_tm": b_tm, "o_tm": o_tm,
            "b_p90": b_p90, "o_p90": o_p90,
            "imp_med": 1 - o_med / b_med, "imp_tm": 1 - o_tm / b_tm}


if __name__ == "__main__":
    q, b_n, o_n = mechanism()
    print("=" * 70)
    print("C6 MECHANISM (exact) — sqlite execute() calls per single search()")
    print("=" * 70)
    print(f"  query={q!r}")
    print(f"  baseline executes = {b_n}   (1 FTS candidate query + {b_n-1} point hydrations)")
    print(f"  opt      executes = {o_n}   (1 FTS candidate query + {o_n-1} batched hydration)")
    print(f"  round-trip reduction: {b_n} -> {o_n}  ({b_n/o_n:.1f}x fewer SQL calls)")

    print("\n" + "=" * 70)
    print("C6 LATENCY (single-stream, variant alternated per call — bias-controlled)")
    print("=" * 70)
    imps = []
    for seed, n in [(1000, 1000), (3000, 3000), (1000, 5000)]:
        r = latency(seed, n)
        imps.append(r["imp_med"])
        print(f"  n={n:<5}  median base={r['b_med']:.4f} opt={r['o_med']:.4f} "
              f"-> {r['imp_med']*100:5.1f}%   |  trimmed-mean base={r['b_tm']:.4f} "
              f"opt={r['o_tm']:.4f} -> {r['imp_tm']*100:5.1f}%   | p90 base={r['b_p90']:.4f} "
              f"opt={r['o_p90']:.4f}")
    print(f"\n  median improvement across sizes: min={min(imps)*100:.1f}%  "
          f"median={statistics.median(imps)*100:.1f}%  max={max(imps)*100:.1f}%")
