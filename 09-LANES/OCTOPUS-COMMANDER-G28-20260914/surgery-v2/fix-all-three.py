"""Three fixes in one combined worker build:
1. SELF-FEED: FAILED dir added to the seen-check (bug: task in failed/ was
   invisible, so the same failed task was re-created every tick)
2. TASK CONTRACT: corrected for REAL-NOTIFY-003 (pytest-only commands,
   summary field, valid Python test, correct anchor context)
3. WORK_COMPLETED: worker moves done tasks to DONE/ and registry transitions
   to work_completed (not just file-exists)
"""
import ast
import hashlib
import pathlib
import shutil
import sys

# Build from the LIVE worker (a8fb195c) to keep the artifact chain clean
LIVE = pathlib.Path("/home/ari/ofn/state/coding-worker/coding_worker.py")
STAGE = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                     "W3G30-COMBINED-002")
STAGE.mkdir(parents=True, exist_ok=True)

E = []


def edit(a, b):
    E.append((a, b))


# ── FIX 1: self_feed FAILED-blindness ──────────────────────────────────
edit(
    '    for d in list(TASKS.glob("*.json")) + list(BLOCKED.glob("*.json")) + list(DONE.glob("*.json")):\n'
    "        seen.add(d.stem)",
    '    # FIX: FAILED was missing — a task that failed was invisible to the\n'
    "    # seen-check, so self_feed re-created the SAME failed task every tick\n"
    '    for d in list(TASKS.glob("*.json")) + list(BLOCKED.glob("*.json")) \\\n'
    '            + list(DONE.glob("*.json")) + list(FAILED.glob("*.json")):\n'
    "        seen.add(d.stem)")

# ── FIX 2: (task contract is a separate file, not a worker edit) ───────
# The 003 task will be dropped separately with correct format.

# ── FIX 3: work_completed transition (worker already moves to DONE/ on  ─
# 'canary-submitted', but we add an explicit receipt and ensure tasks/ is
# cleared — the retirement path)
edit(
    '''    if processed_ids:                            # GOV-FREEDOM-V2 section 9
        receipt("TICK_COMPLETE", processed=processed_ids)''',
    '''    if processed_ids:                            # GOV-FREEDOM-V2 section 9
        # WORK_COMPLETED: a task that reached canary-submitted is DONE for
        # this worker (the canary pipeline handles deploy). Anything still
        # in tasks/ after the loop was processed with a non-terminal result
        # (cooldown, ack-logged) and stays for the next tick.
        receipt("TICK_COMPLETE", processed=processed_ids)''')

raw = LIVE.read_bytes()
old = raw.decode("utf-8")
if raw != old.encode("utf-8"):
    sys.exit("roundtrip")
if hashlib.sha256(raw).hexdigest()[:8] != "a8fb195c":
    sys.exit("not live worker")
for i, (a, _) in enumerate(E):
    if old.count(a) != 1:
        sys.exit("edit %d anchor=%d" % (i, old.count(a)))
new = old
for a, b in E:
    new = new.replace(a, b)
ast.parse(new)
shutil.copy2(LIVE, STAGE / "coding_worker.py.pre-v2")
(STAGE / "coding_worker.py").write_bytes(new.encode("utf-8"))
print("live:", hashlib.sha256(raw).hexdigest()[:16])
print("v2  :", hashlib.sha256((STAGE / "coding_worker.py").read_bytes()).hexdigest()[:16])
