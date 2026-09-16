"""Fix self_feed v3: substring dedup on outcome. Instead of parsing stems,
check if the dashed-outcome appears as a substring in ANY existing task stem.
This catches both SELF-RECUR-PATCH-TESTS-FAILED and SELF-PATCH-TESTS-FAILED-E3B0C442
because both contain 'PATCH-TESTS-FAILED'."""
import ast
import hashlib
import pathlib
import shutil
import sys

P = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                 "W3G30-COMBINED-002/coding_worker.py")
PRE = P.parent / "coding_worker.py.v3-5eca0b72"

OLD = '''    # FIX 1: FAILED was missing — a task that failed was invisible to the
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
NEW = '''    # FIX: FAILED was missing AND the single-failure path appends a hash
    # suffix that changes per learning-row, so exact-match never blocks it.
    # Solution: substring dedup — the dashed-outcome string is checked
    # against ALL existing task stems (catches both SELF-RECUR- and SELF-
    # prefixed IDs for the same underlying outcome).
    _all_stems = []
    for d in list(TASKS.glob("*.json")) + list(BLOCKED.glob("*.json")) \\
            + list(DONE.glob("*.json")) + list(FAILED.glob("*.json")):
        seen.add(d.stem)
        _all_stems.append(d.stem)'''

raw = P.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("roundtrip")
if hashlib.sha256(raw).hexdigest()[:8] != "5eca0b72":
    sys.exit("not v3")
if old.count(OLD) != 1:
    sys.exit("anchor=%d" % old.count(OLD))
new = old.replace(OLD, NEW)

# Now patch the recurrence and single-failure checks to use _all_stems
OLD2 = '''        if _tid in seen:
            continue'''
NEW2 = '''        if _tid in seen or any(_tid[10:] in _s for _s in _all_stems):
            continue  # substring: blocks both RECUR and single variants'''
if new.count(OLD2) < 1:
    sys.exit("OLD2 not found")
new = new.replace(OLD2, NEW2, 1)

ast.parse(new)
shutil.copy2(P, PRE)
P.write_bytes(new.encode("utf-8"))
print("v3 preimage:", hashlib.sha256(PRE.read_bytes()).hexdigest()[:16])
print("v4         :", hashlib.sha256(P.read_bytes()).hexdigest()[:16])
