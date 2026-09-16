#!/usr/bin/env python3
"""Isolated behavioral acceptance for F-NEW-3 + queue its witnessed canary.

Part 1 (always): fixture-isolated check that a budget-blocked request emits
OPS_B_BLOCKED carrying request=<name> (the F-NEW-3 contract), and that the
unmodified emit sites for B2/B3/B5 carry their identifiers.
Part 2 (only if part 1 green): queue the canary against live a255c4c0.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

STAGE = Path(
    "/home/ari/ofn/state/coding-worker/stage/EXECUTOR-SAFETY-FNEW3-20260915/ops_agent.py"
)
LIVE = Path("/home/ari/ofn/state/ops-agent/ops_agent.py")
PRE = Path(
    "/home/ari/ofn/state/ops-agent/preimage/ops_agent.py.a255c4c0deb380cd.orig"
)
REQ = Path("/home/ari/ofn/state/ops-agent/state/canary-requests")
EXPECTED_LIVE = (
    "a255c4c0deb380cdd6d2034671968c9737461798a4db4e857ea1122d9337ea51"
)
EXPECTED_ART = "afefa020caae7b41dfcc543eed224cf5947ab95cfac5a2b20b3a167bfb1811b4"


def part1() -> bool:
    text = STAGE.read_text(encoding="utf-8")
    emits = [l for l in text.splitlines() if 'receipt("OPS_B_BLOCKED"' in l]
    ok_static = len(emits) == 4 and all("request=" in l for l in emits)

    fx = Path(tempfile.mkdtemp(prefix="fnew3-fx-"))
    ag = fx / "ofn/state/ops-agent"
    (ag / "state/canary-requests").mkdir(parents=True)
    for d in ("executed", "closed", "failed", "owner-tasks", "pending",
              "proposals", "awaiting-outcome"):
        (ag / "state" / d).mkdir(parents=True)
    shutil.copyfile(STAGE, ag / "ops_agent.py")
    shutil.copyfile("/home/ari/ofn/state/ops-agent/ops_budgets.json",
                    ag / "ops_budgets.json")
    # force breaker open for the fixture component to trigger OPS_B_BLOCKED
    (ag / "state/ops-receipts.jsonl").write_text("".join(json.dumps(r) + "\n" for r in [
        {"kind": "OPS_B_EXECUTED", "category": "B8_NON_TCB_PATCH_CANARY",
         "at": "2026-09-15T21:00:00+00:00", "verified": False,
         "component": "fx-comp"},
        {"kind": "OPS_B_EXECUTED", "category": "B8_NON_TCB_PATCH_CANARY",
         "at": "2026-09-15T21:01:00+00:00", "verified": False,
         "component": "fx-comp"},
    ]), encoding="utf-8")
    (ag / "state/failure-signatures.json").write_text(
        json.dumps({"signatures": []}), encoding="utf-8")
    (fx / "ofn/state/autonomy").mkdir(parents=True)
    (fx / "ofn/state/autonomy/witness-pins.json").write_text(json.dumps(
        {"ssh_identity": "/x", "witness_host": "127.0.0.1",
         "witness_inbox": "/tmp/nowhere", "witness_receipts_path": "/tmp/x"}),
        encoding="utf-8")
    os.environ["HOME"] = str(fx)
    sys.path.insert(0, str(ag))
    import ops_agent as O
    art = fx / "art.txt"
    art.write_text("x\n", encoding="utf-8")
    (O.STATE / "canary-requests" / "fx-req.json").write_text(json.dumps(
        {"target": "/tmp/fx-target", "target_sha256": "a" * 64,
         "artifact_sha256": "a" * 64, "base_sha256": "0" * 64,
         "patched": str(art), "component": "fx-comp", "dependencies": [],
         "task_id": "fx-req.json",
         "category": "B8_NON_TCB_PATCH_CANARY"}), encoding="utf-8")
    pins = {"ssh_identity": "/x", "witness_host": "127.0.0.1",
            "witness_inbox": "/tmp/nowhere", "witness_receipts_path": "/tmp/x"}
    O.handle_spool_category("B8_NON_TCB_PATCH_CANARY", {"timeout_s": 30}, pins,
                            "canary-requests")
    rows = [json.loads(l) for l in
            (O.STATE / "ops-receipts.jsonl").read_text().splitlines() if l.strip()]
    blocked = [r for r in rows if r.get("kind") == "OPS_B_BLOCKED"]
    ok_behaviour = bool(blocked) and all(
        r.get("request") == "fx-req.json" for r in blocked)
    print(json.dumps({"static_four_emits": ok_static,
                      "blocked_receipts": len(blocked),
                      "behavioural_request_field": ok_behaviour}))
    shutil.rmtree(fx, ignore_errors=True)
    return ok_static and ok_behaviour


def part2() -> int:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    live_sha = hashlib.sha256(LIVE.read_bytes()).hexdigest()
    art_sha = hashlib.sha256(STAGE.read_bytes()).hexdigest()
    assert live_sha == EXPECTED_LIVE, f"live moved: {live_sha[:16]}"
    assert art_sha == EXPECTED_ART, f"artifact: {art_sha[:16]}"
    assert hashlib.sha256(PRE.read_bytes()).hexdigest() == live_sha
    req = {
        "task_id": "F-NEW3-001 [F-NEW-3] [monitoring-debt]",
        "category": "B8_NON_TCB_PATCH_CANARY",
        "kind": "B8_NON_TCB_PATCH_CANARY",
        "component": "ops-agent",
        "target": str(LIVE),
        "base_sha256": live_sha,
        "artifact_sha256": art_sha,
        "expected_post_sha256": art_sha,
        "target_sha256": art_sha,
        "patched": str(STAGE),
        "diff_scope": ["ofn/state/ops-agent/ops_agent.py"],
        "dependencies": [],
        "priority": 5,
        "diagnosis": (
            "F-NEW-3 (owner ratified deploy-after-TRIO, card 2026-09-15): every "
            "OPS_B_BLOCKED emit gains a request= field (B2=unit, B3/B5=fixed "
            "component ids, spool loop=request file name) so blockers join to "
            "the queue without manual matching — the gap that hid TRIO-003's "
            "BUDGET_NODE_24H status from greps for 10 minutes. Built on "
            "post-TRIO base a255c4c0; 4 single-line exact-anchor edits; "
            "acceptance: static 4/4 emits carry request + fixture-isolated "
            "behavioural proof (blocked receipt carries request=fx-req.json)."
        ),
        "evidence": {
            "acceptance": "static+behavioural green at " + now,
            "builder": "09-LANES/OCTOPUS-EXECUTOR-SAFETY-20260915/scripts/patch_fnew3.py",
            "owner_card": "senior-engineer card 2026-09-15: F-NEW-3 ratified after TRIO",
            "pre_image": str(PRE),
            "pre_image_sha256": live_sha,
        },
        "rollback": "restore pre-image: " + str(PRE)
        + " (oneshot-per-tick; no restart needed)",
        "requested_by": "octopus-executor-safety/2026-09-15 (owner card)",
        "at_utc": now,
    }
    out = REQ / "F-NEW3-001.json"
    out.write_text(json.dumps(req, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"queued F-NEW3-001 base={live_sha[:16]} post={art_sha[:16]} at={now}")
    return 0


if __name__ == "__main__":
    sys.exit(0 if part1() and part2() == 0 else 1)
