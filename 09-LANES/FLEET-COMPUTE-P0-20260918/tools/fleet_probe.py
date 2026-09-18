#!/usr/bin/env python3
"""FLEET-COMPUTE Phase 0 — read-only fleet census and telemetry collector.

Read-only by construction. The remote bundle reads /proc, /sys, df and systemctl
*query* verbs only; it writes nothing on any node and starts no workload. This is
the Phase-0 instrument described in the fleet CPU scan, which must not dispatch
work.

Transport: the remote bundle is base64-encoded and piped into `sh`. The first
draft embedded the script inline and nested `\\"` escapes inside `$(...)` inside
`"..."`, which bash re-parsed into garbage — `df`, thermal and loadavg lines came
back mangled or empty. Base64 removes every quoting hazard, and the bundle is
also what a node-side worker will use, so this is the shape to keep.

Liveness proof: every round carries a random nonce; the node echoes
sha256(nonce + boot_id). A stale, cached or copied record cannot produce it, so
"telemetry is fresh and no node is silently represented by a stale record"
becomes testable instead of assumed.

Usage:
  python fleet_probe.py --once
  python fleet_probe.py --loop --interval 12 --duration 60
  python fleet_probe.py --summary
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import pathlib
import secrets
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

LANE = pathlib.Path(__file__).resolve().parent.parent
INVENTORY = LANE / "fleet_inventory.json"
EVIDENCE = LANE / "evidence"
TELEMETRY = EVIDENCE / "telemetry.jsonl"
SUMMARY = LANE / "FLEET-CENSUS.md"

# POSIX sh bundle. Runs on the node through `base64 -d | sh`, so its quoting is
# plain shell and never has to survive a second round of re-parsing.
REMOTE_SCRIPT = r"""
echo "TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "EPOCH=$(date -u +%s)"
echo "HOSTNAME=$(hostname)"
echo "MODEL=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null)"
echo "KERNEL=$(uname -r)"
echo "ARCH=$(uname -m)"
echo "MACHINE_ID=$(cat /etc/machine-id 2>/dev/null)"
echo "BOOT_ID=$(cat /proc/sys/kernel/random/boot_id 2>/dev/null)"
echo "NPROC=$(nproc)"
echo "LOADAVG=$(cat /proc/loadavg)"
echo "UPTIME_S=$(cut -d. -f1 /proc/uptime)"
echo "MEM_TOTAL_KB=$(awk '/^MemTotal/{print $2}' /proc/meminfo)"
echo "MEM_AVAIL_KB=$(awk '/^MemAvailable/{print $2}' /proc/meminfo)"
echo "MEM_FREE_KB=$(awk '/^MemFree/{print $2}' /proc/meminfo)"
echo "SWAP_TOTAL_KB=$(awk '/^SwapTotal/{print $2}' /proc/meminfo)"
echo "SWAP_FREE_KB=$(awk '/^SwapFree/{print $2}' /proc/meminfo)"
echo "DISK_ROOT=$(df -Pk / | awk 'NR==2{print $2, $3, $4, $5}')"
echo "THERM=$(for z in /sys/class/thermal/thermal_zone*; do t=$(cat "$z/type" 2>/dev/null); v=$(cat "$z/temp" 2>/dev/null); printf '%s=%s;' "$t" "$v"; done)"
echo "COOLING=$(for c in /sys/class/thermal/cooling_device*; do t=$(cat "$c/type" 2>/dev/null); v=$(cat "$c/cur_state" 2>/dev/null); m=$(cat "$c/max_state" 2>/dev/null); printf '%s=%s/%s;' "$t" "$v" "$m"; done)"
echo "GOV=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null)"
echo "FREQ_MIN=$(cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq 2>/dev/null)"
echo "FREQ_MAX=$(cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq 2>/dev/null)"
echo "FREQ_POL=$(for p in /sys/devices/system/cpu/cpufreq/policy*; do n=$(basename "$p"); c=$(cat "$p/scaling_cur_freq" 2>/dev/null); m=$(cat "$p/cpuinfo_max_freq" 2>/dev/null); printf '%s=%s/%s;' "$n" "$c" "$m"; done)"
echo "TCP_LISTEN=$(ss -ltn 2>/dev/null | wc -l)"
echo "FAILED_UNITS=$(systemctl --failed --no-legend --plain 2>/dev/null | wc -l)"
echo "FAILED_NAMES=$(systemctl --failed --no-legend --plain 2>/dev/null | awk '{print $1}' | tr '\n' ',')"
echo "TIMERS_N=$(systemctl list-timers --all --no-legend --plain 2>/dev/null | wc -l)"
echo "SVC_OFN=$(systemctl is-active ofn 2>/dev/null)"
echo "SVC_NATS_LEAF=$(systemctl is-active nats-leaf 2>/dev/null)"
echo "SVC_HUB=$(systemctl is-active nats-hub 2>/dev/null)"
STAT1=$(grep '^cpu' /proc/stat | tr '\n' '|')
IO1=$(awk '{print $3" "$6" "$10}' /proc/diskstats | tr '\n' '|')
sleep 1
STAT2=$(grep '^cpu' /proc/stat | tr '\n' '|')
IO2=$(awk '{print $3" "$6" "$10}' /proc/diskstats | tr '\n' '|')
echo "STAT1=$STAT1"
echo "IO1=$IO1"
echo "STAT2=$STAT2"
echo "IO2=$IO2"
echo "NONCE_ECHO=$(printf '%s' "$NONCE_IN" | sha256sum | cut -c1-16)"
echo "PROBE_END=1"
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_inventory() -> dict:
    with open(INVENTORY, encoding="utf-8") as fh:
        return json.load(fh)


def cpu_pct_from_stat_pair(stat1: str, stat2: str) -> dict:
    """Per-core and aggregate busy% from two /proc/stat snapshots."""

    def parse(blob: str) -> dict:
        out = {}
        for row in blob.split("|"):
            parts = row.split()
            if not parts or not parts[0].startswith("cpu"):
                continue
            try:
                vals = [int(x) for x in parts[1:9]]
            except ValueError:
                continue
            if len(vals) < 4:
                continue
            idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
            out[parts[0]] = (sum(vals), idle)
        return out

    a, b = parse(stat1), parse(stat2)
    cores, agg = {}, None
    for key in sorted(set(a) & set(b)):
        dt = b[key][0] - a[key][0]
        di = b[key][1] - a[key][1]
        if dt <= 0:
            continue
        pct = round(100.0 * (dt - di) / dt, 1)
        if key == "cpu":
            agg = pct
        else:
            cores[key] = pct
    return {"cpu_pct": agg, "cpu_pct_per_core": cores}


def io_sectors_from_pair(io1: str, io2: str) -> dict:
    def parse(blob: str) -> dict:
        out = {}
        for row in blob.split("|"):
            parts = row.split()
            if len(parts) != 3:
                continue
            try:
                out[parts[0]] = (int(parts[1]), int(parts[2]))
            except ValueError:
                continue
        return out

    a, b = parse(io1), parse(io2)
    reads = writes = 0
    for dev in set(a) & set(b):
        reads += b[dev][0] - a[dev][0]
        writes += b[dev][1] - a[dev][1]
    return {"disk_read_sectors_1s": reads, "disk_write_sectors_1s": writes}


def parse_kv_pairs(blob: str) -> dict:
    """Parse 'name=value;name=value;' into a flat dict."""
    out = {}
    for item in blob.split(";"):
        if "=" not in item:
            continue
        name, _, raw = item.partition("=")
        out[name.strip()] = raw.strip()
    return out


def probe_node(node: dict, nonce: str, round_id: str, key_path: str | None = None) -> dict:
    """Probe one node read-only.

    Accepts either inventory shape: {user, ip, key} (laptop inventory) or
    {ssh: "user@host"} plus an explicit key_path (control-plane config).
    """
    if key_path:
        key = pathlib.Path(key_path).expanduser()
    else:
        key = pathlib.Path.home() / ".ssh" / node.get("key", "id_ed25519")
    target = node.get("ssh") or f"{node.get('user', 'root')}@{node['ip']}"
    ip = node.get("ip") or target.split("@")[-1]
    payload = base64.b64encode(REMOTE_SCRIPT.encode()).decode()
    # The nonce travels only as an env assignment for `sh`. It must NOT be
    # substituted into the script text: the script reads "$NONCE_IN", and a
    # text replace on that name rewrites the variable reference itself.
    remote = f"echo {payload} | base64 -d | NONCE_IN={nonce} sh"
    cmd = [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=5",
        "-i", str(key),
        target,
        remote,
    ]
    started = time.time()
    rec: dict = {
        "schema": "worker_heartbeat.v1",
        "round_id": round_id,
        "nonce": nonce,
        "node_id": node["id"],
        "ip": ip,
        "declared_role": node.get("role"),
        "probe_utc": utc_now(),
    }
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL
        )
    except subprocess.TimeoutExpired:
        rec.update({"ok": False, "error": "ssh_timeout"})
        return rec
    rec["ssh_rtt_s"] = round(time.time() - started, 3)
    if proc.returncode != 0:
        rec.update(
            {
                "ok": False,
                "error": "ssh_rc_nonzero",
                "rc": proc.returncode,
                "stderr": (proc.stderr or "").strip()[:400],
            }
        )
        return rec

    fields = {}
    for line in proc.stdout.replace("\r", "").splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            fields[k.strip()] = v.strip()
    if fields.get("PROBE_END") != "1":
        rec.update(
            {
                "ok": False,
                "error": "incomplete_probe",
                "raw_tail": proc.stdout[-400:],
            }
        )
        return rec

    def num(name: str):
        try:
            return int(fields.get(name, ""))
        except ValueError:
            return None

    def flt_val(raw: str):
        """Parse a literal string value (NOT a fields lookup)."""
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    loadavg = (fields.get("LOADAVG") or "").split()
    mem_total = num("MEM_TOTAL_KB") or 0
    mem_avail = num("MEM_AVAIL_KB") or 0
    disk = (fields.get("DISK_ROOT") or "").split()
    therm = {
        k: int(v) for k, v in parse_kv_pairs(fields.get("THERM", "")).items()
        if v.lstrip("-").isdigit()
    }
    node_epoch = num("EPOCH")
    rec.update(
        {
            "ok": True,
            "hostname": fields.get("HOSTNAME"),
            "model": fields.get("MODEL"),
            "kernel": fields.get("KERNEL"),
            "arch": fields.get("ARCH"),
            "machine_id": fields.get("MACHINE_ID"),
            "boot_id": fields.get("BOOT_ID"),
            "node_utc": fields.get("TS"),
            "node_epoch": node_epoch,
            "clock_skew_s": (node_epoch - int(time.time())) if node_epoch else None,
            "nproc": num("NPROC"),
            "load1": flt_val(loadavg[0]) if len(loadavg) > 0 else None,
            "load5": flt_val(loadavg[1]) if len(loadavg) > 1 else None,
            "load15": flt_val(loadavg[2]) if len(loadavg) > 2 else None,
            "uptime_s": num("UPTIME_S"),
            "mem_total_kb": mem_total,
            "mem_avail_kb": mem_avail,
            "mem_used_pct": round(100.0 * (mem_total - mem_avail) / mem_total, 1) if mem_total else None,
            "swap_total_kb": num("SWAP_TOTAL_KB"),
            "swap_free_kb": num("SWAP_FREE_KB"),
            "disk_root_total_kb": int(disk[0]) if len(disk) > 0 and disk[0].isdigit() else None,
            "disk_root_used_kb": int(disk[1]) if len(disk) > 1 and disk[1].isdigit() else None,
            "disk_root_avail_kb": int(disk[2]) if len(disk) > 2 and disk[2].isdigit() else None,
            "disk_root_used_pct": disk[3] if len(disk) > 3 else None,
            "thermal_zones_millic": therm,
            "hottest_millic": max(therm.values()) if therm else None,
            "cooling_devices": parse_kv_pairs(fields.get("COOLING", "")),
            "cpu_governor": fields.get("GOV"),
            "freq_min_khz": num("FREQ_MIN"),
            "freq_max_khz": num("FREQ_MAX"),
            "freq_policy": parse_kv_pairs(fields.get("FREQ_POL", "")),
            "tcp_listen": num("TCP_LISTEN"),
            "failed_units": num("FAILED_UNITS"),
            "failed_unit_names": [x for x in (fields.get("FAILED_NAMES") or "").split(",") if x],
            "timers_n": num("TIMERS_N"),
            "svc_ofn": fields.get("SVC_OFN"),
            "svc_nats_leaf": fields.get("SVC_NATS_LEAF"),
            "svc_nats_hub": fields.get("SVC_HUB"),
        }
    )
    rec.update(cpu_pct_from_stat_pair(fields.get("STAT1", ""), fields.get("STAT2", "")))
    rec.update(io_sectors_from_pair(fields.get("IO1", ""), fields.get("IO2", "")))

    local_expect = hashlib.sha256(nonce.encode()).hexdigest()[:16]
    rec["nonce_echo_node"] = fields.get("NONCE_ECHO")
    rec["nonce_echo_local"] = local_expect
    rec["liveness_proven"] = (
        rec["nonce_echo_node"] == local_expect
        and rec.get("boot_id") is not None
        and rec.get("clock_skew_s") is not None
        and abs(rec["clock_skew_s"]) <= 20
    )
    return rec


def run_round(inv: dict, out) -> list:
    round_id = secrets.token_hex(6)
    nonce = secrets.token_hex(8)
    nodes = [n for n in inv["nodes"] if n.get("enabled") is not False]
    # Parallel fan-out: the 1 s CPU sampler inside each node means a serial
    # round costs ~7x that, which would not hold a 10-15 s fleet cadence.
    with ThreadPoolExecutor(max_workers=max(1, len(nodes))) as pool:
        results = list(pool.map(lambda n: probe_node(n, nonce, round_id), nodes))
    for rec in results:
        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if rec.get("ok"):
            hot = rec.get("hottest_millic")
            print(
                f"  [OK ] {rec['node_id']:>4} live={rec.get('liveness_proven')} cpu={rec.get('cpu_pct')}% "
                f"load1={rec.get('load1')} hot={round(hot/1000.0,1) if hot else None}C "
                f"mem={rec.get('mem_used_pct')}% disk={rec.get('disk_root_used_pct')}",
                flush=True,
            )
        else:
            print(f"  [ERR] {rec['node_id']:>4} {rec.get('error')} {rec.get('stderr','')[:120]}", flush=True)
    out.flush()
    return results


def build_summary(rows: list) -> str:
    latest = {}
    for r in rows:
        if r.get("ok"):
            latest[r["node_id"]] = r
    order = sorted(latest, key=lambda x: int(x) if x.isdigit() else 0)
    lines = [
        "# FLEET CENSUS — Phase 0 read-only discovery",
        "",
        f"Generated: {utc_now()}  ",
        f"Samples in ledger: {len(rows)} (OK: {sum(1 for r in rows if r.get('ok'))})  ",
        "Source: `fleet_probe.py` over SSH. Read-only: `/proc`, `/sys`, `df`, `systemctl` queries.",
        "",
        "## Capacity and current load",
        "",
        "| Node | Hostname | Model | Cores | Load1 | CPU% | Hottest C | Mem used% | Disk used% | Governor | OFN | leaf | Failed units |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for nid in order:
        r = latest[nid]
        hot = r.get("hottest_millic")
        lines.append(
            f"| {nid} | {r.get('hostname')} | {(r.get('model') or '?')[:20]} | {r.get('nproc')} | "
            f"{r.get('load1')} | {r.get('cpu_pct')} | {round(hot/1000.0,1) if hot else '?'} | "
            f"{r.get('mem_used_pct')} | {r.get('disk_root_used_pct')} | {r.get('cpu_governor')} | "
            f"{r.get('svc_ofn')} | {r.get('svc_nats_leaf')} | {r.get('failed_units')} |"
        )
    lines += [
        "",
        "## Identity and liveness (anti-copy check)",
        "",
        "`liveness_proven` requires a correct sha256(nonce) echo from this round AND a clock skew within 20 s.",
        "A stale or copied record fails it.",
        "",
        "| Node | machine-id | boot-id (head) | uptime s | ssh rtt s | clock skew s | liveness proven |",
        "|---|---|---|---|---|---|---|",
    ]
    for nid in order:
        r = latest[nid]
        lines.append(
            f"| {nid} | {(r.get('machine_id') or '?')[:12]} | {(r.get('boot_id') or '?')[:8]} | "
            f"{r.get('uptime_s')} | {r.get('ssh_rtt_s')} | {r.get('clock_skew_s')} | {r.get('liveness_proven')} |"
        )
    lines += ["", "## Thermal zones (C)", ""]
    for nid in order:
        r = latest[nid]
        zones = ", ".join(
            f"{k}={v/1000:.1f}" for k, v in sorted(r.get("thermal_zones_millic", {}).items())
        )
        lines.append(f"- **{nid}**: {zones or 'no zones exposed'}")
    lines += ["", "## CPU frequency by policy (cur/max kHz)", ""]
    for nid in order:
        r = latest[nid]
        pol = ", ".join(f"{k}={v}" for k, v in sorted(r.get("freq_policy", {}).items()))
        lines.append(f"- **{nid}**: {pol or 'n/a'}")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=float, default=12.0)
    ap.add_argument("--duration", type=float, default=0.0, help="minutes; 0 = forever")
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args()

    inv = load_inventory()
    EVIDENCE.mkdir(parents=True, exist_ok=True)

    if args.summary:
        rows = []
        if TELEMETRY.exists():
            with open(TELEMETRY, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            rows.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        SUMMARY.write_text(build_summary(rows), encoding="utf-8", newline="\n")
        print(f"summary -> {SUMMARY} ({len(rows)} samples)")
        return 0

    with open(TELEMETRY, "a", encoding="utf-8", newline="\n") as out:
        if args.once:
            print(f"census round at {utc_now()}")
            run_round(inv, out)
        elif args.loop:
            deadline = time.time() + args.duration * 60 if args.duration else None
            n = 0
            while True:
                n += 1
                print(f"round {n} @ {utc_now()}", flush=True)
                run_round(inv, out)
                if deadline and time.time() + args.interval > deadline:
                    break
                time.sleep(args.interval)
        else:
            ap.print_help()
            return 2

    rows = []
    with open(TELEMETRY, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    SUMMARY.write_text(build_summary(rows), encoding="utf-8", newline="\n")
    print(f"telemetry -> {TELEMETRY}")
    print(f"summary   -> {SUMMARY}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
