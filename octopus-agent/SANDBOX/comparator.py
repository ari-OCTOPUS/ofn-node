#!/usr/bin/env python3
"""P5 comparator — deterministic verdict + receipt generator.

Reads an experiment-result.json produced by run_experiment.py and re-derives
every frozen-criterion verdict from the pair data (it never trusts the
verdict strings it finds: it recomputes them). Output is canonical JSON
(sorted keys, no whitespace variance) so byte-identical reproducibility can
be proven by running it repeatedly.

Usage: comparator.py <experiment-result.json> <output-verdict.json>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def verdict_for(pair: dict, min_reduction: float) -> dict:
    recomputed = {
        "index_content_equal": len(pair["drift_files"]) == 0,
        "event_count_equal": pair["event_count_equal"],
        "event_order_equal": len(pair["drift_files"]) == 0,
        "schema_equal": len(pair["drift_files"]) == 0,
        "write_reduction_ok": pair["write_reduction_percent"] >= min_reduction,
        "errors_zero": pair["errors_zero"],
    }
    claimed_pass = pair["verdict"] == "PASS"
    recomputed_pass = all(recomputed.values())
    return {
        "pair": pair["pair"],
        "criteria": recomputed,
        "write_reduction_percent": pair["write_reduction_percent"],
        "per_obs": {"baseline": pair["per_obs_baseline"], "candidate": pair["per_obs_candidate"]},
        "claimed_verdict": pair["verdict"],
        "recomputed_verdict": "PASS" if recomputed_pass else "FAIL",
        "claim_matches_recomputation": claimed_pass == recomputed_pass,
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: comparator.py <experiment-result.json> <output-verdict.json>", file=sys.stderr)
        return 2
    src = json.loads(Path(sys.argv[1]).read_text())
    min_red = src["frozen_criteria"]["write_reduction_min_percent"]
    pairs = [verdict_for(p, min_red) for p in src["pairs"]]
    overall = "PASS" if all(p["recomputed_verdict"] == "PASS" and p["claim_matches_recomputation"]
                            for p in pairs) else "FAIL"
    out = {
        "schema": "octopus.mini-scientist.comparator-verdict.v1",
        "run_id": src["run_id"],
        "experiment_id": src["experiment_id"],
        "pairs": pairs,
        "overall_verdict": overall,
        "may_authorize": False,
    }
    Path(sys.argv[2]).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"{overall} — {len(pairs)} pairs verified (recomputed, not trusted)")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
