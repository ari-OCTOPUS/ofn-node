#!/usr/bin/env python3
"""Metacontrol shadow. Records would_decide plus DENY/PLAN_RECOMMENDED. Never invokes planner."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, "/opt/octopus/cognition/src")
from octopus_cognition.homeostasis.models import interpret_mode  # noqa: E402
from octopus_cognition.ledger import ChainedLedger  # noqa: E402
from octopus_cognition.metacontrol.gate import Wave0MetacontrolGate, WouldDecide  # noqa: E402
from octopus_cognition.metacontrol.skill import SkillReport  # noqa: E402
import sys as _sys
_sys.path.insert(0, "/opt/octopus/scripts")
from authority_mirror import resolve_authority_mirror

HOMEO = Path("/var/lib/octopus/state/homeostasis/latest.json")
SKILL = Path("/var/lib/octopus/state/skill/latest.json")
DIR = Path("/var/lib/octopus/state/metacontrol")
LATEST = DIR / "latest.json"
GATE = Wave0MetacontrolGate()
RECOMMEND = {
    WouldDecide.PLAN: "PLAN_RECOMMENDED",
    WouldDecide.REFLEX: "DENY",
    WouldDecide.BLOCK: "DENY",
}


def _load(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def main() -> int:
    DIR.mkdir(parents=True, exist_ok=True)
    ledger = ChainedLedger(DIR, "octopus.metacontrol-ledger.head.v1")
    last_reason = None
    while True:
        homeo = _load(HOMEO)
        skill = _load(SKILL)
        report = SkillReport(
            score=skill.get("score"),
            lower_bound=skill.get("lower_bound"),
            samples=int(skill.get("samples") or 0),
            eligible=bool(skill.get("eligible")),
            reason=str(skill.get("reason") or "insufficient_samples"),
            calibration_error=skill.get("calibration_error"),
        )
        age = (homeo.get("variables") or {}).get("evidence_freshness") or {}
        energy = float(homeo.get("energy_ratio") if homeo.get("energy_ratio") is not None else 1.0)
        age_s = float(age.get("value") if isinstance(age, dict) and age.get("value") is not None else 999)
        mode = interpret_mode(homeo.get("mode"))
        advisory = GATE.advisory(
            report,
            mode=mode,
            energy_ratio=energy,
            evidence_age_s=age_s,
            calibration_error=report.calibration_error,
        )
        enforced = GATE.enforced(
            report,
            mode=mode,
            energy_ratio=energy,
            evidence_age_s=age_s,
            calibration_error=report.calibration_error,
        )
        doc = {
            "schema": "octopus.metacontrol.advisory.v1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "would_decide": advisory.would_decide.value,
            "would_reason": advisory.would_reason,
            "would_rollout_depth": advisory.would_rollout_depth,
            "executed": "none",
            "executable": False,
            "action": "NONE",
            "kind": enforced.kind.value if enforced.kind else "reflex",
            "enforced_reason": enforced.reason,
            "recommendation": RECOMMEND[advisory.would_decide],
            "depth": advisory.would_rollout_depth,
            "reason": advisory.would_reason,
            "planner_invoked": False,
            "skill_samples": report.samples,
            "skill_eligible": report.eligible,
            "energy_ratio": energy,
            "evidence_age_s": age_s,
            "mode": mode.value,
            "readiness_profile": "WAVE0_OBSERVE_ONLY",
            "actuator_authority": (_am := resolve_authority_mirror()).get("actuator_authority") or "NONE",
            "estop_channel": _am.get("estop_channel"),
            "authority_mirror_note": _am.get("note"),
            "ARMED": False,
        }
        marker = f"{advisory.would_decide.value}:{advisory.would_reason}"
        if marker != last_reason:
            ledger.append(doc)
            last_reason = marker
        LATEST.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        time.sleep(5)


if __name__ == "__main__":
    raise SystemExit(main())
