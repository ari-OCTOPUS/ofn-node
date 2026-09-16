"""Queue EXECUTOR-CORE-F001-OW8 canary + supersede TRIO-002 (same target).

Packet §4.3 ordering: this lands FIRST; TRIO gets its (cheap, tooled) rebase
afterward. W24-BINDER-006 targets a different file and is unaffected.
"""
import hashlib
import json
import time
from pathlib import Path

REQ = Path("/home/ari/ofn/state/ops-agent/state/canary-requests")
SUP = Path("/home/ari/ofn/state/ops-agent/state/superseded-tasks")
ART = Path("/home/ari/ofn/state/coding-worker/stage/EXECUTOR-CORE-F001-OW8-20260915/ops_agent.py")
PRE = Path("/home/ari/ofn/state/ops-agent/preimage/ops_agent.py.c2e290fd96d42685.orig")
LIVE = Path("/home/ari/ofn/state/ops-agent/ops_agent.py")

now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
art_sha = hashlib.sha256(ART.read_bytes()).hexdigest()
live_sha = hashlib.sha256(LIVE.read_bytes()).hexdigest()
assert live_sha[:16] == "c2e290fd96d42685", f"live moved: {live_sha[:16]}"
assert art_sha[:16] == "2074072489fcf209", f"artifact unexpected: {art_sha[:16]}"
assert hashlib.sha256(PRE.read_bytes()).hexdigest() == live_sha

req = {
    "task_id": "EXECUTOR-CORE-F001-OW8-001 [F-001] [OW-8] [F-002]",
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
        "Owner packet OWNER-PACKET-F001-OW8-20260915 (option-1 vote): "
        "F-001 two-layer retirement (move-before-receipt at cycle-close + "
        "verified-by-receipt self-heal with zero budget spend) + OW-8 "
        "disposition-and-continue (never abort category loop) + OW-8b canonical "
        "category key with read-only legacy RY fallback + retire-vocabulary "
        "prefix match. Acceptance: isolated harness T1-T6 = 16/16 green "
        "(HOME-redirected fixture, no live state touched)."
    ),
    "evidence": {
        "acceptance": "16/16 harness checks at " + now + " (lane OCTOPUS-EXECUTOR-CORE-20260915)",
        "harness": "09-LANES/OCTOPUS-EXECUTOR-CORE-20260915/scripts/harness_t1_t6.py",
        "owner_packet": "C:/Users/Armin/Downloads/OWNER-PACKET-F001-OW8-20260915.md (mirror in lane)",
        "pre_image": str(PRE),
        "pre_image_sha256": live_sha,
    },
    "rollback": "restore pre-image: " + str(PRE) + " (oneshot-per-tick service; no restart needed)",
    "requested_by": "octopus-commander/2026-09-15 (owner option-1 selection)",
    "at_utc": now,
}
out = REQ / "EXECUTOR-CORE-F001-OW8-001.json"
out.write_text(json.dumps(req, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"queued EXECUTOR-CORE-F001-OW8-001 base={live_sha[:16]} post={art_sha[:16]}")

# supersede TRIO-002 (same target; this package lands first per packet §4.3)
t = REQ / "native-Z-SUCCESSOR-TRIO-002.json"
if t.exists():
    d = json.loads(t.read_text())
    d["superseded_by"] = "EXECUTOR-CORE-F001-OW8-001.json"
    d["superseded_at"] = now
    d["superseded_why"] = ("same target ops_agent.py; owner packet F-001/OW-8 lands "
                           "first (its retire-block is surgically replaced there); TRIO "
                           "rebases onto the new base afterward (tooling exists)")
    t.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    t.rename(SUP / "native-Z-SUCCESSOR-TRIO-002.json")
    print("superseded TRIO-002 -> superseded-tasks/")
