#!/usr/bin/env python3
"""Analyse the Phase-0 telemetry baseline.

Answers the questions the fleet CPU scan requires before any threshold is
hard-coded: what is each node's idle headroom, how hot does it get without
compute load, are identities stable, and is the telemetry actually fresh and
monotonic.

Usage:
  python baseline_report.py [--telemetry PATH] [--min-samples N]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

LANE = Path(__file__).resolve().parent.parent
DEFAULT_TELEMETRY = LANE / "evidence" / "telemetry.jsonl"


def pct(values: list[float], p: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    idx = min(len(values) - 1, max(0, int(round((p / 100.0) * (len(values) - 1)))))
    return values[idx]


def load_rows(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--telemetry", default=str(DEFAULT_TELEMETRY))
    ap.add_argument("--min-samples", type=int, default=1)
    args = ap.parse_args()

    rows = load_rows(Path(args.telemetry))
    ok = [r for r in rows if r.get("ok")]
    if not ok:
        print("no usable samples")
        return 1

    by_node: dict[str, list[dict]] = defaultdict(list)
    for r in ok:
        by_node[r["node_id"]].append(r)

    stamps = sorted(r["probe_utc"] for r in ok)
    print(f"samples={len(rows)} ok={len(ok)} nodes={len(by_node)}")
    print(f"window: {stamps[0]} -> {stamps[-1]}")
    print()

    # Identity stability: a node that changed boot_id or machine_id mid-baseline
    # was rebooted or is being misreported.
    print("IDENTITY AND LIVENESS")
    print(f"{'node':>5} {'machine_id':>13} {'boot_ids':>9} {'live':>6} {'samples':>8} {'max_age_s':>10}")
    for node in sorted(by_node, key=lambda x: int(x) if x.isdigit() else 0):
        rs = by_node[node]
        mids = {r.get("machine_id") for r in rs}
        boots = {r.get("boot_id") for r in rs}
        live = sum(1 for r in rs if r.get("liveness_proven"))
        max_age = max((abs(r.get("clock_skew_s") or 0) for r in rs), default=None)
        print(f"{node:>5} {str(sorted(mids)[0])[:12] if mids else '?':>13} {len(boots):>9} "
              f"{live:>6} {len(rs):>8} {max_age:>10}")
    print()

    print("HEADROOM (idle baseline; medians with p95 where load or heat appears)")
    header = f"{'node':>5} {'cores':>5} {'cpu%med':>8} {'cpu%p95':>8} {'load1p95':>9} {'hot_med':>8} {'hot_max':>8} {'mem%med':>8} {'disk%':>6}"
    print(header)
    for node in sorted(by_node, key=lambda x: int(x) if x.isdigit() else 0):
        rs = by_node[node]
        if len(rs) < args.min_samples:
            continue
        cpu = [r["cpu_pct"] for r in rs if r.get("cpu_pct") is not None]
        load = [r["load1"] for r in rs if r.get("load1") is not None]
        hot = [r["hottest_millic"] / 1000.0 for r in rs if r.get("hottest_millic")]
        mem = [r["mem_used_pct"] for r in rs if r.get("mem_used_pct") is not None]
        disk = [str(r.get("disk_root_used_pct")) for r in rs if r.get("disk_root_used_pct")]
        print(f"{node:>5} {rs[0].get('nproc'):>5} "
              f"{statistics.median(cpu) if cpu else float('nan'):>8.1f} "
              f"{pct(cpu, 95) if cpu else float('nan'):>8.1f} "
              f"{pct(load, 95) if load else float('nan'):>9.2f} "
              f"{statistics.median(hot) if hot else float('nan'):>8.1f} "
              f"{max(hot) if hot else float('nan'):>8.1f} "
              f"{statistics.median(mem) if mem else float('nan'):>8.1f} "
              f"{disk[-1] if disk else '?':>6}")
    print()

    # Thermal granularity: the RK3588 vendor kernel quantises zone readings, so
    # a threshold finer than the step is meaningless.
    print("THERMAL QUANTISATION (distinct zone readings and their step)")
    for node in sorted(by_node, key=lambda x: int(x) if x.isdigit() else 0):
        vals = sorted({r["hottest_millic"] for r in by_node[node] if r.get("hottest_millic")})
        if len(vals) < 2:
            print(f"{node:>5} distinct={vals}")
            continue
        steps = sorted({b - a for a, b in zip(vals, vals[1:])})
        print(f"{node:>5} distinct={len(vals)} range={vals[0]}..{vals[-1]} step_min={steps[0]} "
              f"step_median={statistics.median(steps):.0f}")
    print()

    # Cadence: is the collector actually holding its interval?
    ts = sorted({r["probe_utc"] for r in ok})
    if len(ts) > 2:
        from datetime import datetime
        parsed = [datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ") for t in ts]
        gaps = [(b - a).total_seconds() for a, b in zip(parsed, parsed[1:])]
        print(f"ROUND CADENCE: rounds={len(ts)} median={statistics.median(gaps):.1f}s "
              f"max={max(gaps):.1f}s")

    failed = [r for r in rows if not r.get("ok")]
    if failed:
        print(f"\nFAILED SAMPLES: {len(failed)}")
        for r in failed[:5]:
            print(f"  {r.get('probe_utc')} node={r.get('node_id')} error={r.get('error')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
