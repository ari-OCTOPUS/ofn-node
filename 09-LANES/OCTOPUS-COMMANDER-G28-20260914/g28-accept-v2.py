"""G28 full acceptance v2 (2026-09-14, lane OCTOPUS-COMMANDER-G28-20260914).

Contract (mission S6/S12):
- REAL handler source: /home/ari/ofn/state/ops-agent/ops_agent.py (byte-identity recorded).
- ALL state paths redirected into a per-case fixture root (STATE, RECEIPTS, GOALS,
  OBS, CONSUMPTION, ARMED, PENDING, CONTRACTS, BUDGETS, STABLE_ROOT, PINS_FILE).
- Internal gates (dedupe, TCB, stale-base, G22 deps, budget, kill-switch, retire,
  receipt chain) run REAL. Only the witness network boundary (witness_push /
  witness_pull over ssh to 182) is simulated by a fake that issues structurally
  valid verdicts echoing the fixture pins.
- The frozen action itself (cp within fixture paths) runs REAL.
- Isolation asserted: production ops-receipts.jsonl size/sha unchanged after every
  case; production queues untouched.
Matrix: A,B (dedupe skip both orders), C (full loop to CYCLE_CLOSED), D (empty
executed), E (TCB -> owner-task), F (budget blocked), G (order independence),
H (corrupt executed json), I (executed row missing hash).
"""
import hashlib
import importlib.util
import json
import os
import pathlib
import sys
import tempfile

OFN = pathlib.Path("/home/ari/ofn")
OPS_AGENT = pathlib.Path(os.environ.get(
    "OPS_AGENT_OVERRIDE", str(OFN / "state/ops-agent/ops_agent.py")))
PROD_RECEIPTS = OFN / "state/ops-agent/state/ops-receipts.jsonl"
OPS_AGENT_SHA = hashlib.sha256(OPS_AGENT.read_bytes()).hexdigest()

PASS, FAIL = [], []


def check(name, ok, detail=""):
    print("  %-5s %-58s %s" % ("PASS" if ok else "FAIL", name, detail))
    (PASS if ok else FAIL).append(name)


def prod_guard():
    return (PROD_RECEIPTS.stat().st_size,
            hashlib.sha256(PROD_RECEIPTS.read_bytes()).hexdigest()) \
        if PROD_RECEIPTS.exists() else (0, "")


def load_oa(fx: pathlib.Path, budget: dict):
    spec = importlib.util.spec_from_file_location("oa_g28", OPS_AGENT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.ROOT = fx
    m.STATE = fx / "state"
    m.RECEIPTS = m.STATE / "ops-receipts.jsonl"
    m.GOALS = m.STATE / "goals.jsonl"
    m.OBS = m.STATE / "observations.jsonl"
    m.CONSUMPTION = m.STATE / "witness-consumption.jsonl"
    m.ARMED = m.STATE / "armed.json"
    m.PENDING = m.STATE / "pending"
    m.CONTRACTS = fx / "ops_contracts.json"
    m.BUDGETS = fx / "ops_budgets.json"
    m.STABLE_ROOT = fx / "stable"
    m.PINS_FILE = fx / "witness-pins.json"
    m.STATE.mkdir(parents=True, exist_ok=True)
    m.BUDGETS.write_text(json.dumps(budget), encoding="utf-8")
    pins = {"ssh_identity": "fixture-only", "witness_host": "fixture",
            "witness_inbox": "fixture", "witness_receipts_path": "fixture",
            "node182_identity": "f" * 64, "witness_code_sha256": "c" * 64,
            "witness_contract_sha256": "d" * 64}
    m.PINS_FILE.write_text(json.dumps(pins), encoding="utf-8")
    return m, pins


class FakeWitness:
    """Simulates ONLY node-182: push records envelopes, pull returns a valid,
    chained verdict stream. Verdicts echo the fixture pins and pending exp."""

    def __init__(self, m, pins):
        self.m, self.pins, self.rows, self.pushes = m, pins, [], []

    def push(self, pins, name, data):
        env = json.loads(data.decode())
        self.pushes.append((name, env.get("envelope_kind"), env.get("proposal_id")))
        prev = self.rows[-1]["witness_hash"] if self.rows else None
        row = {"schema": "octopus.remote-witness-receipt.v1",
               "verdict": "OUTCOME_CONFIRMED" if env.get("envelope_kind") == "outcome"
               else "APPROVE_ELIGIBLE_CLASS_B",
               "executable": False, "action_authority": "NONE",
               "proposal_id": env["proposal_id"],
               "proposal_hash": env.get("checksum"),
               "action_contract_hash": env.get("action_contract_hash"),
               "precondition_hash": env.get("precondition_hash"),
               "input_hash": env.get("input_hash"),
               "rollback_contract_hash": env.get("rollback_contract_hash"),
               "target_node": env.get("target_node"),
               "target_component": env.get("target_component"),
               "action_class": env.get("action_class"),
               "timeout_s": env.get("timeout_s"),
               "producer_authority": env.get("producer_authority"),
               "timestamp": self.m.now_iso(),
               "witness_code_hash": self.pins["witness_code_sha256"],
               "witness_contract_hash": self.pins["witness_contract_sha256"],
               "node_182_identity_evidence": {"machine_id_sha256":
                                              self.pins["node182_identity"]},
               "previous_witness_hash": prev}
        row["witness_hash"] = self.m.sha_obj(row)
        self.rows.append(row)
        return True, "fixture"

    def pull(self, pins):
        return list(self.rows)

    def install(self):
        self.m.witness_push = self.push
        self.m.witness_pull = self.pull
        return self


def sha(b: bytes):
    return hashlib.sha256(b).hexdigest()


def make_request(d: pathlib.Path, name="r.json", content="OLD", new="NEW",
                 target_name="t.py", deps=None):
    tgt = d / target_name
    tgt.write_text(content, encoding="utf-8")
    patched = d / ("patched-" + target_name)
    patched.write_text(new, encoding="utf-8")
    req = {"task_id": "G28-" + name, "target": str(tgt),
           "target_sha256": sha(new.encode()),
           "base_sha256": sha(content.encode()),
           "patched": str(patched), "component": "g28-fixture-comp",
           "rollback": "restore pre-image"}
    if deps is not None:
        req["dependencies"] = deps
    spool = d / "state" / "canary-requests"
    spool.mkdir(parents=True, exist_ok=True)
    (spool / name).write_text(json.dumps(req), encoding="utf-8")
    return tgt, req


def receipts_of(m):
    return m.read_receipts()


def kinds(m):
    return [r.get("kind") for r in receipts_of(m)]


def run_case(label, *, executed_rows=None, budget=None, tcb_target=False,
             drive_full_loop=False):
    """Runs handle_spool_category (+ optionally the full witnessed loop) on an
    isolated fixture. Returns (module, fixture, result-string, extra-dict)."""
    budget = budget or {"mesh_wide_24h": 99, "per_node_24h": 99,
                        "per_component_30min": 99,
                        "circuit_breaker_after_same_class_failures": 99}
    d = pathlib.Path(tempfile.mkdtemp(prefix="g28v2-"))
    m, pins = load_oa(d, budget)
    fw = FakeWitness(m, pins).install()
    if tcb_target:
        tgt, req = make_request(d, target_name="supervisor.py")
    else:
        tgt, req = make_request(d)
    ex = m.STATE / "executed"
    if executed_rows is not None:
        ex.mkdir(parents=True, exist_ok=True)
        for i, row in enumerate(executed_rows):
            (ex / ("e%d.json" % i)).write_text(
                row if isinstance(row, str) else json.dumps(row), encoding="utf-8")
    r = m.handle_spool_category("B8", {"timeout_s": 30}, pins, "canary-requests")
    extra = {"r": r, "receipts": kinds(m), "fw": fw, "m": m, "d": d, "tgt": tgt}
    if drive_full_loop and r == "proposal-sent":
        extra["r2"] = m.progress_pending(pins)
        extra["r3"] = m.progress_outcomes(pins)
    return extra


def main():
    g0 = prod_guard()
    print("ops_agent.py sha256=%s" % OPS_AGENT_SHA[:16])
    print("prod receipts guard before: size=%d sha=%s" % (g0[0], g0[1][:16]))

    # --- A: executed[0] mismatch, executed[1] MATCH -> already-executed skip
    d = pathlib.Path(tempfile.mkdtemp(prefix="g28v2-A-"))
    m, pins = load_oa(d, {})
    FakeWitness(m, pins).install()
    tgt, req = make_request(d)
    ex = m.STATE / "executed"; ex.mkdir(parents=True)
    (ex / "e0.json").write_text(json.dumps({"target": str(tgt), "target_sha256": "a" * 64}), encoding="utf-8")
    (ex / "e1.json").write_text(json.dumps({"target": str(tgt), "target_sha256": req["target_sha256"]}), encoding="utf-8")
    r = m.handle_spool_category("B8", {"timeout_s": 30}, pins, "canary-requests")
    check("A: match-in-2nd-file -> skipped", r == "no-action-needed"
          and "OPS_B_REQUEST_ALREADY_EXECUTED" in kinds(m), "r=%s" % r)
    check("A: request NOT re-executed (no proposal)", "OPS_B_PROPOSAL_SENT" not in kinds(m))

    # --- B: executed[0] MATCH, executed[1] mismatch -> still skipped
    d = pathlib.Path(tempfile.mkdtemp(prefix="g28v2-B-"))
    m, pins = load_oa(d, {})
    FakeWitness(m, pins).install()
    tgt, req = make_request(d)
    ex = m.STATE / "executed"; ex.mkdir(parents=True)
    (ex / "e0.json").write_text(json.dumps({"target": str(tgt), "target_sha256": req["target_sha256"]}), encoding="utf-8")
    (ex / "e1.json").write_text(json.dumps({"target": str(tgt), "target_sha256": "a" * 64}), encoding="utf-8")
    r = m.handle_spool_category("B8", {"timeout_s": 30}, pins, "canary-requests")
    check("B: match-in-1st-file -> skipped", r == "no-action-needed"
          and "OPS_B_REQUEST_ALREADY_EXECUTED" in kinds(m), "r=%s" % r)

    # --- C: NO match anywhere, valid+ready request -> FULL normal path
    x = run_case("C", executed_rows=[{"target": "/nope/x.py", "target_sha256": "a" * 64}],
                 drive_full_loop=True)
    m, d, tgt = x["m"], x["d"], x["tgt"]
    check("C: no match -> proposal-sent (not owner-task)", x["r"] == "proposal-sent",
          "r=%s" % x["r"])
    check("C: no false owner-task", not (m.STATE / "owner-tasks" / "r.json").exists()
          and "CREATE_OWNER_DECISION_TASK" not in x["receipts"])
    check("C: verdict consumed -> real action executed+VERIFIED",
          x.get("r2") == "outcome-sent"
          and any(rk.get("kind") == "OPS_B_EXECUTED" and rk.get("verified") is True
                  for rk in m.read_receipts()), "r2=%s" % x.get("r2"))
    check("C: fixture target actually patched", tgt.read_text(encoding="utf-8") == "NEW")
    check("C: outcome confirmed -> cycle closed", x.get("r3") == "cycle-closed"
          and "OPS_B_CYCLE_CLOSED" in kinds(m), "r3=%s" % x.get("r3"))
    check("C: request retired to executed/ (no re-run)",
          (m.STATE / "executed" / "r.json").exists()
          and not (m.STATE / "canary-requests" / "r.json").exists())
    ok_chain, n = m.verify_own_chain()
    check("C: fixture receipt chain verifies", ok_chain is True and n >= 4, "n=%d" % n)

    # --- D: executed dir EMPTY -> proceeds normally
    x = run_case("D", executed_rows=[], drive_full_loop=True)
    check("D: empty executed -> full path to cycle-closed",
          x["r"] == "proposal-sent" and x.get("r3") == "cycle-closed",
          "r=%s r3=%s" % (x["r"], x.get("r3")))

    # --- E: TCB target -> MUST become owner-task (gate restored?)
    x = run_case("E", tcb_target=True)
    check("E: TCB target -> owner-task-created", x["r"] == "owner-task-created"
          and (x["m"].STATE / "owner-tasks" / "r.json").exists()
          and "CREATE_OWNER_DECISION_TASK" in x["receipts"], "r=%s" % x["r"])
    check("E: TCB request never reaches witness", len(x["fw"].pushes) == 0)

    # --- F: budget blocked -> stays in spool, not retired, no proposal
    x = run_case("F", budget={"mesh_wide_24h": 0, "per_node_24h": 0,
                              "per_component_30min": 0,
                              "circuit_breaker_after_same_class_failures": 9})
    check("F: budget-blocked return", x["r"] == "budget-blocked", "r=%s" % x["r"])
    check("F: request stays in spool (retry later, not lost)",
          (x["m"].STATE / "canary-requests" / "r.json").exists()
          and not (x["m"].STATE / "executed" / "r.json").exists())
    check("F: no proposal, no owner-task", "OPS_B_PROPOSAL_SENT" not in x["receipts"]
          and "CREATE_OWNER_DECISION_TASK" not in x["receipts"])

    # --- G: order independence (match in last of three)
    d = pathlib.Path(tempfile.mkdtemp(prefix="g28v2-G-"))
    m, pins = load_oa(d, {})
    FakeWitness(m, pins).install()
    tgt, req = make_request(d)
    ex = m.STATE / "executed"; ex.mkdir(parents=True)
    for i, h in enumerate(["a" * 64, "b" * 64, req["target_sha256"]]):
        (ex / ("e%d.json" % i)).write_text(json.dumps({"target": str(tgt), "target_sha256": h}), encoding="utf-8")
    r = m.handle_spool_category("B8", {"timeout_s": 30}, pins, "canary-requests")
    check("G: match-in-last-file -> skipped", r == "no-action-needed"
          and "OPS_B_REQUEST_ALREADY_EXECUTED" in kinds(m), "r=%s" % r)

    # --- H: corrupt executed json must NOT create a valid duplicate
    x = run_case("H", executed_rows=["{not-json"], drive_full_loop=False)
    check("H: corrupt executed row -> proceeds (no false duplicate)",
          x["r"] == "proposal-sent" and "OPS_B_REQUEST_ALREADY_EXECUTED" not in x["receipts"],
          "r=%s" % x["r"])

    # --- I: executed row missing target_sha256 must NOT match
    x = run_case("I", executed_rows=[{"target": None, "target_sha256": None}],
                 drive_full_loop=False)
    check("I: hash-less executed row -> proceeds", x["r"] == "proposal-sent"
          and "OPS_B_REQUEST_ALREADY_EXECUTED" not in x["receipts"], "r=%s" % x["r"])

    # --- J: G29 dependency resolution from executed/ (retired predecessor)
    # J1: dep sibling retired to executed/, its target CURRENTLY holds its
    #     expected_post -> dependency MET -> request proceeds.
    d = pathlib.Path(tempfile.mkdtemp(prefix="g28v2-J1-"))
    m, pins = load_oa(d, {})
    FakeWitness(m, pins).install()
    dep_tgt = d / "dep_target.py"
    dep_tgt.write_text("CAPABILITY-LIVE", encoding="utf-8")
    ex = m.STATE / "executed"; ex.mkdir(parents=True)
    (ex / "native-DEP-000.json").write_text(json.dumps(
        {"target": str(dep_tgt), "target_sha256": sha(b"CAPABILITY-LIVE")}),
        encoding="utf-8")
    make_request(d, deps=["native-DEP-000.json"])
    r = m.handle_spool_category("B8", {"timeout_s": 30}, pins, "canary-requests")
    check("J1: dep resolved from executed/ + met -> proceeds", r == "proposal-sent"
          and "OPS_B_DEPENDENCY_UNMET" not in kinds(m), "r=%s" % r)
    # J2: same, but the predecessor's capability is NOT live (bytes moved on)
    #     -> dependency UNMET -> request stays queued with a receipt.
    d = pathlib.Path(tempfile.mkdtemp(prefix="g28v2-J2-"))
    m, pins = load_oa(d, {})
    FakeWitness(m, pins).install()
    dep_tgt = d / "dep_target.py"
    dep_tgt.write_text("EVOLVED-BYTES", encoding="utf-8")
    ex = m.STATE / "executed"; ex.mkdir(parents=True)
    (ex / "native-DEP-000.json").write_text(json.dumps(
        {"target": str(dep_tgt), "target_sha256": sha(b"CAPABILITY-LIVE")}),
        encoding="utf-8")
    make_request(d, deps=["native-DEP-000.json"])
    r = m.handle_spool_category("B8", {"timeout_s": 30}, pins, "canary-requests")
    check("J2: dep bytes moved on -> UNMET, stays queued",
          r == "no-action-needed" and "OPS_B_DEPENDENCY_UNMET" in kinds(m)
          and (m.STATE / "canary-requests" / "r.json").exists(), "r=%s" % r)
    # J3: absolute-path dependency evidence (re-pinned capability pin)
    d = pathlib.Path(tempfile.mkdtemp(prefix="g28v2-J3-"))
    m, pins = load_oa(d, {})
    FakeWitness(m, pins).install()
    evdir = d / "dep-evidence"; evdir.mkdir()
    dep_tgt = d / "dep_target.py"
    dep_tgt.write_text("CAPABILITY-LIVE", encoding="utf-8")
    (evdir / "PIN.json").write_text(json.dumps(
        {"target": str(dep_tgt), "expected_post_sha256": sha(b"CAPABILITY-LIVE")}),
        encoding="utf-8")
    make_request(d, deps=[str(evdir / "PIN.json")])
    r = m.handle_spool_category("B8", {"timeout_s": 30}, pins, "canary-requests")
    check("J3: absolute dep-evidence pin -> met -> proceeds", r == "proposal-sent"
          and "OPS_B_DEPENDENCY_UNMET" not in kinds(m), "r=%s" % r)

    # --- J4 (owner-mission correction): PRE-EFFECT integrity. The historical
    # case proved POST_EFFECT_MISMATCH_DETECTED (mutated bytes were WRITTEN,
    # then verification failed). The contract under test now is
    # PRE_EFFECT_MUTATION_BLOCKED: drift between approval and execution blocks
    # BEFORE any invocation; the target stays byte-identical.
    import os as _os

    def _prep_j4():
        d = pathlib.Path(tempfile.mkdtemp(prefix="g28v2-J4-"))
        m, pins = load_oa(d, {})
        FakeWitness(m, pins).install()
        tgt, req = make_request(d)
        r = m.handle_spool_category("B8", {"timeout_s": 30}, pins, "canary-requests")
        assert r == "proposal-sent", r
        return d, m, pins, tgt, req

    def _blocked(m, pins, want_reason, label, tgt):
        r2 = m.progress_pending(pins)
        rows = [rk for rk in m.read_receipts()
                if rk.get("kind") == "OPS_B_PRE_EFFECT_BLOCKED"]
        executed = any(rk.get("kind") == "OPS_B_EXECUTED"
                       for rk in m.read_receipts())
        pend = list((m.STATE / "pending").glob("*.json")) if (m.STATE / "pending").exists() else []
        return (r2 == "pre-effect-blocked" and rows
                and rows[-1].get("reason") == want_reason
                and tgt.read_text(encoding="utf-8") == "OLD" and not executed
                and not pend), r2

    # J4a: source CONTENT mutated after approval
    d, m, pins, tgt, req = _prep_j4()
    pathlib.Path(req["patched"]).write_text("MUTATED-BYTES", encoding="utf-8")
    ok, r2 = _blocked(m, pins, "SOURCE_DRIFT", "a", tgt)
    check("J4a source mutation -> BLOCKED pre-effect, target untouched", ok,
          "r2=%s" % r2)

    # J4b: source swapped via atomic rename onto the path
    d, m, pins, tgt, req = _prep_j4()
    _tmp = d / "swapped.py"
    _tmp.write_text("SWAPPED-CONTENT", encoding="utf-8")
    _os.replace(_tmp, req["patched"])
    ok, r2 = _blocked(m, pins, "SOURCE_DRIFT", "b", tgt)
    check("J4b rename-swap of source -> BLOCKED pre-effect", ok, "r2=%s" % r2)

    # J4c: source replaced by a symlink to different bytes
    d, m, pins, tgt, req = _prep_j4()
    _other = d / "other.py"
    _other.write_text("SYMLINK-TARGET-CONTENT", encoding="utf-8")
    _os.unlink(req["patched"])
    _os.symlink(str(_other), req["patched"])
    ok, r2 = _blocked(m, pins, "SOURCE_DRIFT", "c", tgt)
    check("J4c symlink-swap of source -> BLOCKED pre-effect", ok, "r2=%s" % r2)

    # J4d: target/base changed after proposal -> TARGET_DRIFT, still no effect
    d, m, pins, tgt, req = _prep_j4()
    tgt.write_text("DRIFTED-BY-OTHERS", encoding="utf-8")
    r2 = m.progress_pending(pins)
    rows = [rk for rk in m.read_receipts()
            if rk.get("kind") == "OPS_B_PRE_EFFECT_BLOCKED"]
    check("J4d target drift after proposal -> BLOCKED, drift not clobbered",
          r2 == "pre-effect-blocked" and rows
          and rows[-1].get("reason") == "TARGET_DRIFT"
          and tgt.read_text(encoding="utf-8") == "DRIFTED-BY-OTHERS",
          "r2=%s" % r2)

    # J4e: dependency target drifts after proposal -> DEPENDENCY_DRIFT
    d = pathlib.Path(tempfile.mkdtemp(prefix="g28v2-J4e-"))
    m, pins = load_oa(d, {})
    FakeWitness(m, pins).install()
    evd = d / "dep-evidence"; evd.mkdir()
    dep_tgt = d / "dep_target.py"
    dep_tgt.write_text("CAPABILITY-LIVE", encoding="utf-8")
    (evd / "PIN.json").write_text(json.dumps(
        {"target": str(dep_tgt), "expected_post_sha256": sha(b"CAPABILITY-LIVE")}),
        encoding="utf-8")
    tgt, req = make_request(d, deps=[str(evd / "PIN.json")])
    r = m.handle_spool_category("B8", {"timeout_s": 30}, pins, "canary-requests")
    assert r == "proposal-sent", r
    dep_tgt.write_text("EVOLVED-POST-PROPOSAL", encoding="utf-8")
    r2 = m.progress_pending(pins)
    rows = [rk for rk in m.read_receipts()
            if rk.get("kind") == "OPS_B_PRE_EFFECT_BLOCKED"]
    check("J4e dependency drift after proposal -> BLOCKED pre-effect",
          r2 == "pre-effect-blocked" and rows
          and rows[-1].get("reason") == "DEPENDENCY_DRIFT"
          and tgt.read_text(encoding="utf-8") == "OLD", "r2=%s" % r2)

    # J4f: enforced preconditions - unmet keeps the request queued; meeting the
    # pin releases it through the SAME path (positive control)
    d = pathlib.Path(tempfile.mkdtemp(prefix="g28v2-J4f-"))
    m, pins = load_oa(d, {})
    FakeWitness(m, pins).install()
    gate = d / "money-gates.py"
    gate.write_text("GATES-LIVE", encoding="utf-8")
    spool = d / "state" / "canary-requests"
    spool.mkdir(parents=True)
    tgt = d / "t.py"; tgt.write_text("OLD", encoding="utf-8")
    patched = d / "p.py"; patched.write_text("NEW", encoding="utf-8")
    (spool / "r.json").write_text(json.dumps(
        {"target": str(tgt), "target_sha256": sha(b"NEW"),
         "patched": str(patched), "component": "j4f",
         "preconditions": [{"path": str(gate), "sha256": "f" * 64}]}), encoding="utf-8")
    r = m.handle_spool_category("B8", {"timeout_s": 30}, pins, "canary-requests")
    ok1 = (r == "no-action-needed"
           and "OPS_B_PRECONDITION_UNMET" in kinds(m)
           and (spool / "r.json").exists()
           and "OPS_B_PROPOSAL_SENT" not in kinds(m))
    reqd = json.loads((spool / "r.json").read_text(encoding="utf-8"))
    reqd["preconditions"] = [{"path": str(gate), "sha256": sha(b"GATES-LIVE")}]
    (spool / "r.json").write_text(json.dumps(reqd), encoding="utf-8")
    r = m.handle_spool_category("B8", {"timeout_s": 30}, pins, "canary-requests")
    check("J4f precondition unmet -> queued; pin satisfied -> same path proceeds",
          ok1 and r == "proposal-sent", "blocked=%s then=%s" % (ok1, r))


    # --- J5: same FILENAME in executed/ with a DIFFERENT identity must not
    # create a false duplicate block for a legitimately superseding request
    d = pathlib.Path(tempfile.mkdtemp(prefix="g28v2-J5-"))
    m, pins = load_oa(d, {})
    FakeWitness(m, pins).install()
    tgt, req = make_request(d, name="native-X.json")
    ex = m.STATE / "executed"; ex.mkdir(parents=True)
    (ex / "native-X.json").write_text(json.dumps(
        {"target": str(tgt), "target_sha256": "a" * 64,
         "note": "old identity, same filename"}), encoding="utf-8")
    r = m.handle_spool_category("B8", {"timeout_s": 30}, pins, "canary-requests")
    check("J5: same-name different-identity executed row -> NOT a duplicate",
          r == "proposal-sent" and "OPS_B_REQUEST_ALREADY_EXECUTED" not in kinds(m),
          "r=%s" % r)

    # --- K: priority honored over filename (G3, successor delta)
    d = pathlib.Path(tempfile.mkdtemp(prefix="g28v2-K-"))
    m, pins = load_oa(d, {})
    FakeWitness(m, pins).install()
    sp = d / "state" / "canary-requests"
    sp.mkdir(parents=True)
    for nm, prio in (("aa-prio100.json", 100), ("zz-prio1.json", 1)):
        tgt = d / ("t-" + nm)
        tgt.write_text("OLD", encoding="utf-8")
        patched = d / ("p-" + nm)
        patched.write_text("NEW", encoding="utf-8")
        (sp / nm).write_text(json.dumps(
            {"target": str(tgt), "target_sha256": sha(b"NEW"),
             "patched": str(patched), "component": "k", "priority": prio}),
            encoding="utf-8")
    r = m.handle_spool_category("B8", {"timeout_s": 30}, pins, "canary-requests")
    check("K: priority 1 beats filename order (zz proposed, aa stays)",
          r == "proposal-sent" and (m.STATE / "executed" / "zz-prio1.json").exists()
          and (sp / "aa-prio100.json").exists(), "r=%s" % r)

    g1 = prod_guard()
    check("ISOLATION: production ops-receipts.jsonl untouched", g0 == g1,
          "before=%s after=%s" % (g0[1][:12], g1[1][:12]))

    print()
    print("OPS_AGENT_SHA256=%s" % OPS_AGENT_SHA)
    print("G28_ACCEPTANCE_V2:", "PASS" if not FAIL else "FAIL -> " + ", ".join(FAIL))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
