#!/usr/bin/env python3
"""P4 experiment executor — runs an ACCEPTed manifest end-to-end.

Flow: validate manifest -> for i in 1..runs_required execute one baseline and
one candidate replay in fresh work dirs via runner.py -> evaluate the frozen
criteria per pair -> write RUNS/<run_id>/experiment-result.json.
Exit 0 only if every pair passes every frozen criterion. No retries, no
tuning: a failure is recorded as FAIL (stop-the-line honesty).

Usage: run_experiment.py <manifest.json> <run_id>
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

SANDBOX = Path(__file__).resolve().parent
sys.path.insert(0, str(SANDBOX))
from validate_manifest import validate  # noqa: E402

RUNNER = SANDBOX / "runner.py"
AGENT = SANDBOX.parent


def run_mode(fixture: Path, work: Path, label: str, env: dict) -> dict:
    cmd = [sys.executable, str(RUNNER), "--fixture", str(fixture),
           "--work", str(work), "--label", label,
           "--flush-every", str(env["OCTOPUS_INDEX_FLUSH_EVERY"])]
    if "OCTOPUS_INDEX_FLUSH_MAX_AGE" in env:
        cmd += ["--flush-max-age", str(env["OCTOPUS_INDEX_FLUSH_MAX_AGE"])]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(SANDBOX))
    if proc.returncode != 0:
        print(proc.stdout[-2000:], proc.stderr[-2000:], sep="\n")
        raise SystemExit(f"runner failed for {label}")
    result_path = work.parent / f"{label}.result.json"
    return json.loads(result_path.read_text())


def evaluate_pair(base: dict, cand: dict, records: int, min_reduction: float) -> dict:
    drift = [k for k in cand["output_tree_sha256"]
             if cand["output_tree_sha256"].get(k) != base["output_tree_sha256"].get(k)]
    wb = base["io_delta"]["write_bytes"]
    wa = cand["io_delta"]["write_bytes"]
    reduction = (1 - wa / wb) * 100 if wb else 0.0
    errors = (records - base["persisted"] - base["skipped_duplicates"]) + \
             (records - cand["persisted"] - cand["skipped_duplicates"])
    return {
        "index_content_equal": not drift,
        "event_count_equal": base["persisted"] == cand["persisted"],
        "event_order_equal": not drift,   # observations.jsonl byte-equality included in tree compare
        "schema_equal": not drift,        # all six index JSONs included in tree compare
        "write_reduction_percent": round(reduction, 1),
        "write_reduction_ok": reduction >= min_reduction,
        "errors_zero": errors == 0,
        "drift_files": drift,
        "write_bytes_baseline": wb,
        "write_bytes_candidate": wa,
        "per_obs_baseline": base["write_bytes_per_persisted_obs"],
        "per_obs_candidate": cand["write_bytes_per_persisted_obs"],
        "elapsed_s": {"baseline": base["elapsed_s"], "candidate": cand["elapsed_s"]},
        "verdict": "PASS" if (not drift and base["persisted"] == cand["persisted"]
                              and reduction >= min_reduction and errors == 0) else "FAIL",
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: run_experiment.py <manifest.json> <run_id>", file=sys.stderr)
        return 2
    manifest_path, run_id = sys.argv[1], sys.argv[2]
    ok, errors = validate(manifest_path)
    if not ok:
        for e in errors:
            print("REJECT", e)
        return 1
    print("ACCEPT manifest", manifest_path)
    m = json.loads(Path(manifest_path).read_text())
    runs_root = AGENT / "RUNS" / run_id
    runs_root.mkdir(parents=True, exist_ok=True)
    fixture = AGENT / m["fixture"]["file"]
    min_red = m["frozen_criteria"]["write_reduction_min_percent"]
    pairs = []
    overall = "PASS"
    for i in range(1, m["runs_required"] + 1):
        base = run_mode(fixture, runs_root / f"R{i}" / "baseline",
                        f"p4-R{i}-baseline", m["modes"]["baseline"]["env"])
        cand = run_mode(fixture, runs_root / f"R{i}" / "batched",
                        f"p4-R{i}-batched", m["modes"]["candidate"]["env"])
        ev = evaluate_pair(base, cand, m["fixture"]["records"], min_red)
        ev["pair"] = f"R{i}"
        pairs.append(ev)
        print(f"R{i}: {ev['verdict']} reduction={ev['write_reduction_percent']}% "
              f"drift={len(ev['drift_files'])} per_obs {ev['per_obs_baseline']}->{ev['per_obs_candidate']}")
        if ev["verdict"] != "PASS":
            overall = "FAIL"
    result = {
        "schema": "octopus.mini-scientist.experiment-result.v1",
        "run_id": run_id,
        "manifest": str(manifest_path),
        "experiment_id": m["experiment_id"],
        "frozen_criteria": m["frozen_criteria"],
        "pairs": pairs,
        "overall_verdict": overall,
        "may_authorize": False,
    }
    out = runs_root / "experiment-result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("overall:", overall, "->", out)
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
