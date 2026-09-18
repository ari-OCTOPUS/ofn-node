"""Queue SUCCESSOR-TRIO (B5+CATSCOPE+G3 combined) — staged, NOT deployed.
Name sorts AFTER G8/W24/G30-wiring so filename order matches the dependency
order. After ITS deploy the executor bytes change -> the G30-wiring request's
dep pin (109e68c0) blocks until re-proven (fail-closed by design; documented
in this request)."""
import hashlib
import importlib.util
import json
import pathlib

OA = "/home/ari/ofn/state/ops-agent/ops_agent.py"
LIVE = pathlib.Path(OA)
ART = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                   "SUCCESSOR-TRIO-20260914/ops_agent.py")
REQ = pathlib.Path("/home/ari/ofn/state/ops-agent/state/canary-requests/"
                   "native-Z-SUCCESSOR-TRIO-001.json")

live = hashlib.sha256(LIVE.read_bytes()).hexdigest()
art = hashlib.sha256(ART.read_bytes()).hexdigest()
assert live.startswith("109e68c0") and art.startswith("d0b86a35")

spec = importlib.util.spec_from_file_location("oa_s", OA)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

req = {
    "task_id": "SUCCESSOR-TRIO-001",
    "target": str(LIVE),
    "base_sha256": live,
    "artifact_sha256": art,
    "target_sha256": art,
    "expected_post_sha256": art,
    "patched": str(ART),
    "component": "ops-agent",
    "priority": 9,
    "diff_scope": ["state/ops-agent/ops_agent.py"],
    "dependencies": ["/home/ari/ofn/state/ops-agent/state/dep-evidence/"
                     "B8-CAPABILITY-20260914.json"],
    "supersedes": {"requests": ["native-B5-MEASURED-RECOVERY-001 (superseded-tasks)",
                                "native-TASK-OPS-BUDGET-CATSCOPE-005 (superseded-tasks)",
                                "native-A4-AB-COMPOSITE-011 (superseded-tasks)"],
                   "at": m.now_iso(),
                   "reason": "their bases died under later verified fixes; deltas "
                             "rebuilt onto 109e68c0 as ONE combined successor "
                             "(saves quota slots); B5 delta REPAIRED: the old "
                             "artifact set cache-bytes-freed only on action_spec "
                             "while the executed action-record still verified "
                             "paths-absent - both are connected now"},
    "provenance": {"class": "REAL_CODE_DEFECT",
                   "source": "superseded trio deltas (B5 paths-absent "
                             "unfalsifiable; CATSCOPE budget suffix scoping; "
                             "G3 filename-order priority)",
                   "source_ts": "2026-09-14T10:30:00Z",
                   "source_hash": art},
    "stage_tests": {"matrix": "g28-accept-v2 32/32 PASS on d0b86a35 "
                              "(incl K: priority beats filename); live "
                              "baseline fails exactly K = the honest "
                              "counterexample of what this adds",
                    "at": m.now_iso()},
    "rollback": {"mechanism": "B4 rollback-requests entry",
                 "pre_image": str(ART.parent / "ops_agent.py.baseline-109e68c0"),
                 "pre_image_sha256": live},
    "post_deploy_note": "executor bytes move to d0b86a35 -> G30-wiring request "
                        "dep pin (109e68c0) blocks until repinned to d0b86a35 "
                        "with provenance (fail-closed, expected)",
    "requested_by": "octopus-commander-editor/2026-09-14"}
REQ.write_text(json.dumps(req, indent=1, sort_keys=True) + "\n", encoding="utf-8")
m.append_jsonl(m.RECEIPTS,
               {"schema": "octopus.ops-receipt.v1", "kind": "OPS_B_REQUEST_QUEUED",
                "agent": "octopus-commander-editor/2026-09-14", "at": m.now_iso(),
                "request": REQ.name, "artifact": art,
                "why": "successor trio rebuilt on live baseline; matrix 32/32"},
               hash_field="ops_hash", prev_field="previous_ops_hash")
ok, n = m.verify_own_chain()
print("chain_verify:", ok, n)
print("queue:", sorted(p.name for p in REQ.parent.glob("*.json")))
