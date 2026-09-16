"""Queue the G30 stage-guard wiring request (NOT deployed - behind quota and
behind the G8/W24 pair; chain_position/priority are informational only, the
ENFORCED ordering is the dependency edge: executor bytes must hold 109e68c0)."""
import hashlib
import importlib.util
import json
import pathlib

OA = "/home/ari/ofn/state/ops-agent/ops_agent.py"
LIVE = pathlib.Path("/home/ari/ofn/state/coding-worker/coding_worker.py")
ART = pathlib.Path("/home/ari/ofn/state/coding-worker/stage/"
                   "G30-STAGE-GUARD-WIRING-001/coding_worker.py")
REQ = pathlib.Path("/home/ari/ofn/state/ops-agent/state/canary-requests/"
                   "native-G30-STAGE-GUARD-WIRING-001.json")

live = hashlib.sha256(LIVE.read_bytes()).hexdigest()
art = hashlib.sha256(ART.read_bytes()).hexdigest()
exec_sha = hashlib.sha256(pathlib.Path(OA).read_bytes()).hexdigest()
assert live.startswith("a8fb195c") and art.startswith("396e0a11")
assert exec_sha.startswith("109e68c0")

spec = importlib.util.spec_from_file_location("oa_q", OA)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

req = {
    "task_id": "G30-STAGE-GUARD-WIRING-001",
    "target": str(LIVE),
    "base_sha256": live,
    "artifact_sha256": art,
    "target_sha256": art,
    "expected_post_sha256": art,
    "patched": str(ART),
    "component": "coding-worker",
    "diff_scope": ["state/coding-worker/coding_worker.py"],
    "dependencies": ["/home/ari/ofn/state/ops-agent/state/dep-evidence/"
                     "B8-CAPABILITY-20260914.json"],
    "provenance": {"class": "REAL_CODE_DEFECT",
                   "source": "G30: 4 literal 0x08 bytes in accepted artifact "
                             "69c8ec8f; root cause = JSON \\b decode in "
                             "files[].replacement at coding_worker.py:406",
                   "source_ts": "2026-09-14T08:00:00Z",
                   "source_hash": art},
    "diagnosis": ("byte-level guard on the STAGED file inside the worker's "
                  "staging loop: control bytes (JSON backspace class) and "
                  "mixed EOLs raise before any test/proposal"),
    "stage_tests": {"path_test": "test-stageguard-wiring.py PASS: backspace "
                                 "replacement -> STAGE_BYTES_DIRTY before "
                                 "proposal; correct \\b text -> staged clean "
                                 "with literal backslash+b -> canary",
                    "at": m.now_iso()},
    "rollback": {"mechanism": "B4 rollback-requests entry",
                 "pre_image": str(ART.parent / "coding_worker.py.pre-g30guard"),
                 "pre_image_sha256": live},
    "requested_by": "octopus-commander-editor/2026-09-14",
    "ordering_note": "deploys AFTER the G8/W24 pair (quota-gated); the dep pin "
                     "on executor 109e68c0 enforces the executor capability"}
REQ.write_text(json.dumps(req, indent=1, sort_keys=True) + "\n", encoding="utf-8")
m.append_jsonl(m.RECEIPTS,
               {"schema": "octopus.ops-receipt.v1", "kind": "OPS_B_REQUEST_QUEUED",
                "agent": "octopus-commander-editor/2026-09-14", "at": m.now_iso(),
                "request": REQ.name, "artifact": art,
                "why": "G30 boundary closed on the real worker staging path"},
               hash_field="ops_hash", prev_field="previous_ops_hash")
ok, n = m.verify_own_chain()
print("chain_verify:", ok, n)
print("queued:", REQ.name, "artifact", art[:16], "base", live[:16])
print("canary queue:", sorted(p.name for p in REQ.parent.glob("*.json")))
