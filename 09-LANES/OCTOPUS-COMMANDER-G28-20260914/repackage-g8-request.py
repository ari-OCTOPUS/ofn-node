"""Repackage the queued G8 producer request onto the G8+G27+G30 artifact.

The queued request keeps its filename (native-A2-G8-PRODUCER-010.json) so the
W24 binder dependency (resolved by name, G29) stays intact. Base stays the LIVE
glass_runner bytes (ddee3da4, unchanged this session). All identity fields move
to the new artifact; provenance records the supersede. Chain receipt appended.
"""
import hashlib
import importlib.util
import json
import pathlib
import sys

OA = "/home/ari/ofn/state/ops-agent/ops_agent.py"
GLASS_LIVE = pathlib.Path("/home/ari/ofn/ofn/agents/glass_runner.py")
ART = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/W24-G8G27-PRODUCER/glass_runner.py")
REQ = pathlib.Path("/home/ari/ofn/state/ops-agent/state/canary-requests/native-A2-G8-PRODUCER-010.json")

live = hashlib.sha256(GLASS_LIVE.read_bytes()).hexdigest()
art = hashlib.sha256(ART.read_bytes()).hexdigest()
assert live.startswith("ddee3da4"), "live glass moved: " + live
assert art.startswith("68132b86"), "artifact moved: " + art

spec = importlib.util.spec_from_file_location("oa_repkg", OA)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

req = json.loads(REQ.read_text(encoding="utf-8"))
req["artifact_sha256"] = art
req["target_sha256"] = art
req["expected_post_sha256"] = art
req["patched"] = str(ART)
req["supersedes"] = {
    "artifact": "69c8ec8fff7b9bf963c6da1bb27f806f279116d963fe01d5e509f66af470eac2",
    "at": m.now_iso(), "by": "octopus-commander-editor/2026-09-14",
    "reason": ("G30: the accepted 69c8ec8f artifact carried 4 literal 0x08 "
               "backspace bytes where word-boundary escapes belonged, so the "
               "hex matcher never matched and EVERY owner message routed to "
               "the MONEY lane (the exact G8 leak); G27: durability contract "
               "added (durable-before-confirm, prefix rule, fsync, update_id "
               "dedupe, durable checkpoint)."),
    "g30_preimage": "/home/ari/ofn/state/coding-worker/stage/W24-G8G27-PRODUCER/glass_runner.py.pre-g30 (bb8fd076d56e5798)",
    "g8_base_artifact": "/home/ari/ofn/state/coding-worker/stage/W24-G8-ROUTING-v2/glass_runner.py (69c8ec8f, preserved unmodified)"}
req["stage_tests"] = {
    "battery": "g27-battery.py 15/15 PASS (S1..S9 of mission S7 + isolation)",
    "import_smoke": "9 successful module loads inside the battery",
    "at": m.now_iso()}
REQ.write_text(json.dumps(req, indent=1, sort_keys=True) + "\n", encoding="utf-8")

m.append_jsonl(
    m.RECEIPTS,
    {"schema": "octopus.ops-receipt.v1", "kind": "OPS_B_REQUEST_ARTIFACT_UPDATED",
     "agent": "octopus-commander-editor/2026-09-14", "at": m.now_iso(),
     "request": REQ.name,
     "old_artifact": "69c8ec8fff7b9bf9...", "new_artifact": art,
     "why": "G30 byte corruption fix + G27 durability (supersede recorded in-file)",
     "evidence": "E/OCTOPUS-COMMANDER-20260913/ROUND26-CHECKPOINT.json"},
    hash_field="ops_hash", prev_field="previous_ops_hash")
ok, n = m.verify_own_chain()
print("chain_verify:", ok, n)
print("request now points at:", art[:16], "base:", live[:16])
