#!/usr/bin/env python3
"""autonomy_audit.py — end-to-end autonomy verification for OCTOPUS on node 138.

Read-only. Prints no credential value. Groups results as PASS / FAIL / UNKNOWN.
"""
import json
import os
import pathlib
import subprocess
import time

HOME = pathlib.Path("/home/ari")
OFN = HOME / "ofn"
STATE = OFN / "state"
NOW = time.time()
results = []


def add(name, ok, detail):
    results.append((("PASS" if ok else ("FAIL" if ok is False else "UNKNOWN")), name, detail))


def sh(cmd, timeout=20):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout)
        return p.returncode, p.stdout.decode("utf-8", "replace").strip()
    except Exception as exc:  # noqa: BLE001
        return 99, "ERR:" + type(exc).__name__


def age_h(path):
    try:
        return round((NOW - path.stat().st_mtime) / 3600.0, 2)
    except OSError:
        return None


print("=" * 78)
print("OCTOPUS AUTONOMY AUDIT  node=138  at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
print("=" * 78)

# ---------------------------------------------------------------- 1. kill switches
ks = [OFN / "state/autonomy/STOP-AUTONOMY", pathlib.Path("/etc/octopus-ops-halt")]
for k in ks:
    add("kill-switch absent (autonomy allowed): " + k.name, not k.exists(),
        "present" if k.exists() else "absent")

# ---------------------------------------------------------------- 2. timers/services
rc, out = sh("systemctl list-timers --all --no-pager --no-legend 2>/dev/null | "
             "grep -iE 'octopus|ofn' | awk '{print $1, $2, $3, $NF}'")
timers = [l for l in out.splitlines() if l.strip()]
add("systemd timers present", bool(timers), "%d timers" % len(timers))
for t in timers:
    print("    timer:", t)

rc, out = sh("systemctl list-units --type=service --all --no-pager --no-legend 2>/dev/null | "
             "grep -iE 'octopus|ofn' | awk '{print $1, $3, $4}'")
svcs = [l for l in out.splitlines() if l.strip()]
add("systemd services present", bool(svcs), "%d units" % len(svcs))
for s in svcs:
    print("    svc:", s)

# ---------------------------------------------------------------- 3. boot survival
rc, out = sh("systemctl is-enabled octopus-autonomy-supervisor.timer 2>&1; "
             "systemctl is-enabled octopus-ops-agent.timer 2>&1; "
             "systemctl is-enabled octopus-coding-worker.timer 2>&1")
print("    enabled-state:", out.replace("\n", " | "))
add("core timers enabled at boot", out.count("enabled") >= 1, out.replace("\n", " | "))

rc, boot = sh("uptime -s 2>/dev/null; who -b 2>/dev/null | head -1")
print("    boot:", boot.replace("\n", " | "))

# ---------------------------------------------------------------- 4. autonomy state
sup = STATE / "autonomy"
if sup.exists():
    files = sorted(sup.glob("*"))
    print("    autonomy files:", ", ".join(f.name for f in files[:18]))
    for name in ("receipts.jsonl", "queue.jsonl", "predictions.jsonl", "supervisor-state.json"):
        p = sup / name
        if p.exists():
            n = sum(1 for _ in p.open(encoding="utf-8", errors="replace"))
            add("autonomy %s present" % name, True, "%d rows, age %.2fh" % (n, age_h(p) or -1))
    st = sup / "supervisor-state.json"
    if st.exists():
        try:
            d = json.loads(st.read_text(encoding="utf-8"))
            print("    supervisor-state:", json.dumps(d)[:300])
        except Exception:
            pass
    rec = sup / "receipts.jsonl"
    if rec.exists():
        tail = rec.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-3:]
        for t in tail:
            print("    last receipt:", t[:220])
        add("supervisor ticked in last 30 min", (age_h(rec) or 999) < 0.5,
            "age %.2fh" % (age_h(rec) or -1))

# ---------------------------------------------------------------- 5. ops-agent
ops = STATE / "ops-agent"
armed = ops / "state/armed.json"
if armed.exists():
    d = json.loads(armed.read_text(encoding="utf-8"))
    add("ops-agent armed", all(bool(v) for v in d.values() if isinstance(v, bool)),
        json.dumps(d)[:200])
    print("    armed:", json.dumps(d)[:300])
orcp = ops / "state/ops-receipts.jsonl"
if orcp.exists():
    add("ops-agent ticked recently", (age_h(orcp) or 999) < 1.0, "age %.2fh" % (age_h(orcp) or -1))

# ---------------------------------------------------------------- 6. coding worker
cw = STATE / "coding-worker"
cr = cw / "state/coding-receipts.jsonl"
if cr.exists():
    add("coding-worker ticked recently", (age_h(cr) or 999) < 2.0, "age %.2fh" % (age_h(cr) or -1))
    tail = cr.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-2:]
    for t in tail:
        print("    cw receipt:", t[:200])

# ---------------------------------------------------------------- 7. paid cognition
rc, out = sh("cd %s/state/api-budget && python3 -c \"import sys;sys.path.insert(0,'.');"
             "import providers;print(providers.candidates());"
             "print({p:providers.health_status(p) for p in providers.provider_ids()})\"" % OFN)
add("paid route has live candidates", "deepseek" in out, out.replace("\n", " "))

# ---------------------------------------------------------------- 8. PC dependency
rc, out = sh("grep -rIl -E '^(/mnt/[a-z]/|F:\\\\|C:\\\\|\\\\\\\\192\\.168\\.)' "
             "%s --include=*.service --include=*.timer --include=*.py --include=*.sh 2>/dev/null | "
             "grep -v -E 'test|docs|__pycache__|preimage|backup' | head -8" % OFN)
add("no PC-path dependency in runtime files", not out.strip(), out.strip() or "none found")

rc, out = sh("systemctl list-units --type=service --all --no-pager --no-legend 2>/dev/null | "
             "grep -iE 'octopus|ofn' | grep -c 'inactive\\|failed'")
print("    non-active octopus/ofn services:", out)

# ---------------------------------------------------------------- 9. witness 182
rc, out = sh("ssh -i /home/ari/.ssh/octopus_mesh_ed25519 -o BatchMode=yes "
             "-o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.0.182 "
             "'systemctl is-active octopus-remote-witness 2>/dev/null || "
             "ls /var/lib/octopus-remote-witness/ | head -5' 2>&1")
add("witness node 182 reachable", "denied" not in out.lower() and "timed out" not in out.lower(),
    out.replace("\n", " ")[:160])

# ---------------------------------------------------------------- 10. resources
rc, out = sh("df -h / /home 2>/dev/null | tail -2; free -m | head -2")
print("    resources:\n      " + out.replace("\n", "\n      "))

# ---------------------------------------------------------------- summary
print()
print("=" * 78)
p = sum(1 for s, _, _ in results if s == "PASS")
f = sum(1 for s, _, _ in results if s == "FAIL")
u = sum(1 for s, _, _ in results if s == "UNKNOWN")
print("SUMMARY  PASS=%d  FAIL=%d  UNKNOWN=%d" % (p, f, u))
for s, n, d in results:
    if s != "PASS":
        print("  %-7s %s -> %s" % (s, n, d))
print("=" * 78)
