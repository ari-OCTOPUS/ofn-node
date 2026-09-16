"""Repackage v2: point the queued G8 producer request at the final artifact
8da9471c (G8 routing + G30 byte fix + G27v2 durability + G31 hex-boundary fix).
Filename kept (W24 by-name dependency). Base stays live ddee3da4. Rollback field
gains the containment precondition (money gates must be live before restoring
the leaky pre-image). Chain receipt appended."""
import hashlib
import importlib.util
import json
import pathlib
import sys

OA = "/home/ari/ofn/state/ops-agent/ops_agent.py"
GLASS_LIVE = pathlib.Path("/home/ari/ofn/ofn/agents/glass_runner.py")
MONEY_GATE = pathlib.Path("/home/ari/ofn/state/revenue-drive/owner_reply.py")
ART = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/W24-G8G27-PRODUCER/glass_runner.py")
REQ = pathlib.Path("/home/ari/ofn/state/ops-agent/state/canary-requests/native-A2-G8-PRODUCER-010.json")

live = hashlib.sha256(GLASS_LIVE.read_bytes()).hexdigest()
art = hashlib.sha256(ART.read_bytes()).hexdigest()
gate = hashlib.sha256(MONEY_GATE.read_bytes()).hexdigest()
assert live.startswith("ddee3da4"), "live glass moved: " + live
assert art.startswith("8da9471c"), "artifact moved: " + art
assert gate.startswith("f8187600"), "money gates NOT live: " + gate

spec = importlib.util.spec_from_file_location("oa_repkg2", OA)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

req = json.loads(REQ.read_text(encoding="utf-8"))
req["artifact_sha256"] = art
req["target_sha256"] = art
req["expected_post_sha256"] = art
req["patched"] = str(ART)
prev_sup = req.get("supersedes", {})
req["supersedes"] = {
    "artifact": "68132b86feb83763360079e740eeba8480c5a25ab8eab6d42232164e4d9ac940",
    "at": m.now_iso(), "by": "octopus-commander-editor/2026-09-14",
    "reason": ("G27v2 owner-mission corrections: cross-lane dedupe, torn-tail "
               "repair, re-fsync on dedupe (counterexample-proven), dir-fsync "
               "disposition, transport validation; G31: >64-char hex runs "
               "silently missed by the trailing boundary, dropping B3 binds "
               "into the MONEY lane"),
    "previous_supersede": prev_sup,
    "preimages": ["glass_runner.py.pre-g27v2 (68132b86)",
                  "glass_runner.py.pre-g31 (6257db2c)"]}
req["stage_tests"] = {
    "battery": "g27b-battery.py 14/14 PASS (T1-T10 stateful transport, real "
               "subprocess crashes, v1-vs-v2 counterexample, routing matrix "
               "incl بفرست/ارسال, isolation guard)",
    "counterexample_proven": "v1 (68132b86) trusted an unproven-durable row on "
                             "dedupe (no re-fsync); v2 re-fsyncs (logged)",
    "at": m.now_iso()}
req["rollback"] = ("restore pre-image /home/ari/ofn/state/owner_dialogue/preimage/"
                   "glass_runner.py.ad34b1388cb9ac9d.orig ONLY AFTER verifying "
                   "state/revenue-drive/owner_reply.py bytes == f8187600... "
                   "(money gates live): the old producer routes everything to "
                   "the revenue lane and the gates are the containment")
REQ.write_text(json.dumps(req, indent=1, sort_keys=True) + "\n", encoding="utf-8")

m.append_jsonl(
    m.RECEIPTS,
    {"schema": "octopus.ops-receipt.v1", "kind": "OPS_B_REQUEST_ARTIFACT_UPDATED",
     "agent": "octopus-commander-editor/2026-09-14", "at": m.now_iso(),
     "request": REQ.name,
     "old_artifact": "68132b86feb83763", "new_artifact": art,
     "why": "G27v2 + G31 (owner-mission corrections; counterexample-proven)",
     "evidence": "E/OCTOPUS-COMMANDER-20260913/ROUND28-CHECKPOINT.json"},
    hash_field="ops_hash", prev_field="previous_ops_hash")
ok, n = m.verify_own_chain()
print("chain_verify:", ok, n)
print("queued artifact:", art[:16], "base:", live[:16], "money_gates:", gate[:16])
