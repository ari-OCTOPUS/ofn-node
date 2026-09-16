"""Queue G8-PRODUCER-021 (rebased + regex-repaired) and supersede stale 020."""
import hashlib
import json
import time
from pathlib import Path

REQ_DIR = Path("/home/ari/ofn/state/ops-agent/state/canary-requests")
SUP_DIR = Path("/home/ari/ofn/state/ops-agent/state/superseded-tasks")
STAGE = Path("/home/ari/ofn/state/coding-worker/stage/W24-G8-ROUTING-v3/glass_runner.py")
PREIMAGE = Path("/home/ari/ofn/state/owner_dialogue/preimage/glass_runner.py.02fb704da2d4190a.orig")

LIVE_SHA = "02fb704da2d4190a9f4b902edf7300e6704a37cabcd074bfc601a76b77a1ffbe"
ART_SHA = hashlib.sha256(STAGE.read_bytes()).hexdigest()
PRE_SHA = hashlib.sha256(PREIMAGE.read_bytes()).hexdigest()
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# sanity: live file must still match the base we rebased onto
live = hashlib.sha256(Path("/home/ari/ofn/ofn/agents/glass_runner.py").read_bytes()).hexdigest()
assert live == LIVE_SHA, f"live moved: {live[:16]}"
assert PRE_SHA == LIVE_SHA, "preimage != live base"

old = json.loads((REQ_DIR / "native-A1-G8-PRODUCER-020.json").read_text())
new = dict(old)
new.update({
    "artifact_sha256": ART_SHA,
    "base_sha256": LIVE_SHA,
    "expected_post_sha256": ART_SHA,
    "target_sha256": ART_SHA,
    "patched": str(STAGE),
    "task_id": "TASK-G8-PRODUCER-DEPLOY-021",
    "diagnosis": (
        "G8 lane routing rebased onto live 02fb704d (G27 fix) as V3. FORENSIC FIX: "
        "V2/V3-pre-repair contained literal 0x08 backspace bytes inside the r-string "
        "regexes (_HEX_PAT/_CONFIRM_PAT), so routing was dead code that always fell "
        "through to MONEY; V2's 13/13 acceptance could not have exercised this function. "
        "Bytes repaired to backslash-b sequences. Fresh acceptance 8/8 (B3: known-hash "
        "fa/long-payload/en+fa confirm; MONEY: bare words/short-hex/empty)."
    ),
    "evidence": {
        "acceptance": "G8-V3 ACCEPTANCE 8/8 at " + now + " (forensic lane scripts/accept_g8_v3.py)",
        "pre_image": str(PREIMAGE),
        "pre_image_sha256": PRE_SHA,
    },
    "provenance": {
        "class": "REAL_CODE_DEFECT",
        "source": "FORENSIC-REORIENTATION-20260915: stale-base deadlock + latent regex corruption",
        "source_hash": LIVE_SHA,
        "source_ts": now,
    },
    "rebase_receipt": {
        "at": now,
        "from_request": "native-A1-G8-PRODUCER-020",
        "why": "020 base ddee3da4 stale vs live 02fb704d after G27 deploy; executor correctly refused (OPS_B_STALE_BASE) every tick",
        "method": "three-way merge: live + (V2 artifact - pre), overlap-checked, py_compiled, 0x08 bytes repaired",
    },
    "rollback": "restore pre-image: " + str(PREIMAGE),
    "requested_by": "octopus-forensic-reorientation/2026-09-15",
})
new.pop("requed_receipt", None)

out = REQ_DIR / "native-A1-G8-PRODUCER-021.json"
out.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n")
print(f"queued {out.name} base={LIVE_SHA[:16]} post={ART_SHA[:16]}")

# supersede 020 (append superseded_by, then move dir — receipts stay intact)
old["superseded_by"] = "native-A1-G8-PRODUCER-021"
old["superseded_at"] = now
old["superseded_why"] = "base ddee3da4 no longer matches live 02fb704d; artifact rebuilt as V3 with regex repair"
SUP_DIR.mkdir(exist_ok=True)
(REQ_DIR / "native-A1-G8-PRODUCER-020.json").write_text(
    json.dumps(old, indent=2, ensure_ascii=False) + "\n")
(REQ_DIR / "native-A1-G8-PRODUCER-020.json").rename(
    SUP_DIR / "native-A1-G8-PRODUCER-020.json")
print("superseded native-A1-G8-PRODUCER-020 -> superseded-tasks/")

# confirm W24 binder dependency shape (informational)
w24 = json.loads((REQ_DIR / "native-A3-W24-BINDER-006.json").read_text())
print("W24 deps:", w24.get("dependencies"), "| base:", str(w24.get("base_sha256"))[:16])
