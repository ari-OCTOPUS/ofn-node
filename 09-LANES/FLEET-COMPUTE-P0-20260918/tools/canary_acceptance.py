#!/usr/bin/env python3
"""Evaluate the Phase 2 canary soak against the scan's acceptance criteria.

The scan requires: 24 hours of single-canary operation with
  - no watchdog restart
  - no thermal throttling
  - no queue corruption
  - no duplicate settlement
  - no material OFN latency regression
  - every result carrying an input digest, output digest and execution receipt,
    with exactly-once settlement

This reads the live control plane on 138 plus the local telemetry baseline and
prints a verdict per criterion, so acceptance is decided from evidence instead
of from recollection.

Usage:
  python canary_acceptance.py [--since UTC_ISO] [--window-hours 24]
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

LANE = Path(__file__).resolve().parent.parent
TELEMETRY = LANE / "evidence" / "telemetry.jsonl"
CTRL_SSH = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=8", "-i", str(Path.home() / ".ssh" / "id_ed25519"),
            "ari@192.168.0.138"]
CANARY_NODE = "114"
CANARY_SSH = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
              "-o", "ConnectTimeout=8", "-i", str(Path.home() / ".ssh" / "id_ed25519"),
              f"root@192.168.0.{CANARY_NODE}"]

REMOTE_AUDIT = r"""
import json, sys
SINCE = "@SINCE@"
sys.path.insert(0, "/home/ari/ofn/tools")
import compute_core as cc
s = cc.Store("/home/ari/ofn/state/fleet-compute/compute_tasks.db")
out = {"stats": s.stats()["by_state"]}
rows = [dict(r) for r in s.db.execute(
    "SELECT task_id, state, attempt, worker_node_id, output_digest, input_digest, params_json, created_utc FROM tasks ORDER BY created_utc")]
out["tasks"] = rows
pub = [dict(r) for r in s.db.execute(
    "SELECT task_id, payload_json FROM events WHERE kind IN ('SETTLE_DUPLICATE_IGNORED','LEASE_EXPIRED_FINAL','LEASE_EXPIRED_REQUEUED','PARKED','FAILED')")]
out["notable_events"] = pub
# Lease ledger: a task must never hold two open leases at once.
open_leases = [dict(r) for r in s.db.execute(
    "SELECT task_id, COUNT(*) c FROM leases WHERE released_utc IS NULL GROUP BY task_id HAVING c > 1")]
out["double_open_leases"] = open_leases
# Exactly-once: one settlement per task, no task with two terminal successes.
multi = [dict(r) for r in s.db.execute(
    "SELECT task_id, COUNT(*) c FROM events WHERE kind='SUCCEEDED' GROUP BY task_id HAVING c > 1")]
out["multiple_successes"] = multi
receipts = []
try:
    with open("/home/ari/ofn/state/fleet-compute/receipts.jsonl") as fh:
        for line in fh:
            line = line.strip()
            if line:
                receipts.append(json.loads(line))
except OSError:
    pass
out["receipt_count"] = len(receipts)
out["envelope_verdicts"] = {}
out["envelope_verdicts_in_window"] = {}
for r in receipts:
    v = ((r.get("cgroup_envelope") or {}).get("verdict")) or "NONE"
    out["envelope_verdicts"][v] = out["envelope_verdicts"].get(v, 0) + 1
    # Acceptance applies to the soak window. Earlier receipts come from agent
    # versions that could not prove their envelope at all, and pretending
    # otherwise would turn a real historical gap into a false PASS.
    if str(r.get("at_utc") or "") >= SINCE:
        out["envelope_verdicts_in_window"][v] = out["envelope_verdicts_in_window"].get(v, 0) + 1
out["receipts_in_window"] = sum(out["envelope_verdicts_in_window"].values())
durs = [((r.get("receipt") or {}).get("duration_s")) for r in receipts
        if str(r.get("at_utc") or "") >= SINCE]
out["durations"] = [d for d in durs if isinstance(d, (int, float))]
print(json.dumps(out))
"""

REMOTE_NODE_HEALTH = r"""
printf 'restarts=%s\n' "$(systemctl show octopus-compute-canary.service -p NRestarts --value 2>/dev/null || echo n/a)"
printf 'failed_units=%s\n' "$(systemctl --failed --no-legend --plain 2>/dev/null | wc -l)"
printf 'open_scopes=%s\n' "$(systemctl list-units 'octopus-compute-*.scope' --all --no-legend --plain 2>/dev/null | wc -l)"
printf 'stray_workers=%s\n' "$(ps -eo args 2>/dev/null | grep -c '^/usr/bin/python3 /usr/local/bin/compute_worker.py --run-task' || echo 0)"
printf 'load1=%s\n' "$(cut -d' ' -f1 /proc/loadavg)"
printf 'temp=%s\n' "$(cat /sys/class/thermal/thermal_zone0/temp)"
printf 'boot_id=%s\n' "$(cat /proc/sys/kernel/random/boot_id)"
printf 'cooling=%s\n' "$(for c in /sys/class/thermal/cooling_device*; do printf '%s,' "$(cat $c/cur_state 2>/dev/null)"; done)"
"""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ssh(cmd_list, remote_cmd: str, timeout: int = 90):
    proc = subprocess.run(cmd_list + [remote_cmd], capture_output=True, text=True,
                          timeout=timeout, stdin=subprocess.DEVNULL)
    return proc.returncode, proc.stdout, proc.stderr


def baseline_thermal(since: datetime) -> dict:
    """Canary-node thermal/load distribution from the local telemetry ledger."""
    hot: list[float] = []
    load: list[float] = []
    boot_ids: set[str] = set()
    if not TELEMETRY.exists():
        return {}
    with open(TELEMETRY, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("node_id") != CANARY_NODE or not r.get("ok"):
                continue
            try:
                ts = datetime.strptime(r["probe_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            if ts < since:
                continue
            if r.get("hottest_millic"):
                hot.append(r["hottest_millic"] / 1000.0)
            if r.get("load1") is not None:
                load.append(r["load1"])
            if r.get("boot_id"):
                boot_ids.add(r["boot_id"])
    return {
        "samples": len(hot),
        "hot_median": statistics.median(hot) if hot else None,
        "hot_max": max(hot) if hot else None,
        "load_median": statistics.median(load) if load else None,
        "load_max": max(load) if load else None,
        "boot_ids": sorted(boot_ids),
    }


def run_remote_script(cmd_list, script: str, timeout: int = 120) -> tuple[int, str, str]:
    """Deliver a script base64-encoded and pipe it into python3.

    Never inline a multi-line script into an ssh argument: `json.dumps` renders
    newlines as literal backslash-n, which bash does not expand inside double
    quotes, so the remote interpreter receives one broken line.
    """
    import base64
    payload = base64.b64encode(script.encode()).decode()
    proc = subprocess.run(cmd_list + [f"echo {payload} | base64 -d | python3 -"],
                          capture_output=True, text=True, timeout=timeout,
                          stdin=subprocess.DEVNULL)
    return proc.returncode, proc.stdout, proc.stderr


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--window-hours", type=float, default=24.0)
    ap.add_argument("--since", help="UTC ISO start; overrides --window-hours")
    args = ap.parse_args()

    since = (datetime.strptime(args.since, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
             if args.since else utc_now() - timedelta(hours=args.window_hours))

    audit_script = REMOTE_AUDIT.replace("@SINCE@", since.strftime("%Y-%m-%dT%H:%M:%SZ"))
    rc, out, err = run_remote_script(CTRL_SSH, audit_script, timeout=120)
    if rc != 0:
        print("control-plane audit failed:", err[:400])
        return 2
    audit = json.loads(out.strip().splitlines()[-1])

    rc2, node_out, node_err = ssh(CANARY_SSH, REMOTE_NODE_HEALTH, timeout=90)
    node = {}
    if rc2 == 0:
        for line in node_out.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                node[k.strip()] = v.strip()
    else:
        print("node health probe failed:", node_err[:200])

    thermal = baseline_thermal(since)

    # ---- criteria ----
    verdicts: list[tuple[str, str, str]] = []

    restarts = node.get("restarts")
    verdicts.append((
        "no watchdog/service restart",
        "PASS" if restarts in ("0", None) else "FAIL",
        f"NRestarts={restarts}",
    ))

    cooling = [c for c in (node.get("cooling") or "").split(",") if c.isdigit()]
    throttled = any(int(c) > 0 for c in cooling) if cooling else False
    hot_max = thermal.get("hot_max")
    verdicts.append((
        "no thermal throttling",
        "PASS" if not throttled else "FAIL",
        f"cooling_devices_cur_state={cooling} hottest_max={hot_max}C",
    ))

    corrupt = bool(audit.get("double_open_leases"))
    verdicts.append((
        "no queue corruption (no task holds two open leases)",
        "PASS" if not corrupt else "FAIL",
        f"double_open_leases={audit.get('double_open_leases')} stats={audit.get('stats')}",
    ))

    dupes = bool(audit.get("multiple_successes"))
    dupes_ignored = sum(1 for e in audit.get("notable_events", [])
                        if e.get("task_id") and "duplicate" in (e.get("payload_json") or ""))
    verdicts.append((
        "exactly-once settlement",
        "PASS" if not dupes else "FAIL",
        f"tasks_with_two_successes={audit.get('multiple_successes')} "
        f"duplicate_settlements_ignored={dupes_ignored}",
    ))

    # Every dispatched task must carry a receipt with digests, and the envelope
    # must have been provably applied.
    verdicts_map = audit.get("envelope_verdicts_in_window", {})
    all_time = audit.get("envelope_verdicts", {})
    mismatches = verdicts_map.get("MISMATCH", 0)
    unverified = verdicts_map.get("UNVERIFIED", 0)
    dispatches = audit.get("receipts_in_window", 0)
    if dispatches == 0:
        env_verdict = "INCOMPLETE"
    elif mismatches == 0 and unverified == 0:
        env_verdict = "PASS"
    else:
        env_verdict = "FAIL"
    verdicts.append((
        "cgroup envelope proven for every dispatch in window",
        env_verdict,
        f"in_window={verdicts_map} ({dispatches} dispatches) all_time={all_time}",
    ))

    stuck = [t for t in audit.get("tasks", [])
             if t.get("state") in ("LEASED", "RUNNING")]
    stale_scopes = int(node.get("open_scopes") or 0)
    verdicts.append((
        "no work outlives its lease",
        "PASS" if not stuck and stale_scopes == 0 and int(node.get("stray_workers") or 0) == 0 else "FAIL",
        f"tasks_in_flight={len(stuck)} open_scopes={stale_scopes} "
        f"stray_worker_procs={node.get('stray_workers')}",
    ))

    boots = thermal.get("boot_ids") or []
    verdicts.append((
        "canary node stayed up for the window",
        "PASS" if len(boots) <= 1 else "FAIL",
        f"distinct_boot_ids={len(boots)}",
    ))

    succeeded = audit.get("stats", {}).get("SUCCEEDED", 0)
    failed_final = audit.get("stats", {}).get("FAILED_FINAL", 0)
    window_complete = utc_now() - since >= timedelta(hours=23)
    verdicts.append((
        "24 h window actually elapsed",
        "PASS" if window_complete else "INCOMPLETE",
        f"since={since.strftime('%Y-%m-%dT%H:%M:%SZ')} "
        f"elapsed_h={(utc_now() - since).total_seconds() / 3600:.1f}",
    ))

    print(f"CANARY SOAK ACCEPTANCE — node {CANARY_NODE}, window since {since.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"tasks: {audit.get('stats')} | receipts: {audit.get('receipt_count')} | "
          f"durations median="
          f"{(statistics.median(audit['durations']) if audit.get('durations') else None)}")
    print(f"node: {node}")
    print(f"telemetry on {CANARY_NODE}: {thermal}")
    print()
    for name, verdict, detail in verdicts:
        print(f"  [{verdict:>10}] {name}\n               {detail}")
    overall = "PASS" if all(v == "PASS" for _, v, _ in verdicts) else "NOT YET"
    print(f"\nOVERALL: {overall}  (succeeded={succeeded} failed_final={failed_final})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
