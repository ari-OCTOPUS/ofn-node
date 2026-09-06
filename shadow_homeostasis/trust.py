"""Pure local validation. A source label is not authenticated origin."""
from copy import deepcopy
import math

from .canonical import digest, finite_number
from .observation import Observation, Quality, parse_dt
from .registry import MetricRegistry


def validate_observation(obs: Observation, registry: MetricRegistry, *, decision_time=None):
    out = deepcopy(obs)
    out._validation_hash = None
    reasons = list(out.quality_reasons or [])
    claimed_quality = out.quality

    def finish(quality, reason):
        out.quality = quality
        out.quality_reasons = sorted(set(reasons + [reason]))
        out._validation_hash = digest(out.to_dict())
        return out

    try:
        occ, rec = parse_dt(out.occurred_at), parse_dt(out.recorded_at)
        embedded = parse_dt(out.decision_time)
        dec = parse_dt(decision_time) if decision_time is not None else embedded
    except (TypeError, ValueError, OverflowError):
        return finish("MISSING", "TIME_MALFORMED_OR_NAIVE")
    if occ is None or rec is None or dec is None or embedded is None:
        return finish("MISSING", "TIME_MISSING")
    out.occurred_at, out.recorded_at, out.decision_time = occ, rec, dec
    if embedded != dec:
        reasons.append("CLOCK_OVERRIDDEN_BY_CALLER")
    spec = registry.get(out.metric)
    if spec is None:
        return finish("UNLOCATED", "METRIC_UNREGISTERED")
    if not registry.source_ok(out.source_id):
        return finish("UNLOCATED", "SOURCE_UNREGISTERED")
    if out.source_id not in spec.source_priority:
        return finish("UNLOCATED", "SOURCE_METRIC_MISMATCH")
    if not out.observation_id or not out.provenance_path or not out.source_hash:
        return finish("UNLOCATED", "PROVENANCE_MISSING")
    if not occ <= rec <= dec:
        return finish("FUTURE_DATA", "TIME_ORDER_VIOLATION")
    if out.unit != spec.canonical_unit:
        return finish("UNIT_MISMATCH", "UNIT_MISMATCH")
    if out.latest_only and out.historical_claim:
        return finish("UNLOCATED", "LATEST_ONLY_NOT_HISTORICAL")
    if out.value is None:
        return finish("MISSING", "VALUE_MISSING_NOT_ZERO")
    if spec.canonical_unit == "enum":
        if not isinstance(out.value, str) or not out.value:
            return finish("MISSING", "VALUE_TYPE")
    else:
        if type(out.value) not in (int, float):
            return finish("MISSING", "VALUE_TYPE")
        if not finite_number(out.value):
            return finish("MISSING", "VALUE_NONFINITE")
        if spec.canonical_unit == "count" and (out.value < 0 or int(out.value) != out.value):
            return finish("MISSING", "VALUE_RANGE")
        if spec.canonical_unit == "ratio" and not 0 <= out.value <= 1:
            return finish("MISSING", "VALUE_RANGE")
        if spec.canonical_unit == "percent" and not 0 <= out.value <= 100:
            return finish("MISSING", "VALUE_RANGE")
        if spec.canonical_unit in ("s", "life_credit") and out.value < 0:
            return finish("MISSING", "VALUE_RANGE")
    for name in ("beat", "window_n", "window_ready"):
        value = getattr(out, name)
        if value is not None and (type(value) is not int or value < 0):
            return finish("MISSING", "COUNTER_INVALID:" + name)
    if (dec - occ).total_seconds() > spec.max_age_s:
        return finish("STALE", "AGE_EXCEEDS_MAX")
    # Restrictive annotations are data: do not silently promote them.
    if claimed_quality not in ("VALID", ""):
        if claimed_quality in {q.value for q in Quality}:
            return finish(claimed_quality, "RESTRICTIVE_INPUT_QUALITY_PRESERVED")
        return finish("UNLOCATED", "QUALITY_UNRECOGNIZED")
    if spec.restart_sensitive and spec.warmup_window:
        if ((out.window_n is None and spec.warmup_window > 1)
                or (out.window_n is not None and out.window_n < spec.warmup_window)):
            return finish("WARMUP", "RESTART_WINDOW_NOT_READY")
    return finish("VALID", "LOCAL_CONTRACT_OK_ORIGIN_UNAUTHENTICATED")


def eligibility(obs):
    return (obs.quality == "VALID" and obs._validation_hash is not None
            and obs._validation_hash == digest(obs.to_dict()))


def mark_conflicting(observations, metric):
    result = deepcopy(observations)
    groups = {}
    for obs in result:
        if obs.metric != metric or not eligibility(obs):
            continue
        # A missing beat never makes unrelated samples coincident.
        key = (obs.node_id, obs.boot_id, obs.metric, obs.beat, obs.occurred_at)
        if obs.beat is None or obs.boot_id is None or obs.node_id is None:
            continue
        groups.setdefault(key, []).append(obs)
    for group in groups.values():
        if len({digest({"value": o.value, "unit": o.unit}) for o in group}) > 1:
            for obs in group:
                obs.quality = "CONFLICTING"
                obs.quality_reasons = sorted(set(obs.quality_reasons + ["COINCIDENT_VALUE_CONFLICT"]))
    return result


def never_zero_from_unknown(value, quality):
    if quality != "VALID" or type(value) not in (int, float):
        return None
    return float(value) if finite_number(value) else None
