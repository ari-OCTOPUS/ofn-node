#!/usr/bin/env python3
"""OCTOPUS ops-agent v1 — node-138 non-TCB autonomous operations executor.

Lane AUTONOMOUS-OPS-BUNDLE-20260913. Standing owner authority: non-TCB
operational categories (directive section 2). Every Class B action follows the
full node-182 remote-witness protocol (proposal -> verdict -> 16-field
validation -> single-use consumption -> frozen literal action -> verification
-> outcome envelope -> outcome verdict). NO local fallback.

NON-TCB by construction: never writes the STABLE supervisor, TCB manifest,
pins, or witness code; deployment actions come ONLY as literal command lists
from the frozen ops_contracts.json; no shell is ever generated.

Stdlib only. Kill-switch: STABLE STOP-AUTONOMY and /etc/octopus-ops-halt are
honored before every phase.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
ROOT = HOME / "ofn" / "state" / "ops-agent"
STABLE_ROOT = HOME / "ofn" / "state" / "autonomy"
CONTRACTS = ROOT / "ops_contracts.json"
BUDGETS = ROOT / "ops_budgets.json"
PINS_FILE = STABLE_ROOT / "witness-pins.json"
STATE = ROOT / "state"
RECEIPTS = STATE / "ops-receipts.jsonl"
GOALS = STATE / "goals.jsonl"
OBS = STATE / "observations.jsonl"
CONSUMPTION = STATE / "witness-consumption.jsonl"
ARMED = STATE / "armed.json"
PENDING = STATE / "pending"          # witness proposals awaiting verdicts
def _stable_kill():
    return STABLE_ROOT / "STOP-AUTONOMY"
HALT = Path("/etc/octopus-ops-halt")
VERSION = "octopus-ops-agent/1.3.0"

_TCB_TARGETS = ("supervisor.py", "tcb-manifest.json", "recovery-contract.json",
                "witness-pins.json", "witness_verifier.py")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def canon(o) -> str:
    return json.dumps(o, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def sha_obj(o) -> str:
    return hashlib.sha256(canon(o).encode()).hexdigest()


def _ts(iso: str) -> float:
    return datetime.fromisoformat(iso).replace(tzinfo=timezone.utc).timestamp() \
        if "+" not in iso and "Z" not in iso else datetime.fromisoformat(
            iso.replace("Z", "+00:00")).timestamp()


def append_jsonl(p: Path, row: dict, hash_field: str, prev_field: str) -> dict:
    prev = None
    if p.exists():
        last = None
        for l in p.read_text(encoding="utf-8").splitlines():
            if l.strip():
                last = l
        prev = json.loads(last).get(hash_field) if last else None
    row = dict(row)
    row[prev_field] = prev
    row[hash_field] = sha_obj({k: v for k, v in row.items() if k != hash_field})
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    return row


def receipt(kind: str, **kw) -> dict:
    return append_jsonl(RECEIPTS, {"schema": "octopus.ops-receipt.v1", "kind": kind,
                                   "agent": VERSION, "at": now_iso(), **kw},
                        hash_field="ops_hash", prev_field="previous_ops_hash")


def read_receipts() -> list:
    if not RECEIPTS.exists():
        return []
    return [json.loads(l) for l in RECEIPTS.read_text(encoding="utf-8").splitlines() if l.strip()]


def verify_own_chain() -> tuple:
    ok, prev, n = True, None, 0
    if not RECEIPTS.exists():
        return True, 0
    for l in RECEIPTS.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        try:
            d = json.loads(l)
        except json.JSONDecodeError:
            return False, n
        n += 1
        if sha_obj({k: v for k, v in d.items() if k != "ops_hash"}) != d.get("ops_hash"):
            ok = False
        if d.get("previous_ops_hash") != prev:
            ok = False
        prev = d.get("ops_hash")
    return ok, n


def killed() -> bool:
    return _stable_kill().exists() or HALT.exists()


def load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------- budgets
def budget_allows(category: str, component: str, now: float | None = None) -> tuple:
    b = load_json(BUDGETS) or {}
    now = now or time.time()
    rows = read_receipts()
    ex = [r for r in rows if r.get("kind") == "OPS_B_EXECUTED"]
    # breaker: same-class failures (execution- or outcome-rejected) or unknown effect
    fails = [r for r in ex
             if (r.get("category") == category
                 or str(r.get("category", "")).startswith(category + "_"))
             and r.get("verified") is False]
    orej = [r for r in rows if r.get("kind") == "OPS_B_OUTCOME_REJECTED"
            and category[-2:] in str(r.get("category", ""))]
    # failures root-caused and fixed (state/failure-signatures.json) stop counting;
    # the signature blacklist itself is append-only and operator-audited
    sigs = load_json(STATE / "failure-signatures.json") or {"signatures": []}
    # OW-8b: honour legacy accidental keys read-only ("RY" was what
    # category[-2:] extracted from "...CANARY"); new signatures use the
    # canonical key.
    _legacy = {"B8": "RY"}.get(category)
    fixed_at = max([sg.get("fixed_at", "") for sg in sigs["signatures"]
                    if sg.get("category") == category
                    or (_legacy and sg.get("category") == _legacy)], default="")

    def counts(r):
        return (not fixed_at) or r.get("at", "") > fixed_at

    n_bad = len([r for r in fails + orej if counts(r)])
    if n_bad >= int(b.get("circuit_breaker_after_same_class_failures", 2)) or \
            any(r.get("outcome") == "UNKNOWN_EFFECT" and counts(r) for r in ex):
        return False, "CIRCUIT_BREAKER_OPEN"
    # mesh-wide: ops + STABLE supervisor class B executions in 24h
    stable = []
    sl = STABLE_ROOT / "receipts.jsonl"
    if sl.exists():
        for l in sl.read_text(encoding="utf-8").splitlines():
            if not l.strip():
                continue
            try:
                stable.append(json.loads(l))
            except json.JSONDecodeError:
                continue
    mesh = [r for r in ex if now - _ts(r["at"]) < 86400] + \
           [r for r in stable if r.get("kind") == "CLASS_B_EXECUTED" and now - _ts(r["at"]) < 86400]
    if len(mesh) >= int(b.get("mesh_wide_24h", 3)):
        return False, "BUDGET_MESH_24H"
    node = [r for r in ex if now - _ts(r["at"]) < 86400]
    if len(node) >= int(b.get("per_node_24h", 2)):
        return False, "BUDGET_NODE_24H"
    comp = [r for r in ex if r.get("component") == component and now - _ts(r["at"]) < 1800]
    if len(comp) >= int(b.get("per_component_30min", 1)):
        return False, "BUDGET_COMPONENT_30MIN"
    return True, "OK"


# ---------------------------------------------------------------- witness client
def witness_pins():
    return load_json(PINS_FILE)


def _ssh_argv(pins: dict, remote_cmd: str) -> list:
    return ["ssh", "-i", pins["ssh_identity"], "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=8", "-o", "StrictHostKeyChecking=yes",
            "root@" + pins["witness_host"], remote_cmd]


def witness_push(pins: dict, name: str, data: bytes) -> tuple:
    argv = _ssh_argv(pins, "cat > " + pins["witness_inbox"] + "/" + name)
    try:
        r = subprocess.run(argv, input=data, capture_output=True, timeout=20)
        return r.returncode == 0, (r.stderr or b"").decode("utf-8", "replace")[:120]
    except subprocess.TimeoutExpired:
        return False, "ssh timeout"


def witness_pull(pins: dict):
    argv = _ssh_argv(pins, "cat " + pins["witness_receipts_path"])
    try:
        r = subprocess.run(argv, capture_output=True, timeout=20)
        if r.returncode != 0:
            return None
        rows = []
        for line in (r.stdout or b"").decode("utf-8", "replace").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    return None
        return rows
    except subprocess.TimeoutExpired:
        return None


def witness_chain_ok(rows: list) -> bool:
    prev = None
    for d in rows:
        body = {k: v for k, v in d.items() if k != "witness_hash"}
        if sha_obj(body) != d.get("witness_hash") or d.get("previous_witness_hash") != prev:
            return False
        prev = d.get("witness_hash")
    return True


def build_proposal(category: str, component: str, action_spec: dict,
                   evidence: dict, pins: dict, timeout_s: int) -> dict:
    env = {"schema": "octopus.remote-witness-envelope.v1",
           "envelope_kind": "proposal",
           "proposal_id": "op-" + uuid.uuid4().hex[:16],
           "producer_authority": "node-138-ops-agent", "producer_node": "138",
           "witness_node": "182", "action_class": "B",
           "target_node": "138", "target_component": component,
           "timeout_s": timeout_s, "created_at": now_iso(), "ttl_s": 1800,
           "replay_nonce": uuid.uuid4().hex,
           "action_contract_hash": sha_obj(action_spec),
           "precondition_hash": sha_obj(evidence),
           "input_hash": sha_obj(evidence),
           "rollback_contract_hash": sha_obj(action_spec.get("rollback", "")),
           "simulation_hash": None,
           "payload": {"claim_type": "ops_category_" + category,
                       "target": component + " on node 138",
                       "intent": "execute", "artifact": evidence}}
    env["checksum"] = sha_obj({k: v for k, v in env.items() if k != "checksum"})
    return env


def validate_verdict(row: dict, pins: dict, exp: dict) -> tuple:
    if row.get("schema") != "octopus.remote-witness-receipt.v1":
        return False, "WITNESS_RECEIPT_INVALID"
    if row.get("verdict") != "APPROVE_ELIGIBLE_CLASS_B":
        return False, "WITNESS_REJECTED"
    if row.get("executable") is not False or row.get("action_authority") != "NONE":
        return False, "WITNESS_RECEIPT_INVALID"
    if (row.get("node_182_identity_evidence") or {}).get("machine_id_sha256") != pins["node182_identity"]:
        return False, "WITNESS_IDENTITY_MISMATCH"
    if row.get("witness_code_hash") != pins["witness_code_sha256"] or \
            row.get("witness_contract_hash") != pins["witness_contract_sha256"]:
        return False, "WITNESS_CONTRACT_DRIFT"
    for f, want in (("proposal_id", exp["proposal_id"]),
                    ("proposal_hash", exp["proposal_hash"]),
                    ("action_contract_hash", exp["action_contract_hash"]),
                    ("precondition_hash", exp["precondition_hash"]),
                    ("input_hash", exp["input_hash"]),
                    ("rollback_contract_hash", exp["rollback_contract_hash"]),
                    ("target_node", exp["target_node"]),
                    ("target_component", exp["target_component"]),
                    ("action_class", "B"), ("timeout_s", exp["timeout_s"]),
                    ("producer_authority", exp["producer_authority"])):
        if row.get(f) != want:
            return False, "WITNESS_HASH_MISMATCH"
    try:
        if _ts(row["timestamp"]) + exp["ttl_s"] < time.time() or \
                _ts(row["timestamp"]) > time.time() + 300:
            return False, "WITNESS_STALE"
    except (KeyError, TypeError, ValueError):
        return False, "WITNESS_RECEIPT_INVALID"
    wh = dict(row)
    stored = wh.pop("witness_hash", None)
    if not stored or sha_obj(wh) != stored:
        return False, "WITNESS_HASH_MISMATCH"
    return True, "OK"


def consumed_hashes() -> set:
    if not CONSUMPTION.exists():
        return set()
    return {json.loads(l).get("verdict_receipt_hash")
            for l in CONSUMPTION.read_text(encoding="utf-8").splitlines() if l.strip()}


def consume_verdict(row: dict, action_id: str, action_receipt) -> dict:
    rows = [json.loads(l) for l in CONSUMPTION.read_text().splitlines()] if CONSUMPTION.exists() else []
    prev = rows[-1].get("consumption_hash") if rows else None
    rec = {"schema": "octopus.witness-consumption.v1",
           "verdict_receipt_hash": row.get("witness_hash"),
           "proposal_hash": row.get("proposal_hash"), "action_id": action_id,
           "consumed_at": now_iso(), "executor_version": VERSION,
           "resulting_action_receipt_hash": action_receipt,
           "previous_consumption_hash": prev}
    rec["consumption_hash"] = sha_obj({k: v for k, v in rec.items() if k != "consumption_hash"})
    with CONSUMPTION.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def build_outcome(env: dict, approval: dict, action_receipt: str,
                  result: dict) -> dict:
    expected = env["payload"]["claim_type"] + " completed with verified effect"
    observed = (expected if result.get("verified")
                else result.get("outcome", "UNKNOWN_EFFECT"))
    row = {"schema": "octopus.remote-witness-outcome-envelope.v1",
           "envelope_kind": "outcome",
           "proposal_id": "oo-" + uuid.uuid4().hex[:12],
           "producer_authority": "node-138-ops-agent", "producer_node": "138",
           "witness_node": "182", "action_class": "B",
           "target_node": "138", "target_component": env.get("target_component"),
           "created_at": now_iso(), "ttl_s": 1800,
           "replay_nonce": uuid.uuid4().hex,
           "proposal_hash": env["checksum"],
           "approval_verdict_hash": approval.get("witness_hash"),
           "action_receipt_hash": action_receipt,
           "expected_effect": expected, "observed_effect": observed,
           "rollback_status": "completed" if result.get("verified") else "pending",
           "before_hash": env["input_hash"],
           "after_hash": sha_obj({"after": result.get("after_state", "unknown")}),
           "unexpected_effects": [] if result.get("verified") else [observed],
           "executor_result": {"exit_codes": result.get("exit_codes", [])},
           "queue_state": result.get("queue_state", "n/a"),
           "timestamp": now_iso()}
    row["checksum"] = sha_obj({k: v for k, v in row.items() if k != "checksum"})
    return row


# ---------------------------------------------------------------- frozen action executor
def run_frozen_action(argv: list, timeout_s: int) -> tuple:
    """Executes ONLY a literal argv from the frozen contract (no shell)."""
    try:
        r = subprocess.run(argv, capture_output=True, timeout=timeout_s)
        return r.returncode, ((r.stdout or b"") + (r.stderr or b"")).decode("utf-8", "replace")[:200]
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"


# ---------------------------------------------------------------- observations
def observe_workers(units: list) -> dict:
    out = {}
    for u in units:
        r = subprocess.run(["systemctl", "is-active", u], capture_output=True, text=True)
        out[u] = (r.stdout or "").strip()
    return out


def observe_supervisor_age() -> float:
    p = STABLE_ROOT / "receipts.jsonl"
    if not p.exists():
        return 1e9
    last = None
    for l in p.read_text(encoding="utf-8").splitlines():
        if l.strip():
            last = l
    if not last:
        return 1e9
    try:
        return time.time() - _ts(json.loads(last)["at"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return 1e9


def record_observation(kind: str, data: dict) -> dict:
    return append_jsonl(OBS, {"schema": "octopus.ops-observation.v1", "at": now_iso(),
                              "kind": kind, "fixture": False, **data},
                        hash_field="obs_hash", prev_field="previous_obs_hash")


def last_observations(kind: str, n: int) -> list:
    if not OBS.exists():
        return []
    rows = [json.loads(l) for l in OBS.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("kind") == kind and not r.get("fixture")]
    return rows[-n:]


def degraded_streak(kind: str, min_n: int, min_span_s: int, predicate) -> tuple:
    obs = last_observations(kind, min_n)
    if len(obs) < min_n or not all(predicate(o) for o in obs):
        return False, obs
    span = _ts(obs[-1]["at"]) - _ts(obs[0]["at"])
    return span >= min_span_s, obs


# ---------------------------------------------------------------- category handlers
def handle_b2_worker_recovery(cat: dict, pins: dict) -> str:
    units = cat["observation"]["units"]
    states = observe_workers(units)
    record_observation("worker_states", {"states": states})
    for unit, st in states.items():
        if st == "active":
            continue
        ok_streak, obs = degraded_streak("worker_states", 3, 600,
                                         lambda o: o.get("states", {}).get(unit) == "failed")
        if not ok_streak:
            continue
        ok_b, why_b = budget_allows("B2", unit)
        if not ok_b:
            receipt("OPS_B_BLOCKED", category="B2", component=unit, reason=why_b)
            return "budget-blocked"
        action_spec = {"commands": [["sudo", "-n", "systemctl", "restart", unit]],
                       "rollback": cat["rollback"], "timeout_s": cat["timeout_s"]}
        evidence = {"observations": [o["at"] for o in obs], "states":
                    [o.get("states", {}).get(unit) for o in obs], "unit": unit}
        return _witnessed_action(
            "B2_OCTOPUS_OWNED_WORKER_RECOVERY", unit, action_spec, evidence, pins,
            {"argv": [["sudo", "-n", "systemctl", "restart", unit]],
             "verify_kind": "is-active:" + unit, "timeout_s": 60})
    return "no-action-needed"


def handle_b3_supervisor_recovery(cat: dict, pins: dict) -> str:
    age = observe_supervisor_age()
    record_observation("supervisor_age", {"age_s": round(age, 1)})
    ok_streak, obs = degraded_streak("supervisor_age", 3, 600, lambda o: o.get("age_s", 0) > 1800)
    if not ok_streak:
        return "no-action-needed"
    ok_b, why_b = budget_allows("B3", "autonomy-supervisor")
    if not ok_b:
        receipt("OPS_B_BLOCKED", category="B3", component="autonomy-supervisor", reason=why_b)
        return "budget-blocked"
    action_spec = {"commands": [["sudo", "-n", "systemctl", "restart",
                                 "octopus-autonomy-supervisor.timer"]],
                   "rollback": cat["rollback"], "timeout_s": cat["timeout_s"]}
    evidence = {"ages": [o.get("age_s") for o in obs], "at": [o["at"] for o in obs]}
    return _witnessed_action(
        "B3_OCTOPUS_OWNED_SUPERVISOR_RECOVERY", "autonomy-supervisor",
        action_spec, evidence, pins,
        {"argv": [["sudo", "-n", "systemctl", "restart",
                   "octopus-autonomy-supervisor.timer"]],
         "verify_kind": "supervisor-age<300", "timeout_s": 60})


def handle_b5_storage(cat: dict, pins: dict) -> str:
    """Whitelist-only cache cleanup. NEVER touches the never_delete list."""
    import fnmatch
    findings = []
    roots = [STABLE_ROOT] + list(Path.home().glob("wt-*"))
    for root in roots:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dp = Path(dirpath)
            for d in list(dirnames):
                if d in ("__pycache__", ".pytest_cache"):
                    findings.append(dp / d)
            for f in filenames:
                if fnmatch.fnmatch(f, "*.pyc"):
                    findings.append(dp / f)
    findings = [f for f in findings if any(
        str(f).startswith(str(hp)) for hp in roots)]
    if not findings:
        return "no-action-needed"
    ok_b, why_b = budget_allows("B5", "storage-cache")
    if not ok_b:
        receipt("OPS_B_BLOCKED", category="B5", component="storage-cache", reason=why_b)
        return "budget-blocked"
    action_spec = {"commands": [["rm", "-rf", str(f)] for f in findings[:20]],
                   "rollback": "caches regenerate (reproducible artifacts only)",
                   "timeout_s": cat["timeout_s"]}
    evidence = {"paths": [str(f) for f in findings[:20]],
                "note": "whitelist-matched reproducible caches only"}
    targets = findings[:20]
    return _witnessed_action("B5_SAFE_STORAGE_MAINTENANCE", "storage-cache",
                             action_spec, evidence, pins,
                             {"argv": [["rm", "-rf", str(f)] for f in targets],
                              "verify_kind": "paths-absent:" + "|".join(str(f) for f in targets),
                              "timeout_s": 30})



# OW-8b (2026-09-15): explicit category keys — never slice a long category
# name again (category[-2:] on "B8_NON_TCB_PATCH_CANARY" produced the accidental
# breaker key "RY"). Legacy short keys stay read-only-honoured in budget_allows.
CANONICAL_CATEGORY = {
    "B8_NON_TCB_PATCH_CANARY": "B8",
    "B5_SAFE_STORAGE_MAINTENANCE": "B5",
    "B2_OCTOPUS_OWNED_WORKER_RECOVERY": "B2",
}


def _verified_by_receipt(req: dict, request: str | None = None) -> bool:
    """True only when a verified receipt binds this request to this artifact.

    New receipts carry the exact request name. Legacy receipts have no request
    field, so they retain the sha-only fallback needed to self-heal old queue
    entries without allowing a mismatched named receipt to retire a request.
    """
    want = str(req.get("target_sha256") or req.get("artifact_sha256") or "")
    if len(want) < 32:
        return False
    try:
        lines = (STATE / "ops-receipts.jsonl").read_text(
            encoding="utf-8").splitlines()[-400:]
    except OSError:
        return False
    for line in reversed(lines):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("kind") != "OPS_B_EXECUTED" or d.get("verified") is not True:
            continue
        receipt_request = d.get("request")
        if receipt_request is not None and request is not None and receipt_request != request:
            continue
        vk = str(d.get("verify_kind", ""))
        if want[:64] and want[:64] in vk:
            return True
    return False


def _retire_executed(src: Path, name: str, category: str) -> None:
    _exec = STATE / "executed"
    _exec.mkdir(parents=True, exist_ok=True)
    dst = _exec / name
    if dst.exists():
        receipt("OPS_B_REQUEST_ALREADY_EXECUTED", category=category,
                request=name, note="already in executed/")
        return
    try:
        os.replace(src, dst)
        receipt("F001_SELF_RETIRE", category=category, request=name,
                note="verified-by-receipt; retired with zero budget spend")
    except OSError as e:
        receipt("RETIRE_FAULT", category=category, request=name, note=str(e)[:120])


def handle_spool_category(category: str, cat: dict, pins: dict, subdir: str) -> str:
    """B4/B6/B8: act only on real request artifacts in the spool."""
    spool = STATE / subdir
    if not spool.exists():
        return "no-action-needed"
    (STATE / "owner-tasks").mkdir(parents=True, exist_ok=True)
    _any_blocked = False          # OW-8: blocked requests disposition, never abort
    for name in sorted(os.listdir(spool)):
        req = load_json(spool / name)
        if not req:
            continue
        target = str(req.get("target", ""))
        # G28-E FIX 2026-09-14: restore the TCB gate that was lost when the dedupe
        # loop was repaired (pre-retire line 488). TCB targets always become owner
        # decisions; they must never reach the witnessed deploy path from here.
        if any(t in target for t in _TCB_TARGETS):
            receipt("CREATE_OWNER_DECISION_TASK", category=category,
                    reason="TCB target requested", request=name)
            os.replace(spool / name, STATE / "owner-tasks" / name)
            return "owner-task-created"
        # FIX 2026-09-14: retire executed requests so the same artifact+target pair
        # cannot re-execute on a later tick and burn another class-B slot (observed:
        # the same B8 request executed at 01:56:08Z and again at 02:34:47Z).
        _exec = STATE / "executed"
        _exec.mkdir(parents=True, exist_ok=True)
        # G28 FIX: scan ALL executed files before deciding. A non-match in the first
        # file must NOT trigger an owner-task transfer. Only a positive match means
        # the request was already executed and should be skipped.
        _already = False
        for _df in _exec.glob("*.json"):
            try:
                _dr = load_json(_df) or {}
            except OSError:
                continue
            if (_dr.get("target") == target
                    and _dr.get("target_sha256") == req.get("target_sha256")):
                receipt("OPS_B_REQUEST_ALREADY_EXECUTED", category=category,
                        request=name, earlier=_df.name)
                _already = True
                break
        if _already:
            continue
        # F-001 LAYER-2 (2026-09-15): self-healing retire. A request whose
        # execution already receipts verified=True removes itself with ZERO
        # budget spend instead of re-fighting its own deployed bytes as
        # STALE_BASE every tick (observed: G8-021 burned the component
        # window for hours after its verified 06:54Z deploy).
        if _verified_by_receipt(req, name):
            _retire_executed(spool / name, name, category)
            continue
        # deploy candidate is the PATCHED artifact; a "backup" key is only the
        # rollback pre-image and is never the deploy source (owner 2026-09-13).
        backup = req.get("patched") or req.get("backup")
        # never overwrite a target that has moved on since this request was built:
        # a stale candidate reports STALE_BASE and keeps its place in the queue.
        want_base = req.get("base_sha256")
        if want_base and Path(target).exists():
            have_base = hashlib.sha256(Path(target).read_bytes()).hexdigest()
            if have_base != want_base:
                receipt("OPS_B_STALE_BASE", category=category, request=name,
                        want=want_base[:16], have=have_base[:16])
        # G22: dependencies must be MET BY EVIDENCE, not by their presence in JSON.
        # A dependency is satisfied only when its target currently holds that
        # expected post hash of that request. Unmet / failed / rolled back / cyclic
        # block, take no action, and leave this request in the queue.
        _deps = req.get("dependencies") or []
        _deps_verified = []
        if _deps:
            _unmet = []
            for _dep in _deps:
                # G29 FIX 2026-09-14: resolve dependency files deterministically:
                # absolute path first, then this spool, then executed/ by name (a
                # retired predecessor). The old CWD-relative resolution could
                # never find a sibling request after it retired to executed/.
                _dp = None
                _cands = ([Path(str(_dep))] if str(_dep).startswith("/")
                          else [spool / str(_dep), _exec / Path(str(_dep)).name])
                for _c in _cands:
                    if _c.exists():
                        _dp = _c
                        break
                if _dp is None:
                    _dr = {}
                else:
                    try:
                        _dr = load_json(_dp) or {}
                    except OSError:
                        _dr = {}
                _dt = _dr.get("target")
                _dw = _dr.get("expected_post_sha256") or _dr.get("target_sha256")
                _ok_dep = bool(_dt and _dw and Path(_dt).exists()
                               and hashlib.sha256(Path(_dt).read_bytes()).hexdigest() == _dw)
                if _ok_dep:
                    _deps_verified.append({"target": _dt, "sha256": _dw})
                else:
                    _unmet.append(str(_dep)[:40])
            if _unmet:
                receipt("OPS_B_DEPENDENCY_UNMET", category=category, request=name,
                        unmet=_unmet[:3])
                continue
        # owner-mission (j): preconditions are ENFORCED here (and stay
        # fail-closed: the request waits in the queue, re-checked every tick)
        _preconds = req.get("preconditions") or []
        _unmet_pc = []
        for _pc in _preconds:
            _pp = Path(str(_pc.get("path", "")))
            _have_pc = (hashlib.sha256(_pp.read_bytes()).hexdigest()
                        if _pp.exists() else None)
            if _have_pc != _pc.get("sha256"):
                _unmet_pc.append({"path": str(_pp)[:60],
                                  "want": str(_pc.get("sha256"))[:16],
                                  "have": (_have_pc or "absent")[:16]})
        if _unmet_pc:
            receipt("OPS_B_PRECONDITION_UNMET", category=category, request=name,
                    unmet=_unmet_pc[:3])
            continue
        if not backup or not Path(backup).exists():
            continue
        component = req.get("component", category)
        # OW-8 FIX (2026-09-15): disposition + continue, never abort the
        # category loop — one blocked request must not starve independent
        # ready requests (runtime-proven: g22-probe unevaluated 34+ min).
        # OW-8b FIX: canonical category key replaces category[-2:].
        ok_b, why_b = budget_allows(CANONICAL_CATEGORY.get(category, category),
                                    component)
        if not ok_b:
            receipt("OPS_B_BLOCKED", category=category, component=component, reason=why_b)
            _any_blocked = True
            continue
        action_spec = {"commands": [["cp", str(Path(backup)), target]],
                       "rollback": req.get("rollback", "restore pre-image"),
                       "timeout_s": cat["timeout_s"]}
        evidence = {"request": name, "deploy_sha256":
                    hashlib.sha256(Path(backup).read_bytes()).hexdigest(),
                    "target": target}

        want = req.get("target_sha256") or hashlib.sha256(
            Path(backup).read_bytes()).hexdigest()
        _tgt_p = Path(target)
        _out = _witnessed_action(category, component, action_spec, evidence, pins,
                                 {"argv": [["cp", str(Path(backup)), target]],
                                  "verify_kind": "sha256:" + target + ":" + want,
                                  "timeout_s": 30,
                                  # PRE-EFFECT freeze: argv pins PATHS, these pin
                                  # the CONTENT that was reviewed and approved
                                  "source_path": str(Path(backup)),
                                  "source_sha256": evidence["deploy_sha256"],
                                  "target_path": target,
                                  "pre_target_sha256":
                                      (hashlib.sha256(_tgt_p.read_bytes()).hexdigest()
                                       if _tgt_p.exists() else None),
                                  "deps_verified": _deps_verified})
        # FIX 2026-09-15: retire ONLY on successful execution. The 2026-09-14
        # version retired unconditionally, which consumed G8 without deploying
        # it (observed: proposal sent at 04:53Z, no OPS_B_EXECUTED, file moved
        # to executed/, glass_runner stayed at the base hash).
        # A request retires only after a successful hand-off/execution. Every
        # witnessed-action return beginning with "witness" is a failure state;
        # witness-unavailable must stay queued for retry and must never enter
        # executed/, where target+sha dedupe would create a false positive.
        if str(_out).startswith(("ok", "executed", "proposal-sent")):
            try:
                os.replace(spool / name, STATE / "executed" / name)
            except OSError:
                receipt("EXECUTE_RETIRE_FAILED", category=category, request=name)
        else:
            receipt("EXECUTE_DEFERRED_NOT_RETIRED", category=category, request=name,
                    witness_result=str(_out)[:60])
        return _out
    return "budget-blocked" if _any_blocked else "no-action-needed"


# ---------------------------------------------------------------- witnessed action core
def _witnessed_action(category: str, component: str, action_spec: dict,
                       evidence: dict, pins: dict, action_record: dict) -> str:
    """The ONLY path to an executing action: witness verdict -> consume ->
    frozen act -> verify -> outcome envelope -> outcome verdict."""
    if killed():
        receipt("OPS_KILL_SWITCH_STOP", note="kill active; no action")
        return "killed"
    env = build_proposal(category, component, action_spec, evidence, pins,
                         action_spec.get("timeout_s", 60))
    (STATE / "proposals").mkdir(parents=True, exist_ok=True)
    (STATE / "proposals" / (env["proposal_id"] + ".json")).write_text(
        json.dumps(env, sort_keys=True) + "\n", encoding="utf-8")
    ok, err = witness_push(pins, env["proposal_id"] + ".json",
                           (canon(env) + "\n").encode())
    if not ok:
        receipt("OPS_B_PAUSED_WITNESS_UNAVAILABLE", category=category, reason=err[:80])
        return "witness-unavailable"
    exp = {"proposal_id": env["proposal_id"], "proposal_hash": env["checksum"],
           "action_contract_hash": env["action_contract_hash"],
           "precondition_hash": env["precondition_hash"],
           "input_hash": env["input_hash"],
           "rollback_contract_hash": env["rollback_contract_hash"],
           "target_node": env["target_node"],
           "target_component": env["target_component"],
           "timeout_s": env["timeout_s"], "ttl_s": env["ttl_s"],
           "producer_authority": env["producer_authority"]}
    (STATE / "pending").mkdir(parents=True, exist_ok=True)
    (PENDING / (env["proposal_id"] + ".json")).write_text(
        json.dumps({"exp": exp, "category": category, "component": component},
                   sort_keys=True) + "\n", encoding="utf-8")
    am = STATE / "proposals" / "action-map"
    am.mkdir(parents=True, exist_ok=True)
    arec = dict(action_record)
    arec["component"] = component
    arec["request"] = evidence.get("request")
    arec["proposal_id"] = env["proposal_id"]
    (am / (env["proposal_id"] + ".json")).write_text(
        json.dumps(arec, sort_keys=True) + "\n", encoding="utf-8")
    receipt("OPS_B_PROPOSAL_SENT", category=category, component=component,
            proposal=env["proposal_id"])
    return "proposal-sent"


def progress_pending(pins: dict) -> str:
    """Advance proposals awaiting verdicts (one per tick; budgets enforced)."""
    if not PENDING.exists():
        return None
    for sub in ("failed", "awaiting-outcome", "closed", "owner-tasks"):
        (STATE / sub).mkdir(parents=True, exist_ok=True)
    for name in sorted(os.listdir(PENDING)):
        d = load_json(PENDING / name)
        if not d:
            continue
        exp, category, component = d["exp"], d["category"], d["component"]
        rows = witness_pull(pins)
        if rows is None:
            receipt("OPS_B_PAUSED_WITNESS_UNAVAILABLE", category=category, reason="pull failed")
            return "witness-unavailable"
        if not witness_chain_ok(rows):
            receipt("OPS_B_WITNESS_CHAIN_INVALID", category=category)
            os.replace(PENDING / name, STATE / "failed" / name)
            return "witness-chain-invalid"
        row = next((r for r in rows if r.get("proposal_id") == exp["proposal_id"]), None)
        if row is None:
            return "still-waiting"
        if row.get("witness_hash") in consumed_hashes():
            receipt("REJECT_REMOTE_WITNESS_REPLAY", category=category)
            os.replace(PENDING / name, STATE / "failed" / name)
            return "witness-replay"
        ok, why = validate_verdict(row, pins, exp)
        if not ok:
            receipt("OPS_B_WITNESS_REJECTED", category=category, reason=why)
            os.replace(PENDING / name, STATE / "failed" / name)
            return "witness-rejected"
        if killed():
            receipt("OPS_KILL_SWITCH_STOP", note="kill active post-verdict; no execution")
            return "killed-post-verdict"
        # execute the category's frozen action for this pending proposal
        result = _execute_pending(category, exp)
        if result.get("outcome") == "BLOCKED_NO_EFFECT":
            receipt("OPS_B_PRE_EFFECT_CYCLE_FAILED", category=category,
                    reason=result.get("reason"))
            os.replace(PENDING / name, STATE / "failed" / name)
            return "pre-effect-blocked"
        consume_verdict(row, exp["proposal_id"], result.get("ops_hash"))
        outcome = build_outcome(load_json(STATE / "proposals" / (exp["proposal_id"] + ".json")),
                                row, result.get("ops_hash") or "", result)
        ok2, err2 = witness_push(pins, outcome["proposal_id"] + ".json",
                                 (canon(outcome) + "\n").encode())
        (STATE / "outcomes").mkdir(parents=True, exist_ok=True)
        (STATE / "outcomes" / (outcome["proposal_id"] + ".json")).write_text(
            json.dumps(outcome, sort_keys=True) + "\n", encoding="utf-8")
        receipt("OPS_B_OUTCOME_SENT", category=category, outcome_proposal=outcome["proposal_id"],
                pushed=ok2)
        os.replace(PENDING / name, STATE / "awaiting-outcome" / name)
        (STATE / "awaiting-outcome" / name).write_text(json.dumps(
            {"exp": exp, "category": category, "component": component,
             "outcome_proposal": outcome["proposal_id"],
             "approval_hash": row["witness_hash"]}, sort_keys=True) + "\n", encoding="utf-8")
        return "outcome-sent"
    return None


def _execute_pending(category: str, exp: dict) -> dict:
    """Runs the recorded FROZEN action for this proposal; verify by frozen kind."""
    m = load_json(STATE / "proposals" / "action-map" / (exp["proposal_id"] + ".json"))
    if not m:
        return receipt("OPS_B_EXECUTED", category=category,
                       component=exp["target_component"], verified=False,
                       outcome="NO_ACTION_MAP", exit_codes=[],
                       request=None, proposal_id=exp["proposal_id"])
    # PRE-EFFECT integrity (owner mission J4): connect the reviewed bytes to the
    # executed bytes. Drift between approval and execution blocks BEFORE any
    # invocation; the target is never written with unreviewed bytes.
    if m.get("source_sha256"):
        _sp = Path(str(m.get("source_path", "")))
        _have_src = (hashlib.sha256(_sp.read_bytes()).hexdigest()
                     if _sp.exists() else None)
        if _have_src != m["source_sha256"]:
            return receipt("OPS_B_PRE_EFFECT_BLOCKED", category=category,
                           component=m.get("component"), reason="SOURCE_DRIFT",
                           source=str(_sp)[:80], want=m["source_sha256"][:16],
                           have=(_have_src or "absent")[:16],
                           outcome="BLOCKED_NO_EFFECT", exit_codes=[])
    if m.get("pre_target_sha256") is not None or "pre_target_sha256" in m:
        _tp = Path(str(m.get("target_path", "")))
        _have_t = (hashlib.sha256(_tp.read_bytes()).hexdigest()
                   if _tp.exists() else None)
        if _have_t != m.get("pre_target_sha256"):
            return receipt("OPS_B_PRE_EFFECT_BLOCKED", category=category,
                           component=m.get("component"), reason="TARGET_DRIFT",
                           target=str(_tp)[:80],
                           outcome="BLOCKED_NO_EFFECT", exit_codes=[])
    for _dv in (m.get("deps_verified") or []):
        _dpt = Path(str(_dv.get("target", "")))
        _have_d = (hashlib.sha256(_dpt.read_bytes()).hexdigest()
                   if _dpt.exists() else None)
        if _have_d != _dv.get("sha256"):
            return receipt("OPS_B_PRE_EFFECT_BLOCKED", category=category,
                           component=m.get("component"), reason="DEPENDENCY_DRIFT",
                           dep=str(_dpt)[:80],
                           outcome="BLOCKED_NO_EFFECT", exit_codes=[])
    raw = m.get("argv", [])
    argvs = raw if (raw and isinstance(raw[0], list)) else ([raw] if raw else [])
    codes = []
    for a in argvs:
        rc, out = run_frozen_action(a, m.get("timeout_s", 60))
        codes.append(rc)
    rc = max(codes) if codes else 1
    vk = m.get("verify_kind", "")
    verified = False
    if rc == 0:
        if vk.startswith("is-active:"):
            unit = vk.split(":", 1)[1]
            verified = subprocess.run(["systemctl", "is-active", unit],
                                      capture_output=True, text=True).stdout.strip() == "active"
        elif vk == "supervisor-age<300":
            verified = observe_supervisor_age() < 300
        elif vk.startswith("paths-absent:"):
            paths = vk.split(":", 1)[1].split("|")
            verified = all(not Path(x).exists() for x in paths)
        elif vk.startswith("sha256:"):
            _, target, want = vk.split(":", 2)
            verified = Path(target).exists() and hashlib.sha256(
                Path(target).read_bytes()).hexdigest() == want
    outcome = "VERIFIED" if verified else ("UNKNOWN_EFFECT" if rc == 124 else "FAILED")
    return receipt("OPS_B_EXECUTED", category=category, component=m["component"],
                   argv=argvs, exit_codes=codes, verified=verified, outcome=outcome,
                   verify_kind=vk, request=m.get("request"),
                   proposal_id=exp["proposal_id"])


def progress_outcomes(pins: dict) -> str:
    d = STATE / "awaiting-outcome"
    if not d.exists():
        return None
    for name in sorted(os.listdir(d)):
        info = load_json(d / name)
        if not info:
            continue
        rows = witness_pull(pins)
        if rows is None:
            return "outcome-pending"
        ov = next((r for r in rows if r.get("proposal_id") == info.get("outcome_proposal")), None)
        if ov is None:
            return "outcome-pending"
        cat = info["category"]
        if ov.get("verdict") in ("OUTCOME_CONFIRMED", "ROLLBACK_CONFIRMED"):
            # F-001 LAYER-1 (2026-09-15): retire the originating canary
            # request BEFORE the closure receipt — a receipt without the
            # file move is how requests stayed queued forever. Failure is
            # its own disposition and does not silently close the cycle.
            _req_name = info.get("request")
            if _req_name:
                _src = STATE / "canary-requests" / str(_req_name)
                if _src.exists():
                    try:
                        os.replace(_src, STATE / "executed" / _src.name)
                    except OSError as _e:
                        receipt("RETIRE_FAULT", category=cat, request=str(_req_name),
                                note=str(_e)[:120])
                        os.replace(d / name, STATE / "failed" / name)
                        return "retire-fault"
            receipt("OPS_B_CYCLE_CLOSED", category=cat, component=info["component"],
                    outcome_verdict=ov.get("verdict"), witness=ov.get("witness_hash", "")[:16])
            os.replace(d / name, STATE / "closed" / name)
            return "cycle-closed"
        receipt("OPS_B_OUTCOME_REJECTED", category=cat, outcome_verdict=ov.get("verdict"),
                note="breaker opens; category paused; no retry")
        os.replace(d / name, STATE / "failed" / name)
        return "outcome-rejected"
    return None


# ---------------------------------------------------------------- goal engine (Class A)
def goal_engine(contracts: dict) -> str:
    """Observe and receipt goals; never invent problems. Healthy => health cycle."""
    findings = []
    workers = observe_workers(contracts["categories"]["B2_OCTOPUS_OWNED_WORKER_RECOVERY"]
                              ["observation"]["units"])
    bad_workers = {u: s for u, s in workers.items() if s == "failed"}
    if bad_workers:
        findings.append({"source": "inactive-service", "detail": bad_workers, "class": "B"})
    age = observe_supervisor_age()
    if age > 1800:
        findings.append({"source": "supervisor-silent", "age_s": round(age, 1), "class": "B"})
    store = STABLE_ROOT.parent / "eti-telemetry" / "node-telemetry.jsonl"
    if store.exists():
        stale = time.time() - store.stat().st_mtime > 900
        if stale:
            findings.append({"source": "store-not-advancing", "class": "B"})
    du = subprocess.run(["df", "-h", "/"], capture_output=True, text=True).stdout
    for line in du.splitlines():
        if line.startswith("/"):
            try:
                pct = int(line.split()[4].replace("%", ""))
                if pct >= 85:
                    findings.append({"source": "disk-pressure", "pct": pct, "class": "B"})
            except (ValueError, IndexError):
                pass
    for f in findings:
        append_jsonl(GOALS, {"schema": "octopus.ops-goal.v1", "at": now_iso(), **f},
                     hash_field="goal_hash", prev_field="previous_goal_hash")
        receipt("GOAL_GENERATED", **f)
    if not findings:
        receipt("STABLE_HEALTH_CYCLE", workers=len(workers),
                supervisor_age_s=round(age, 1), note="nothing needs action")
        return "healthy"
    return "goals-recorded"


# ---------------------------------------------------------------- main tick
def tick() -> int:
    contracts = load_json(CONTRACTS)
    budgets = load_json(BUDGETS)
    pins = witness_pins()
    if contracts is None or budgets is None or pins is None:
        print("FAIL_CLOSED: contracts/budgets/pins missing")
        return 2
    ok, n = verify_own_chain()
    if not ok:
        print(f"FAIL_CLOSED: ops receipt chain broken at {n}")
        return 2
    if killed():
        receipt("OPS_KILL_SWITCH_STOP", note="halted before work")
        return 0
    armed = load_json(ARMED) or {}
    # progress existing witness cycles first (one Class B at a time)
    r1 = progress_pending(pins) if armed.get("any") else None
    r2 = progress_outcomes(pins) if armed.get("any") else None
    busy = r1 in ("outcome-sent", "cycle-closed", "outcome-rejected") or \
        r2 in ("outcome-sent", "cycle-closed", "outcome-rejected")
    # Class A goal engine every tick
    ge = goal_engine(contracts)
    # category handlers (skip if a witness cycle is mid-flight: one at a time)
    results = {"goal_engine": ge, "progress": r1 or r2}
    if not busy:
        cats = contracts["categories"]
        if armed.get("B2"):
            results["B2"] = handle_b2_worker_recovery(cats["B2_OCTOPUS_OWNED_WORKER_RECOVERY"], pins)
        if armed.get("B3"):
            results["B3"] = handle_b3_supervisor_recovery(cats["B3_OCTOPUS_OWNED_SUPERVISOR_RECOVERY"], pins)
        if armed.get("B5"):
            results["B5"] = handle_b5_storage(cats["B5_SAFE_STORAGE_MAINTENANCE"], pins)
        if armed.get("B4"):
            results["B4"] = handle_spool_category("B4_NON_TCB_DEPLOYMENT_ROLLBACK",
                                                 cats["B4_NON_TCB_DEPLOYMENT_ROLLBACK"], pins, "rollback-requests")
        if armed.get("B6"):
            results["B6"] = handle_spool_category("B6_DERIVED_ARTIFACT_REBUILD",
                                                 cats["B6_DERIVED_ARTIFACT_REBUILD"], pins, "rebuild-requests")
        if armed.get("B8"):
            results["B8"] = handle_spool_category("B8_NON_TCB_PATCH_CANARY",
                                                 cats["B8_NON_TCB_PATCH_CANARY"], pins, "canary-requests")
    receipt("OPS_TICK_COMPLETE", **{k: v for k, v in results.items() if v is not None})
    print(json.dumps(results))
    return 0


def main() -> int:
    try:
        return tick()
    except Exception as exc:  # noqa: BLE001
        try:
            receipt("OPS_TICK_ABNORMAL", error=type(exc).__name__, detail=str(exc)[:200])
        except Exception:  # noqa: BLE001, S110
            pass
        print("OPS_TICK_ABNORMAL", type(exc).__name__)
        return 2


if __name__ == "__main__":
    sys.exit(main())
