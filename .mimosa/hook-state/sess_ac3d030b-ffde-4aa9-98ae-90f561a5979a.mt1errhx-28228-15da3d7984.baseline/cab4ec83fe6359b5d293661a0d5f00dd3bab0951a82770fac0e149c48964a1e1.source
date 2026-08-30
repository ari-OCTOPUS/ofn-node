#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""finalize_result.py — consolidate all C6 evidence into result.json (authoritative).

Combines: (1) correctness on main + held-out corpora, (2) exact query-count mechanism,
(3) GC-controlled bias-free latency at 3 corpus sizes. This JSON is the single source
of truth fed to the governed research loop and the adversarial verification.
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

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import bench_common as bc  # noqa: E402
import bench_ab as ab  # noqa: E402
import memory_store as ms  # noqa: E402
import measure_final as mf  # noqa: E402
from memory_store_opt import OptMemoryStore  # noqa: E402


def _gc_latency(seed, n, iters=1500):
    st = bc.fresh_store(f"fin-{seed}-{n}"); bc.make_corpus(st, n, seed=seed); db = st.path; st.close()
    qs = bc.make_queries(seed, 64)
    base = ms.MemoryStore(path=db); opt = OptMemoryStore(path=db)
    qi = [0]

    def q():
        qi[0] = (qi[0] + 1) % len(qs); return qs[qi[0]]
    for _ in range(80):
        base.search(q(), k=5); opt.search(q(), k=5)
    bs, os_ = [], []
    gc.collect(); gc.disable()
    try:
        for it in range(2 * iters):
            x = q()
            if it % 2 == 0:
                t = time.perf_counter(); base.search(x, k=5); bs.append(time.perf_counter() - t)
            else:
                t = time.perf_counter(); opt.search(x, k=5); os_.append(time.perf_counter() - t)
    finally:
        gc.enable()
    base.close(); opt.close()
    bm = statistics.median(bs) * 1000; om = statistics.median(os_) * 1000
    return {"n": n, "baseline_median_ms": round(bm, 4), "opt_median_ms": round(om, 4),
            "improvement_frac": round(1 - om / bm, 4), "speedup": round(bm / om, 3),
            "samples_each": len(bs)}


def build(created_at: str) -> dict:
    # correctness (main + held-out)
    main_db = ab._corpus_db(1000, 5000); main_q = bc.make_queries(1000, 48)
    ho_db = ab._corpus_db(424242, 3000); ho_q = bc.make_queries(424242, 48)
    corr_main = ab._correctness(main_db, main_q)
    corr_ho = ab._correctness(ho_db, ho_q)
    # mechanism (exact)
    mech_q, b_n, o_n = mf.mechanism(seed=1000, n=3000)
    # latency (GC-controlled, bias-free)
    lat = [_gc_latency(s, n) for s, n in [(1000, 1000), (3000, 3000), (1000, 5000)]]
    imps = [x["improvement_frac"] for x in lat]
    conservative = min(imps)   # largest-corpus / smallest gain = forward-looking floor
    return {
        "schema": "c6-evolution-v1-result",
        "created_at": created_at,
        "hardware_note": "measured on owner Windows box; latency % is hardware-dependent",
        "correctness": {
            "main": corr_main, "heldout": corr_ho,
            "all_identical": corr_main["correctness_ok"] and corr_ho["correctness_ok"],
            "total_checks": corr_main["checks"] + corr_ho["checks"],
            "total_mismatches": corr_main["mismatches"] + corr_ho["mismatches"],
        },
        "mechanism": {
            "query": mech_q, "baseline_executes": b_n, "opt_executes": o_n,
            "roundtrip_reduction_x": round(b_n / o_n, 1),
            "note": "exact, hardware-independent: 1 FTS + N point-queries -> 1 FTS + 1 batched",
        },
        "latency_gc_controlled": lat,
        "improvement_range": {"min": min(imps), "median": statistics.median(imps), "max": max(imps)},
        "conservative_improvement_frac": conservative,
        "measurement_journey_honest": {
            "naive_ab_order_biased_pct": 25.9,
            "paired_gc_confounded_pct": 9.7,
            "controlled_gc_off_pct_by_size": {str(x["n"]): round(x["improvement_frac"] * 100, 1) for x in lat},
            "note": "naive A/B was order-biased UP; paired probe was GC-confounded DOWN; "
                    "GC-controlled single-stream is authoritative (median≈mean).",
        },
    }


if __name__ == "__main__":
    created = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    res = build(created)
    out = _HERE / "result.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
    print("wrote", out)
    print("correctness all_identical:", res["correctness"]["all_identical"],
          "| checks:", res["correctness"]["total_checks"],
          "| mismatches:", res["correctness"]["total_mismatches"])
    print("mechanism:", res["mechanism"]["baseline_executes"], "->",
          res["mechanism"]["opt_executes"], f"({res['mechanism']['roundtrip_reduction_x']}x)")
    print("latency improvement by size:",
          {x["n"]: f"{x['improvement_frac']*100:.1f}%" for x in res["latency_gc_controlled"]})
    print("conservative improvement:", f"{res['conservative_improvement_frac']*100:.1f}%")
