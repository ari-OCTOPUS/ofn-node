"""Synthetic telemetry only. Never allocates large RAM, spins CPU, fills disk, or talks to NATS."""

from __future__ import annotations

from collections.abc import Iterator


def samples(scenario: str, count: int = 300) -> Iterator[dict]:
    if scenario not in {"energy_depletion", "error_burst", "model_degradation"}:
        raise ValueError(f"unknown scenario: {scenario}")
    if count < 0:
        raise ValueError("count must be non-negative")
    for index in range(count):
        ratio = (index + 1) / max(count, 1)
        if scenario == "energy_depletion":
            energy = max(0.0, 1.0 - ratio)
            error_rate = 0.01
            skill = 0.0
        elif scenario == "error_burst":
            energy = 0.8
            error_rate = min(1.0, 0.02 + ratio)
            skill = 0.0
        else:
            energy = 0.8
            error_rate = 0.02
            skill = max(-1.0, 0.5 - ratio)
        yield {
            "synthetic": True,
            "scenario": scenario,
            "index": index,
            "energy_ratio": energy,
            "error_rate": error_rate,
            "skill": skill,
            "source": "shadow-chaos",
        }


def may_update_production_skill(observation: dict) -> bool:
    if observation.get("synthetic") is True:
        return False
    if observation.get("source") == "shadow-chaos":
        return False
    if observation.get("namespace") == "chaos":
        return False
    return True
