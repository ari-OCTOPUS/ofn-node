"""Pure Homeostatic Core. executable always false. No planner/policy import."""
from __future__ import annotations

import hashlib
import json
import uuid
from copy import deepcopy
from .canonical import canonical, digest
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .observation import Observation, Quality, parse_dt
from .trust import eligibility, never_zero_from_unknown

SETPOINTS_V1 = {
    "version": "setpoints.v1",
    "hrv_min_for_green": 0.2,
    "hrv_window_ready": 2,
    "period_conflict_fail_closed": True,
    "life_currency_unit": "life_credit",
    "tokens_starvation": 0.0,
    "identity_missing_is_unknown": True,
}

DOMAINS = (
    "cardiac",
    "resource_health",
    "telemetry_integrity",
    "identity_integrity",
    "life_currency_integrity",
    "judge_reliability",
)


def _id(prefix: str, blob: str) -> str:
    return prefix + hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _state_reasons(state: str, why: str) -> list[str]:
    return [f"state={state}", why]


@dataclass
class HomeostaticInput:
    decision_time: datetime
    observations: list[Observation]
    setpoints: dict[str, Any] = field(default_factory=lambda: dict(SETPOINTS_V1))
    previous_assessment: dict[str, Any] | None = None
    boot_id: str | None = None


def assess(inp: HomeostaticInput) -> dict[str, Any]:
    dt = parse_dt(inp.decision_time)
    if dt is None:
        raise ValueError("decision_time required")
    inp = deepcopy(inp)
    for o in inp.observations:
        if o.quality == Quality.VALID.value and (not eligibility(o) or parse_dt(o.decision_time) != dt):
            o.quality = Quality.UNLOCATED.value
            o.quality_reasons.append("UNVALIDATED_MODIFIED_OR_DIFFERENT_EVALUATION_CLOCK")
    inp.observations.sort(key=lambda o: (str(o.occurred_at), canonical(o.to_dict())), reverse=True)
    eligible = [o for o in inp.observations if eligibility(o)]
    excluded = [o.to_dict() for o in inp.observations if not eligibility(o)]
    evidence_ids = [o.observation_id for o in eligible]
    domain_states: dict[str, dict[str, Any]] = {}
    contradictions: list[str] = []
    reasons: list[str] = []

    by_metric: dict[str, list[Observation]] = {}
    for o in inp.observations:
        by_metric.setdefault(o.metric, []).append(o)

    # cardiac / heartbeat regularity
    hrv_obs = by_metric.get("rhythm.hrv") or []
    win_obs = by_metric.get("rhythm.window_n") or []
    hrv_q = hrv_obs[0].quality if hrv_obs else Quality.MISSING.value
    win_n = None
    if win_obs and eligibility(win_obs[0]) and win_obs[0].value is not None:
        try:
            win_n = int(win_obs[0].value)
        except (TypeError, ValueError):
            win_n = None
    if hrv_q == Quality.WARMUP.value or (win_n is not None and win_n < int(inp.setpoints["hrv_window_ready"])):
        cardiac = "WARMUP"
        cr = _state_reasons("WARMUP", "HRV window empty/short after restart; not false AMBER")
    elif not hrv_obs or hrv_q in (Quality.MISSING.value, Quality.UNLOCATED.value):
        cardiac = "UNKNOWN"
        cr = _state_reasons("UNKNOWN", "HRV observation missing; not coerced to 0")
    elif hrv_q == Quality.STALE.value:
        cardiac = "UNKNOWN"
        cr = _state_reasons("UNKNOWN", "HRV stale; fail-closed")
    else:
        hrv_val = never_zero_from_unknown(hrv_obs[0].value if hrv_obs else None, hrv_q)
        if hrv_val is None:
            cardiac = "UNKNOWN"
            cr = _state_reasons("UNKNOWN", "HRV unknown")
        elif hrv_val < float(inp.setpoints["hrv_min_for_green"]):
            cardiac = "AMBER"
            cr = _state_reasons("AMBER", f"hrv={hrv_val} < {inp.setpoints['hrv_min_for_green']} with ready window")
        else:
            cardiac = "GREEN"
            cr = _state_reasons("GREEN", f"hrv={hrv_val} window ready")
    domain_states["cardiac"] = {"state": cardiac, "reasons": cr}
    reasons.extend(cr)

    # resource health
    cpu = by_metric.get("resource.cpu_pct") or []
    if not cpu:
        resource = "UNKNOWN"
        rr = _state_reasons("UNKNOWN", "resource.cpu_pct UNLOCATED in this slice")
    elif cpu[0].quality != Quality.VALID.value:
        resource = "UNKNOWN"
        rr = _state_reasons("UNKNOWN", f"cpu quality={cpu[0].quality}")
    else:
        resource = "GREEN"
        rr = _state_reasons("GREEN", f"cpu={cpu[0].value}")
    domain_states["resource_health"] = {"state": resource, "reasons": rr}
    reasons.extend(rr)

    # telemetry integrity + period conflict
    periods = [o for o in (by_metric.get("arbiter.period_s") or [])]
    if any(o.quality == Quality.CONFLICTING.value for o in inp.observations):
        tel = "UNKNOWN"
        conflict_metrics = sorted({o.metric for o in inp.observations if o.quality == Quality.CONFLICTING.value})
        tr = _state_reasons("UNKNOWN", "CONFLICTING evidence: " + ", ".join(conflict_metrics))
        contradictions.extend("conflict:" + metric for metric in conflict_metrics)
        if "arbiter.period_s" in conflict_metrics:
            contradictions.append("C-045 coincident period conflict")
    elif any(o.quality == Quality.FUTURE_DATA.value for o in inp.observations):
        tel = "UNKNOWN"
        tr = _state_reasons("UNKNOWN", "FUTURE_DATA present; excluded from computation")
    elif any(o.quality == Quality.UNLOCATED.value for o in inp.observations):
        tel = "AMBER"
        tr = _state_reasons("AMBER", "some telemetry UNLOCATED")
    elif not eligible or any(o.quality == Quality.STALE.value for o in inp.observations):
        tel = "UNKNOWN"
        tr = _state_reasons("UNKNOWN", "no eligible telemetry or stale telemetry present")
    else:
        tel = "GREEN"
        tr = _state_reasons("GREEN", "no period conflict; bitemporal ok on eligible set")
    domain_states["telemetry_integrity"] = {"state": tel, "reasons": tr}
    reasons.extend(tr)

    # identity
    idh = by_metric.get("identity_health") or []
    learner = by_metric.get("identity.learner") or []
    if not idh and not learner:
        ident = "UNKNOWN"
        ir = _state_reasons("UNKNOWN", "identity component missing; not optimistic default")
    elif (idh and idh[0].quality in (Quality.MISSING.value, Quality.WARMUP.value, Quality.RESTART_ARTIFACT_SUSPECTED.value)) or (
        learner and learner[0].quality == Quality.MISSING.value
    ):
        ident = "UNKNOWN"
        ir = _state_reasons("UNKNOWN", "identity missing/warmup/restart-artifact; not improvement")
    elif idh and idh[0].quality == Quality.RESTART_ARTIFACT_SUSPECTED.value:
        ident = "WARMUP"
        ir = _state_reasons("WARMUP", "identity_health restart artifact suspected")
    else:
        q = (idh[0].quality if idh else Quality.MISSING.value)
        if q != Quality.VALID.value:
            ident = "UNKNOWN"
            ir = _state_reasons("UNKNOWN", f"identity quality={q}")
        else:
            ident = "GREEN"
            ir = _state_reasons("GREEN", "identity_health VALID (not claimed as improvement)")
    domain_states["identity_integrity"] = {"state": ident, "reasons": ir}
    reasons.extend(ir)

    # life_currency — no AUD
    unit_obs = by_metric.get("life_currency.unit") or []
    tok = by_metric.get("life_currency.tokens_min") or []
    cap = by_metric.get("life_currency.daily_cap") or []
    if tok and tok[0].quality == Quality.VALID.value:
        tv = never_zero_from_unknown(tok[0].value, tok[0].quality)
        if tv is not None and tv <= float(inp.setpoints["tokens_starvation"]):
            lc = "AMBER"
            lr = _state_reasons("AMBER", "C-042 milli-rounding starvation tokens_min=0.000")
            contradictions.append("C-042 starvation")
        elif unit_obs and (not eligibility(unit_obs[0]) or str(unit_obs[0].value) != "life_credit"):
            lc = "UNKNOWN"
            lr = _state_reasons("UNKNOWN", "unit mismatch; no AUD conversion")
        else:
            lc = "GREEN"
            lr = _state_reasons("GREEN", f"unit=life_credit tokens_min={tv} no AUD path")
    elif not tok:
        lc = "UNKNOWN"
        lr = _state_reasons("UNKNOWN", "tokens_min missing")
    else:
        lc = "UNKNOWN"
        lr = _state_reasons("UNKNOWN", f"tokens quality={tok[0].quality}")
    domain_states["life_currency_integrity"] = {"state": lc, "reasons": lr}
    reasons.extend(lr)

    # judge reliability observation only — do not change D6
    judge = by_metric.get("judge.rs_ba") or []
    if not judge:
        jd = "UNKNOWN"
        jr = _state_reasons("UNKNOWN", "judge.rs_ba absent; D6 remains BETWEEN_RUN_VARIANCE")
    elif judge[0].quality != Quality.VALID.value:
        jd = "UNKNOWN"
        jr = _state_reasons("UNKNOWN", f"judge quality={judge[0].quality}; D6 unchanged")
    else:
        jd = "GREEN"
        jr = _state_reasons("GREEN", "judge observed only; D6=BETWEEN_RUN_VARIANCE not upgraded")
    domain_states["judge_reliability"] = {"state": jd, "reasons": jr}
    reasons.extend(jr)

    # Restart WARMUP must not be reported as false AMBER (owner #4 T23).
    scopes = {(o.node_id, o.boot_id) for o in inp.observations}
    scope_known = len(scopes) == 1 and all(node and boot for node, boot in scopes)
    if not scope_known:
        for domain in domain_states.values():
            domain["state"] = "UNKNOWN"
            domain["reasons"] = ["state=UNKNOWN", "IDENTITY_SCOPE_UNKNOWN_OR_MIXED; no synthetic whole-body health"]
        reasons.append("IDENTITY_SCOPE_UNKNOWN_OR_MIXED")
    states = [d["state"] for d in domain_states.values()]
    if "RED" in states:
        global_state = "RED"
    elif domain_states["cardiac"]["state"] == "WARMUP":
        global_state = "WARMUP"
    elif "UNKNOWN" in states:
        global_state = "UNKNOWN"
    elif "AMBER" in states:
        global_state = "AMBER"
    elif "WARMUP" in states:
        global_state = "WARMUP"
    else:
        global_state = "GREEN"
    n_el = len(eligible)
    n_all = max(1, len(inp.observations))
    confidence = round(n_el / n_all, 4)
    if global_state in ("UNKNOWN", "WARMUP"):
        # completeness/quality — do not boost from color
        pass
    reasons.append(f"global={global_state}")
    if inp.previous_assessment:
        prev = (inp.previous_assessment or {}).get("global_state")
        if prev and prev != global_state:
            reasons.append(f"transition {prev}->{global_state}")

    blob = canonical({"dt": dt.isoformat(), "g": global_state,
                      "observations": [o.to_dict() for o in inp.observations],
                      "setpoints": inp.setpoints, "previous": inp.previous_assessment})
    out = {
        "schema": "homeostatic-assessment.v1",
        "assessment_id": _id("ha-", blob),
        "decision_time": dt.isoformat(),
        "boot_id": inp.boot_id,
        "identity_scopes": [{"node_id": n, "boot_id": b} for n, b in sorted(scopes, key=str)],
        "domain_states": domain_states,
        "global_state": global_state,
        "confidence": confidence,
        "confidence_semantics": "eligible fraction; not calibrated predictive confidence",
        "evidence_ids": evidence_ids,
        "excluded_evidence": excluded,
        "reasons": reasons,
        "contradictions": contradictions,
        "setpoints_version": inp.setpoints.get("version"),
        "executable": False,
    }
    if not out["reasons"]:
        out["reasons"] = ["state=UNKNOWN", "reasons-required invariant"]
    for d in domain_states.values():
        assert d["reasons"], "domain reasons must be non-empty"
    return out
