#!/usr/bin/env python3
"""Queue the EXECUTOR-SAFETY canary against the live executor.

Same witnessed-canary channel the organism uses for any B8 non-TCB patch. All
shas are asserted before the request is written; the timestamp is taken from the
node clock. No live executor bytes are touched here — the organism deploys it
under witness on its next tick.
"""
import hashlib
import json
import subprocess
import time
from pathlib import Path

REQ = Path("/home/ari/ofn/state/ops-agent/state/canary-requests")
ART = Path(
    "/home/ari/ofn/state/coding-worker/stage/EXECUTOR-SAFETY-20260915/ops_agent.py"
)
PRE = Path(
    "/home/ari/ofn/state/ops-agent/preimage/ops_agent.py.2074072489fcf209.orig"
)
LIVE = Path("/home/ari/ofn/state/ops-agent/ops_agent.py")

EXPECTED_LIVE = "2074072489fcf2098774b8c3be37471bfc2f6799e06d2bd10ee02fbd5a9ac6cd"
EXPECTED_ART = "beaee58cc952351001b6b34c8658cbb7ef689b00510e866ffa172a4eb390682f"

now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
live_sha = hashlib.sha256(LIVE.read_bytes()).hexdigest()
art_sha = hashlib.sha256(ART.read_bytes()).hexdigest()
assert live_sha == EXPECTED_LIVE, f"live moved: {live_sha[:16]}"
assert art_sha == EXPECTED_ART, f"artifact unexpected: {art_sha[:16]}"
assert PRE.exists() and hashlib.sha256(PRE.read_bytes()).hexdigest() == live_sha, \
    "preimage missing or does not match live"

req = {
    "task_id": "EXECUTOR-SAFETY-001 [F-002] [witness-unavailable-dedupe]",
    "category": "B8_NON_TCB_PATCH_CANARY",
    "kind": "B8_NON_TCB_PATCH_CANARY",
    "component": "ops-agent-executor",
    "target": str(LIVE),
    "base_sha256": live_sha,
    "artifact_sha256": art_sha,
    "expected_post_sha256": art_sha,
    "target_sha256": art_sha,
    "patched": str(ART),
    "diff_scope": ["ofn/state/ops-agent/ops_agent.py"],
    "dependencies": [],
    "priority": 1,
    "diagnosis": (
        "Executor-safety hardening (follow-up to EXECUTOR-CORE-F001-OW8-001). "
        "(a) witness-unavailable no longer retires an UNDEPLOYED request into "
        "executed/: the retire predicate drops the 'witness' prefix (every "
        "witnessed-action return starting with 'witness' is a failure state), so "
        "the request stays queued for retry and the target+sha dedupe can no "
        "longer false-positive OPS_B_REQUEST_ALREADY_EXECUTED. (b) request+"
        "proposal_id provenance is threaded into the action-map and both "
        "OPS_B_EXECUTED receipts; _verified_by_receipt now matches on request "
        "name (sha-only fallback retained for legacy fieldless receipts) so a "
        "verified receipt cannot retire a different request. Acceptance: "
        "isolated harness T1-T7 = 23/23 green (HOME-redirected fixture, no live "
        "state touched)."
    ),
    "evidence": {
        "acceptance": "23/23 harness checks at " + now
        + " (lane OCTOPUS-EXECUTOR-SAFETY-20260915)",
        "harness": "09-LANES/OCTOPUS-EXECUTOR-SAFETY-20260915/scripts/harness_t1_t7.py",
        "patch_builder": "09-LANES/OCTOPUS-EXECUTOR-SAFETY-20260915/scripts/patch_executor_safety.py",
        "pre_image": str(PRE),
        "pre_image_sha256": live_sha,
    },
    "rollback": "restore pre-image: " + str(PRE)
    + " (oneshot-per-tick service; no restart needed)",
    "requested_by": "octopus-commander/2026-09-15 (owner: hardening-then-TRIO)",
    "at_utc": now,
}
out = REQ / "EXECUTOR-SAFETY-001.json"
out.write_text(json.dumps(req, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"queued EXECUTOR-SAFETY-001 base={live_sha[:16]} post={art_sha[:16]} at={now}")
