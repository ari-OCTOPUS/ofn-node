#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_robust.py — C6 self-skeptic: kill the two obvious refutations of the A/B.

R1 "order artifact": whoever runs second gets a warm cache, faking the speedup.
    -> measure improvement under baseline-first, opt-first, AND strict per-call
       alternation. If the gain survives all three, it is not an ordering artifact.
R2 "identical-because-empty": results match only because both return nothing.
    -> report substantive result sizes; require non-trivial non-empty results.
"""
from __future__ import annotations

import io
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


def _median(fn, iters, warmup=25):
    for _ in range(warmup):
        fn()
    xs = []
    for _ in range(iters):
        t0 = time.perf_counter()
        fn()
        xs.append(time.perf_counter() - t0)
    xs.sort()
    return xs[len(xs) // 2] * 1000.0


def main():
    seed, n = 777, 5000
    store = bc.fresh_store(f"robust-{seed}")
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

    iters = 400
    print("=" * 66)
    print("C6 self-skeptic — order robustness & non-emptiness")
    print("=" * 66)

    # R2: substantive non-emptiness (no filter, k=20)
    sizes = [len(base.search(q, k=20)) for q in qs]
    nonzero = sum(1 for s in sizes if s > 0)
    print(f"\nR2 non-emptiness: {nonzero}/{len(qs)} queries return results; "
          f"avg={sum(sizes)/len(sizes):.1f}, max={max(sizes)} (k=20)")
    # cross-check opt returns same sizes
    osizes = [len(opt.search(q, k=20)) for q in qs]
    print(f"   opt sizes identical to baseline: {sizes == osizes}")

    # R1: three orderings
    b1 = _median(lambda: base.search(_q(), k=5), iters)   # baseline first
    o1 = _median(lambda: opt.search(_q(), k=5), iters)    # opt second
    o2 = _median(lambda: opt.search(_q(), k=5), iters)    # opt first
    b2 = _median(lambda: base.search(_q(), k=5), iters)   # baseline second

    def _alt():   # strict per-call alternation, timed together
        bt = ot = 0.0
        for _ in range(20):
            base.search(_q(), k=5); opt.search(_q(), k=5)   # warmup
        for _ in range(iters):
            q = _q()
            t0 = time.perf_counter(); base.search(q, k=5); bt += time.perf_counter() - t0
            t0 = time.perf_counter(); opt.search(q, k=5); ot += time.perf_counter() - t0
        return bt / iters * 1000.0, ot / iters * 1000.0

    ba, oa = _alt()
    base.close(); opt.close()

    def imp(b, o):
        return f"{(1 - o / b) * 100:5.1f}%  (base {b:.4f} / opt {o:.4f})"

    print("\nR1 order robustness (improvement = 1 - opt/base):")
    print(f"  baseline-first, opt-second : {imp(b1, o1)}")
    print(f"  opt-first, baseline-second : {imp(b2, o2)}")
    print(f"  strict per-call alternation: {imp(ba, oa)}")
    survives = min((1 - o1 / b1), (1 - o2 / b2), (1 - oa / ba)) > 0.05
    print(f"\n  gain > 5% under ALL three orderings: {survives}")


if __name__ == "__main__":
    main()
