"""W3G30 combined E2E — full chain: producer → decision → consumer → worker
→ internal handler → effect → receipt → read-back.
Uses the COMBINED worker (72fed2e2) which has identity binding + enum check +
log_ack_and_report handler + G30 stage-guard.
All under kernel fence (nobody + scratch)."""
import hashlib
import importlib.machinery
import importlib.util
import json
import pathlib
import sys
import tempfile

TRIO = ("/home/ari/ofn/state/coding-worker/stage/"
        "SUCCESSOR-TRIO-20260914/ops_agent.py")
WORKER = ("/home/ari/ofn/state/coding-worker/stage/"
          "W3G30-COMBINED-001/coding_worker.py")
X = "f" * 64
PASS, FAIL = [], []
_WORKER_TASK_ID = "LIVE-TEST-WORKER-001"


def check(name, ok, detail=""):
    print("  %-5s %-58s %s" % ("PASS" if ok else "FAIL", name, detail))
    (PASS if ok else FAIL).append(name)


def load_mod(artifact, nm):
    spec = importlib.util.spec_from_file_location(
        nm, artifact,
        loader=importlib.machinery.SourceFileLoader(nm, artifact))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def make_env():
    fx = pathlib.Path(tempfile.mkdtemp(prefix="w3g30-"))
    pathlib.Path.home = classmethod(lambda cls, _f=fx: _f)
    (fx / "ofn/state/owner_dialogue").mkdir(parents=True)
    (fx / "ofn/state/coding-worker/tasks").mkdir(parents=True)
    (fx / "ofn/state/coding-worker/blocked").mkdir(parents=True)
    (fx / "ofn/state/coding-worker/stage").mkdir(parents=True)
    (fx / "ofn/state/ops-agent/state").mkdir(parents=True)
    (fx / "ofn/state/ops-agent").mkdir(parents=True, exist_ok=True)
    (fx / "ofn/state/autonomy").mkdir(parents=True)
    return fx


def setup_trio(fx):
    m = load_mod(TRIO, "trio_%d" % id(fx))
    m.ROOT = fx / "ofn/state/ops-agent"
    m.STATE = m.ROOT / "state"
    m.RECEIPTS = m.STATE / "ops-receipts.jsonl"
    m.STABLE_ROOT = fx / "ofn/state/autonomy"
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
    m.PENDING.mkdir(parents=True, exist_ok=True)
    m.BUDGETS.write_text("{}", encoding="utf-8")
    m.PINS_FILE.write_text("{}", encoding="utf-8")
    m.CONTRACTS.write_text("{}", encoding="utf-8")
    return m


def setup_worker(fx):
    w = load_mod(WORKER, "worker_%d" % id(fx))
    w.HOME = fx
    w.STATE = fx / "ofn/state/coding-worker"
    w.TASKS = w.STATE / "tasks"
    w.BLOCKED = w.STATE / "blocked"
    w.STAGE_ROOT = w.STATE / "stage"
    w.CANARY_DIR = fx / "ofn/state/ops-agent/state/canary-requests"
    w.CANARY_SPOOL = w.CANARY_DIR
    w.DONE = w.STATE / "done"
    w.DONE.mkdir(parents=True, exist_ok=True)
    return w


def register_task_and_card(fx, payload_sha=X, worker_task_id=_WORKER_TASK_ID):
    """PRODUCER: registers the task in the registry AND parks the worker task
    BEFORE any card is displayed."""
    od = fx / "ofn/state/owner_dialogue"
    (od / "decision_tasks.json").write_text(json.dumps(
        {"tasks": [{"task_id": "CARD-001", "payload_sha256": payload_sha,
                    "state": "awaiting_ack",
                    "created_at": "2026-09-14T10:00:00Z",
                    "scope": "internal-inert",
                    "resume_action": "log_ack_and_report",
                    "worker_task_id": worker_task_id}]}), encoding="utf-8")


def park_worker_task(w, task_id, payload_sha=X):
    w.BLOCKED.mkdir(parents=True, exist_ok=True)
    (w.BLOCKED / (task_id + ".json")).write_text(json.dumps(
        {"task": {"task_id": task_id,
                  "purpose": "log_ack_and_report",
                  "depends_on": [{"type": "owner_ack",
                                  "payload_sha256": payload_sha}],
                  "_payload_sha256": payload_sha,
                  "provenance": {"class": "REAL_INTERNAL_WORK",
                                 "source": "live-test-card-spec",
                                 "source_ts": "2026-09-14T14:00:00Z",
                                 "source_hash": "spec"}},
         "unmet": [{"why": "awaiting_owner_ack"}],
         "parked_at": "2026-09-14T10:00:00Z"}) + "\n", encoding="utf-8")


def owner_sends_ack(fx, payload_sha=X):
    od = fx / "ofn/state/owner_dialogue"
    with (od / "owner_decision.v1.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"schema": "octopus.owner_decision.v1",
                            "at": "2026-09-14T10:05:00Z",
                            "verdict": "ACK_SEEN",
                            "bound_request_payload_sha256": payload_sha,
                            "source_text_sha256": "live_test_msg"}) + "\n")


def run_tick(fx, trio, worker):
    trio.consume_decisions()
    unblocked = worker.unblock()
    processed = 0
    for f in sorted(worker.TASKS.glob("*.json")):
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
            task = doc.get("task") if isinstance(doc.get("task"), dict) else doc
            result = worker.process_task(task)
            processed += 1
        except Exception:
            pass
    return unblocked, processed


# ==================== TESTS ====================
print("=== C1: no ACK + healthy deps -> zero unpark ===")
fx = make_env()
t = setup_trio(fx)
w = setup_worker(fx)
register_task_and_card(fx)
park_worker_task(w, _WORKER_TASK_ID)
# NO owner ACK sent
n, p = run_tick(fx, t, w)
check("C1 no-ACK zero unpark, zero process",
      n == 0 and p == 0 and (w.BLOCKED / (_WORKER_TASK_ID + ".json")).exists())

print("=== C2: ACK valid + identity match -> full chain to effect ===")
fx = make_env()
t = setup_trio(fx)
w = setup_worker(fx)
register_task_and_card(fx)     # producer registers BEFORE card
park_worker_task(w, _WORKER_TASK_ID)
owner_sends_ack(fx)            # owner sends real ACK
n, p = run_tick(fx, t, w)
ack_log = fx / "ofn/state/coding-worker/ack-log.jsonl"
has_effect = ack_log.exists() and len(
    [l for l in ack_log.read_text(encoding="utf-8").splitlines() if l.strip()]) > 0
task_done = (w.DONE / (_WORKER_TASK_ID + ".json")).exists() or not (
    w.TASKS.glob(_WORKER_TASK_ID + ".json"))
check("C2 full chain: unpark+process+ack-log effect",
      n == 1 and p == 1 and has_effect,
      "unparked=%d processed=%d effect=%s" % (n, p, has_effect))
if has_effect:
    row = json.loads(ack_log.read_text(encoding="utf-8").splitlines()[0])
    check("C2b ack-log row has idempotency key + task identity",
          row.get("task_id") == _WORKER_TASK_ID
          and row.get("idempotency_key", "").startswith(_WORKER_TASK_ID)
          and row.get("effect") == "owner acknowledgment recorded")

print("=== C3: wrong task_id (FOREIGN) -> zero dispatch ===")
fx = make_env()
t = setup_trio(fx)
w = setup_worker(fx)
register_task_and_card(fx, worker_task_id="CORRECT-ID")
park_worker_task(w, "FOREIGN_TASK")  # different worker task, same payload
owner_sends_ack(fx)
n, p = run_tick(fx, t, w)
check("C3 foreign task_id -> zero unpark (identity gate blocks)",
      n == 0 and (w.BLOCKED / "FOREIGN_TASK.json").exists())

print("=== C4: wrong resume_action (approval needed) -> zero dispatch ===")
fx = make_env()
t = setup_trio(fx)
w = setup_worker(fx)
register_task_and_card(fx)
# overwrite with wrong action
od = fx / "ofn/state/owner_dialogue"
(od / "decision_tasks.json").write_text(json.dumps(
    {"tasks": [{"task_id": "CARD-001", "payload_sha256": X,
                "state": "resumed", "created_at": "2026-09-14T10:00:00Z",
                "scope": "internal", "resume_action": "enable_customer_contact",
                "worker_task_id": _WORKER_TASK_ID}]}), encoding="utf-8")
park_worker_task(w, _WORKER_TASK_ID)
owner_sends_ack(fx)
n, p = run_tick(fx, t, w)
check("C4 approval-needed action -> zero unpark (enum gate blocks)",
      n == 0 and (w.BLOCKED / (_WORKER_TASK_ID + ".json")).exists())

print("=== C5: replay after full chain -> zero additional effect ===")
# fresh env: full chain succeeds first, THEN replay
fx = make_env()
t = setup_trio(fx)
w = setup_worker(fx)
register_task_and_card(fx)
park_worker_task(w, _WORKER_TASK_ID)
owner_sends_ack(fx)
n, p = run_tick(fx, t, w)  # first pass: full chain
ack_log = fx / "ofn/state/coding-worker/ack-log.jsonl"
lines_before = len(ack_log.read_text(encoding="utf-8").splitlines()) if ack_log.exists() else 0
# replay: same decision, same everything
n2, p2 = run_tick(fx, t, w)
lines_after = len(ack_log.read_text(encoding="utf-8").splitlines()) if ack_log.exists() else 0
check("C5 replay -> zero additional ack-log rows",
      lines_after == lines_before,
      "before=%d after=%d" % (lines_before, lines_after))

print("=== C6: crash simulation: state written but receipt lost ===")
fx = make_env()
t = setup_trio(fx)
w = setup_worker(fx)
register_task_and_card(fx)
park_worker_task(w, _WORKER_TASK_ID)
owner_sends_ack(fx)
# simulate crash: consume_decisions runs but then we DON'T call unblock
t.consume_decisions()
# "restart": fresh modules, same filesystem
t2 = setup_trio(fx)
w2 = setup_worker(fx)
n, p = run_tick(fx, t2, w2)
ack_log = fx / "ofn/state/coding-worker/ack-log.jsonl"
check("C6 crash recovery -> exactly one effect",
      n <= 1 and p <= 1 and ack_log.exists()
      and len(ack_log.read_text(encoding="utf-8").splitlines()) <= 1)

print("=== C7: registry absent (corrupt/missing) -> fail-closed ===")
fx = make_env()
t = setup_trio(fx)
w = setup_worker(fx)
park_worker_task(w, _WORKER_TASK_ID)
owner_sends_ack(fx)
# NO registry file (decision exists, registry doesn't)
n, p = run_tick(fx, t, w)
check("C7 registry absent -> stays blocked",
      n == 0 and (w.BLOCKED / (_WORKER_TASK_ID + ".json")).exists())

print("=== C8: dependency-only regression ===")
fx = make_env()
t = setup_trio(fx)
w = setup_worker(fx)
dep_file = fx / "marker.txt"
dep_file.write_text("READY", encoding="utf-8")
w.BLOCKED.mkdir(parents=True, exist_ok=True)
(w.BLOCKED / "DEP-ONLY.json").write_text(json.dumps(
    {"task": {"task_id": "DEP-ONLY", "depends_on": [
        {"type": "build", "path": str(dep_file), "must_contain": "READY"}]},
     "unmet": [], "parked_at": "2026-09-14T10:00:00Z"}) + "\n", encoding="utf-8")
n = w.unblock()
check("C8 dependency-only regression -> still unblocks",
      n == 1 and (w.TASKS / "DEP-ONLY.json").exists())

print()
print("W3G30_E2E:", "PASS" if not FAIL else "FAIL -> " + ", ".join(FAIL))
sys.exit(0 if not FAIL else 1)
