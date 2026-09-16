"""REQUEST_RECOVERY 2026-09-14 (lane OCTOPUS-COMMANDER-G28-20260914).

Dispositions (per mission S6, after G28+G29 acceptance 22/22 on 8e1c43e8):
- native-A2-G8-PRODUCER-010.json  -> RECOVER to canary-requests/
    base ddee3da4 == live glass_runner bytes; artifact 69c8ec8f verified on stage.
    Dependency re-pinned from the broken CWD-relative 'native-A-B8-DEPLOY-SOURCE-
    008.json' (whose expected_post ee7f021c-era hash can never hold again) to an
    absolute capability pin on the CURRENT executor bytes 8e1c43e8 (which contain
    the B8 prefer-patched + base-verify capability the ordering was about).
- native-A3-W24-BINDER-006.json    -> RECOVER to canary-requests/
    base 00dd4ef3 == live binder bytes; artifact b9c504f8 verified on stage.
    Dependency on native-A2-G8-PRODUCER-010.json kept: G29 now resolves it from
    the spool and, after G8 retires, from executed/; met exactly when
    glass_runner == 69c8ec8f (safe-ordering contract preserved).
- native-B5-MEASURED-RECOVERY-001.json, native-TASK-OPS-BUDGET-CATSCOPE-005.json,
  native-A4-AB-COMPOSITE-011.json -> SUPERSEDE to superseded-tasks/
    their bases (ee7f021c / ddf4aa5a / aa87316c) are dead: live ops_agent moved to
    8e1c43e8 with G22+G28+retire+dedupe+TCB protections these artifacts do not
    carry; deploying them would revert live protections. Their capability deltas
    (B5 measured-recovery predicate, CATSCOPE budget scoping, A/B priority
    ordering) remain OPEN and must be rebuilt as successors on the live base.

untouched: executed/native-A-B8-DEPLOY-SOURCE-008.json,
withdrawn/freedom-TASK-OPS-QUEUE-PRIORITY-009-A-0.json.
All moves receipted into the production ops chain via append_jsonl (no rewrite).
"""
import hashlib
import importlib.util
import json
import os
import pathlib
import sys

OA = "/home/ari/ofn/state/ops-agent/ops_agent.py"
spec = importlib.util.spec_from_file_location("oa_rec", OA)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

STATE = pathlib.Path("/home/ari/ofn/state/ops-agent/state")
OWNER = STATE / "owner-tasks"
SPOOL = STATE / "canary-requests"
SUP = STATE / "superseded-tasks"
DEPEV = STATE / "dep-evidence"

live_sha = hashlib.sha256(pathlib.Path(OA).read_bytes()).hexdigest()
assert live_sha.startswith("8e1c43e8"), "live executor bytes moved: " + live_sha

SPOOL.mkdir(parents=True, exist_ok=True)
SUP.mkdir(parents=True, exist_ok=True)
DEPEV.mkdir(parents=True, exist_ok=True)


def chain_receipt(kind, **kw):
    return m.append_jsonl(
        m.RECEIPTS,
        {"schema": "octopus.ops-receipt.v1", "kind": kind,
         "agent": "octopus-commander-editor/2026-09-14", "at": m.now_iso(), **kw},
        hash_field="ops_hash", prev_field="previous_ops_hash")


# 1) capability pin for the G8 dependency
pin = {"schema": "octopus.dependency-evidence.v1",
       "target": OA,
       "expected_post_sha256": live_sha,
       "pinned_at": m.now_iso(),
       "pinned_by": "octopus-commander-editor/2026-09-14",
       "capability": ("executor holds B8 prefer-patched deploy-source + base "
                      "verify + G22 evidence-enforced dependencies + retire/dedupe "
                      "G28 + TCB owner-gate + G29 dep resolution"),
       "evidence": ("g28-accept-v2 22/22 PASS on 8e1c43e8 (lane "
                    "OCTOPUS-COMMANDER-G28-20260914); supersedes the historical "
                    "expected_post of native-A-B8-DEPLOY-SOURCE-008 which can no "
                    "longer hold byte-equality after later verified fixes"),
       "rollback": "delete this file; the dependent request then blocks "
                   "(OPS_B_DEPENDENCY_UNMET) rather than deploying"}
pin_path = DEPEV / "B8-CAPABILITY-20260914.json"
pin_path.write_text(json.dumps(pin, indent=1, sort_keys=True) + "\n", encoding="utf-8")

moves = []

# 2) G8 producer: re-pin dependency, recover
p = OWNER / "native-A2-G8-PRODUCER-010.json"
req = json.loads(p.read_text(encoding="utf-8"))
assert req["base_sha256"].startswith("ddee3da4")
assert req["artifact_sha256"].startswith("69c8ec8f")
req["dependencies_original"] = req["dependencies"]
req["dependencies"] = [str(pin_path)]
req["recovery_receipt"] = {
    "at": m.now_iso(), "by": "octopus-commander-editor/2026-09-14",
    "from": "owner-tasks (false G28 transfer)", "to": "canary-requests",
    "why": ("non-duplicate, base matches live bytes, artifact verified; dep "
            "re-pinned per G29 after G28 acceptance 22/22"),
    "acceptance": "g28-accept-v2 PASS on 8e1c43e8"}
p.write_text(json.dumps(req, indent=1, sort_keys=True) + "\n", encoding="utf-8")
os.replace(p, SPOOL / p.name)
moves.append(("RECOVER", p.name))

# 3) W24 binder: recover unchanged (G29 resolves its dep after G8 retires)
p = OWNER / "native-A3-W24-BINDER-006.json"
req = json.loads(p.read_text(encoding="utf-8"))
assert req["base_sha256"].startswith("00dd4ef3")
assert req["artifact_sha256"].startswith("b9c504f8")
req["recovery_receipt"] = {
    "at": m.now_iso(), "by": "octopus-commander-editor/2026-09-14",
    "from": "owner-tasks (false G28 transfer)", "to": "canary-requests",
    "why": ("non-duplicate, base matches live bytes, artifact verified; dep on "
            "G8 producer preserved (met when glass_runner==69c8ec8f via G29)"),
    "acceptance": "g28-accept-v2 PASS on 8e1c43e8"}
p.write_text(json.dumps(req, indent=1, sort_keys=True) + "\n", encoding="utf-8")
os.replace(p, SPOOL / p.name)
moves.append(("RECOVER", p.name))

# 4) supersede the dead-base ops_agent chain requests
supersede = {
    "native-B5-MEASURED-RECOVERY-001.json":
        ("base ee7f021c dead (live=8e1c43e8); delta = measured byte recovery "
         "for paths-absent verify — REBUILD as successor on live base"),
    "native-TASK-OPS-BUDGET-CATSCOPE-005.json":
        ("base ddf4aa5a dead (live=8e1c43e8); delta = budget category scoping "
         "— REBUILD as successor on live base"),
    "native-A4-AB-COMPOSITE-011.json":
        ("base aa87316c dead (live=8e1c43e8); delta = module-level _spool_order "
         "priority (G3) — REBUILD as successor on live base"),
}
for name, why in supersede.items():
    p = OWNER / name
    req = json.loads(p.read_text(encoding="utf-8"))
    req["supersede_receipt"] = {
        "at": m.now_iso(), "by": "octopus-commander-editor/2026-09-14",
        "from": "owner-tasks (false G28 transfer)", "to": "superseded-tasks",
        "why": why + "; deploying the stale artifact would revert live G22/G28/"
               "retire/dedupe/TCB protections",
        "acceptance": "g28-accept-v2 PASS on 8e1c43e8"}
    p.write_text(json.dumps(req, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(p, SUP / p.name)
    moves.append(("SUPERSEDE", p.name))

# 5) receipt every move + the pin into the production chain
chain_receipt("OPS_B_DEP_EVIDENCE_PINNED", pin=str(pin_path),
              target=OA, pinned_sha256=live_sha)
for action, name in moves:
    chain_receipt("OPS_B_REQUEST_RECOVERED" if action == "RECOVER"
                  else "OPS_B_REQUEST_SUPERSEDED",
                  request=name, action=action,
                  evidence="E/OCTOPUS-COMMANDER-20260913/REQUEST-RECOVERY-20260914.json")

# 6) verify: chain still valid + final queue shape
ok, n = m.verify_own_chain()
print("chain_verify:", ok, n)
print("canary-requests:", sorted(x.name for x in SPOOL.glob("*.json")))
print("owner-tasks:", sorted(x.name for x in OWNER.glob("*.json")))
print("executed:", sorted(x.name for x in (STATE / "executed").glob("*.json")))
print("superseded-tasks:", sorted(x.name for x in SUP.glob("*.json")))
print("dep-evidence:", sorted(x.name for x in DEPEV.glob("*.json")))
sys.exit(0 if ok else 1)
