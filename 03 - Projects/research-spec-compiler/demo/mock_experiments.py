"""
SYNTHETIC reference experiments.

These are NOT results. They are deterministic, seeded stand-ins that let the
harness run end-to-end with zero dependencies and zero real data, so you can
see the *pipeline* (ablation -> failure check -> decision_rule -> verdict)
before writing the real experiment. Each condition draws a metric value from a
fixed Normal(center, sd); swap `run` for your real evaluation to go live.

Epistemic note (matches the project's methodology): replacing these with real
runs is mandatory before any claim. The centers below are illustrative only.
"""
from __future__ import annotations

from random import Random
from typing import Dict, List, Tuple

from spec_compiler.harness import Condition


def _draw(center: float, sd: float, lo: float = 0.0, hi: float = 1.0):
    def run(rng: Random) -> float:
        return max(lo, min(hi, rng.gauss(center, sd)))
    return run


# --- Demo 1: multi-agent debate for extraction --------------------------------
# Reproduces the narrative in the reference example: single-agent ~0.71,
# debate w/o resolver ~0.76, debate + resolver ~0.83.
def debate_extraction() -> Tuple[List[Condition], str]:
    conditions = [
        Condition("single_agent", _draw(0.71, 0.015), "extraction with one agent"),
        Condition("debate_no_resolver", _draw(0.76, 0.018), "A extracts + B critiques, no arbiter"),
        Condition("debate_resolver", _draw(0.83, 0.015), "A + B + resolver merges/selects"),
    ]
    return conditions, "debate_resolver"


# --- Demo 2: working-memory bottleneck -> abstraction (H-OWN-03 / EXP-001) -----
# Reference file, principle 7: abstraction is stable when useful for
# prediction / compression / transfer. So the metric is transfer accuracy.
def wm_abstraction() -> Tuple[List[Condition], str]:
    conditions = [
        Condition("unlimited_memory", _draw(0.62, 0.020), "raw unlimited state buffer (baseline)"),
        Condition("limited_wm", _draw(0.74, 0.020), "K-slot working-memory bottleneck"),
    ]
    return conditions, "limited_wm"


REGISTRY: Dict[str, callable] = {
    "debate_extraction": debate_extraction,
    "wm_abstraction": wm_abstraction,
}
