"""G22 live-enforcement behavioral probe — negative test, zero intended effect.

A synthetic canary request whose ONLY defect is a dependency on a request file
that does not exist. Expected from a live G22: disposition OPS_B_DEPENDENCY_UNMET,
request retained, no copy, no quota consumption. If the executor runs the copy
anyway, G22 is NOT enforced at runtime — the effect is a harmless probe file in
state/probe-scratch (documented, reversible).

Component is a distinct 'g22-probe' so it cannot consume the ofn-agents budget
window that G8-021 is waiting for.
"""
import hashlib
import json
import time
from pathlib import Path

S = Path("/home/ari/ofn/state/ops-agent/state")
SCRATCH = S / "probe-scratch"
SCRATCH.mkdir(exist_ok=True)

base_file = SCRATCH / "g22-probe-target.txt"
base_file.write_text("g22-probe-base-v1\n")
art_file = SCRATCH / "g22-probe-artifact.txt"
art_file.write_text("g22-probe-patched-v1\n")

base_sha = hashlib.sha256(base_file.read_bytes()).hexdigest()
art_sha = hashlib.sha256(art_file.read_bytes()).hexdigest()
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

req = {
    "task_id": "TASK-G22-ENFORCEMENT-PROBE-001",
    "category": "B8_NON_TCB_PATCH_CANARY",
    "component": "g22-probe",
    "target": str(base_file),
    "target_sha256": art_sha,
    "base_sha256": base_sha,
    "artifact_sha256": art_sha,
    "expected_post_sha256": art_sha,
    "patched": str(art_file),
    "diff_scope": [str(base_file)],
    "dependencies": ["native-XX-DEPENDENCY-NEVER-EXISTS-99999.json"],
    "priority": 9,
    "diagnosis": "G22 runtime-enforcement behavioral probe: dependency references a nonexistent request; expect OPS_B_DEPENDENCY_UNMET with no execution",
    "evidence": {
        "acceptance": "probe acceptance = blocked-with-disposition, request retained, target file byte-identical after tick",
        "pre_image": str(base_file),
        "pre_image_sha256": base_sha,
    },
    "provenance": {"class": "BEHAVIORAL_PROBE", "source": "FORENSIC-REORIENTATION-20260915 wave-1", "source_ts": now},
    "rollback": "restore " + str(base_file) + " from its own bytes (kept in probe-scratch)",
    "requested_by": "octopus-forensic-reorientation/2026-09-15",
    "probe_note": "cleanup: supersede after disposition; scratch dir owned by this probe",
}
out = S / "canary-requests" / "native-PROBE-G22-ENFORCEMENT-001.json"
out.write_text(json.dumps(req, indent=2) + "\n")
print(f"PROBE_QUEUED base={base_sha[:16]} target={base_file}")
print("watch: next ops-agent tick must emit OPS_B_DEPENDENCY_UNMET for this task")
