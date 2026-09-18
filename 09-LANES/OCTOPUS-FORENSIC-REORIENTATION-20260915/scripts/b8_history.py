"""Full history of B8 OPS_B_EXECUTED receipts: did any ofn/ofn deploy ever verify?"""
import json
from pathlib import Path

S = Path("/home/ari/ofn/state/ops-agent/state")
for line in (S / "ops-receipts.jsonl").read_text().splitlines():
    d = json.loads(line)
    if d.get("kind") == "OPS_B_EXECUTED":
        argv = d.get("argv") or []
        target = argv[0][-1] if argv and argv[0] else "?"
        print(d.get("at"), "| verified:", d.get("verified"), "| exit:", d.get("exit_codes"),
              "| target:", str(target)[:70])
