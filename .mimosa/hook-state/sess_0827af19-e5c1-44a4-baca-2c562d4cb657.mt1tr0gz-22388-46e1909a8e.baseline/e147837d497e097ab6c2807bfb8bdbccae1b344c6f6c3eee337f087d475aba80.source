"""Shadow pipeline: Trust → Homeostasis → World Model → Metacontrol."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .homeostasis import HomeostaticInput, assess
from .metacontrol import decide
from .observation import Observation
from .registry import MetricRegistry, default_registry
from .trust import mark_conflicting, validate_observation
from .world_model import build_world_state


def run_shadow_pipeline(
    observations: list[Observation],
    *,
    decision_time: datetime,
    boot_id: str | None = None,
    registry: MetricRegistry | None = None,
    previous_assessment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    reg = registry or default_registry()
    validated = [validate_observation(o, reg) for o in observations]
    validated = mark_conflicting(validated, "arbiter.period_s")
    assessment = assess(HomeostaticInput(
        decision_time=decision_time,
        observations=validated,
        previous_assessment=previous_assessment,
        boot_id=boot_id,
    ))
    world = build_world_state(validated, assessment, decision_time=decision_time)
    gates = decide(validated, assessment, world)
    payload = {
        "schema": "shadow-pipeline.v1",
        "observations": [o.to_dict() for o in validated],
        "eligibility": {o.observation_id: o.quality for o in validated},
        "homeostatic_assessment": assessment,
        "world_state": world,
        "skill_scores": [g["skill_score"] for g in gates],
        "gate_decisions": gates,
        "executable": False,
        "code_version": "shadow_homeostasis/0.1.0",
    }
    blob = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
    payload["output_hash"] = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    return payload
