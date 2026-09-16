"""Second signature entry with the SHORT category 'B8'.

The agent's execution path calls budget_allows(category[-2:], ...) — the
existing B5 signature proves the registry is keyed by short category. The
long-form entry appended earlier is harmless (never matches) and stays.
"""
import json
import time
from pathlib import Path

SIG = Path("/home/ari/ofn/state/ops-agent/state/failure-signatures.json")
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

d = json.loads(SIG.read_text())
entry = {
    "category": "B8",
    "signature": "stale-base-artifact-after-g27-deploy",
    "root_cause": (
        "G8-020 artifact built on base ddee3da4; G27 (02fb704d) deployed after creation; "
        "05:04:43Z executed-unverified + 05:10:16Z outcome-rejected opened the B8 breaker. "
        "Short-form category entry because budget_allows is called with category[-2:]."
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
assert after["signatures"][-1]["category"] == "B8"
print(f"SHORT_SIGNATURE_APPENDED fixed_at={now} categories={[s['category'] for s in after['signatures']]}")
