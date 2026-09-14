"""Apply the G28-E bounded fix: restore the lost TCB gate in handle_spool_category.
Preimage kept as ops_agent.py.pre-g28e-20260914. Anchor-count asserted == 1.
LF endings preserved (read_bytes/decode/encode, no text-mode rewrite)."""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/ops-agent/ops_agent.py")
PRE = P.parent / "ops_agent.py.pre-g28e-20260914"

ANCHOR = '        target = str(req.get("target", ""))\n        # FIX 2026-09-14: retire executed requests so the same artifact+target pair'
INSERT = '''        target = str(req.get("target", ""))
        # G28-E FIX 2026-09-14: restore the TCB gate that was lost when the dedupe
        # loop was repaired (pre-retire line 488). TCB targets always become owner
        # decisions; they must never reach the witnessed deploy path from here.
        if any(t in target for t in _TCB_TARGETS):
            receipt("CREATE_OWNER_DECISION_TASK", category=category,
                    reason="TCB target requested", request=name)
            os.replace(spool / name, STATE / "owner-tasks" / name)
            return "owner-task-created"
        # FIX 2026-09-14: retire executed requests so the same artifact+target pair'''

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("ABORT: round-trip mismatch (encoding)")
n = old.count(ANCHOR)
if n != 1:
    sys.exit("ABORT: anchor count = %d (expected 1)" % n)
if "G28-E FIX" in old:
    sys.exit("ABORT: fix already present")
shutil.copy2(P, PRE)
new = old.replace(ANCHOR, INSERT)
ast.parse(new)
P.write_bytes(new.encode("utf-8"))
print("preimage sha256:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("new sha256:", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
