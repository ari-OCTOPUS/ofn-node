#!/usr/bin/env python3
"""Offline validator for the designed Telegram access contract.

No imports from runtime packages, no network and no writes. It checks the owner contract,
the target routing document, and any future capability manifests when they exist.
Exit 0 means the static contract is internally coherent — never that Telegram is LIVE.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPS = HERE.parent
ROOT = OPS.parent
CONTRACT = HERE / "TELEGRAM-ACCESS-CONTRACT.v1.json"
ROUTING = OPS / "telegram_center" / "surface-routing.json"
MANIFEST_NAME = "capability-manifest.json"

CORE_TARGETS = {
    "chat": ("outer", "dm"),
    "doctor-intent": ("outer", "dm"),
    "doctor-diff": ("outer", "dm"),
    "doctor-daily": ("inner", "dm"),
    "critical-alerts": ("inner", "dm"),
    "organ-digest": ("inner", "dm"),
    "money-pulse": ("inner", "dm"),
    "approvals-organism": ("inner", "dm"),
}
REQUIRED_INVARIANTS = {
    "one_poller_per_token",
    "group_is_legs_only",
    "unknown_group_input_cannot_reach_core",
    "every_emitted_callback_is_handled_by_emitting_bot",
    "capability_registration_does_not_grant_execution",
}


def load(path: Path):
    return json.loads(path.read_text("utf-8"))


def validate_manifest(path: Path, errors: list[str]) -> None:
    try:
        d = load(path)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"manifest unreadable {path.relative_to(ROOT)}: {type(exc).__name__}")
        return
    required = {
        "schema", "capability_id", "title", "version", "owner_phrases",
        "read_handler", "action_contract", "risk_class", "owner_gate",
        "surface", "runtime_status_probe", "tests",
    }
    missing = sorted(required - set(d))
    if missing:
        errors.append(f"manifest missing {path.relative_to(ROOT)}: {','.join(missing)}")
    if d.get("schema") != "octopus.capability-manifest.v1":
        errors.append(f"bad manifest schema: {path.relative_to(ROOT)}")
    if d.get("registration_is_authorization") is not False:
        errors.append(f"manifest may grant authorization: {path.relative_to(ROOT)}")
    surface = d.get("surface")
    if surface not in {"owner_outer_dm", "owner_inner_dm", "legs_forum_group"}:
        errors.append(f"bad surface in {path.relative_to(ROOT)}: {surface}")
    if surface == "legs_forum_group" and not d.get("leg_key"):
        errors.append(f"group capability lacks leg_key: {path.relative_to(ROOT)}")
    if d.get("risk_class") in {"medium", "high", "forbidden"} and not d.get("owner_gate"):
        errors.append(f"risky capability lacks owner gate: {path.relative_to(ROOT)}")


def main() -> int:
    errors: list[str] = []
    try:
        c = load(CONTRACT)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL contract unreadable: {type(exc).__name__}")
        return 2
    if c.get("schema") != "octopus.telegram-access.v1":
        errors.append("contract schema mismatch")
    invariants = set(c.get("invariants") or [])
    missing_inv = sorted(REQUIRED_INVARIANTS - invariants)
    if missing_inv:
        errors.append("missing invariants: " + ",".join(missing_inv))
    surfaces = c.get("surfaces") or {}
    if set(surfaces) != {"owner_outer_dm", "owner_inner_dm", "legs_forum_group"}:
        errors.append("surface set must be exactly outer-dm, inner-dm, legs-group")
    if (surfaces.get("legs_forum_group") or {}).get("role") != "legs-only":
        errors.append("group is not legs-only")
    if (c.get("safe_defaults") or {}).get("unknown_group_command") != "DENY_AND_REDIRECT":
        errors.append("unknown group command is not fail-closed")
    try:
        r = load(ROUTING)
        streams = r.get("streams") or {}
        for name, expected in CORE_TARGETS.items():
            target = (streams.get(name) or {}).get("target") or {}
            got = (target.get("bot"), target.get("surface"))
            if got != expected:
                errors.append(f"routing target {name}: got={got} expected={expected}")
        legs = (streams.get("legs-all") or {}).get("target") or {}
        if (legs.get("bot"), legs.get("surface"), legs.get("topic")) != (
                "outer", "group", "per-leg"):
            errors.append("legs-all target must be outer/group/per-leg")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"routing unreadable: {type(exc).__name__}")

    manifests = [p for p in OPS.rglob(MANIFEST_NAME)
                 if not any(part in {"state", "__pycache__", "tests", ".git"} for part in p.parts)]
    for p in manifests:
        validate_manifest(p, errors)

    if errors:
        print("STATIC CONTRACT: FAIL")
        for e in errors:
            print("-", e)
        return 1
    print("STATIC CONTRACT: PASS")
    print(f"capability manifests found: {len(manifests)}")
    print("NOTE: static PASS is not runtime LIVE; execute ACCEPTANCE-RUNBOOK.md later.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
