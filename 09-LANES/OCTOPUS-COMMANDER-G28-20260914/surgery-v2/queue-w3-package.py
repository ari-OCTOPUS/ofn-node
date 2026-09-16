"""Queue the W3 ACK-gate worker package (Class B, behind TRIO in the DAG).
Two deploy units needed: TRIO (consumer) then W3-worker (gate). The TRIO
is already queued; this queues the worker gate."""
import hashlib
import importlib.util
import json
import pathlib

OA = "/home/ari/ofn/state/ops-agent/ops_agent.py"
TRIO_ART = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                        "SUCCESSOR-TRIO-20260914/ops_agent.py")
WORKER_ART = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                          "W3-ACK-GATE-001/coding_worker.py")
LIVE_WORKER = pathlib.Path("/home/ari/ofn/state/coding-worker/coding_worker.py")
SP = pathlib.Path("/home/ari/ofn/state/ops-agent/state/canary-requests")

trio_sha = hashlib.sha256(TRIO_ART.read_bytes()).hexdigest()
worker_sha = hashlib.sha256(WORKER_ART.read_bytes()).hexdigest()
live_sha = hashlib.sha256(LIVE_WORKER.read_bytes()).hexdigest()
assert trio_sha.startswith("f6bc8d1c") and worker_sha.startswith("3d0a5b9a")
assert live_sha.startswith("a8fb195c")

spec = importlib.util.spec_from_file_location("oa_w3q", OA)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

req = {
    "task_id": "W3-ACK-GATE-001",
    "target": str(LIVE_WORKER),
    "base_sha256": live_sha,
    "artifact_sha256": worker_sha,
    "target_sha256": worker_sha,
    "expected_post_sha256": worker_sha,
    "patched": str(WORKER_ART),
    "component": "coding-worker",
    "priority": 10,
    "diff_scope": ["state/coding-worker/coding_worker.py"],
    "dependencies": ["native-Z-SUCCESSOR-TRIO-001.json"],
    "dependency_note": "deploy-ordering on TRIO: the ACK gate reads the "
                       "decision_tasks registry that consume_decisions "
                       "(inside TRIO) writes; the worker gate is inert "
                       "without the consumer deployed first",
    "provenance": {"class": "REAL_CODE_DEFECT",
                   "source": "W3 counterexample: worker unblocks a task with "
                             "awaiting_owner_ack without any ACK",
                   "source_ts": "2026-09-14T13:35:00Z",
                   "source_hash": worker_sha},
    "stage_tests": {
        "e2e": "w3-e2e.py 8/8 PASS under kernel fence (nobody): C1 no-ACK "
               "zero-unpark, C2 ACK->continuation, C4 dep-unmet stays "
               "blocked, C5 delayed-registration recovered, C6 no-audit-"
               "spam, C7 replay zero-effect, C8 dependency-only regression",
        "at": m.now_iso()},
    "rollback": {"mechanism": "B4 rollback-requests entry",
                 "pre_image": str(WORKER_ART.parent / "coding_worker.py.pre-ack-gate"),
                 "pre_image_sha256": live_sha},
    "requested_by": "octopus-commander-editor/2026-09-14"}
p = SP / "native-W3-ACK-GATE-001.json"
p.write_text(json.dumps(req, indent=1, sort_keys=True) + "\n", encoding="utf-8")
m.append_jsonl(m.RECEIPTS,
               {"schema": "octopus.ops-receipt.v1", "kind": "OPS_B_REQUEST_QUEUED",
                "agent": "octopus-commander-editor/2026-09-14",
                "at": m.now_iso(), "request": p.name, "artifact": worker_sha,
                "why": "W3 ACK gate in worker's own dependency_blocked; "
                       "e2e 8/8 fenced"},
               hash_field="ops_hash", prev_field="previous_ops_hash")
ok, n = m.verify_own_chain()
print("chain:", ok, n)
print("queue:", sorted(x.name for x in SP.glob("*.json")))
