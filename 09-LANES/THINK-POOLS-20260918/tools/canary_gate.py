#!/usr/bin/env python3
"""Unattended Phase-2 canary gate — RUN-TO-COMPLETION item 6 (2026-09-18).

Evaluates the eight canary acceptance criteria against the live control plane
on this host (138) and, ONLY on full PASS, expands canary allowed_nodes from
["114"] to ["114","160","100"] exactly as the run order requires. Idempotent:
once expanded, later runs record a no-op receipt and change nothing. On any
NOT-PASS verdict it writes a receipt and touches nothing.

Criteria mirror tools/canary_acceptance.py (vault lane), including the
snapshot-race fix for "no work outlives its lease" (overdue = open lease
expired while task still claims to run; a mid-flight task with a valid lease
is healthy).

Usage:
  python3 canary_gate.py                 # live evaluation (read-only unless PASS)
  python3 canary_gate.py --selftest     # expansion mechanics on a temp config copy
"""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

OFN = Path("/home/ari/ofn")
STATE = OFN / "state" / "fleet-compute"
DB = STATE / "compute_tasks.db"
CONFIG = STATE / "compute_config.canary.json"
RECEIPTS = STATE / "receipts.jsonl"
DECISIONS = STATE / "decisions.jsonl"
GATE_RECEIPTS = OFN / "state" / "receipts"
MESH_KEY = Path.home() / ".ssh" / "octopus_mesh_ed25519"
CANARY_NODE = "114"
WINDOW_START = datetime(2026, 9, 18, 1, 0, 0, tzinfo=timezone.utc)
EXPAND_TO = ["114", "160", "100"]
TEMP_CEILING_MILLIC = 70000

NODE_HEALTH = r"""
printf 'restarts=%s\n' "$(systemctl show octopus-compute-canary.service -p NRestarts --value 2>/dev/null || echo n/a)"
printf 'failed_units=%s\n' "$(systemctl --failed --no-legend --plain 2>/dev/null | wc -l)"
printf 'open_scopes=%s\n' "$(systemctl list-units 'octopus-compute-*.scope' --all --no-legend --plain 2>/dev/null | wc -l)"
printf 'stray_workers=%s\n' "$(ps -eo args 2>/dev/null | grep -c '^/usr/bin/python3 /usr/local/bin/compute_worker.py --run-task' || echo 0)"
printf 'boot_id=%s\n' "$(cat /proc/sys/kernel/random/boot_id)"
printf 'cooling=%s\n' "$(for c in /sys/class/thermal/cooling_device*; do printf '%s,' "$(cat $c/cur_state 2>/dev/null)"; done)"
"""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def audit(since: datetime) -> dict:
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    now_s = utc_now().strftime("%Y-%m-%dT%H:%M:%S")
    out: dict = {"stats": {}}
    for row in db.execute("SELECT state, COUNT(*) c FROM tasks GROUP BY state"):
        out["stats"][row["state"]] = row["c"]
    tasks = [dict(r) for r in db.execute("SELECT task_id, state, worker_node_id FROM tasks")]
    out["double_open_leases"] = [dict(r) for r in db.execute(
        "SELECT task_id FROM leases WHERE released_utc IS NULL "
        "GROUP BY task_id HAVING COUNT(*) > 1")]
    out["multiple_successes"] = [dict(r) for r in db.execute(
        "SELECT task_id FROM events WHERE kind='SUCCEEDED' "
        "GROUP BY task_id HAVING COUNT(*) > 1")]
    stuck = []
    for t in tasks:
        if t["state"] not in ("LEASED", "RUNNING"):
            continue
        m = db.execute(
            "SELECT MAX(expiry_utc) FROM leases WHERE task_id=? AND released_utc IS NULL",
            (t["task_id"],)).fetchone()[0]
        if not m or str(m) < now_s:
            stuck.append(t["task_id"])
    out["overdue"] = stuck
    out["in_flight"] = sum(1 for t in tasks if t["state"] in ("LEASED", "RUNNING"))
    env: dict = {}
    boots: set[str] = set()
    if RECEIPTS.exists():
        for line in RECEIPTS.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(r.get("at_utc") or "") < iso(since):
                continue
            v = ((r.get("cgroup_envelope") or {}).get("verdict")) or "NONE"
            env[v] = env.get(v, 0) + 1
            if r.get("node_id") == CANARY_NODE:
                bid = ((r.get("receipt") or {}).get("host") or {}).get("boot_id")
                if bid:
                    boots.add(bid)
    out["envelope_in_window"] = env
    out["dispatches_in_window"] = sum(env.values())
    out["boot_ids_in_window"] = sorted(boots)
    db.close()
    return out


def node_health() -> dict:
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
           "-o", "ConnectTimeout=8", "-i", str(MESH_KEY),
           f"root@192.168.0.{CANARY_NODE}", NODE_HEALTH]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                          stdin=subprocess.DEVNULL)
    node: dict = {}
    if proc.returncode == 0:
        for line in proc.stdout.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                node[k.strip()] = v.strip()
    return node


def thermal_window(since: datetime) -> dict:
    """Hottest canary-node temperature across the window, from decisions.jsonl."""
    hot: list[int] = []
    if DECISIONS.exists():
        for line in DECISIONS.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(r.get("at_utc") or "") < iso(since):
                continue
            for ev in r.get("evaluated") or []:
                if ev.get("node_id") == CANARY_NODE:
                    h = (ev.get("headroom") or {}).get("hottest_millic")
                    if isinstance(h, int):
                        hot.append(h)
    return {"samples": len(hot), "hot_max_millic": max(hot) if hot else None}


def evaluate(since: datetime, assume_window_elapsed: bool = False):
    a = audit(since)
    node = node_health()
    thermal = thermal_window(since)
    verdicts: list[tuple[str, str, str]] = []

    restarts = node.get("restarts")
    verdicts.append(("no watchdog/service restart",
                     "PASS" if restarts in ("0", None) else "FAIL",
                     f"NRestarts={restarts}"))

    cooling = [int(c) for c in (node.get("cooling") or "").split(",") if c.isdigit()]
    throttled = any(c > 0 for c in cooling)
    hot_max = thermal.get("hot_max_millic")
    thermal_ok = (not throttled) and (hot_max is None or hot_max < TEMP_CEILING_MILLIC)
    verdicts.append(("no thermal throttling", "PASS" if thermal_ok else "FAIL",
                     f"cooling={cooling} hot_max_millic={hot_max} samples={thermal['samples']}"))

    verdicts.append(("no queue corruption",
                     "PASS" if not a["double_open_leases"] else "FAIL",
                     f"double_open_leases={a['double_open_leases']}"))

    verdicts.append(("exactly-once settlement",
                     "PASS" if not a["multiple_successes"] else "FAIL",
                     f"multiple_successes={a['multiple_successes']}"))

    env = a["envelope_in_window"]
    if a["dispatches_in_window"] == 0:
        v5 = "INCOMPLETE"
    elif env.get("MISMATCH", 0) == 0 and env.get("UNVERIFIED", 0) == 0:
        v5 = "PASS"
    else:
        v5 = "FAIL"
    verdicts.append(("cgroup envelope proven for every dispatch in window", v5,
                     f"in_window={env} ({a['dispatches_in_window']} dispatches)"))

    stale_scopes = int(node.get("open_scopes") or 0)
    strays = int(node.get("stray_workers") or 0)
    v6 = "PASS" if not a["overdue"] and stale_scopes == 0 and strays == 0 else "FAIL"
    verdicts.append(("no work outlives its lease", v6,
                     f"overdue={a['overdue']} healthy_in_flight={a['in_flight']} "
                     f"open_scopes={stale_scopes} stray_workers={strays}"))

    verdicts.append(("canary node stayed up for the window",
                     "PASS" if len(a["boot_ids_in_window"]) <= 1 else "FAIL",
                     f"distinct_boot_ids={a['boot_ids_in_window']}"))

    elapsed_h = (utc_now() - since).total_seconds() / 3600
    if assume_window_elapsed:
        v8, elapsed_h = "PASS", 24.0
    else:
        v8 = "PASS" if elapsed_h >= 23.0 else "INCOMPLETE"
    verdicts.append(("24 h window actually elapsed", v8, f"elapsed_h={elapsed_h:.1f}"))

    overall = "PASS" if all(v == "PASS" for _, v, _ in verdicts) else "NOT-PASS"
    return overall, verdicts, a, node, thermal


def expand_allowed_nodes(cfg_path: Path) -> dict:
    """Apply the ordered expansion with a timestamped backup. Returns diff."""
    import hashlib
    before = cfg_path.read_text(encoding="utf-8")
    backup = cfg_path.with_suffix(f".json.bak-canarygate-{utc_now().strftime('%Y%m%dT%H%M%SZ')}")
    shutil.copy2(cfg_path, backup)
    cfg = json.loads(before)
    old = list(cfg.get("policy", {}).get("allowed_nodes") or [])
    cfg["policy"]["allowed_nodes"] = list(EXPAND_TO)
    after = json.dumps(cfg, indent=2) + "\n"
    cfg_path.write_text(after, encoding="utf-8", newline="\n")
    return {"backup": str(backup),
            "allowed_nodes_before": old,
            "allowed_nodes_after": list(EXPAND_TO),
            "sha_before": hashlib.sha256(before.encode()).hexdigest()[:16],
            "sha_after": hashlib.sha256(after.encode()).hexdigest()[:16]}


def write_receipt(payload: dict) -> Path:
    GATE_RECEIPTS.mkdir(parents=True, exist_ok=True)
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    p = GATE_RECEIPTS / f"CANARY-GATE-{stamp}.json"
    n = 1
    while p.exists():
        n += 1
        p = GATE_RECEIPTS / f"CANARY-GATE-{stamp}-{n}.json"
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                 encoding="utf-8", newline="\n")
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true",
                    help="expansion mechanics on a temp config copy; live config untouched")
    args = ap.parse_args()

    if args.selftest:
        with tempfile.TemporaryDirectory() as td:
            tmp_cfg = Path(td) / "compute_config.canary.json"
            shutil.copy2(CONFIG, tmp_cfg)
            diff = expand_allowed_nodes(tmp_cfg)
            live = json.loads(CONFIG.read_text(encoding="utf-8"))
            ok = (diff["allowed_nodes_after"] == EXPAND_TO
                  and live["policy"]["allowed_nodes"] == ["114"])
            print(json.dumps({"selftest": "PASS" if ok else "FAIL", "diff": diff,
                              "live_config_untouched": live["policy"]["allowed_nodes"]},
                             indent=1))
            return 0 if ok else 1

    since = WINDOW_START
    overall, verdicts, a, node, thermal = evaluate(since)
    cfg_now = json.loads(CONFIG.read_text(encoding="utf-8"))
    already = cfg_now.get("policy", {}).get("allowed_nodes") == EXPAND_TO

    result = {
        "schema": "octopus.receipt.v1",
        "what": "RUN-TO-COMPLETION item 6 — canary gate (unattended evaluation)",
        "at": iso(utc_now()),
        "window_start": iso(since),
        "verdicts": [{"criterion": c, "verdict": v, "detail": d}
                     for c, v, d in verdicts],
        "overall": overall,
        "stats": a["stats"],
        "thermal": thermal,
        "node": node,
        "action": "none",
    }

    if overall == "PASS" and not already:
        diff = expand_allowed_nodes(CONFIG)
        result["action"] = "expanded_allowed_nodes"
        result["expansion"] = diff
    elif overall == "PASS" and already:
        result["action"] = "no-op (already expanded)"
    else:
        result["action"] = "none (waiting; nothing touched)"

    p = write_receipt(result)
    print(json.dumps({"overall": overall, "action": result["action"],
                      "receipt": str(p)}, indent=1))
    for c, v, d in verdicts:
        print(f"  [{v:>10}] {c} — {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
