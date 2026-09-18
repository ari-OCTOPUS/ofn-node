#!/usr/bin/env python3
"""BRAIN-WIRING-SCAN gatherer (read-only, node 138)."""
import collections
import glob
import json
import os
import pathlib
import subprocess
import time

R = pathlib.Path("/home/ari/ofn")
OUT = {}


def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              timeout=60).stdout
    except Exception as e:  # noqa: BLE001
        return "ERR:%s" % e


print("== 1. SERVICES (ExecStart) ==")
raw = sh("systemctl list-units --type=service --all --no-pager --plain | awk '{print $1, $3, $4}'")
uni = {}
for line in raw.splitlines():
    p = line.split()
    if p and p[0].startswith(("octopus", "ofn", "capability", "nats")):
        uni[p[0]] = p[1] if len(p) > 1 else "?"
print(json.dumps(uni, indent=0)[:1400])

print("\n== 2. EXECSTART (what each live unit actually runs) ==")
ex = {}
for name in sorted(uni):
    if uni[name] != "active":
        continue
    out = sh("systemctl show -p ExecStart --value %s" % name)
    paths = [w for w in out.replace(";", " ").split() if w.startswith("/")]
    ex[name] = paths[0] if paths else "?"
print(json.dumps(ex, indent=0)[:1600])

print("\n== 3. BRAIN/BUDGET LEDGER ==")
led = R / "state/api-budget/budget-ledger.jsonl"
prov = collections.Counter()
models = collections.Counter()
cost = collections.Counter()
rows = 0
if led.exists():
    for ln in led.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        rows += 1
        if d.get("kind") == "reserve":
            prov[str(d.get("provider"))] += 1
            models[str(d.get("model"))] += 1
        if d.get("kind") == "settle":
            cost[str(d.get("provider") or "?")] += float(d.get("cost_usd") or 0)
print("ledger_rows", rows)
print("providers", prov.most_common(8))
print("models", models.most_common(8))
print("cost_by_provider", [(k, round(v, 4)) for k, v in cost.most_common(8)])

print("\n== 4. DECISION-CODE INVENTORY ==")
mods = {
    "ops_agent(state)": "state/ops-agent/ops_agent.py",
    "cognition_factory": "state/cognition/cognition_factory.py",
    "deep_scan_tick": "state/deep-scan/deep_scan_tick.py",
    "glass_runner": "ofn/agents/glass_runner.py",
    "owner_reply": "state/revenue-drive/owner_reply.py",
    "owner_ask": "state/revenue-drive/owner_ask.py",
    "money_tools": "state/revenue-drive/money_tools.py",
    "money_executor": "state/revenue-drive/money_executor.py",
    "revenue_state": "state/revenue-drive/revenue_state.py",
    "action_executor": "state/revenue-drive/action_executor.py",
    "proposal_intake": "state/revenue-drive/proposal_intake.py",
    "lead_enrich": "state/revenue-drive/lead_enrich.py",
    "b2b_discovery": "ofn/agents/b2b_discovery.py",
    "imap_listener": "ofn/agents/imap_listener.py",
    "reply_alert": "state/revenue-drive/reply_alert.py",
    "scheduler": "state/fleet-scheduler",
    "self_model": "state/self-model",
    "coding_worker": "state/coding-worker",
    "api_budget": "state/api-budget/api_budget.py",
}
inv = {}
for k, p in mods.items():
    fp = R / p
    if fp.is_file():
        inv[k] = {"path": p, "lines": len(fp.read_text(errors="replace").splitlines()),
                  "mtime": time.strftime("%m-%dT%H:%M", time.gmtime(fp.stat().st_mtime))}
    elif fp.is_dir():
        n = len(list(fp.rglob("*")))
        inv[k] = {"path": p + "/", "files": n,
                  "mtime": time.strftime("%m-%dT%H:%M", time.gmtime(fp.stat().st_mtime))}
    else:
        inv[k] = {"path": p, "MISSING": True}
print(json.dumps(inv, indent=0)[:2000])

print("\n== 5. WIRING PROBES (who reads / who writes) ==")
probes = {
    "v_account_last_call": "painting.sqlite view use",
    "painting_call_log": "call-log table consumers",
    "AUTO_DISCOVERY_TAG": "discovery tag consumers",
    "sakana-fugu": "default provider",
    "local-insufficient": "local tier route",
    "OUTBOUND-EFFECTS": "outbound effects db",
}
for needle in ("v_account_last_call", "painting_call_log", "AUTO_DISCOVERY_TAG",
               "sakana-fugu", "local-insufficient", "outbound-effects"):
    out = sh("grep -rl --include='*.py' --include='*.sh' '%s' %s 2>/dev/null | grep -v __pycache__ | wc -l" % (needle, R))
    files = sh("grep -rl --include='*.py' '%s' %s 2>/dev/null | grep -v __pycache__ | head -4" % (needle, R)).strip().replace("\n", ", ")
    print("  %-22s consumers=%s  %s" % (needle, out.strip(), files[:150]))

print("\n== 6. STATE TIER (which modules are alive) ==")
for d in sorted((R / "state").iterdir()):
    if d.is_dir():
        m = max((f.stat().st_mtime for f in d.rglob("*") if f.is_file()), default=0)
        print("  %-18s last_write=%s" % (d.name, time.strftime("%m-%dT%H:%M", time.gmtime(m)) if m else "-"))
