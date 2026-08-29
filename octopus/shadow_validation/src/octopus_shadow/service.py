"""Staging validator. Does not replace the live persistence world-model service."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from octopus_shadow.enforcement import Authority, EnforcementGuard
from octopus_shadow.policy import Wave0ObserveOnlyPolicy

LIVE_STATUS = Path("/var/lib/octopus/state/shadow_validation/status.json")


def load_config(path: Path) -> dict:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise SystemExit("invalid config")
    if doc.get("profile") != "WAVE0_OBSERVE_ONLY":
        raise SystemExit("profile must remain WAVE0_OBSERVE_ONLY")
    if doc.get("execute_enabled") is not False:
        raise SystemExit("execute_enabled must be false")
    if len(doc.get("state_names") or []) != len(doc.get("homeostatic_weights") or []):
        raise SystemExit("state_names/homeostatic_weights length mismatch")
    if int((doc.get("runtime") or {}).get("torch_threads") or 0) > 2:
        raise SystemExit("torch_threads must be <= 2")
    if doc.get("torch_enabled") is True:
        raise SystemExit("torch is not allowed on WAVE0 Sensorium")
    return doc


def live_snapshot() -> dict:
    def _json(path: str) -> dict:
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    skill = _json("/var/lib/octopus/state/skill/latest.json")
    meta = _json("/var/lib/octopus/state/metacontrol/latest.json")
    wm = _json("/var/lib/octopus/state/world_model/latest.json")
    return {
        "profile": "WAVE0_OBSERVE_ONLY",
        "world_model": "SHADOW_ACTIVE" if wm.get("ledger_ok") else "UNKNOWN",
        "prediction_ledger": "ACTIVE" if wm.get("ledger_detail") else "UNKNOWN",
        "skill_tracker": "EVALUATING" if int(skill.get("samples") or 0) < 50 else "SCORED",
        "synthetic_stress": "ISOLATED",
        "policy": "NO_ACTION",
        "execute_enabled": False,
        "actuator_authority": "NONE",
        "executed_actions": 0,
        "planner_invoked": False,
        "metacontrol": meta.get("reason"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("/etc/octopus/world-model.yaml"))
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    load_config(args.config)
    policy = Wave0ObserveOnlyPolicy()
    decision = policy.decide({}, {"recommendation": "ADVISORY_RESTART", "executable": True})
    allowed, reason = EnforcementGuard().authorize(
        "ADVISORY_RESTART",
        Authority(
            profile="WAVE0_OBSERVE_ONLY",
            execute_enabled=False,
            registry_signature_valid=True,
            verifier_ready=True,
            gates_failed=(),
            owner_approval=True,
        ),
    )
    if decision.executable or allowed:
        raise SystemExit("wave0_invariant_broken")
    snapshot = live_snapshot()
    snapshot["guard_reason"] = reason
    if args.once:
        print("CONFIG_OK")
        print(json.dumps(snapshot, indent=2))
        return 0
    LIVE_STATUS.parent.mkdir(parents=True, exist_ok=True)
    LIVE_STATUS.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print("CONFIG_OK")
    print(json.dumps(snapshot, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
