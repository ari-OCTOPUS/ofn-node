"""Deterministic shadow dataflow through frozen metacontrol."""
from .canonical import canonical, digest, assert_shadow
from .homeostasis import HomeostaticInput, assess
from .metacontrol import decide
from .observation import parse_dt
from .registry import default_registry
from .trust import mark_conflicting, validate_observation
from .world_model import build_world_state


def run_shadow_pipeline(observations, *, decision_time, boot_id=None, registry=None, previous_assessment=None):
    decision_time = parse_dt(decision_time)
    if decision_time is None:
        raise ValueError("explicit decision_time required")
    reg = registry or default_registry()
    # Exact repeats collapse. ID collisions retain every distinct version, ineligible.
    unique = {canonical(o.to_dict()): o for o in observations}
    validated = [validate_observation(o, reg, decision_time=decision_time)
                 for _, o in sorted(unique.items())]
    groups = {}
    for obs in validated:
        groups.setdefault(obs.observation_id, []).append(obs)
    for group in groups.values():
        if len(group) > 1:
            for obs in group:
                obs.quality = "CONFLICTING"
                obs.quality_reasons = sorted(set(obs.quality_reasons + ["OBSERVATION_ID_COLLISION"]))
    for metric in sorted({o.metric for o in validated}):
        validated = mark_conflicting(validated, metric)
    validated.sort(key=lambda o: canonical(o.to_dict()))
    assessment = assess(HomeostaticInput(decision_time, validated,
                        previous_assessment=previous_assessment, boot_id=boot_id))
    world = build_world_state(validated, assessment, decision_time=decision_time)
    gates = decide(validated, assessment, world)
    payload = {
        "schema": "shadow-pipeline.v2",
        "observations": [o.to_dict() for o in validated],
        "eligibility": {o.observation_id: o.quality for o in validated},
        "identity_collisions": sorted(k for k, v in groups.items() if len(v) > 1),
        "homeostatic_assessment": assessment, "world_state": world,
        "skill_scores": [g["skill_score"] for g in gates], "gate_decisions": gates,
        "score_semantics": "frozen heuristic; not empirically calibrated; not authority",
        "executable": False, "code_version": "shadow_homeostasis/exec-001.v2",
    }
    assert_shadow(payload)
    payload["output_hash"] = digest(payload)
    return payload
