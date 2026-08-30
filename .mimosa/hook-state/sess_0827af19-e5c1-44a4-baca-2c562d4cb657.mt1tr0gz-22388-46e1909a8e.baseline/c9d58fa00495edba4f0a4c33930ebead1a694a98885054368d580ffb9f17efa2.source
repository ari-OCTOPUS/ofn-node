#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""experiment2_v3.py — Cycle-2, experiment 2: UNSEEN cells (n=2000, n=10000, fresh seeds).

Purpose: legitimate recalibration after run-1 quarantine. PREDICTION2.json was registered
BEFORE this runs. Measures the same paired-latency protocol + a correctness pass on the
unseen seeds. No changes to the patch itself.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import experiment_v3 as ex  # noqa: E402

if __name__ == "__main__":
    cells = [(2000, 21), (10000, 22)]
    lat = [ex.paired_latency(n, s) for n, s in cells]
    fracs = []
    print("unseen-cell latency (symmetric paired, GC off):")
    for r in lat:
        gg = 1.0 - r["get_idx_ms"] / r["get_base_ms"]
        gi = 1.0 - r["ins_idx_ms"] / r["ins_base_ms"]
        fracs += [gg, gi]
        print(f"  n={r['n']:<6} get {r['get_base_ms']:8.4f}->{r['get_idx_ms']:8.4f} "
              f"({r['get_speedup']}x, gain {gg:.3f})   insert {r['ins_base_ms']:8.4f}->"
              f"{r['ins_idx_ms']:8.4f} ({r['ins_speedup']}x, gain {gi:.3f})")
    conserv = max(0.0, min(fracs))
    print(f"\nconservative (min unseen cell) gain: {conserv:.3f}")

    corr = ex.correctness(n=2000, seed=2121)
    print(f"unseen-seed correctness: checks={corr['checks']} mismatches={corr['mismatches']} "
          f"leaks={corr['admission_leaks']} replay={corr['replay_ops_equal']}")

    out = {"schema": "c6-evolution-v3-exp2", "cells": lat,
           "conservative_gain_unseen": round(conserv, 4), "correctness_unseen": corr}
    (HERE / "result_exp2.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
    print("wrote result_exp2.json")
