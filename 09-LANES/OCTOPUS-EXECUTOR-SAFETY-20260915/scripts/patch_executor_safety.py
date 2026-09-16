#!/usr/bin/env python3
"""Build the executor-safety artifact from sha-pinned live ops_agent.py bytes.

Hardens the witnessed-canary lifecycle against false retirement and binds every
OPS_B_EXECUTED receipt to its originating request/proposal. Every edit is an
exact-string replacement whose anchor must occur exactly once.
"""
import hashlib
import py_compile
import shutil
import sys
from pathlib import Path

LIVE = Path("/home/ari/ofn/state/ops-agent/ops_agent.py")
STAGE = Path(
    "/home/ari/ofn/state/coding-worker/stage/EXECUTOR-SAFETY-20260915/ops_agent.py"
)
PREIMAGE = Path(
    "/home/ari/ofn/state/ops-agent/preimage/ops_agent.py.2074072489fcf209.orig"
)
EXPECTED_LIVE_SHA = (
    "2074072489fcf2098774b8c3be37471bfc2f6799e06d2bd10ee02fbd5a9ac6cd"
)

EDITS: list[tuple[str, str, str]] = []


def edit(tag: str, old: str, new: str) -> None:
    EDITS.append((tag, old, new))


edit(
    "E1-request-first-receipt-match",
    '''def _verified_by_receipt(req: dict) -> bool:
    """F-001 layer-2 helper: True when this request's artifact already has an
    OPS_B_EXECUTED verified=True receipt (matched on the exact verify sha)."""
    want = str(req.get("target_sha256") or req.get("artifact_sha256") or "")
    if len(want) < 32:
        return False
    try:
        lines = (STATE / "ops-receipts.jsonl").read_text(
            encoding="utf-8").splitlines()[-400:]
    except OSError:
        return False
    for line in reversed(lines):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("kind") != "OPS_B_EXECUTED" or d.get("verified") is not True:
            continue
        vk = str(d.get("verify_kind", ""))
        if want[:64] and want[:64] in vk:
            return True
    return False
''',
    '''def _verified_by_receipt(req: dict, request: str | None = None) -> bool:
    """True only when a verified receipt binds this request to this artifact.

    New receipts carry the exact request name. Legacy receipts have no request
    field, so they retain the sha-only fallback needed to self-heal old queue
    entries without allowing a mismatched named receipt to retire a request.
    """
    want = str(req.get("target_sha256") or req.get("artifact_sha256") or "")
    if len(want) < 32:
        return False
    try:
        lines = (STATE / "ops-receipts.jsonl").read_text(
            encoding="utf-8").splitlines()[-400:]
    except OSError:
        return False
    for line in reversed(lines):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("kind") != "OPS_B_EXECUTED" or d.get("verified") is not True:
            continue
        receipt_request = d.get("request")
        if receipt_request is not None and request is not None and receipt_request != request:
            continue
        vk = str(d.get("verify_kind", ""))
        if want[:64] and want[:64] in vk:
            return True
    return False
''',
)

edit(
    "E2-pass-request-name",
    "        if _verified_by_receipt(req):\n",
    "        if _verified_by_receipt(req, name):\n",
)

edit(
    "E3-action-map-request",
    '''    arec = dict(action_record)
    arec["component"] = component
''',
    '''    arec = dict(action_record)
    arec["component"] = component
    arec["request"] = evidence.get("request")
    arec["proposal_id"] = env["proposal_id"]
''',
)

edit(
    "E4-no-action-map-receipt",
    '''        return receipt("OPS_B_EXECUTED", category=category,
                       component=exp["target_component"], verified=False,
                       outcome="NO_ACTION_MAP", exit_codes=[])
''',
    '''        return receipt("OPS_B_EXECUTED", category=category,
                       component=exp["target_component"], verified=False,
                       outcome="NO_ACTION_MAP", exit_codes=[],
                       request=None, proposal_id=exp["proposal_id"])
''',
)

edit(
    "E5-executed-receipt-provenance",
    '''    return receipt("OPS_B_EXECUTED", category=category, component=m["component"],
                   argv=argvs, exit_codes=codes, verified=verified, outcome=outcome,
                   verify_kind=vk)
''',
    '''    return receipt("OPS_B_EXECUTED", category=category, component=m["component"],
                   argv=argvs, exit_codes=codes, verified=verified, outcome=outcome,
                   verify_kind=vk, request=m.get("request"),
                   proposal_id=exp["proposal_id"])
''',
)

edit(
    "E6-success-only-retire",
    '''        # F-001 root fix: prefix match absorbs return-value vocabulary
        # drift (the observed miss class behind G8-021 never retiring).
        if str(_out).startswith(("ok", "executed", "witness", "proposal-sent")):
''',
    '''        # A request retires only after a successful hand-off/execution. Every
        # witnessed-action return beginning with "witness" is a failure state;
        # witness-unavailable must stay queued for retry and must never enter
        # executed/, where target+sha dedupe would create a false positive.
        if str(_out).startswith(("ok", "executed", "proposal-sent")):
''',
)


def main() -> int:
    live = LIVE.read_bytes()
    live_sha = hashlib.sha256(live).hexdigest()
    if live_sha != EXPECTED_LIVE_SHA:
        print(f"ABORT: live sha moved to {live_sha[:16]} — re-derive anchors")
        return 1

    text = live.decode("utf-8")
    for tag, old, new in EDITS:
        count = text.count(old)
        if count != 1:
            print(f"ABORT: anchor {tag} count={count} (want 1)")
            return 2
        text = text.replace(old, new)

    STAGE.parent.mkdir(parents=True, exist_ok=True)
    STAGE.write_text(text, encoding="utf-8")
    py_compile.compile(str(STAGE), doraise=True)

    checks = {
        "request_match": "_verified_by_receipt(req, name)" in text,
        "legacy_sha_fallback": "receipt_request is not None" in text,
        "action_map_request": 'arec["request"] = evidence.get("request")' in text,
        "action_map_proposal": 'arec["proposal_id"] = env["proposal_id"]' in text,
        "both_executed_emits_bound": text.count('proposal_id=exp["proposal_id"]') == 2,
        "success_only_retire": 'startswith(("ok", "executed", "proposal-sent"))' in text,
        "bad_witness_prefix_absent": 'startswith(("ok", "executed", "witness"' not in text,
    }
    print("checks:", checks)
    if not all(checks.values()):
        STAGE.unlink(missing_ok=True)
        return 3

    if PREIMAGE.exists():
        if hashlib.sha256(PREIMAGE.read_bytes()).hexdigest() != live_sha:
            print("ABORT: existing preimage does not match live sha")
            STAGE.unlink(missing_ok=True)
            return 4
    else:
        PREIMAGE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(LIVE, PREIMAGE)
        print("preimage_written")

    print("PATCH_OK new_sha=" + hashlib.sha256(STAGE.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
