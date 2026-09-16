"""Read-ONLY adapters for the off-loop epistemics layer.

SCAFFOLD. Every path below is a [CLAIM] from the roadmap and MUST be verified
against the live repo by GLM before use (git grep + open the file). These
functions NEVER write anything. If a source is missing, return None/[] gracefully
so metrics degrade instead of crashing.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

# TODO(GLM): verify these paths against the live repo. Adjust as needed.
FITNESS_HISTORY = "_ops/state/fitness-history.json"
DEBATE_DIR = "_ops/debate"
TELEMETRY = "_ops/state/telemetry-latest.json"
RECONCILE_DIR = "_ops/reconcile"
DOCTOR_DIR = "_ops/doctor"
# topology is exposed in code (unified_bus.py); GLM wires the real accessor.


def _load_json(path: str) -> Optional[Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, IsADirectoryError):
        return None


def read_fitness_history() -> Optional[Any]:
    return _load_json(FITNESS_HISTORY)


def read_telemetry() -> Optional[Any]:
    return _load_json(TELEMETRY)


def read_debate() -> list:
    if not os.path.isdir(DEBATE_DIR):
        return []
    out = []
    for name in sorted(os.listdir(DEBATE_DIR)):
        rec = _load_json(os.path.join(DEBATE_DIR, name))
        if rec is not None:
            out.append(rec)
    return out


def read_topology() -> Optional[Any]:
    # TODO(GLM): return adjacency (edge list or matrix) from unified_bus.py.
    # Kept None so the scaffold is honest about the missing wire.
    return None


def read_self_vs_twin() -> Optional[dict]:
    # TODO(GLM): return {"err_self": [...], "err_other": [...]} paired over the same
    # targets, sourced from _ops/doctor/* + a baseline twin. None until wired.
    return None
