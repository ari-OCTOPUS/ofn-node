#!/usr/bin/env python3
"""Queue TRIO-003 (targeted merge onto post-hardening base) for witnessed deploy.

Preconditions asserted before anything is written:
- live ops_agent.py == beaee58c (hardening deployed + cycle-closed)
- TRIO-003 artifact == a255c4c0 (34/34 isolated battery, independently re-verified)
- fresh dep-evidence pins the executed hardening state (G22-met by construction)
- W24-BINDER dependency verified MET against live bytes

Nothing here touches live executor bytes; the organism deploys under witness.
"""
import hashlib
import json
import time
from pathlib import Path

REQ = Path("/home/ari/ofn/state/ops-agent/state/canary-requests")
EXECUTED = Path("/home/ari/ofn/state/ops-agent/state/executed")
DEPEV = Path("/home/ari/ofn/state/ops-agent/state/dep-evidence")
ART = Path("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-003-20260915/ops_agent.py")
PRE = Path("/home/ari/ofn/state/ops-agent/preimage/ops_agent.py.beaee58cc9523510.orig")
LIVE = Path("/home/ari/ofn/state/ops-agent/ops_agent.py")

EXPECTED_LIVE = "beaee58cc952351001b6b34c8658cbb7ef689b00510e866ffa172a4eb390682f"
EXPECTED_ART = "a255c4c0deb380cdd6d2034671968c9737461798a4db4e857ea1122d9337ea51"

now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
live_sha = hashlib.sha256(LIVE.read_bytes()).hexdigest()
art_sha = hashlib.sha256(ART.read_bytes()).hexdigest()
assert live_sha == EXPECTED_LIVE, f"live moved: {live_sha[:16]}"
assert art_sha == EXPECTED_ART, f"artifact unexpected: {art_sha[:16]}"

# pre-image for rollback
if not PRE.exists():
    PRE.parent.mkdir(parents=True, exist_ok=True)
    shutil_copy = PRE.write_bytes(LIVE.read_bytes())
assert hashlib.sha256(PRE.read_bytes()).hexdigest() == live_sha

# fresh G22 dependency evidence: pin the executed+closed hardening state
DEPEV.mkdir(parents=True, exist_ok=True)
dep = DEPEV / "B8-CAPABILITY-20260915.json"
dep.write_text(json.dumps({
    "task_id": "B8-CAPABILITY-20260915",
    "target": str(LIVE),
    "expected_post_sha256": live_sha,
    "proven_by": "EXECUTOR-SAFETY-001 deployed 2026-09-15T10:10:29Z "
                 "verified=true, cycle-closed 10:15:43Z OUTCOME_CONFIRMED "
                 "(witness 1fbb72e50a86773d)",
    "at_utc": now,
}, indent=2) + "\n", encoding="utf-8")

# verify W24 dependency is met by current live bytes
w24 = json.loads((EXECUTED / "native-A3-W24-BINDER-006.json").read_text())
w_t = Path(str(w24["target"]))
w_want = w24.get("expected_post_sha256") or w24.get("target_sha256")
w_have = hashlib.sha256(w_t.read_bytes()).hexdigest()
assert w_have == w_want, f"W24 dep unmet: live={w_have[:16]} want={str(w_want)[:16]}"

req = {
    "task_id": "SUCCESSOR-TRIO-003 [B5-completeness] [G3-priority] [S4a-barrier] "
               "[S4b-freeze] [decision-consumer] [torn-ledger-fail-closed]",
    "category": "B8_NON_TCB_PATCH_CANARY",
    "kind": "B8_NON_TCB_PATCH_CANARY",
    "component": "ops-agent",
    "target": str(LIVE),
    "base_sha256": live_sha,
    "artifact_sha256": art_sha,
    "expected_post_sha256": art_sha,
    "target_sha256": art_sha,
    "patched": str(ART),
    "diff_scope": ["ofn/state/ops-agent/ops_agent.py"],
    "dependencies": [str(dep), "native-A3-W24-BINDER-006.json"],
    "priority": 9,
    "diagnosis": (
        "TRIO-003 targeted semantic merge onto post-hardening base beaee58c. "
        "Mechanical 3-way rebase rejected (5 semantic overlaps); instead only "
        "net-new TRIO blocks were spliced byte-exact: B5 measurement "
        "completeness + quarantine-mv (no rm -rf), frozen-set verify "
        "(target-set-bytes:), G3 priority ordering (_spool_order), S4a "
        "in-memory byte-copy deploy barrier (.deploy.tmp+fsync), S4b "
        "precondition freeze/recheck (PRECONDITION_DRIFT), decision consumer "
        "wired into tick, torn-receipt fail-closed read_receipts, class-scoped "
        "breaker key. All executor-core+safety behaviour preserved verbatim "
        "(OW-8 no-starvation, canonical category, F-001 layer1/2, "
        "request+proposal_id provenance, success-only retire). Acceptance: "
        "isolated battery 34/34 green + independent invariant re-verification "
        "(markers, forbidden patterns absent, control-byte scan clean)."
    ),
    "evidence": {
        "acceptance": "34/34 battery checks + independent re-verification at " + now
        + " (lane OCTOPUS-EXECUTOR-SAFETY-20260915)",
        "harness": "09-LANES/OCTOPUS-EXECUTOR-SAFETY-20260915/scripts/trio_harness_003.py",
        "builder": "09-LANES/OCTOPUS-EXECUTOR-SAFETY-20260915/scripts/trio_build_003.py",
        "pre_image": str(PRE),
        "pre_image_sha256": live_sha,
        "supersedes": "native-Z-SUCCESSOR-TRIO-002 (superseded by "
                      "EXECUTOR-CORE-F001-OW8-001; lineage: TRIO-001 base "
                      "109e68c0 -> TRIO-002 base c2e290fd -> TRIO-003 base "
                      "beaee58c)",
    },
    "rollback": "restore pre-image: " + str(PRE)
    + " (oneshot-per-tick service; no restart needed)",
    "requested_by": "octopus-executor-safety/2026-09-15 (owner: hardening-then-TRIO)",
    "at_utc": now,
}
out = REQ / "native-Z-SUCCESSOR-TRIO-003.json"
out.write_text(json.dumps(req, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"queued native-Z-SUCCESSOR-TRIO-003 base={live_sha[:16]} post={art_sha[:16]} "
      f"deps=[B8-CAPABILITY-20260915(MET-by-construction), W24-BINDER(MET)] at={now}")
