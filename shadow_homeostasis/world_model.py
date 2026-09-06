"""Content-addressed bitemporal world state; no authority inference."""
from .canonical import canonical, digest
from .observation import parse_dt
from .trust import eligibility


def build_world_state(observations, assessment, *, decision_time, valid_at=None, known_at=None):
    dt = parse_dt(decision_time)
    if dt is None:
        raise ValueError("decision_time required")
    va, ka = parse_dt(valid_at) or dt, parse_dt(known_at) or dt
    if va > dt or ka > dt:
        raise ValueError("query time exceeds decision_time")
    facts, hypotheses, uncertainties = [], [], []
    contradictions = list(assessment.get("contradictions") or [])
    for obs in sorted(observations, key=lambda o: canonical(o.to_dict())):
        content = obs.to_dict()
        content["id"] = content.pop("observation_id")
        try:
            occ, rec = parse_dt(obs.occurred_at), parse_dt(obs.recorded_at)
            temporal = occ is not None and rec is not None and occ <= va and rec <= ka and occ <= rec
        except (ValueError, TypeError, OverflowError):
            temporal = False
        if not temporal:
            uncertainties.append({"kind": "BITEMPORAL_EXCLUDED", "observation": content})
        elif obs.quality == "RESTART_ARTIFACT_SUSPECTED":
            hypotheses.append({"label": "hypothesis", "observation": content,
                               "confidence": None, "reason": "restart artifact is not a fact"})
        elif eligibility(obs) and parse_dt(obs.decision_time) == dt:
            facts.append(content)
        else:
            uncertainties.append({"kind": obs.quality if obs.quality != "VALID" else "UNVALIDATED",
                                  "observation": content})
            if obs.quality == "CONFLICTING":
                contradictions.append("conflict:" + obs.metric + ":" + obs.observation_id)
    out = {
        "schema": "world-state.v2", "valid_at": va.isoformat(), "known_at": ka.isoformat(),
        "decision_time": dt.isoformat(),
        "entities": {"organism": {"kind": "hybrid_organism_model", "live_status": "UNVERIFIED"},
                     "nodes": sorted({o.node_id for o in observations if o.node_id}),
                     "unlocated_observation_count": sum(o.node_id is None for o in observations)},
        "facts": facts, "hypotheses": hypotheses, "predictions": [],
        "uncertainties": uncertainties, "contradictions": sorted(set(contradictions)),
        "evidence_ids": sorted(f["id"] for f in facts),
        "homeostatic_assessment_id": assessment.get("assessment_id"),
        "confidence": None,
        "coverage_ratio": len(facts) / max(1, len(observations)),
        "confidence_semantics": "uncalibrated; coverage is not predictive confidence",
        "executable": False,
    }
    out["state_id"] = "ws-" + digest(out)
    return out
