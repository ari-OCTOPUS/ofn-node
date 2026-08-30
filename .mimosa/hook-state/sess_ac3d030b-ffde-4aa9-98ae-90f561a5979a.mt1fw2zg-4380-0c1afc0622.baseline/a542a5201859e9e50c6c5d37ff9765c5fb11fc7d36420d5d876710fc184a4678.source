"""Pure validators. UNKNOWN is never coerced to zero."""
from __future__ import annotations

from datetime import datetime, timezone

from .observation import Observation, Quality, parse_dt
from .registry import MetricRegistry


def _age_s(occurred: datetime, decision: datetime) -> float:
    return (decision - occurred).total_seconds()


def validate_observation(obs: Observation, registry: MetricRegistry) -> Observation:
    reasons = list(obs.quality_reasons or [])
    occ = parse_dt(obs.occurred_at)
    rec = parse_dt(obs.recorded_at)
    dec = parse_dt(obs.decision_time)
    obs.occurred_at, obs.recorded_at, obs.decision_time = occ, rec, dec  # type: ignore[assignment]

    spec = registry.get(obs.metric)
    if spec is None:
        obs.quality = Quality.UNLOCATED.value
        reasons.append(f"metric {obs.metric} not in registry")
        obs.quality_reasons = reasons
        return obs
    if not registry.source_ok(obs.source_id):
        obs.quality = Quality.UNLOCATED.value
        reasons.append(f"source {obs.source_id} not registered")
        obs.quality_reasons = reasons
        return obs
    if occ is None or rec is None or dec is None:
        obs.quality = Quality.MISSING.value
        reasons.append("bitemporal timestamp missing")
        obs.quality_reasons = reasons
        return obs
    if not (occ <= rec <= dec):
        obs.quality = Quality.FUTURE_DATA.value
        reasons.append("violates occurred_at <= recorded_at <= decision_time")
        obs.quality_reasons = reasons
        return obs
    if obs.unit != spec.canonical_unit:
        obs.quality = Quality.UNIT_MISMATCH.value
        reasons.append(f"unit {obs.unit} != {spec.canonical_unit}")
        obs.quality_reasons = reasons
        return obs
    if obs.latest_only and obs.historical_claim:
        obs.quality = Quality.UNLOCATED.value
        reasons.append("latest-only evidence cannot prove a historical beat")
        obs.quality_reasons = reasons
        return obs
    if spec.restart_sensitive and obs.window_n is not None and spec.warmup_window:
        if obs.window_n < spec.warmup_window:
            obs.quality = Quality.WARMUP.value
            reasons.append(f"restart-sensitive window_n={obs.window_n} < {spec.warmup_window}")
            obs.quality_reasons = reasons
            return obs
    age = _age_s(occ, dec)
    if age > spec.max_age_s:
        obs.quality = Quality.STALE.value
        reasons.append(f"age {age:.1f}s > max_age {spec.max_age_s}s")
        obs.quality_reasons = reasons
        return obs
    if obs.value is None and spec.unknown_is_not_zero:
        obs.quality = Quality.MISSING.value
        reasons.append("value is None; UNKNOWN not coerced to zero")
        obs.quality_reasons = reasons
        return obs
    obs.quality = Quality.VALID.value
    if not reasons:
        reasons.append("bitemporal+unit+source+freshness ok")
    obs.quality_reasons = reasons
    return obs


def mark_conflicting(observations: list[Observation], metric: str) -> list[Observation]:
    """Same metric, different values at same beat remain visible and ineligible."""
    by_beat: dict[int | None, list[Observation]] = {}
    for o in observations:
        if o.metric != metric:
            continue
        by_beat.setdefault(o.beat, []).append(o)
    for group in by_beat.values():
        vals = {str(o.value) for o in group}
        if len(vals) > 1:
            for o in group:
                o.quality = Quality.CONFLICTING.value
                o.quality_reasons = list(o.quality_reasons) + ["conflicting values at same beat"]
    return observations


def eligibility(obs: Observation) -> bool:
    return obs.quality == Quality.VALID.value


def never_zero_from_unknown(value: float | int | str | bool | None, quality: str) -> float | None:
    if quality in (Quality.MISSING.value, Quality.UNLOCATED.value, Quality.WARMUP.value):
        return None
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
