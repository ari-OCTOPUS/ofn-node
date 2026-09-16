#!/usr/bin/env python3
"""INCIDENT REPAIR 2026-09-16: ops receipt chain broken at row 3932 by
senior-agent's hand-written OPS_B_REQUEST_QUEUED (wrong canonical form:
spaced separators instead of compact). FAIL_CLOSED has the organism down.

Repair (minimal, content-preserving, fully documented):
 1. snapshot the whole ledger + the broken row verbatim (evidence)
 2. recompute ONLY row 3932's ops_hash with the correct canon() — content
    byte-identical, no field touched
 3. verify chain end-to-end with the organism's own rule
 4. append an OPS_CHAIN_INCIDENT receipt (correct mechanics) documenting it
"""
import json, hashlib, shutil, time
from pathlib import Path

RECEIPTS = Path("/home/ari/ofn/state/ops-agent/state/ops-receipts.jsonl")
EVDIR = Path("/home/ari/ofn/state/ops-agent/state/incidents")
NOW = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())

def canon(o):
    return json.dumps(o, sort_keys=True, ensure_ascii=True, separators=(",", ":"))

def sha_obj(o):
    return hashlib.sha256(canon(o).encode()).hexdigest()

lines = RECEIPTS.read_text(encoding="utf-8").splitlines()
rows = [json.loads(l) for l in lines if l.strip()]
assert len(rows) == 3932, f"expected 3932 rows, got {len(rows)}"
bad = rows[3931]
assert bad.get("kind") == "OPS_B_REQUEST_QUEUED" and "B5-SCOPE-GUARD" in str(bad.get("request")), "row 3932 is not the incident row"
assert bad.get("agent") == "octopus-senior-agent/2026-09-16", "not my row"

EVDIR.mkdir(parents=True, exist_ok=True)
stamp = NOW.replace(":", "")
shutil.copy2(RECEIPTS, EVDIR / f"ops-receipts.pre-chain-repair.{stamp}.jsonl")
(EVDIR / f"broken-row-3932.verbatim.{stamp}.json").write_text(
    json.dumps(bad, indent=1, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")

correct_hash = sha_obj({k: v for k, v in bad.items() if k != "ops_hash"})
old_hash = bad["ops_hash"]
rows[3931]["ops_hash"] = correct_hash
with RECEIPTS.open("w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, sort_keys=True, ensure_ascii=True) + "\n")

# full re-verify with the organism's rule
ok = True
prev = None
for i, r in enumerate(rows, 1):
    if r.get("previous_ops_hash") != prev:
        ok = False; print(f"prev-link broken at {i}"); break
    if r.get("ops_hash") != sha_obj({k: v for k, v in r.items() if k != "ops_hash"}):
        ok = False; print(f"hash broken at {i}"); break
    prev = r["ops_hash"]
assert ok, "chain still broken — STOP"

inc = {"schema": "octopus.ops-receipt.v1", "kind": "OPS_CHAIN_INCIDENT_REPAIRED",
       "agent": "octopus-senior-agent/2026-09-16", "at": NOW,
       "incident": "row 3932 ops_hash computed with spaced separators (default json.dumps) "
                   "instead of canon() compact separators; FAIL_CLOSED halted every tick "
                   "08:52:56Z and 08:58:14Z",
       "repair": "ops_hash of row 3932 recomputed with correct canon(); all other fields "
                 "byte-identical; content untouched; full-ledger + broken-row snapshots kept",
       "evidence": [str(EVDIR / f"ops-receipts.pre-chain-repair.{stamp}.jsonl"),
                    str(EVDIR / f"broken-row-3932.verbatim.{stamp}.json")],
       "old_broken_hash": old_hash, "new_correct_hash": correct_hash,
       "downstream_rows_affected": 0}
inc["previous_ops_hash"] = prev
inc["ops_hash"] = sha_obj({k: v for k, v in inc.items() if k != "ops_hash"})
with RECEIPTS.open("a", encoding="utf-8") as f:
    f.write(json.dumps(inc, sort_keys=True, ensure_ascii=True) + "\n")

print(json.dumps({"repaired": True, "row": 3932, "old": old_hash[:16],
                  "new": correct_hash[:16], "incident_receipt": inc["ops_hash"][:16],
                  "verified_full_chain": True}))
