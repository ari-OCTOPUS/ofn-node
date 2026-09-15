"""Classify the 5 failed/ ops files: category, status, cause, disposability."""
import json
from pathlib import Path

F = Path("/home/ari/ofn/state/ops-agent/state/failed")
for f in sorted(F.glob("*.json")):
    d = json.loads(f.read_text())
    exp = d.get("exp") or {}
    print("==", f.name)
    print("   category:", d.get("category"), "| proposal:", exp.get("proposal_id"))
    print("   target:", exp.get("target_component"), "@", exp.get("target_node"))
    print("   outcome_proposal:", d.get("outcome_proposal"),
          "| approval:", str(d.get("approval_hash"))[:12])
    for k in ("status", "state", "failed_at", "reason", "error", "verdict", "witness_verdict"):
        if d.get(k) is not None:
            print(f"   {k}: {str(d[k])[:120]}")
