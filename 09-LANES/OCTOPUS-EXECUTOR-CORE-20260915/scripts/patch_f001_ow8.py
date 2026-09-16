#!/usr/bin/env python3
"""F-001 + OW-8 + OW-8b surgical patch builder for ops_agent.py.

Builds the staged artifact from the LIVE bytes (read at run time, sha-pinned
to c2e290fd96d42685). Seven exact-string replacements; each anchor MUST occur
exactly once or the build aborts. Output: stage/EXECUTOR-CORE-F001-OW8-20260915/
ops_agent.py + pre-image of live.
"""
import hashlib
import py_compile
import shutil
import sys
from pathlib import Path

LIVE = Path("/home/ari/ofn/state/ops-agent/ops_agent.py")
STAGE = Path("/home/ari/ofn/state/coding-worker/stage/EXECUTOR-CORE-F001-OW8-20260915/ops_agent.py")
PREIMAGE = Path("/home/ari/ofn/state/ops-agent/preimage/ops_agent.py.c2e290fd96d42685.orig")

EDITS: list[tuple[str, str, str]] = []


def edit(tag: str, old: str, new: str) -> None:
    EDITS.append((tag, old, new))


# --- E1: canonical map + layer-2 helpers (inserted before handle_spool_category)
edit("E1-helpers",
     'def handle_spool_category(category: str, cat: dict, pins: dict, subdir: str) -> str:\n',
     '''# OW-8b (2026-09-15): explicit category keys — never slice a long category
# name again (category[-2:] on "B8_NON_TCB_PATCH_CANARY" produced the accidental
# breaker key "RY"). Legacy short keys stay read-only-honoured in budget_allows.
CANONICAL_CATEGORY = {
    "B8_NON_TCB_PATCH_CANARY": "B8",
    "B5_SAFE_STORAGE_MAINTENANCE": "B5",
    "B2_OCTOPUS_OWNED_WORKER_RECOVERY": "B2",
}


def _verified_by_receipt(req: dict) -> bool:
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


def _retire_executed(src: Path, name: str, category: str) -> None:
    _exec = STATE / "executed"
    _exec.mkdir(parents=True, exist_ok=True)
    dst = _exec / name
    if dst.exists():
        receipt("OPS_B_REQUEST_ALREADY_EXECUTED", category=category,
                request=name, note="already in executed/")
        return
    try:
        os.replace(src, dst)
        receipt("F001_SELF_RETIRE", category=category, request=name,
                note="verified-by-receipt; retired with zero budget spend")
    except OSError as e:
        receipt("RETIRE_FAULT", category=category, request=name, note=str(e)[:120])


def handle_spool_category(category: str, cat: dict, pins: dict, subdir: str) -> str:
''')

# --- E2: init _any_blocked
edit("E2-init",
     '    (STATE / "owner-tasks").mkdir(parents=True, exist_ok=True)\n    for name in sorted(os.listdir(spool)):',
     '    (STATE / "owner-tasks").mkdir(parents=True, exist_ok=True)\n'
     '    _any_blocked = False          # OW-8: blocked requests disposition, never abort\n'
     '    for name in sorted(os.listdir(spool)):')

# --- E3: layer-2 self-heal insert (after G28 dedupe block)
edit("E3-layer2",
     '        if _already:\n            continue\n'
     '        # deploy candidate is the PATCHED artifact; a "backup" key is only the',
     '        if _already:\n            continue\n'
     '        # F-001 LAYER-2 (2026-09-15): self-healing retire. A request whose\n'
     '        # execution already receipts verified=True removes itself with ZERO\n'
     '        # budget spend instead of re-fighting its own deployed bytes as\n'
     '        # STALE_BASE every tick (observed: G8-021 burned the component\n'
     '        # window for hours after its verified 06:54Z deploy).\n'
     '        if _verified_by_receipt(req):\n'
     '            _retire_executed(spool / name, name, category)\n'
     '            continue\n'
     '        # deploy candidate is the PATCHED artifact; a "backup" key is only the')

# --- E4: OW-8 continue + OW-8b canonical key at the budget gate
edit("E4-budget-gate",
     '        component = req.get("component", category)\n'
     '        ok_b, why_b = budget_allows(category[-2:], component)\n'
     '        if not ok_b:\n'
     '            receipt("OPS_B_BLOCKED", category=category, component=component, reason=why_b)\n'
     '            return "budget-blocked"',
     '        component = req.get("component", category)\n'
     '        # OW-8 FIX (2026-09-15): disposition + continue, never abort the\n'
     '        # category loop — one blocked request must not starve independent\n'
     '        # ready requests (runtime-proven: g22-probe unevaluated 34+ min).\n'
     '        # OW-8b FIX: canonical category key replaces category[-2:].\n'
     '        ok_b, why_b = budget_allows(CANONICAL_CATEGORY.get(category, category),\n'
     '                                    component)\n'
     '        if not ok_b:\n'
     '            receipt("OPS_B_BLOCKED", category=category, component=component, reason=why_b)\n'
     '            _any_blocked = True\n'
     '            continue')

# --- E5: retire vocabulary (prefix match kills the return-value drift class)
edit("E5-retire-vocab",
     '        if _out in ("ok", "executed", "witness-ok", "proposal-sent-ok"):',
     '        # F-001 root fix: prefix match absorbs return-value vocabulary\n'
     '        # drift (the observed miss class behind G8-021 never retiring).\n'
     '        if str(_out).startswith(("ok", "executed", "witness", "proposal-sent")):')

# --- E6: function tail summary return
edit("E6-tail",
     '        return _out\n    return "no-action-needed"',
     '        return _out\n'
     '    return "budget-blocked" if _any_blocked else "no-action-needed"')

# --- E7: cycle-close layer-1 (move file BEFORE the closure receipt)
edit("E7-cycle-close",
     '        if ov.get("verdict") in ("OUTCOME_CONFIRMED", "ROLLBACK_CONFIRMED"):\n'
     '            receipt("OPS_B_CYCLE_CLOSED", category=cat, component=info["component"],\n'
     '                    outcome_verdict=ov["verdict"], witness=ov.get("witness_hash", "")[:16])',
     '        if ov.get("verdict") in ("OUTCOME_CONFIRMED", "ROLLBACK_CONFIRMED"):\n'
     '            # F-001 LAYER-1 (2026-09-15): retire the originating canary\n'
     '            # request BEFORE the closure receipt — a receipt without the\n'
     '            # file move is how requests stayed queued forever. Failure is\n'
     '            # its own disposition and does not silently close the cycle.\n'
     '            _req_name = info.get("request")\n'
     '            if _req_name:\n'
     '                _src = STATE / "canary-requests" / str(_req_name)\n'
     '                if _src.exists():\n'
     '                    try:\n'
     '                        os.replace(_src, STATE / "executed" / _src.name)\n'
     '                    except OSError as _e:\n'
     '                        receipt("RETIRE_FAULT", category=cat, request=str(_req_name),\n'
     '                                note=str(_e)[:120])\n'
     '                        os.replace(d / name, STATE / "failed" / name)\n'
     '                        return "retire-fault"\n'
     '            receipt("OPS_B_CYCLE_CLOSED", category=cat, component=info["component"],\n'
     '                    outcome_verdict=ov.get("verdict"), witness=ov.get("witness_hash", "")[:16])')

# --- E8: budget_allows — legacy signature fallback + canonical fails match
edit("E8a-sig-legacy",
     '    sigs = load_json(STATE / "failure-signatures.json") or {"signatures": []}\n'
     '    fixed_at = max([sg.get("fixed_at", "") for sg in sigs["signatures"]\n'
     '                    if sg.get("category") == category], default="")',
     '    sigs = load_json(STATE / "failure-signatures.json") or {"signatures": []}\n'
     '    # OW-8b: honour legacy accidental keys read-only ("RY" was what\n'
     '    # category[-2:] extracted from "...CANARY"); new signatures use the\n'
     '    # canonical key.\n'
     '    _legacy = {"B8": "RY"}.get(category)\n'
     '    fixed_at = max([sg.get("fixed_at", "") for sg in sigs["signatures"]\n'
     '                    if sg.get("category") == category\n'
     '                    or (_legacy and sg.get("category") == _legacy)], default="")')

edit("E8b-fails-match",
     '    fails = [r for r in ex if r.get("category") == category and r.get("verified") is False]',
     '    fails = [r for r in ex\n'
     '             if (r.get("category") == category\n'
     '                 or str(r.get("category", "")).startswith(category + "_"))\n'
     '             and r.get("verified") is False]')


def main() -> int:
    live = LIVE.read_bytes()
    live_sha = hashlib.sha256(live).hexdigest()
    if live_sha[:16] != "c2e290fd96d42685":
        print(f"ABORT: live sha moved to {live_sha[:16]} — re-derive anchors")
        return 1
    text = live.decode("utf-8")
    for tag, old, new in EDITS:
        n = text.count(old)
        if n != 1:
            print(f"ABORT: anchor {tag} count={n} (want 1)")
            return 2
        text = text.replace(old, new)
    STAGE.parent.mkdir(parents=True, exist_ok=True)
    STAGE.write_text(text, encoding="utf-8")
    py_compile.compile(str(STAGE), doraise=True)
    # marker checks
    checks = {
        "canonical_map": "CANONICAL_CATEGORY" in text,
        "layer2": text.count("_verified_by_receipt") >= 2,
        "ow8_continue": "_any_blocked = True" in text,
        "retire_vocab_prefix": 'startswith(("ok", "executed"' in text,
        "layer1_close": "RETIRE_FAULT" in text and text.count("RETIRE_FAULT") >= 2,
        "legacy_sig": '_legacy = {"B8": "RY"}.get(category)' in text,
        "no_old_slice_at_gate": 'budget_allows(category[-2:], component)' not in text,
    }
    print("checks:", checks)
    if not all(checks.values()):
        STAGE.unlink(missing_ok=True)
        return 3
    if not PREIMAGE.exists():
        shutil.copyfile(LIVE, PREIMAGE)
        print("preimage_written")
    print("PATCH_OK new_sha=" + hashlib.sha256(STAGE.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
