#!/usr/bin/env python3
"""Read-only WAVE0 shadow-exit checklist. Never arms Reflex or flips execute_enabled."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, "/opt/octopus/cognition/src")
sys.path.insert(0, "/opt/octopus/shadow_validation/src")

from octopus_cognition.ledger import ChainedLedger  # noqa: E402

STATE = Path("/var/lib/octopus/state")
ARMING = Path("/etc/octopus/reflex_arming_criteria.yaml")


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _active(unit: str) -> str:
    proc = subprocess.run(["systemctl", "is-active", unit], capture_output=True, text=True, check=False)
    return (proc.stdout or "").strip() or "unknown"


def _yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml

        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        return doc if isinstance(doc, dict) else {}
    except (OSError, ValueError):
        return {}


def evaluate() -> dict[str, Any]:
    boot = _json(STATE / "boot_report.json")
    skill = _json(STATE / "skill" / "latest.json")
    meta = _json(STATE / "metacontrol" / "latest.json")
    gap001 = _json(STATE / "gaps" / "GAP-001-cold_boot_unverified.json")
    gap002 = _json(STATE / "gaps" / "GAP-002-audit_head_unsigned.json")
    criteria = _yaml(ARMING)
    required = criteria.get("required_all") or {}
    ledger = ChainedLedger(STATE / "world_model", "octopus.prediction-ledger.head.v1")
    ledger_ok, broken, detail = ledger.verify()
    samples = int(skill.get("samples") or 0)
    gates_failed = boot.get("gates_failed") or []
    checklist = {
        "schema": "octopus.shadow-exit-checklist.v1",
        "profile": "WAVE0_OBSERVE_ONLY",
        "execute_enabled": False,
        "shadow": True,
        "arm_reflex": False,
        "owner_approval": "required",
        "does_not_mutate_authority": True,
        "live_units": {
            "stability": _active("octopus-stability"),
            "world_model": _active("octopus-world-model"),
            "skill_tracker": _active("octopus-skill-tracker"),
            "metacontrol": _active("octopus-metacontrol"),
            "reflex": _active("octopus-reflex"),
        },
        "checks": {
            "verifier_ready": boot.get("readiness_state") == "READY" and not gates_failed,
            "gates_failed": gates_failed,
            "skill_samples_ge_50": samples >= 50,
            "skill_samples": samples,
            "ledger_chain_valid": bool(ledger_ok),
            "ledger_detail": detail,
            "ledger_broken_seq": broken,
            "gap001_pass": gap001.get("status") == required.get("gap001_status", "PASS"),
            "gap001_status": gap001.get("status"),
            "gap002_closed": gap002.get("status") == required.get("gap002_status", "CLOSED"),
            "gap002_status": gap002.get("status"),
            "metacontrol_executable_false": meta.get("executable") is False,
            "metacontrol_action_none": str(meta.get("action") or "NONE") == "NONE",
            "reflex_armed_false": criteria.get("armed") is False,
            "owner_approval_required": criteria.get("owner_approval") == "required",
        },
        "arming_criteria": required,
        "verdict": "HOLD_OBSERVE_ONLY",
        "note": (
            "This script only prints a checklist. It never disables shadow mode, "
            "never enables execute, and never arms Reflex. Owner approval remains required."
        ),
    }
    ready_to_discuss = all(
        [
            checklist["checks"]["verifier_ready"],
            checklist["checks"]["skill_samples_ge_50"],
            checklist["checks"]["ledger_chain_valid"],
            checklist["checks"]["gap001_pass"],
            checklist["checks"]["gap002_closed"],
            checklist["checks"]["metacontrol_executable_false"],
            checklist["checks"]["reflex_armed_false"],
        ]
    )
    checklist["ready_to_discuss_with_owner"] = bool(ready_to_discuss)
    if ready_to_discuss:
        checklist["verdict"] = "STILL_HOLD_PENDING_OWNER_APPROVAL"
    return checklist


def main() -> int:
    text = json.dumps(evaluate(), indent=2) + "\n"
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
