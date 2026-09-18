#!/usr/bin/env python3
"""Sustained canary: repeated cgroup-bounded loads with continuous sampling.

The 40-second calibration runs never let the heatsink reach steady state, so
they cannot answer "how much can this board sustain". This runs N bounded tasks
back to back through the real control plane (lease -> dispatch -> receipt ->
settle) while sampling temperature, load, frequency and SSH latency on the node.

Every task still carries the profile's own 120 s ceiling; sustained load comes
from repetition, not from one unbounded run. That is deliberate: no single task
can outlive its lease.

Usage:
  python sustained_canary.py --tasks 6 --seconds 120 --workers 8 --quota 400%
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANE = HERE.parent
EVIDENCE = LANE / "evidence"

BOARD_SSH = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
             "-o", "ConnectTimeout=5", "-i", str(Path.home() / ".ssh" / "id_ed25519"),
             "root@192.168.0.114"]
CTRL_SSH = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=8", "-i", str(Path.home() / ".ssh" / "id_ed25519"),
            "ari@192.168.0.138"]

SAMPLE_CMD = (
    'python3 -c "'
    "import json,time;"
    "z=[int(open(f'/sys/class/thermal/thermal_zone{i}/temp').read()) for i in range(7)];"
    "print(json.dumps({'t':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),"
    "'zones':z,'hottest':max(z),"
    "'load1':float(open('/proc/loadavg').read().split()[0]),"
    "'freq_big':int(open('/sys/devices/system/cpu/cpufreq/policy6/scaling_cur_freq').read()),"
    "'mem_avail_kb':[l for l in open('/proc/meminfo') if l.startswith('MemAvailable')][0].split()[1]}))\""
)


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sample() -> dict | None:
    started = time.time()
    proc = subprocess.run(BOARD_SSH + [SAMPLE_CMD], capture_output=True, text=True,
                          timeout=25, stdin=subprocess.DEVNULL)
    rtt_ms = int((time.time() - started) * 1000)
    if proc.returncode != 0:
        return {"ok": False, "rtt_ms": rtt_ms, "err": proc.stderr.strip()[:200]}
    try:
        row = json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"ok": False, "rtt_ms": rtt_ms, "err": proc.stdout.strip()[:200]}
    row["ok"] = True
    row["rtt_ms"] = rtt_ms
    return row


def dispatch(seconds: int, workers: int, quota: str, key: str) -> subprocess.Popen:
    cmd = (
        "cd /home/ari/ofn/state/fleet-compute && "
        "python3 /home/ari/ofn/tools/compute_scheduler.py "
        "--config ./compute_config.canary.json --state . --once --auto-enqueue "
        f"--auto-profile cpu_bench --auto-seconds {seconds} "
        f"--auto-params '{{\"workers\":{workers},\"block_mb\":2}}' --cgroup-quota {quota} "
        f"--enqueue-key sustained-{key}"
    )
    return subprocess.Popen(CTRL_SSH + [cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", type=int, default=6)
    ap.add_argument("--seconds", type=int, default=120)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--quota", default="400%")
    ap.add_argument("--interval", type=float, default=15.0)
    args = ap.parse_args()

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    samples_path = EVIDENCE / "sustained-canary-samples.jsonl"
    results_path = EVIDENCE / "sustained-canary-results.jsonl"

    idle = [sample() for _ in range(2)]
    print(f"[{utc()}] idle baseline: hottest={max(s['hottest'] for s in idle if s.get('ok'))/1000:.2f}C "
          f"rtt={[s.get('rtt_ms') for s in idle]}", flush=True)

    with open(samples_path, "a", encoding="utf-8", newline="\n") as sf, \
         open(results_path, "a", encoding="utf-8", newline="\n") as rf:
        for i in range(1, args.tasks + 1):
            key = f"{int(time.time())}-{i}"
            proc = dispatch(args.seconds, args.workers, args.quota, key)
            print(f"[{utc()}] task {i}/{args.tasks} dispatched "
                  f"({args.seconds}s, workers={args.workers}, quota={args.quota})", flush=True)
            deadline = time.time() + args.seconds + 60
            while proc.poll() is None and time.time() < deadline:
                row = sample()
                if row:
                    row["phase"] = f"task{i}"
                    sf.write(json.dumps(row, sort_keys=True) + "\n")
                    sf.flush()
                    if row.get("ok"):
                        print(f"   {row['t']} hot={row['hottest']/1000:.2f}C load1={row['load1']} "
                              f"freq_big={row['freq_big']} rtt={row['rtt_ms']}ms", flush=True)
                time.sleep(args.interval)
            out, err = proc.communicate(timeout=60)
            try:
                payload = json.loads(out)
                disp = payload.get("dispatched")
            except (ValueError, TypeError):
                disp = {"ok": False, "error": f"unparsable: {out[:200]} {err[:200]}"}
            rf.write(json.dumps({"at_utc": utc(), "task_index": i, "dispatched": disp},
                                sort_keys=True) + "\n")
            rf.flush()
            print(f"   -> {json.dumps(disp, ensure_ascii=False)}", flush=True)

        cooldown = [sample()]
        for _ in range(6):
            time.sleep(20)
            row = sample()
            if row:
                row["phase"] = "cooldown"
                sf.write(json.dumps(row, sort_keys=True) + "\n")
                sf.flush()
                cooldown.append(row)
        peak = max((r["hottest"] for r in cooldown if r.get("ok")), default=0)
        print(f"[{utc()}] done. peak hottest now={peak/1000:.2f}C", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
