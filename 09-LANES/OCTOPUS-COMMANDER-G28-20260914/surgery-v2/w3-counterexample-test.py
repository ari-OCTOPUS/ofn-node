"""W3 counterexample test: delayed task registration after a valid decision.
Reproduces the exact scenario the reviewer measured, then proves the fix.
Runs entirely in fixture (load_oa from the battery harness pattern)."""
import hashlib
import importlib.machinery
import importlib.util
import json
import pathlib
import sys
import tempfile

sys.path.insert(0, "/tmp")
V3D = ("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/"
       "ops_agent.py.trio-v3d-9e157b4d")       # the BUGGY version
W3V2 = ("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/"
        "ops_agent.py")                         # the FIXED version

X = "a" * 64
DECISION = {"schema": "octopus.owner_decision.v1", "at": "2026-09-14T10:05:00Z",
            "verdict": "ACK_SEEN", "bound_request_payload_sha256": X,
            "source_text_sha256": "deadbeef" * 8}
TASK = {"task_id": "DELAYED-TASK", "payload_sha256": X,
        "state": "awaiting_ack", "created_at": "2026-09-14T10:00:00Z",
        "scope": "internal-inert", "resume_action": "unpark_existing_internal_task"}


def load(artifact):
    _base = pathlib.Path(tempfile.mkdtemp(prefix="w3ce-"))
    nm = "oa_" + hashlib.sha256(artifact.encode()).hexdigest()[:8]
    spec = importlib.util.spec_from_file_location(
        nm, artifact,
        loader=importlib.machinery.SourceFileLoader(nm, artifact))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.ROOT = _base / "ops-agent"
    m.STATE = m.ROOT / "state"
    m.RECEIPTS = m.STATE / "ops-receipts.jsonl"
    m.STABLE_ROOT = m.ROOT / "autonomy"
    m.PINS_FILE = m.ROOT / "pins.json"
    m.BUDGETS = m.ROOT / "budget.json"
    m.CONTRACTS = m.ROOT / "contracts.json"
    m.PENDING = m.STATE / "pending"
    m.GOALS = m.STATE / "goals.jsonl"
    m.OBS = m.STATE / "observations.jsonl"
    m.CONSUMPTION = m.STATE / "witness-consumption.jsonl"
    m.ARMED = m.STATE / "armed.json"
    m.ROOT.mkdir(parents=True, exist_ok=True)
    m.STATE.mkdir(parents=True, exist_ok=True)
    m.STABLE_ROOT.mkdir(parents=True, exist_ok=True)
    m.BUDGETS.write_text("{}", encoding="utf-8")
    m.PINS_FILE.write_text("{}", encoding="utf-8")
    m.CONTRACTS.write_text("{}", encoding="utf-8")
    od = m.ROOT.parent / "owner_dialogue"
    od.mkdir(parents=True, exist_ok=True)
    return m, od


def scenario(artifact, delay_registration):
    m, od = load(artifact)
    (od / "owner_decision.v1.jsonl").write_text(
        json.dumps(DECISION) + "\n", encoding="utf-8")
    if not delay_registration:
        (od / "decision_tasks.json").write_text(
            json.dumps({"tasks": [TASK]}), encoding="utf-8")
    r1 = m.consume_decisions()
    if delay_registration:
        # register the task AFTER the first consumption pass
        (od / "decision_tasks.json").write_text(
            json.dumps({"tasks": [TASK]}), encoding="utf-8")
        r2 = m.consume_decisions()
    else:
        r2 = r1
    tasks = json.loads((od / "decision_tasks.json").read_text(encoding="utf-8"))
    return r1, r2, tasks["tasks"][0]["state"]


print("=== COUNTEREXAMPLE: delayed task registration ===")
# buggy version: decision consumed as NO_TASK, task never resumes
r1, r2, state = scenario(V3D, True)
buggy_ok = (r1 == "consumed" and r2 == "idle"
            and state == "awaiting_ack")
print("  v3d (buggy): first=%s second=%s task=%s -> %s" %
      (r1, r2, state, "PERMANENTLY LOST" if buggy_ok else "unexpected"))
# fixed version: NO_TASK is retryable, task resumes on second pass
r1, r2, state = scenario(W3V2, True)
fixed_ok = (r1 == "consumed" and r2 == "consumed"
            and state == "resumed")
print("  W3v2 (fixed): first=%s second=%s task=%s -> %s" %
      (r1, r2, state, "RECOVERED" if fixed_ok else "unexpected"))
# control: task registered before decision
r1, r2, state = scenario(W3V2, False)
ctrl_ok = (r1 == "consumed" and state == "resumed")
print("  control (registered first): %s task=%s -> %s" %
      (r1, state, "OK" if ctrl_ok else "unexpected"))

PASS = buggy_ok and fixed_ok and ctrl_ok
print()
print("W3_COUNTEREXAMPLE:", "PASS" if PASS else "FAIL")
sys.exit(0 if PASS else 1)
