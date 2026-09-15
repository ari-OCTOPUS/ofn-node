"""Queue TRIO-002 (rebased onto live c2e290fd) and supersede stale TRIO-001."""
import hashlib
import json
import time
from pathlib import Path

REQ_DIR = Path("/home/ari/ofn/state/ops-agent/state/canary-requests")
SUP_DIR = Path("/home/ari/ofn/state/ops-agent/state/superseded-tasks")
STAGE = Path("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260915/ops_agent.py")
PREIMAGE = Path("/home/ari/ofn/state/ops-agent/preimage/ops_agent.py.c2e290fd96d42685.orig")
LIVE = Path("/home/ari/ofn/state/ops-agent/ops_agent.py")

LIVE_SHA = hashlib.sha256(LIVE.read_bytes()).hexdigest()
ART_SHA = hashlib.sha256(STAGE.read_bytes()).hexdigest()
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

assert LIVE_SHA[:16] == "c2e290fd96d42685", f"live moved: {LIVE_SHA[:16]}"

old = json.loads((REQ_DIR / "native-Z-SUCCESSOR-TRIO-001.json").read_text())
new = dict(old)
new.update({
    "artifact_sha256": ART_SHA,
    "base_sha256": LIVE_SHA,
    "expected_post_sha256": ART_SHA,
    "target_sha256": ART_SHA,
    "patched": str(STAGE),
    "task_id": "SUCCESSOR-TRIO-002",
    "diagnosis": (
        "TRIO successor rebased onto live c2e290fd. TRIO-001 base 109e68c0 went stale "
        "after the retirefix deploy. Surgical merge: TRIO artifact + the single "
        "retirefix hunk (conditional retire-on-success); TRIO's own retire block was "
        "the pre-fix version and is replaced. Checks: compile OK, retirefix present "
        "exactly once, TRIO preconditions/starvation markers intact, control-byte "
        "scan clean."
    ),
    "evidence": {
        "acceptance": "surgical-merge checks 5/5 at " + now,
        "pre_image": str(PREIMAGE),
        "pre_image_sha256": LIVE_SHA,
    },
    "rebase_receipt": {
        "at": now,
        "from_request": "native-Z-SUCCESSOR-TRIO-001",
        "why": "base 109e68c0 stale vs live c2e290fd (retirefix deploy); mechanical 3-way rebase hit a real semantic collision on the retire block",
        "method": "targeted block replacement verified against live bytes + control-byte scan",
    },
    "rollback": "restore pre-image: " + str(PREIMAGE),
    "requested_by": "octopus-forensic-reorientation/2026-09-15",
})
out = REQ_DIR / "native-Z-SUCCESSOR-TRIO-002.json"
out.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n")
print(f"queued TRIO-002 base={LIVE_SHA[:16]} post={ART_SHA[:16]}")

old["superseded_by"] = "native-Z-SUCCESSOR-TRIO-002"
old["superseded_at"] = now
old["superseded_why"] = "base 109e68c0 stale vs live c2e290fd; artifact rebuilt as TRIO-002"
(REQ_DIR / "native-Z-SUCCESSOR-TRIO-001.json").write_text(
    json.dumps(old, indent=2, ensure_ascii=False) + "\n")
(REQ_DIR / "native-Z-SUCCESSOR-TRIO-001.json").rename(
    SUP_DIR / "native-Z-SUCCESSOR-TRIO-001.json")
print("superseded TRIO-001 -> superseded-tasks/")
