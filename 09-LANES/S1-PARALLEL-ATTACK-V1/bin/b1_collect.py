#!/usr/bin/env python3
"""S1-PARALLEL-ATTACK-V1 / L-B (GAP-02B) - read-only telemetry collector for node 182.

Samples cgroup v2 memory/swap/pressure + process IO/CPU for octopus-sensorium.service
every 30s for a bounded window (default 4h). Appends JSONL. NEVER writes to any service
or state file of the organism. Rollback: kill PID, delete this file and its outputs.
"""
import json, os, time, subprocess

OUT = "/var/lib/octopus/state/s1pa-attack/telemetry-02B.jsonl"
CG = "/sys/fs/cgroup/system.slice/octopus-sensorium.service"
INTERVAL = 30
MAX_SAMPLES = 480  # 4h hard bound

def read(p):
    try:
        with open(p) as f:
            return f.read().strip()
    except Exception as e:
        return "ERR:" + type(e).__name__

def cgroup_snapshot():
    keys = ["memory.current", "memory.min", "memory.max", "memory.peak",
            "memory.events", "memory.stat", "memory.pressure", "cpu.pressure",
            "memory.swap.current", "memory.swap.max", "cpu.stat", "io.stat"]
    return {k.replace(".", "_"): read(os.path.join(CG, k)) for k in keys}

def proc_snapshot():
    # main sensorium pid + any transient apply/verify children
    out = {}
    try:
        pids = subprocess.run(["pgrep", "-f", "octopus-(sensorium|apply|verify)"],
                              capture_output=True, text=True, timeout=10).stdout.split()
    except Exception:
        pids = []
    procs = []
    try:
        ps = subprocess.run(["ps", "-eo", "pid,pcpu,pmem,rss,etimes,comm,args", "--sort=-pcpu"],
                            capture_output=True, text=True, timeout=10).stdout.splitlines()
        for line in ps[1:12]:
            procs.append(line)
    except Exception:
        pass
    for pid in set(pids):
        io = read("/proc/%s/io" % pid)
        statm = read("/proc/%s/statm" % pid)
        out[pid] = {"io": io, "statm": statm}
    return {"matched": out, "top": procs}

def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    n = 0
    while n < MAX_SAMPLES:
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "sample": n, "cgroup": cgroup_snapshot(), "procs": proc_snapshot()}
        with open(OUT, "a") as f:
            f.write(json.dumps(rec) + "\n")
        n += 1
        time.sleep(INTERVAL)
    with open(OUT, "a") as f:
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "collector": "b1", "status": "COMPLETED_BOUND_REACHED"}) + "\n")

if __name__ == "__main__":
    main()
