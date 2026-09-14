"""W3 consumer v2b: the v2 patch changed only the label but _record_decision
still writes the key into the consumption log, and the consumed set reads ALL
keys regardless of kind. Fix: filter the consumed set to TERMINAL kinds only
(the audit log keeps everything; the dedup gate only counts terminal)."""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                 "SUCCESSOR-TRIO-20260914/ops_agent.py")
PRE = P.parent / "ops_agent.py.w3v2-c4a016cc"

OLD = '''    consumed = set()
    if cons_path.exists():
        for l in cons_path.read_text(encoding="utf-8").splitlines():
            try:
                consumed.add(json.loads(l).get("key"))
            except ValueError:
                continue'''
NEW = '''    # TERMINAL dispositions only: a retryable disposition (e.g. the task
    # wasn't registered yet) must NOT permanently consume the decision key;
    # the next tick re-evaluates it against a possibly-registered task.
    _TERMINAL = {"DECISION_CONSUMED", "DECISION_TASK_NOT_WAITING",
                 "DECISION_STALE", "DECISION_IGNORED"}
    consumed = set()
    if cons_path.exists():
        for l in cons_path.read_text(encoding="utf-8").splitlines():
            try:
                _r = json.loads(l)
                if _r.get("kind") in _TERMINAL:
                    consumed.add(_r.get("key"))
            except ValueError:
                continue'''

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("roundtrip")
if hashlib.sha256(raw).hexdigest()[:8] != "c4a016cc":
    sys.exit("not w3v2")
if old.count(OLD) != 1:
    sys.exit("anchor=%d" % old.count(OLD))
new = old.replace(OLD, NEW)
ast.parse(new)
shutil.copy2(P, PRE)
P.write_bytes(new.encode("utf-8"))
print("w3v2 preimage:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("w3v2b        :", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
