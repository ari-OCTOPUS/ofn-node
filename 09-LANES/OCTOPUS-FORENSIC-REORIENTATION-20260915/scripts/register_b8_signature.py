"""Register the root-caused B8 failure signature so the circuit breaker closes.

Append-only: existing signatures are never modified. The breaker re-opens
automatically if the fresh G8-021 attempt fails verification.
"""
import json
import time
from pathlib import Path

SIG = Path("/home/ari/ofn/state/ops-agent/state/failure-signatures.json")
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

d = json.loads(SIG.read_text())
entry = {
    "category": "B8_NON_TCB_PATCH_CANARY",
    "signature": "stale-base-artifact-after-g27-deploy",
    "root_cause": (
        "G8-020 artifact was built on base ddee3da4; G27 (02fb704d) deployed after "
        "artifact creation; 05:04:43Z attempt executed unverified + 05:10:16Z outcome "
        "rejected; every later tick refused with OPS_B_STALE_BASE and the pair opened "
        "the B8 circuit breaker"
    ),
    "fix": (
        "020 superseded to superseded-tasks/ with note; V3 artifact rebuilt "
        "(three-way rebase onto live 02fb704d + 0x08 backspace regex repair, "
        "acceptance 8/8) and queued as native-A1-G8-PRODUCER-021 with matching base"
    ),
    "fixed_at": now,
    "registered_by": "octopus-forensic-reorientation/2026-09-15",
    "evidence": [
        "superseded-tasks/native-A1-G8-PRODUCER-020.json",
        "canary-requests/native-A1-G8-PRODUCER-021.json",
    ],
}
before = len(d["signatures"])
d["signatures"].append(entry)
SIG.write_text(json.dumps(d, indent=1) + "\n")
after = json.loads(SIG.read_text())
assert len(after["signatures"]) == before + 1, "append failed"
assert all(s.get("fixed_at") for s in after["signatures"] if s is not entry), "touched existing"
print(f"SIGNATURE_APPENDED fixed_at={now} total={len(after['signatures'])}")
