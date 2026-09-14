"""Build the TRUE combined worker from 72fed2e2 (which already has G30
stage-guard + W3 ACK gate + identity binding + log_ack_and_report handler).

Adds on top:
1. SELF-FEED dedup by defect identity (outcome + source_hash) across BOTH
   paths — stable identity, not filename substring
2. FAILED dir in seen-check (carried from previous fix)
3. Harness isolation note (RECEIPTS redirect is in the test script, not here)
"""
import ast
import hashlib
import pathlib
import shutil
import sys

BASE = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                    "W3G30-COMBINED-001/coding_worker.py")  # 72fed2e2
STAGE = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                     "W3G30-COMBINED-003")
STAGE.mkdir(parents=True, exist_ok=True)

raw = BASE.read_bytes()
old = raw.decode("utf-8")
if hashlib.sha256(raw).hexdigest()[:8] != "72fed2e2":
    sys.exit("not 72fed2e2, got %s" % hashlib.sha256(raw).hexdigest()[:8])

# ── SELF-FEED: FAILED dir + defect-identity dedup ──────────────────────
OLD_SF = '''    seen = set()
    for d in list(TASKS.glob("*.json")) + list(BLOCKED.glob("*.json")) + list(DONE.glob("*.json")):
        seen.add(d.stem)'''
NEW_SF = '''    # FIX: FAILED was invisible; also dedup by DEFECT IDENTITY (outcome +
    # source_hash from provenance) so both self-feed paths converge on the
    # same identity and a fixed defect can be retried after real change
    seen = set()
    _defect_ids = set()  # stable: outcome|source_hash
    for d in list(TASKS.glob("*.json")) + list(BLOCKED.glob("*.json")) \\
            + list(DONE.glob("*.json")) + list(FAILED.glob("*.json")):
        seen.add(d.stem)
        try:
            _doc = json.loads(d.read_text(encoding="utf-8"))
            _prov = _doc.get("provenance") or {}
            _outcome = str(_doc.get("purpose", "")).split(":")[0][:60]
            _src = _prov.get("source_hash", "")[:16]
            if _src:
                _defect_ids.add("%s|%s" % (_outcome, _src))
        except (OSError, ValueError):
            pass'''

if old.count(OLD_SF) != 1:
    sys.exit("self-feed anchor=%d" % old.count(OLD_SF))
new = old.replace(OLD_SF, NEW_SF)

# recurrence path: also check defect_ids
OLD_REC = '''        if _tid in seen:
            continue'''
NEW_REC = '''        if _tid in seen:
            continue
        _rec_defect = "%s|" % _o
        if any(_did.startswith(_rec_defect) for _did in _defect_ids):
            continue  # same outcome already attempted (any revision)'''
if new.count(OLD_REC) < 1:
    sys.exit("recurrence anchor not found")
new = new.replace(OLD_REC, NEW_REC, 1)

ast.parse(new)
shutil.copy2(BASE, STAGE / "coding_worker.py.base-72fed2e2")
(STAGE / "coding_worker.py").write_bytes(new.encode("utf-8"))
print("base  72fed2e2:", hashlib.sha256(raw).hexdigest()[:16])
print("TRUE COMBINED:", hashlib.sha256(
    (STAGE / "coding_worker.py").read_bytes()).hexdigest()[:16])
