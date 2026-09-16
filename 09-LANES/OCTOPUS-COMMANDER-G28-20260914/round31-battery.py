"""ROUND31 battery - runs INSIDE the kernel fence (uid nobody, scratch root).
Sections: L = ledger integrity through the REAL tick gate; B = B5 measurement
completeness (v2d counterexample vs v3c); D = decision consumer (full path,
negatives, crash boundary, tick wiring); G = queue-DAG shuffle (edges beat
filenames). Only the witness boundary is simulated."""
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import time

FXROOT = pathlib.Path(os.environ["FXROOT"])
TRIO = str(FXROOT / "trio_ops_agent.py")            # v3c db03333d
V2D = str(FXROOT / "v2d_ops_agent")                 # preimage a85db3b0
LIVE = str(FXROOT / "live_ops_agent.py")            # 109e68c0 copy
REQDIR = FXROOT / "requests"                        # real queue copies
PASS, FAIL = [], []
PINS = {"node182_identity": "f" * 64, "witness_code_sha256": "c" * 64,
        "witness_contract_sha256": "d" * 64}
_now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

# pin home battery-wide (belt; the fence is the real boundary)
_home = pathlib.Path(tempfile.mkdtemp(dir=str(FXROOT)))
pathlib.Path.home = classmethod(lambda cls, _h=_home: _h)


def check(name, ok, detail=""):
    print("  %-5s %-62s %s" % ("PASS" if ok else "FAIL", name, detail))
    (PASS if ok else FAIL).append(name)


def load_oa(artifact, budget=None):
    nm = "oa_" + hashlib.sha256((artifact + str(time.time())).encode()).hexdigest()[:8]
    if artifact.endswith(".py"):
        spec = importlib.util.spec_from_file_location(nm, artifact)
    else:
        spec = importlib.util.spec_from_file_location(
            nm, artifact, loader=importlib.machinery.SourceFileLoader(nm, artifact))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    _base = pathlib.Path(tempfile.mkdtemp(dir=str(FXROOT)))
    m.ROOT = _base / "ops-agent"      # nest: ROOT.parent is per-fixture
    m.STATE = m.ROOT / "state"
    m.RECEIPTS = m.STATE / "ops-receipts.jsonl"
    m.GOALS = m.STATE / "goals.jsonl"
    m.OBS = m.STATE / "observations.jsonl"
    m.CONSUMPTION = m.STATE / "witness-consumption.jsonl"
    m.ARMED = m.STATE / "armed.json"
    m.PENDING = m.STATE / "pending"
    m.CONTRACTS = m.ROOT / "ops_contracts.json"
    m.BUDGETS = m.ROOT / "ops_budgets.json"
    m.STABLE_ROOT = m.ROOT / "stable"
    m.PINS_FILE = m.ROOT / "witness-pins.json"
    m.STATE.mkdir(parents=True, exist_ok=True)
    m.STABLE_ROOT.mkdir(parents=True, exist_ok=True)
    m.BUDGETS.write_text(json.dumps(budget or {
        "mesh_wide_24h": 99, "per_node_24h": 99, "per_component_30min": 99,
        "circuit_breaker_after_same_class_failures": 99}), encoding="utf-8")
    m.PINS_FILE.write_text(json.dumps({"k": 1}), encoding="utf-8")
    m.CONTRACTS.write_text(json.dumps({"categories": {
        "B2_OCTOPUS_OWNED_WORKER_RECOVERY": {"observation": {"units": []}},
        "B3_OCTOPUS_OWNED_SUPERVISOR_RECOVERY": {"timeout_s": 30},
        "B4_NON_TCB_DEPLOYMENT_ROLLBACK": {"timeout_s": 30},
        "B5_SAFE_STORAGE_MAINTENANCE": {"timeout_s": 30},
        "B6_DERIVED_ARTIFACT_REBUILD": {"timeout_s": 30},
        "B8_NON_TCB_PATCH_CANARY": {"timeout_s": 30}}}), encoding="utf-8")
    m.ARMED.write_text(json.dumps({"B2": True, "B3": True, "B4": True,
                                   "B5": True, "B6": True, "B8": True,
                                   "any": True}), encoding="utf-8")
    m.witness_push = lambda pins, name, data: (True, "fx")
    m.witness_pull = lambda pins: []
    m.observe_workers = lambda units: {u: "active" for u in units}
    m.observe_supervisor_age = lambda: 10.0
    return m


def witness_rows(m):
    rows = []
    for name in (m.STATE / "pending").glob("*.json"):
        d = json.loads(name.read_text(encoding="utf-8"))
        exp = d["exp"]
        row = {"schema": "octopus.remote-witness-receipt.v1",
               "verdict": "APPROVE_ELIGIBLE_CLASS_B", "executable": False,
               "action_authority": "NONE",
               "node_182_identity_evidence": {"machine_id_sha256": "f" * 64},
               "witness_code_hash": "c" * 64, "witness_contract_hash": "d" * 64,
               "action_class": "B", "timestamp": m.now_iso(),
               "previous_witness_hash": None}
        row.update({k: exp[k] for k in ("proposal_id", "proposal_hash",
                                        "action_contract_hash",
                                        "precondition_hash", "input_hash",
                                        "rollback_contract_hash", "target_node",
                                        "target_component", "timeout_s",
                                        "producer_authority")})
        row["witness_hash"] = m.sha_obj(row)
        rows.append(row)
    return rows


def approve_pending(m):
    rows = witness_rows(m)
    m.witness_pull = lambda pins: rows
    return m.progress_pending(PINS)


def b8_request(m, name="r.json"):
    sp = m.STATE / "canary-requests"
    sp.mkdir(parents=True, exist_ok=True)
    tgt = m.ROOT / "t.py"
    tgt.write_text("OLD", encoding="utf-8")
    p = m.ROOT / "p.py"
    p.write_text("NEW", encoding="utf-8")
    (sp / name).write_text(json.dumps(
        {"target": str(tgt), "target_sha256": hashlib.sha256(b"NEW").hexdigest(),
         "patched": str(p), "component": "c"}), encoding="utf-8")
    return tgt


def b5_fixture(m, n=3, kb=1024):
    for i in range(n):
        d = m.STABLE_ROOT / ("pkg%d/__pycache__" % i)
        d.mkdir(parents=True, exist_ok=True)
        (d / "x.pyc").write_bytes(b"Z" * kb)


# ---------------- L: ledger integrity through the REAL tick ----------------
m = load_oa(TRIO)
b8_request(m)
rc = m.tick()
kinds = [r.get("kind") for r in m.read_receipts()]
check("L1 healthy ledger + free capacity -> admission passes",
      rc == 0 and "OPS_B_PROPOSAL_SENT" in kinds, "rc=%s" % rc)

m = load_oa(TRIO)
b8_request(m)
with m.RECEIPTS.open("a", encoding="utf-8") as f:
    f.write('{"torn-tail...')
rc = m.tick()
check("L2 torn ledger row -> whole tick FAIL_CLOSED (rc=2)",
      rc == 2, "rc=%s" % rc)

m = load_oa(TRIO)
b8_request(m)
m.append_jsonl(m.RECEIPTS, {"schema": "octopus.ops-receipt.v1",
                            "kind": "OPS_B_EXECUTED", "category": "B8_X",
                            "verified": True, "component": "c",
                            "at": _now + "+00:00"},
               hash_field="ops_hash", prev_field="previous_ops_hash")
lines = m.RECEIPTS.read_text(encoding="utf-8").splitlines()
lines[0] = lines[0].replace("OPS_B_EXECUTED", "OPS_B_TAMPERED")
m.RECEIPTS.write_text("\n".join(lines) + "\n", encoding="utf-8")
rc = m.tick()
check("L3 tampered row (chain mismatch) -> tick FAIL_CLOSED",
      rc == 2, "rc=%s" % rc)

m = load_oa(TRIO)
b8_request(m)
m.append_jsonl(m.RECEIPTS, {"schema": "octopus.ops-receipt.v1",
                            "kind": "NOT_A_REAL_KIND", "junk": True,
                            "at": _now + "+00:00"},
              hash_field="ops_hash", prev_field="previous_ops_hash")
rc = m.tick()
kinds = [r.get("kind") for r in m.read_receipts()]
check("L4 valid-JSON invalid-schema (chain intact) -> tick proceeds, "
      "grants nothing", rc == 0 and "OPS_B_PROPOSAL_SENT" in kinds
      and kinds.count("NOT_A_REAL_KIND") == 1, "rc=%s" % rc)

m = load_oa(TRIO, budget={"mesh_wide_24h": 99, "per_node_24h": 99,
                          "per_component_30min": 99,
                          "circuit_breaker_after_same_class_failures": 1})
m.append_jsonl(m.RECEIPTS, {"schema": "octopus.ops-receipt.v1",
                            "kind": "OPS_B_EXECUTED", "category": "B8_X",
                            "verified": False, "component": "c",
                            "at": _now + "+00:00"},
               hash_field="ops_hash", prev_field="previous_ops_hash")
# bit-rot the COUNTED fail row itself into a torn tail
lines = m.RECEIPTS.read_text(encoding="utf-8").splitlines()
lines[-1] = lines[-1][: len(lines[-1]) // 2]
m.RECEIPTS.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
ok_direct = m.budget_allows("B8_X", "c")[0]
rc_tick = m.tick()
check("L5 a rotted execution row can NEVER relax authority: budget_allows "
      "alone would ALLOW (dangerous primitive) but the runtime tick "
      "fail-closes first",
      ok_direct is True and rc_tick == 2,
      "direct=%s tick=%s" % (ok_direct, rc_tick))

# ---------------- B: B5 completeness ----------------
def b5_cycle(artifact, blocker=None):
    m = load_oa(artifact)
    b5_fixture(m)
    r1 = m.handle_b5_storage({"timeout_s": 30}, {})
    if r1 != "proposal-sent":
        return r1, None, m
    if blocker:
        blocker(m)
    r2 = approve_pending(m)
    ex = [x for x in m.read_receipts() if x.get("kind") == "OPS_B_EXECUTED"]
    return r1, (r2, ex[-1] if ex else {}), m


def block_unmoved(m):
    for i in range(3):
        os.chmod(m.STABLE_ROOT / ("pkg%d" % i), 0o500)   # mv fails: no move
    os.chmod(m.STABLE_ROOT / "pkg1/__pycache__", 0o000)  # after-read blocked


r1, res, _ = b5_cycle(V2D, blocker=block_unmoved)
ex = res[1] if res else {}
check("B-CE v2d: NOTHING moved + unreadable-after -> FALSE VERIFIED "
      "(rglob silently counts the dir as zero)",
      res is not None and ex.get("verified") is True
      and ex.get("bytes_freed", 0) > 0,
      "verified=%s freed=%s" % (ex.get("verified"), ex.get("bytes_freed")))
r1, res, m = b5_cycle(TRIO, blocker=block_unmoved)
ex = res[1] if res else {}
check("B v3c: same scenario -> MEASUREMENT_INCOMPLETE, NOT verified, "
      "lower-bound reported",
      res is not None and ex.get("verified") is False
      and ex.get("measurement_complete") is False
      and ex.get("targets_unreadable_after", 0) >= 1
      and "LOWER BOUND" in str(ex.get("outcome_detail", "")),
      "verified=%s unreadable=%s" % (ex.get("verified"),
                                     ex.get("targets_unreadable_after")))
for i in range(3):
    os.chmod(m.STABLE_ROOT / ("pkg%d" % i), 0o755)

r1, res, _ = b5_cycle(TRIO)
ex = res[1] if res else {}
check("B v3c all-moved + complete -> VERIFIED with per-target report",
      res is not None and ex.get("verified") is True
      and ex.get("targets_moved") == 3
      and ex.get("measurement_complete") is True
      and ex.get("bytes_freed", 0) == ex.get("bytes_before"),
      "moved=%s freed=%s" % (ex.get("targets_moved"), ex.get("bytes_freed")))


def partial_block(m):
    os.chmod(m.STABLE_ROOT / "pkg2", 0o500)  # one mv fails, dirs measurable


r1, res, _ = b5_cycle(TRIO, blocker=partial_block)
ex = res[1] if res else {}
check("B v3c partial REAL effect, fully measured -> VERIFIED + failed-count",
      res is not None and ex.get("verified") is True
      and ex.get("targets_move_failed") == 1,
      "failed=%s freed=%s" % (ex.get("targets_move_failed"),
                              ex.get("bytes_freed")))

m = load_oa(TRIO)
b5_fixture(m)
os.chmod(m.STABLE_ROOT / "pkg1/__pycache__", 0o000)
r1 = m.handle_b5_storage({"timeout_s": 30}, {})
check("B v3c before-error -> NO proposal, explicit disposition",
      r1 == "measurement-incomplete"
      and any(x.get("kind") == "B5_MEASUREMENT_INCOMPLETE"
              for x in m.read_receipts()), "r1=%s" % r1)
os.chmod(m.STABLE_ROOT / "pkg1/__pycache__", 0o755)

r1, res, m = b5_cycle(TRIO)
# regeneration: caches reappear at an original path after the move
(m.STABLE_ROOT / "pkg0/__pycache__").mkdir(parents=True, exist_ok=True)
(m.STABLE_ROOT / "pkg0/__pycache__/new.pyc").write_bytes(b"R" * 512)
ex2 = res[1] if res else {}
check("B v3c regeneration after move -> still VERIFIED (witness=quarantine)",
      res is not None and ex2.get("verified") is True
      and ex2.get("targets_moved") == 3,
      "moved=%s after=%s" % (ex2.get("targets_moved"), ex2.get("bytes_after")))
# frozen-argv replay: sources gone -> honest FAILED, no fake freed
am = list((m.STATE / "proposals/action-map").glob("*.json"))[0]
doc = json.loads(am.read_text(encoding="utf-8"))
codes = []
for a in doc["argv"]:
    rc2, _ = m.run_frozen_action(a, 30)
    codes.append(rc2)
check("B v3c frozen-argv replay -> moves fail, nothing fake-freed",
      any(c != 0 for c in codes), "codes=%s" % codes)

# ---------------- D: decision consumer ----------------
def od_of(m):
    od = m.ROOT.parent / "owner_dialogue"   # production: ROOT=state/ops-agent
    od.mkdir(parents=True, exist_ok=True)
    return od


def task_row(tid, sha, state="awaiting_ack", created="2026-09-14T10:00:00Z"):
    return {"task_id": tid, "payload_sha256": sha, "state": state,
            "created_at": created, "scope": "internal-inert",
            "resume_action": "clear_awaiting"}


def decision_row(bound, verdict="ACK_SEEN", at="2026-09-14T10:05:00Z",
                 src="deadbeef" * 8):
    return {"schema": "owner_decision.v1", "at": at, "verdict": verdict,
            "bound_request_payload_sha256": bound,
            "source_text_sha256": src}


X = "a" * 64
m = load_oa(TRIO)
od = od_of(m)
(od / "decision_tasks.json").write_text(json.dumps(
    {"tasks": [task_row("TASK-INERT-1", X)]}), encoding="utf-8")
(od / "owner_decision.v1.jsonl").write_text(
    json.dumps(decision_row(X)) + "\n", encoding="utf-8")
r = m.consume_decisions()
tasks = json.loads((od / "decision_tasks.json").read_text(encoding="utf-8"))
cons = [json.loads(l) for l in
        (od / "decision_consumption.jsonl").read_text(encoding="utf-8").splitlines()]
check("D happy: valid ACK_SEEN resumes EXACTLY that task + receipts",
      r == "consumed" and tasks["tasks"][0]["state"] == "resumed"
      and any(c["kind"] == "DECISION_CONSUMED" for c in cons)
      and any(x.get("kind") == "DECISION_CONSUMED"
              for x in m.read_receipts()),
      "state=%s" % tasks["tasks"][0]["state"])
r2 = m.consume_decisions()
tasks = json.loads((od / "decision_tasks.json").read_text(encoding="utf-8"))
cons2 = [json.loads(l) for l in
         (od / "decision_consumption.jsonl").read_text(encoding="utf-8").splitlines()]
check("D replay: idempotent NO-OP (task behavior, not just a cursor)",
      r2 == "idle" and tasks["tasks"][0]["state"] == "resumed"
      and sum(1 for c in cons2 if c["kind"] == "DECISION_CONSUMED") == 1)

m = load_oa(TRIO)
od = od_of(m)
(od / "decision_tasks.json").write_text(json.dumps(
    {"tasks": [task_row("TASK-STALE", X)]}), encoding="utf-8")
(od / "owner_decision.v1.jsonl").write_text(json.dumps(
    decision_row(X, at="2026-09-13T00:00:00Z")) + "\n", encoding="utf-8")
m.consume_decisions()
tasks = json.loads((od / "decision_tasks.json").read_text(encoding="utf-8"))
check("D stale decision (older than task) -> NOT auto-executed",
      tasks["tasks"][0]["state"] == "awaiting_ack")

m = load_oa(TRIO)
od = od_of(m)
(od / "decision_tasks.json").write_text(json.dumps(
    {"tasks": [task_row("TASK-1", X)]}), encoding="utf-8")
(od / "owner_decision.v1.jsonl").write_text(json.dumps(
    decision_row("b" * 64)) + "\n", encoding="utf-8")   # other request
m.consume_decisions()
tasks = json.loads((od / "decision_tasks.json").read_text(encoding="utf-8"))
check("D decision bound to ANOTHER request -> NO_TASK, task untouched, "
      "no card re-pended",
      tasks["tasks"][0]["state"] == "awaiting_ack")

m = load_oa(TRIO)
od = od_of(m)
(od / "decision_tasks.json").write_text(json.dumps(
    {"tasks": [task_row("TASK-V", X)]}), encoding="utf-8")
(od / "owner_decision.v1.jsonl").write_text(json.dumps(
    decision_row(X, verdict="REJECT_AMBIGUOUS")) + "\n", encoding="utf-8")
m.consume_decisions()
tasks = json.loads((od / "decision_tasks.json").read_text(encoding="utf-8"))
check("D non-ACK verdict -> IGNORED (ACK_SEEN is not approval; seeing != "
      "choosing)", tasks["tasks"][0]["state"] == "awaiting_ack")

m = load_oa(TRIO)
od = od_of(m)
(od / "decision_tasks.json").write_text(json.dumps(
    {"tasks": [task_row("TASK-DONE", X, state="terminal:done")]}),
    encoding="utf-8")
(od / "owner_decision.v1.jsonl").write_text(json.dumps(
    decision_row(X)) + "\n", encoding="utf-8")
m.consume_decisions()
check("D already-finished task -> TASK_NOT_WAITING, no resurrection",
      json.loads((od / "decision_tasks.json").read_text(encoding="utf-8"))
      ["tasks"][0]["state"] == "terminal:done")

m = load_oa(TRIO)
od = od_of(m)
(od / "decision_tasks.json").write_text(json.dumps(
    {"tasks": [task_row("TASK-CRASH", X)]}), encoding="utf-8")
# crash AFTER task-state write, BEFORE consumption record: state=resumed,
# no consumption row yet
t = json.loads((od / "decision_tasks.json").read_text(encoding="utf-8"))
t["tasks"][0]["state"] = "resumed"
(od / "decision_tasks.json").write_text(json.dumps(t), encoding="utf-8")
(od / "owner_decision.v1.jsonl").write_text(json.dumps(
    decision_row(X)) + "\n", encoding="utf-8")
m.consume_decisions()
cons = [json.loads(l) for l in
        (od / "decision_consumption.jsonl").read_text(encoding="utf-8").splitlines()]
check("D crash boundary (state written, receipt lost) -> replay records "
      "NOT_WAITING, still exactly one resume",
      any(c["kind"] == "DECISION_TASK_NOT_WAITING" for c in cons))

# tick wiring: the consumer runs inside the existing tick
m = load_oa(TRIO)
od = od_of(m)
(od / "decision_tasks.json").write_text(json.dumps(
    {"tasks": [task_row("TASK-TICK", X)]}), encoding="utf-8")
(od / "owner_decision.v1.jsonl").write_text(json.dumps(
    decision_row(X)) + "\n", encoding="utf-8")
rc = m.tick()
tickrow = [x for x in m.read_receipts() if x.get("kind") == "OPS_TICK_COMPLETE"]
tasks = json.loads((od / "decision_tasks.json").read_text(encoding="utf-8"))
check("D tick wiring: decisions consumed inside the existing tick",
      rc == 0 and tasks["tasks"][0]["state"] == "resumed"
      and tickrow and tickrow[-1].get("decisions") == "consumed")

# ---------------- G: DAG shuffle (edges beat filenames) ----------------
m = load_oa(TRIO)
sp = m.STATE / "canary-requests"
sp.mkdir(parents=True)
g8 = json.loads((REQDIR / "native-A2-G8-PRODUCER-010.json").read_text(encoding="utf-8"))
w24 = json.loads((REQDIR / "native-A3-W24-BINDER-006.json").read_text(encoding="utf-8"))
trio = json.loads((REQDIR / "native-Z-SUCCESSOR-TRIO-001.json").read_text(encoding="utf-8"))
g30 = json.loads((REQDIR / "native-G30-STAGE-GUARD-WIRING-001.json").read_text(encoding="utf-8"))
# G8's pin: point at a FIXTURE dep-evidence matching the real executor bytes
pin = m.ROOT / "dep-evidence"
pin.mkdir()
(pin / "PIN.json").write_text(json.dumps(
    {"target": "/home/ari/ofn/state/ops-agent/ops_agent.py",
     "expected_post_sha256": hashlib.sha256(
         pathlib.Path(LIVE).read_bytes()).hexdigest()}), encoding="utf-8")
g8["dependencies"] = [str(pin / "PIN.json")]
for req, art in ((g8, "art_glass.py"), (w24, "art_binder.py"),
                 (trio, "art_trio.py"), (g30, "art_worker.py")):
    src = pathlib.Path(req["patched"])
    cp = FXROOT / art
    if cp.exists():
        req["patched"] = str(cp)
# TRIO renamed to sort FIRST; W24/G8 keep their names so the name-edges stay
(sp / "aaa-trio.json").write_text(json.dumps(trio), encoding="utf-8")
(sp / "native-A2-G8-PRODUCER-010.json").write_text(json.dumps(g8), encoding="utf-8")
(sp / "native-A3-W24-BINDER-006.json").write_text(json.dumps(w24), encoding="utf-8")
(sp / "native-G30-STAGE-GUARD-WIRING-001.json").write_text(json.dumps(g30),
                                                           encoding="utf-8")
r = m.handle_spool_category("B8", {"timeout_s": 30}, PINS, "canary-requests")
check("G-a with G8 present+admissible: G8 wins by PRIORITY; TRIO untouched",
      r == "proposal-sent"
      and (m.STATE / "executed/native-A2-G8-PRODUCER-010.json").exists()
      and (sp / "aaa-trio.json").exists(), "r=%s" % r)

# G-b: TRIO alone (sorts FIRST inevitably) with its W24 prerequisite
# EXECUTED-but-rolled-back (binder bytes drifted): the edge must block it
m2 = load_oa(TRIO)
sp2 = m2.STATE / "canary-requests"
sp2.mkdir(parents=True)
ex2 = m2.STATE / "executed"
ex2.mkdir(parents=True)
(sp2 / "aaa-trio.json").write_text(json.dumps(trio), encoding="utf-8")
(ex2 / "native-A3-W24-BINDER-006.json").write_text(json.dumps(
    {"target": "/home/ari/ofn/ofn/agents/go_b3_owner_bind.py",
     "expected_post_sha256": w24["expected_post_sha256"]}),
    encoding="utf-8")     # real binder is 00dd4ef3, not b9c504f8 -> drifted
r2 = m2.handle_spool_category("B8", {"timeout_s": 30}, PINS, "canary-requests")
kinds2 = [x.get("kind") for x in m2.read_receipts()]
check("G-b TRIO first + prerequisite ROLLED BACK -> edge blocks (no jump)",
      r2 in ("no-action-needed", "budget-blocked")
      and (sp2 / "aaa-trio.json").exists()
      and "OPS_B_DEPENDENCY_UNMET" in kinds2, "r2=%s" % r2)

# G-c: prerequisite file simply absent -> unresolvable edge still blocks
m3 = load_oa(TRIO)
sp3 = m3.STATE / "canary-requests"
sp3.mkdir(parents=True)
(sp3 / "aaa-trio.json").write_text(json.dumps(trio), encoding="utf-8")
r3 = m3.handle_spool_category("B8", {"timeout_s": 30}, PINS, "canary-requests")
kinds3 = [x.get("kind") for x in m3.read_receipts()]
check("G-c prerequisite absent -> UNMET, TRIO stays queued (fail-closed)",
      r3 == "no-action-needed" and "OPS_B_DEPENDENCY_UNMET" in kinds3)

print()
print("ROUND31_BATTERY:", "PASS" if not FAIL else "FAIL -> " + ", ".join(FAIL))
sys.exit(0 if not FAIL else 1)
