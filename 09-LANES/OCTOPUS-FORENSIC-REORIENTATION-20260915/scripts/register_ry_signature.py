"""Third signature entry keyed 'RY' — the string the code actually queries.

ops_agent.py line 587 calls budget_allows(category[-2:], ...) with the long
category "B8_NON_TCB_PATCH_CANARY", so the breaker/unbreaker registry is
queried under "RY" (from "...CANARY"). This entry documents the same
root-caused fix under the key the code reads. The 'B8' entry from earlier
is harmless and stays (append-only registry).
"""
import json
import time
from pathlib import Path

SIG = Path("/home/ari/ofn/state/ops-agent/state/failure-signatures.json")
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

d = json.loads(SIG.read_text())
entry = {
    "category": "RY",
    "category_note": (
        "queried as category[-2:] of 'B8_NON_TCB_PATCH_CANARY' -> 'RY' "
        "(ops_agent.py:587). Any future B8 breaker trip is also untripped via 'RY'."
    ),
    "signature": "stale-base-artifact-after-g27-deploy",
    "root_cause": (
        "G8-020 artifact built on base ddee3da4; G27 (02fb704d) deployed after creation; "
        "05:04:43Z executed-unverified + 05:10:16Z outcome-rejected; breaker keyed 'RY' "
        "stayed open because no signature existed under that key"
    ),
    "fix": (
        "020 superseded; V3 artifact (rebase onto 02fb704d + 0x08 regex repair, 8/8 "
        "acceptance) queued as native-A1-G8-PRODUCER-021 base-matched"
    ),
    "fixed_at": now,
    "registered_by": "octopus-forensic-reorientation/2026-09-15",
    "evidence": [
        "superseded-tasks/native-A1-G8-PRODUCER-020.json",
        "canary-requests/native-A1-G8-PRODUCER-021.json",
    ],
}
d["signatures"].append(entry)
SIG.write_text(json.dumps(d, indent=1) + "\n")

after = json.loads(SIG.read_text())
assert after["signatures"][-1]["category"] == "RY"
print(f"RY_SIGNATURE_APPENDED fixed_at={now}")
