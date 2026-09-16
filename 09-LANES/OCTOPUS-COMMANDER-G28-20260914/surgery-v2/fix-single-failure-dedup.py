"""Fix the single-failure path: add defect-id check BEFORE creating.
The recurrence path already checks _defect_ids; the single-failure path
only checked `tid in seen` which doesn't block because the ID includes
an evidence-hash suffix that differs from the recurrence ID."""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                 "W3G30-COMBINED-003/coding_worker.py")
PRE = P.parent / "coding_worker.py.v003-b7ec15f8"

OLD = '''        tid = "SELF-" + sig
        if tid in seen:
            continue'''
NEW = '''        tid = "SELF-" + sig
        if tid in seen:
            continue
        # single-failure defect-id check: same outcome already attempted
        # (prevents the one-extra-task-from-second-path bug)
        _sf_outcome = re.sub(r"[^A-Za-z0-9]+", "-",
                             outcome).strip("-").upper()[:30]
        if any(_did.startswith(_sf_outcome + "|") or
               _did.startswith(_sf_outcome[:20]) for _did in _defect_ids):
            continue'''

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("roundtrip")
if hashlib.sha256(raw).hexdigest()[:8] != "b7ec15f8":
    sys.exit("not v003")
if old.count(OLD) != 1:
    sys.exit("anchor=%d" % old.count(OLD))
new = old.replace(OLD, NEW)
ast.parse(new)
shutil.copy2(P, PRE)
P.write_bytes(new.encode("utf-8"))
print("v003:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("v004:", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
