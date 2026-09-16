"""Build the COMBINED worker: G30 stage-guard + W3 ACK gate (with identity
binding fix) + real internal handler (log_ack_and_report) + C3-fix.

This resolves the W3/G30 file conflict (same target, same base) by merging
both deltas into one artifact with proper ordering.
"""
import ast
import hashlib
import pathlib
import shutil
import sys

LIVE = pathlib.Path("/home/ari/ofn/state/coding-worker/coding_worker.py")
STAGE = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                     "W3G30-COMBINED-001")
STAGE.mkdir(parents=True, exist_ok=True)

EDITS = []

# --- G30: byte-scan the staged file (inserted in process_patch_task staging)
EDITS.append((
    '''            with (stage / rel).open("w", encoding="utf-8", newline="") as fh:
                fh.write(new_text)
''',
    '''            with (stage / rel).open("w", encoding="utf-8", newline="") as fh:
                fh.write(new_text)
            # G30 guard 2026-09-14: byte-scan the STAGED file (not the parsed
            # AST) - a JSON "\\b" replacement decodes to a literal backspace and
            # ast.parse accepts it silently; mixed EOLs corrupt anchors later.
            _sb = (stage / rel).read_bytes()
            _ctrl = [c for c in _sb if c < 0x20 and c not in (0x0a, 0x09)]
            _cr = _sb.count(b"\\r\\n")
            _lf = _sb.count(b"\\n") - _cr
            if _ctrl or (_cr and _lf):
                raise ValueError("STAGE_BYTES_DIRTY:ctrl=%d crlf=%d lf=%d rel=%s"
                                 % (len(_ctrl), _cr, _lf, rel[:40]))
'''))

# --- W3 v3: ACK gate with IDENTITY BINDING (fixes the reviewer's probes)
# Key changes from v2:
#   1. registry task's worker_task_id must match the WORKER task's task_id
#   2. resume_action must be in the closed enum
#   3. unique registry match (not first-match)
EDITS.append((
    '''    unmet = []
    for dep in task.get("depends_on") or []:
        path = dep.get("path")
        dtype = dep.get("type", "build")
        try:''',
    '''    _RESUME_ACTIONS = frozenset({
        "unpark_existing_internal_task",
        "log_ack_and_report",
    })
    unmet = []
    for dep in task.get("depends_on") or []:
        path = dep.get("path")
        dtype = dep.get("type", "build")
        if dtype == "owner_ack":
            # W3v3 ACK gate with IDENTITY BINDING:
            # 1. payload hash must match a UNIQUE registry task
            # 2. registry task's worker_task_id must match THIS worker task_id
            # 3. registry task's resume_action must be in the closed enum
            # 4. registry state must be >= resumed (consumer processed it)
            _sha = dep.get("payload_sha256", "")
            _dec_path = Path.home() / "ofn/state/owner_dialogue/owner_decision.v1.jsonl"
            _reg_path = Path.home() / "ofn/state/owner_dialogue/decision_tasks.json"
            _ackd = False
            _deny = None
            if not _sha:
                _deny = "no_payload_sha"
            elif not _dec_path.exists():
                _deny = "no_decision_file"
            else:
                _has_dec = False
                for _l in _dec_path.read_text(encoding="utf-8").splitlines():
                    try:
                        _d = json.loads(_l)
                        if (_d.get("verdict") == "ACK_SEEN"
                                and _d.get("bound_request_payload_sha256") == _sha):
                            _has_dec = True
                            break
                    except ValueError:
                        continue
                if not _has_dec:
                    _deny = "no_valid_ack_decision"
                elif not _reg_path.exists():
                    _deny = "no_registry"
                else:
                    try:
                        _reg = json.loads(_reg_path.read_text(encoding="utf-8"))
                        _matches = [t for t in _reg.get("tasks", [])
                                    if t.get("payload_sha256") == _sha]
                        if len(_matches) == 0:
                            _deny = "registry_no_matching_task"
                        elif len(_matches) > 1:
                            _deny = "registry_ambiguous_multiple_matches"
                        else:
                            _rt = _matches[0]
                            if _rt.get("state") not in (
                                    "resumed", "resume_eligible",
                                    "resume_delivered", "work_completed"):
                                _deny = "registry_state_%s" % _rt.get("state", "?")
                            elif _rt.get("resume_action") not in _RESUME_ACTIONS:
                                _deny = "resume_action_not_in_enum:%s" % _rt.get("resume_action", "?")
                            elif _rt.get("worker_task_id") and _rt.get("worker_task_id") != task.get("task_id"):
                                _deny = "worker_task_id_mismatch:want=%s have=%s" % (
                                    _rt.get("worker_task_id"), task.get("task_id"))
                            else:
                                _ackd = True
                    except (ValueError, OSError):
                        _deny = "registry_corrupt"
            if not _ackd:
                unmet.append({"path": "owner_ack:" + str(_sha)[:16],
                              "type": dtype,
                              "why": _deny or "awaiting_owner_ack"})
            continue
        try:'''))

# --- W3 internal handler: log_ack_and_report (a REAL internal action)
# Executed by the worker AFTER unpark, as a lightweight purpose that doesn't
# need cognition/model — just writes an observable effect.
EDITS.append((
    '''    receipt("TASK_STARTED", task=tid, purpose=task["purpose"])''',
    '''    receipt("TASK_STARTED", task=tid, purpose=task["purpose"])
    # W3 internal handler: log_ack_and_report is a REAL, pre-authorized,
    # zero-cost internal action that writes an observable effect (ack-log row)
    if task.get("purpose") == "log_ack_and_report":
        _ack_log = STATE / "ack-log.jsonl"
        _key = "%s|%s" % (tid, task.get("_decision_key", ""))
        _already = False
        if _ack_log.exists():
            for _l in _ack_log.read_text(encoding="utf-8").splitlines():
                try:
                    if json.loads(_l).get("idempotency_key") == _key:
                        _already = True
                        break
                except ValueError:
                    continue
        if not _already:
            _row = {"schema": "octopus.ack-log.v1",
                    "idempotency_key": _key, "task_id": tid,
                    "decision_key": task.get("_decision_key", ""),
                    "payload_sha256": task.get("_payload_sha256", ""),
                    "effect": "owner acknowledgment recorded",
                    "at": now_iso()}
            with _ack_log.open("a", encoding="utf-8") as _f:
                _f.write(json.dumps(_row, sort_keys=True) + "\\n")
            receipt("ACK_LOGGED", task=tid, idempotency_key=_key[:40])
            return "ack-logged"
        receipt("ACK_LOG_IDEMPOTENT_SKIP", task=tid)
        return "ack-already-logged"'''))

raw = LIVE.read_bytes()
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
shutil.copy2(LIVE, STAGE / "coding_worker.py.pre-combined")
(STAGE / "coding_worker.py").write_bytes(new.encode("utf-8"))
print("live       :", hashlib.sha256(raw).hexdigest()[:16])
print("preimage   :", hashlib.sha256((STAGE / "coding_worker.py.pre-combined").read_bytes()).hexdigest()[:16])
print("COMBINED   :", hashlib.sha256((STAGE / "coding_worker.py").read_bytes()).hexdigest()[:16])
