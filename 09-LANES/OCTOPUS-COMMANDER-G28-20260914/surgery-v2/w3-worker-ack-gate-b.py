"""W3 ACK gate v2: the v1 patch placed the owner_ack check AFTER the file
read (Path(path).read_bytes()), but owner_ack deps have no path field.
This patch places it BEFORE the file read, as the first check in the loop."""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                 "W3-ACK-GATE-001/coding_worker.py")
PRE = P.parent / "coding_worker.py.ack-gate-v1-c9de1860"

# replace the misplaced block (it was inserted inside the runtime check)
OLD = '''    unmet = []
    for dep in task.get("depends_on") or []:
        path = dep.get("path")
        dtype = dep.get("type", "build")
        try:
            raw = Path(path).read_bytes()
        except OSError:
            unmet.append({"path": path, "type": dtype, "why": "unreadable"})
            continue
        if dtype == "owner_ack":
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

NEW = '''    unmet = []
    for dep in task.get("depends_on") or []:
        path = dep.get("path")
        dtype = dep.get("type", "build")
        if dtype == "owner_ack":
            # W3 ACK gate: satisfied ONLY by a valid ACK_SEEN decision bound
            # to this task's payload hash AND the decision consumer has
            # processed it (state >= resume_eligible in the registry).
            # Checked BEFORE the file read — owner_ack deps have no path field.
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
                            if _reg_path.exists():
                                try:
                                    _reg = json.loads(_reg_path.read_text(encoding="utf-8"))
                                    _t = next((t for t in _reg.get("tasks", [])
                                               if t.get("payload_sha256") == _sha), None)
                                    if _t and _t.get("state") in (
                                            "resumed", "resume_eligible",
                                            "resume_delivered", "work_completed"):
                                        _ackd = True
                                except (ValueError, OSError):
                                    pass
                            break
                    except ValueError:
                        continue
            if not _ackd:
                unmet.append({"path": "owner_ack:" + str(_sha)[:16],
                              "type": dtype, "why": "awaiting_owner_ack"})
            continue
        try:
            raw = Path(path).read_bytes()
        except OSError:
            unmet.append({"path": path, "type": dtype, "why": "unreadable"})
            continue
        if dtype == "runtime":'''

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("roundtrip")
if hashlib.sha256(raw).hexdigest()[:8] != "c9de1860":
    sys.exit("not v1")
if old.count(OLD) != 1:
    sys.exit("anchor=%d" % old.count(OLD))
new = old.replace(OLD, NEW)
ast.parse(new)
shutil.copy2(P, PRE)
P.write_bytes(new.encode("utf-8"))
print("v1 preimage:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("v2         :", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
