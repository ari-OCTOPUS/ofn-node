"""Verify receipt chains of all 9 shipped runs against their local integrity.json anchors."""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "package", "octopus_qd_lab"))
from octopus_bridge import verify_ledger  # noqa: E402

root = os.path.join(os.path.dirname(__file__), "package", "octopus_qd_lab", "results")
for integ_path in sorted(glob.glob(os.path.join(root, "*_seed*", "integrity.json"))):
    run = os.path.basename(os.path.dirname(integ_path))
    integ = json.load(open(integ_path, encoding="utf-8"))
    ledger = os.path.join(os.path.dirname(integ_path), "receipts.jsonl")
    r = verify_ledger(ledger, expected_head=integ["head"], expected_count=integ["count"])
    print(f"{run:18s} -> {'VALID' if r['valid'] else 'INVALID'}  count={integ['count']}"
          + ("" if r["valid"] else f"  errors={r.get('errors', [])[:2]}"))
