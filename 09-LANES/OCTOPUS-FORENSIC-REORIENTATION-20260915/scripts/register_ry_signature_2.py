"""Second RY signature: the 06:15:31Z cp-exit-1 failure was the unit sandbox gap.

Root cause fixed at 06:20Z (unit backup .pre-agentspath-20260915 beside the unit,
ReadWritePaths += /home/ari/ofn/ofn/agents, daemon-reload). This failure's
fixed_at must postdate 06:21:01Z (its outcome rejection) to stop it counting.
"""
import json
import time
from pathlib import Path

SIG = Path("/home/ari/ofn/state/ops-agent/state/failure-signatures.json")
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

d = json.loads(SIG.read_text())
entry = {
    "category": "RY",
    "signature": "cp-exit-1-sandbox-missing-agents-path",
    "root_cause": (
        "06:15:31Z OPS_B_EXECUTED verified=False: cp of the V3 artifact to "
        "/home/ari/ofn/ofn/agents/glass_runner.py exited 1 because the unit's "
        "ProtectHome=read-only sandbox ReadWritePaths lacked /home/ari/ofn/ofn/agents "
        "(all three historical B8 canary attempts to the agents tree failed identically; "
        "state/-targets always succeeded)"
    ),
    "fix": (
        "06:20Z: octopus-ops-agent.service ReadWritePaths += /home/ari/ofn/ofn/agents, "
        "backup octopus-ops-agent.service.pre-agentspath-20260915, daemon-reload done; "
        "sandbox otherwise unchanged (same fix class as the 09-13 B5 unit fix)"
    ),
    "fixed_at": now,
    "registered_by": "octopus-forensic-reorientation/2026-09-15",
    "evidence": [
        "ops-receipts.jsonl OPS_B_EXECUTED 2026-09-15T06:15:31Z (exit_codes [1], verify sha fc993720)",
        "scripts/b8_history.py output: agents-tree attempts 3/3 exit 1",
        "/etc/systemd/system/octopus-ops-agent.service.pre-agentspath-20260915",
    ],
}
d["signatures"].append(entry)
SIG.write_text(json.dumps(d, indent=1) + "\n")

after = json.loads(SIG.read_text())
assert after["signatures"][-1]["fixed_at"] == now
print(f"RY_SIGNATURE_2_APPENDED fixed_at={now}")
