"""TRIO v2b: B5 findings dedupe - a *.pyc INSIDE an already-found cache dir
must not appear as a separate target (mv of the parent makes the child mv fail
with rc=1 -> the whole action FAILED; measured exit_codes [0,0,1,1,...])."""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                 "SUCCESSOR-TRIO-20260914/ops_agent.py")
PRE = P.parent / "ops_agent.py.trio-v2-9126c388"

TAIL = '    if not findings:\n        return "no-action-needed"'
OLD = ('    findings = [f for f in findings if any(\n'
       '        str(f).startswith(str(hp)) for hp in roots)]\n' + TAIL)
NEW = ('    findings = [f for f in findings if any(\n'
       '        str(f).startswith(str(hp)) for hp in roots)]\n'
       '    # v2b dedupe: a *.pyc living INSIDE an already-found cache dir is\n'
       '    # carried by that dir own move; keeping both made the child mv fail\n'
       '    # (rc=1) and the whole action FAILED. Prevents double counting too.\n'
       '    _dirs = [f for f in findings if f.is_dir()]\n'
       '    if _dirs:\n'
       '        findings = [f for f in findings if f.is_dir() or not any(\n'
       '            str(f).startswith(str(_d) + os.sep) for _d in _dirs)]\n'
       + TAIL)

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("roundtrip")
if old.count(OLD) != 1:
    sys.exit("anchor=%d" % old.count(OLD))
new = old.replace(OLD, NEW)
ast.parse(new)
shutil.copy2(P, PRE)
P.write_bytes(new.encode("utf-8"))
print("v2 preimage:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("v2b        :", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
