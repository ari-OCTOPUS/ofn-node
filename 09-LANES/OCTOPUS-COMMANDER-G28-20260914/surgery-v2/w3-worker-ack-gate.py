"""W3: ACK gate in the WORKER's own eligibility check (before unpark).

Adds `owner_ack` as a new dependency type to dependency_blocked().
A task with {"type":"owner_ack","payload_sha256":"<hash>"} stays blocked
until owner_decision.v1.jsonl contains a matching ACK_SEEN AND
decision_tasks.json shows state >= "resume_eligible" for that hash.

This is the COUNTEREXAMPLE fix: without the gate, unblock() would move
a task with a healthy build dependency even if the owner hasn't ACKed.
"""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/coding-worker/coding_worker.py")
PRE = P.parent / "coding_worker.py.pre-ack-gate-20260914"
STAGE = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                     "W3-ACK-GATE-001")
STAGE.mkdir(parents=True, exist_ok=True)

# 1) owner_ack check in dependency_blocked
OLD_DEP = '''        if dtype == "runtime":'''
NEW_DEP = '''        if dtype == "owner_ack":
            # W3 ACK gate: satisfied ONLY by a valid ACK_SEEN decision bound
            # to this task's payload hash AND the decision consumer has
            # processed it (state >= resume_eligible in the registry).
            # This gate is INSIDE the worker's eligibility, before unpark.
            _sha = dep.get("payload_sha256", "")
            _dec_path = Path.home() / "ofn/state/owner_dialogue/owner_decision.v1.jsonl"
            _reg_path = Path.home() / "ofn/state/owner_dialogue/decision_tasks.json"
            _ackd = False
            if _dec_path.exists() and _sha:
                for _l in _dec_path.read_text(encoding="utf-8").splitlines():
                    try:
                        _d = json.loads(_l)
                        if (_d.get("verdict") == "ACK_SEEN"
                                and _d.get("bound_request_payload_sha256") == _sha):
                            # also check the consumer processed it
                            if _reg_path.exists():
                                try:
                                    _reg = json.loads(_reg_path.read_text(encoding="utf-8"))
                                    _t = next((t for t in _reg.get("tasks", [])
                                               if t.get("payload_sha256") == _sha), None)
                                    if _t and _t.get("state") in ("resume_eligible",
                                                                  "resume_delivered",
                                                                  "work_completed"):
                                        _ackd = True
                                except (ValueError, OSError):
                                    pass
                            else:
                                # registry absent: decision exists but consumer
                                # hasn't run yet -> NOT satisfied (fail-closed)
                                pass
                            break
                    except ValueError:
                        continue
            if not _ackd:
                unmet.append({"path": "owner_ack:" + str(_sha)[:16],
                              "type": dtype, "why": "awaiting_owner_ack"})
            continue
        if dtype == "runtime":'''

# 2) make sure the worker also stages a canary that goes through the gate
EDITS = [
    (OLD_DEP, NEW_DEP),
]

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("roundtrip")
if hashlib.sha256(raw).hexdigest()[:8] != "a8fb195c":
    sys.exit("not live worker")
for i, (a, _) in enumerate(EDITS):
    if old.count(a) != 1:
        sys.exit("edit %d anchor=%d" % (i, old.count(a)))
new = old
for a, b in EDITS:
    new = new.replace(a, b)
ast.parse(new)
shutil.copy2(P, PRE)
(STAGE / "coding_worker.py").write_bytes(new.encode("utf-8"))
shutil.copy2(P, STAGE / "coding_worker.py.pre-ack-gate")
print("live worker :", hashlib.sha256(raw).hexdigest()[:16], "(untouched)")
print("preimage    :", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("ACK-gated   :", hashlib.sha256(
    (STAGE / "coding_worker.py").read_bytes()).hexdigest()[:16])
