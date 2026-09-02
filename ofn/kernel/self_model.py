"""The honest grammar of a system describing itself.

A self-model is only worth anything if every value in it carries where it
came from and when it was seen. This module is the pure vocabulary:
classification and assembly only. It reads no clock, opens no file, and
touches no network — the adapter that calls it owns all observation, and
injects every timestamp as an epoch number.

Two distinctions do most of the work here:

* ABSENT is a measured negative — "we looked, and it is not there". It is
  not a failure and not a guess. UNKNOWN is the absence of a measurement.
  Collapsing either into the other is how a screen ends up green on top
  of a hole.
* A missing value is not zero. Zero is a measurement ("there were none");
  ABSENT and UNKNOWN carry no numeric value at all and render as None.

Kernel purity: no clock, no I/O. Freshness arithmetic is plain float math
on injected epoch seconds.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass
from typing import Any, Sequence

SCHEMA = "self-model.v2"

# A reading stamped moments in the future by a producer whose clock is
# slightly ahead is measurement skew, not time travel. Beyond this many
# seconds, a future-dated reading is untrusted and fails closed.
FUTURE_TOLERANCE_SECONDS = 5.0


class SensorStatus(str, enum.Enum):
    HEALTHY = "healthy"
    STALE = "stale"
    ABSENT = "absent"
    FAILED = "failed"
    UNKNOWN = "unknown"


HEALTHY = SensorStatus.HEALTHY.value
STALE = SensorStatus.STALE.value
ABSENT = SensorStatus.ABSENT.value
FAILED = SensorStatus.FAILED.value
UNKNOWN = SensorStatus.UNKNOWN.value
STATUS_VALUES = tuple(status.value for status in SensorStatus)


@dataclass(frozen=True)
class Reading:
    """One sensor value with its provenance.

    ``value`` is the measured value or None when nothing was measured.
    It is NEVER a fabricated fallback: absent and unknown have no value.
    """

    sensor_id: str
    implementation: str
    status: str
    value: Any = None
    source: str | None = None
    observed_epoch: float | None = None
    detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "sensor_id": self.sensor_id,
            "implementation": self.implementation,
            "status": self.status,
            "value": self.value,
            "source": self.source,
            "observed_epoch": self.observed_epoch,
            "detail": self.detail,
        }


def _finite_epoch(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def classify_freshness(
    observed_epoch: float | None,
    now_epoch: float | None,
    max_age_seconds: float,
) -> tuple[str, int | None]:
    """Classify one observation by age. Fail-closed by construction.

    No observation time -> unknown (never healthy). Future-dated beyond
    tolerance -> unknown (a clock we do not trust is not evidence).
    Older than the window -> stale. Otherwise healthy.
    """
    observed = _finite_epoch(observed_epoch)
    now = _finite_epoch(now_epoch)
    if observed is None or now is None or max_age_seconds < 0:
        return UNKNOWN, None
    age = now - observed
    if age < -FUTURE_TOLERANCE_SECONDS:
        return UNKNOWN, None
    age_seconds = int(max(0.0, age))
    if age > float(max_age_seconds):
        return STALE, age_seconds
    return HEALTHY, age_seconds


def freshness_with_fallback(
    observed_epoch: float | None,
    now_epoch: float | None,
    max_age_seconds: float,
    fallback_status: str,
) -> tuple[str, int | None]:
    """Freshness classification for readings that already carry a status.

    A producer-measured status (absent, failed) survives; freshness only
    decides between healthy and stale when there is something to age.
    An unknown fallback with no observation time stays unknown.
    """
    if fallback_status not in STATUS_VALUES:
        return UNKNOWN, None
    if fallback_status in {ABSENT, FAILED}:
        return fallback_status, None
    status, age = classify_freshness(observed_epoch, now_epoch, max_age_seconds)
    if status is UNKNOWN and fallback_status is not UNKNOWN:
        # A healthy claim we cannot date is not a healthy claim.
        return UNKNOWN, None
    return status, age


def process_reading(
    sensor_id: str,
    implementation: str,
    alive: bool | None,
    observed_epoch: float | None,
    source: str | None,
    detail: str | None = None,
) -> Reading:
    """A liveness probe result. ``alive`` is True/False when measured,
    None when the probe itself could not answer (timeout, unknown error).

    False is a measured negative and is rendered as value False — which is
    a boolean, never a number, so it cannot be mistaken for a count.
    """
    if alive is None:
        return Reading(sensor_id, implementation, UNKNOWN, None, source,
                       observed_epoch, detail or "probe inconclusive")
    status = HEALTHY if alive else ABSENT
    return Reading(sensor_id, implementation, status, bool(alive), source,
                   observed_epoch, detail)


def capability_reading(
    sensor_id: str,
    implementation: str,
    present: bool | None,
    source: str | None,
    detail: str | None = None,
) -> Reading:
    """A capability check against the code that should provide it.

    present=False is a verified absence (the module/symbol is not in this
    checkout). present=None means the check itself failed — unknown.
    """
    if present is None:
        return Reading(sensor_id, implementation, UNKNOWN, None, source,
                       None, detail or "check failed")
    status = HEALTHY if present else ABSENT
    return Reading(sensor_id, implementation, status, bool(present), source,
                   None, detail)


def brain_probe_verdict(
    evidence_epoch: float | None,
    evidence_source: str | None,
    now_epoch: float | None,
    max_age_seconds: float,
) -> dict[str, Any]:
    """Derive a probe verdict from run evidence. Fail-closed.

    Without dated evidence the verdict is unknown/unverifiable — it is
    never "healthy", because the absence of evidence is not a passing
    probe. Deterministic for identical inputs.
    """
    if evidence_epoch is None or evidence_source is None:
        return {
            "status": UNKNOWN,
            "verdict": "unverifiable",
            "source": evidence_source,
            "observed_epoch": None,
            "detail": "no dated run evidence",
        }
    status, age = classify_freshness(evidence_epoch, now_epoch, max_age_seconds)
    verdict = {
        HEALTHY: "probe-evidence-fresh",
        STALE: "probe-evidence-stale",
        UNKNOWN: "unverifiable",
    }[status]
    return {
        "status": status,
        "verdict": verdict,
        "source": evidence_source,
        "observed_epoch": _finite_epoch(evidence_epoch),
        "age_seconds": age,
    }


def overall_status(statuses: Sequence[str]) -> str:
    """The model-level status from sensor statuses. Strictest-first.

    unknown anywhere -> "unverifiable" (the model refuses to look green
    while part of it is unmeasured). stale or failed anywhere ->
    "degraded". Absent counts as a verified negative, not a fault. An
    empty sensor list is unverifiable, not healthy.
    """
    seen = set(statuses)
    if not seen:
        return "unverifiable"
    if UNKNOWN in seen:
        return "unverifiable"
    if STALE in seen or FAILED in seen:
        return "degraded"
    if not seen.issubset({HEALTHY, ABSENT}):
        return "unverifiable"
    return "ok"


def _sorted_readings(readings: Sequence[Reading]) -> list[Reading]:
    return sorted(readings, key=lambda reading: reading.sensor_id)


def status_counts(readings: Sequence[Reading]) -> dict[str, int]:
    counts = {status: 0 for status in STATUS_VALUES}
    for reading in readings:
        if reading.status in counts:
            counts[reading.status] += 1
    return counts


def build_model(
    *,
    code_identity: dict[str, Any] | None,
    sensors: Sequence[Reading],
    processes: Sequence[Reading],
    capabilities: Sequence[Reading],
    events: Sequence[dict[str, Any]],
    brain_probe: dict[str, Any],
    authority: dict[str, Any] | None = None,
    budgets: dict[str, int] | None = None,
    unknowns: Sequence[str] = (),
) -> dict[str, Any]:
    """Assemble the self-model document. Pure and deterministic:
    identical inputs produce an identical document.

    Provenance is structural: every reading carries its source and
    observation time; events carry theirs; nothing here is asserted
    without a pointer.
    """
    ordered_sensors = _sorted_readings(sensors)
    ordered_processes = _sorted_readings(processes)
    ordered_capabilities = _sorted_readings(capabilities)
    all_readings = ordered_sensors + ordered_processes + ordered_capabilities
    statuses = [reading.status for reading in all_readings]
    if brain_probe.get("status") in STATUS_VALUES:
        statuses.append(brain_probe["status"])
    return {
        "schema": SCHEMA,
        "code_identity": dict(code_identity or {}),
        "sensors": [reading.as_dict() for reading in ordered_sensors],
        "processes": [reading.as_dict() for reading in ordered_processes],
        "capabilities": [
            reading.as_dict() for reading in ordered_capabilities
        ],
        "events": [dict(event) for event in events],
        "brain_probe": dict(brain_probe),
        "authority": dict(authority or {}),
        "budgets": dict(budgets or {}),
        "unknowns": list(unknowns),
        "status": overall_status(statuses),
        "counts": {
            "sensors": len(ordered_sensors),
            "processes": len(ordered_processes),
            "capabilities": len(ordered_capabilities),
            "events": len(events),
            **status_counts(all_readings),
        },
    }
