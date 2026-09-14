"""Fix both self_feed bugs:
1. FAILED dir in seen (already applied)
2. Outcome-prefix dedup: single-failure path creates IDs like
   SELF-PATCH-TESTS-FAILED-E3B0C442 where the hash changes each time;
   check outcome PREFIX against seen, not just exact match.
"""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                 "W3G30-COMBINED-002/coding_worker.py")
PRE = P.parent / "coding_worker.py.v2-57fab938"

OLD = '''    # FIX: FAILED was missing — a task that failed was invisible to the
    # seen-check, so self_feed re-created the SAME failed task every tick
    for d in list(TASKS.glob("*.json")) + list(BLOCKED.glob("*.json")) \\
            + list(DONE.glob("*.json")) + list(FAILED.glob("*.json")):
        seen.add(d.stem)'''
NEW = '''    # FIX 1: FAILED was missing — a task that failed was invisible to the
    # seen-check, so self_feed re-created the SAME failed task every tick
    # FIX 2: outcome-prefix dedup — the single-failure path appends a hash
    # suffix that changes per learning-row, so exact-match never blocks it;
    # we also add the outcome PREFIX to prevent infinite re-creation
    for d in list(TASKS.glob("*.json")) + list(BLOCKED.glob("*.json")) \\
            + list(DONE.glob("*.json")) + list(FAILED.glob("*.json")):
        seen.add(d.stem)
        _stem = d.stem
        # SELF-RECUR-OUTCOME or SELF-OUTCOME-HASH -> add SELF-OUTCOME prefix
        if _stem.startswith("SELF-"):
            _rest = _stem[5:]
            for _sep in ("-",):
                _parts = _rest.split(_sep, 1)
                if len(_parts) == 2 and _parts[1]:
                    # add both SELF-RECUR-OUTCOME and SELF-OUTCOME prefixes
                    if _parts[0] == "RECUR":
                        _outcome_prefix = _parts[1].rsplit("-", 1)[0] if "-" in _parts[1] else _parts[1]
                        seen.add("SELF-RECUR-" + _outcome_prefix)
                    else:
                        seen.add("SELF-" + _parts[0])
                    break'''

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("roundtrip")
if hashlib.sha256(raw).hexdigest()[:8] != "57fab938":
    sys.exit("not v2")
if old.count(OLD) != 1:
    sys.exit("anchor=%d" % old.count(OLD))
new = old.replace(OLD, NEW)
ast.parse(new)
shutil.copy2(P, PRE)
P.write_bytes(new.encode("utf-8"))
print("v2 preimage:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("v3         :", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
