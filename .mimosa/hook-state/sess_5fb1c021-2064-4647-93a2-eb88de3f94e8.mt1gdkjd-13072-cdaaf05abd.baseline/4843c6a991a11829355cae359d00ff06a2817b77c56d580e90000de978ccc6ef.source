#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""correct_result.py — apply the measurement-validity correction to result.json.

The adversarial 'measurement-validity' lens proved measure_final/_gc_latency timed baseline
and opt on DISJOINT unequal-cost query subsets (odd vs even indices), inflating the gain
~8pts. This rebuilds the latency section from measure_paired (same query both variants,
lead alternated, GC off) and marks the old numbers superseded. Correctness + mechanism
are unchanged (they were confirmed by the other four lenses).
"""
from __future__ import annotations

import io
import json
import statistics
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import measure_paired as mp  # noqa: E402

res = json.loads((_HERE / "result.json").read_text("utf-8"))

paired = [mp.paired(s, n) for s, n in [(1000, 1000), (3000, 3000), (1000, 5000)]]
imps = [p["improvement_frac_median"] for p in paired]
n5 = [p["improvement_frac_median"] for p in paired if p["n"] == 5000]
conservative = min(n5)

res["latency_paired_corrected"] = paired
res["improvement_range"] = {"min": min(imps), "median": statistics.median(imps), "max": max(imps)}
res["conservative_improvement_frac"] = conservative
res["latency_gc_controlled_SUPERSEDED"] = res.pop("latency_gc_controlled", None)
res["measurement_journey_honest"]["controlled_gc_off_DISJOINT_SUBSET_pct_by_size"] = \
    res["measurement_journey_honest"].pop("controlled_gc_off_pct_by_size", None)
res["measurement_journey_honest"]["corrected_paired_pct_by_size"] = \
    {str(p["n"]): round(p["improvement_frac_median"] * 100, 1) for p in paired}
res["measurement_journey_honest"]["correction_note"] = (
    "adversarial measurement-validity lens caught that the GC-off single-stream still timed "
    "baseline/opt on disjoint unequal-cost query subsets (odd vs even), inflating ~8pts. "
    "measure_paired (same query both variants, lead alternated) is authoritative: "
    "n=5000 ~24%, median across sizes ~29%.")

(_HERE / "result.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
print("corrected result.json")
print("  paired improvement by size:", {p["n"]: f"{p['improvement_frac_median']*100:.1f}%" for p in paired})
print("  conservative (n=5000):", f"{conservative*100:.1f}%")
print("  correctness unchanged:", res["correctness"]["all_identical"],
      "checks:", res["correctness"]["total_checks"])
print("  mechanism unchanged:", res["mechanism"]["baseline_executes"], "->", res["mechanism"]["opt_executes"])
