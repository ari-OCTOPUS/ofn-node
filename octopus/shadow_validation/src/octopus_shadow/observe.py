"""Synthetic observe payload validation. Extra fields are forbidden (HTTP 422)."""

from __future__ import annotations

from typing import Any

ALLOWED_FIELDS = frozenset(
    {"synthetic", "scenario", "index", "energy_ratio", "error_rate", "skill", "source", "namespace"}
)
ALLOWED_SCENARIOS = frozenset({"energy_depletion", "error_burst", "model_degradation"})


class ObserveError(ValueError):
    def __init__(self, message: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def parse_synthetic_observation(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ObserveError("payload_must_be_object", 422)
    extra = set(payload) - ALLOWED_FIELDS
    if extra:
        raise ObserveError("extra_forbidden", 422)
    if payload.get("synthetic") is not True:
        raise ObserveError("must_be_synthetic", 422)
    if payload.get("source") not in {None, "shadow-chaos"}:
        raise ObserveError("source_must_be_shadow_chaos", 422)
    if payload.get("namespace") not in {None, "chaos"}:
        raise ObserveError("namespace_must_be_chaos", 422)
    scenario = payload.get("scenario")
    if scenario not in ALLOWED_SCENARIOS:
        raise ObserveError("unknown_scenario", 422)
    return {
        "synthetic": True,
        "scenario": scenario,
        "index": int(payload.get("index") or 0),
        "energy_ratio": float(payload.get("energy_ratio") or 0.0),
        "error_rate": float(payload.get("error_rate") or 0.0),
        "skill": float(payload.get("skill") or 0.0),
        "source": "shadow-chaos",
        "namespace": "chaos",
        "executable": False,
        "action": "NONE",
        "executed": "none",
    }
