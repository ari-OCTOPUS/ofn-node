#!/usr/bin/env python3
"""Stage B5-SCOPE-GUARD canary request + queue receipt on 138 (run ON 138)."""
import json, hashlib, time
from pathlib import Path

HOME = Path.home()
ROOT = HOME / "ofn" / "state" / "ops-agent"
STATE = ROOT / "state"
REQ = STATE / "canary-requests" / "native-B5-SCOPE-GUARD-001.json"
RECEIPTS = STATE / "ops-receipts.jsonl"
ARTIFACT = HOME / "ofn" / "state" / "coding-worker" / "stage" / "B5-SCOPE-GUARD-20260916" / "ops_agent.py"
TARGET = ROOT / "ops_agent.py"
NOW = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def sha_obj(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=True).encode()).hexdigest()

art = sha(ARTIFACT)
base = sha(TARGET)
assert art == "b2d48553458bb920d33611df1cfbd6808ed7a86e2ba64ea80e4f8c4ab902208e", "artifact sha mismatch: %s" % art
assert base == "afefa020caae7b41dfcc543eed224cf5947ab95cfac5a2b20b3a167bfb1811b4", "live base moved: %s" % base

req = {
    "task_id": "TASK-B5-SCOPE-GUARD-001",
    "category": "B8_NON_TCB_PATCH_CANARY",
    "component": "ops-agent",
    "target": str(TARGET),
    "target_sha256": base,
    "base_sha256": base,
    "artifact_sha256": art,
    "expected_post_sha256": art,
    "patched": str(ARTIFACT),
    "diff_scope": [str(TARGET)],
    "dependencies": [],
    "priority": 9,
    "diagnosis": "B5 root-cause-3: handle_b5_storage quarantines targets from wt-* worktrees, "
                 "but rename(2) needs write permission on the SOURCE dir; the unit sandbox "
                 "(ProtectHome=read-only) grants writes only under ReadWritePaths, so every "
                 "wt-* mv fails rc=1 (22:02:43Z: 7/8 fail) and the pair with the 22:08:21Z "
                 "outcome rejection honestly opened the B5 breaker. Fix: scope guard — targets "
                 "outside the writable roots get a B5_PATH_OUTSIDE_WRITABLE_SCOPE disposition "
                 "instead of a doomed mv; only in-scope targets (autonomy/ops-agent state) are "
                 "quarantined. Patch adds 24 lines to handle_b5_storage; compile OK; classifier "
                 "unit tests 7/7 incl. prefix-sibling trap.",
    "evidence": {
        "acceptance": "live sha == b2d4855 after deploy; next B5 tick emits "
                      "B5_PATH_OUTSIDE_WRITABLE_SCOPE for wt-* paths and either quarantines "
                      "in-scope targets or returns an honest non-failure disposition; no new "
                      "verified=false B5 rows",
        "pre_image": str(TARGET),
        "pre_image_sha256": base
    },
    "provenance": {
        "class": "ROOT_CAUSE_3_FIX",
        "source": "senior-agent session 2026-09-16 (owner: start and complete the B5 fix)",
        "source_ts": NOW
    },
    "rollback": "restore ops_agent.py from preimage (executor saves preimage on deploy); "
                "breaker re-opens automatically on any 2 new B5 failures",
    "requested_by": "octopus-senior-agent/2026-09-16",
    "owner_context": "owner approved B5 breaker reset 2026-09-16 (owner-decisions.jsonl "
                     "B5_RESET=APPROVED_BUT_HELD); reset deliberately withheld until this "
                     "root-cause fix is live and one cycle verified"
}
REQ.write_text(json.dumps(req, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")

# queue receipt with exact chain discipline (same as append_jsonl in ops_agent)
prev = None
last = None
for l in RECEIPTS.read_text(encoding="utf-8").splitlines():
    if l.strip():
        last = l
if last:
    prev = json.loads(last).get("ops_hash")
row = {"schema": "octopus.ops-receipt.v1", "kind": "OPS_B_REQUEST_QUEUED",
       "agent": "octopus-senior-agent/2026-09-16", "at": NOW,
       "request": "native-B5-SCOPE-GUARD-001.json",
       "artifact": art,
       "why": "B5 root-cause-3 scope-guard: skip outside-ReadWritePaths sources with honest disposition",
       "priority": 9}
row["previous_ops_hash"] = prev
row["ops_hash"] = sha_obj({k: v for k, v in row.items() if k != "ops_hash"})
with RECEIPTS.open("a", encoding="utf-8") as f:
    f.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")

print(json.dumps({"staged": str(REQ), "artifact_sha256": art, "base": base,
                  "receipt_ops_hash": row["ops_hash"][:16], "prev": (prev or "")[:16]}))
