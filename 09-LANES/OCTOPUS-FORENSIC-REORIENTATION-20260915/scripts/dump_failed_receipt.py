"""Dump the last OPS_B_EXECUTED receipt and newest failed request."""
import json
from pathlib import Path

S = Path("/home/ari/ofn/state/ops-agent/state")
lines = (S / "ops-receipts.jsonl").read_text().splitlines()
for line in reversed(lines):
    d = json.loads(line)
    if d.get("kind") == "OPS_B_EXECUTED":
        print(json.dumps(d, indent=1, ensure_ascii=False)[:1600])
        break

failed = sorted((S / "failed").glob("*.json"), key=lambda p: p.stat().st_mtime)
if failed:
    f = json.loads(failed[-1].read_text())
    print("\n--NEWEST FAILED FILE--", failed[-1].name)
    print(json.dumps({k: f.get(k) for k in
                      ("task_id", "category", "witness_verdict", "error",
                       "failure", "note", "detail", "rollback")}, indent=1)[:800])
