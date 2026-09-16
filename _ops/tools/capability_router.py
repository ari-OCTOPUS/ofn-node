#!/usr/bin/env python3
"""capability_router.py — F5/MP-FIX-01: route structural tasks to code, NEVER to model.

ADR-050: The 0.6b brain is PROVEN unreliable at:
  - extraction (33% pass^5, ACD-01)
  - corrupt-output handling (54% fabrication, ACD-07)
  - nested extraction (0/6)
  - abstention (never abstains, ACD-01/07)

This router ensures those task classes NEVER reach the model.
Only language understanding, choice, synthesis, and summarization go to the brain.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Task classification: what goes to CODE vs MODEL
STRUCTURAL_TASKS = frozenset({
    "field_extraction",       # dict lookup, key check — ACD-01 proved model fails
    "schema_validation",      # parse, type check — INV-TOOL-GUARD
    "presence_check",         # field exists? — model never abstains
    "tool_output_validation", # corrupt/stale/injected — 54% fabrication
    "abstain_decision",       # incomplete data → halt — model can't
    "data_transformation",    # format conversion, unit check
    "hash_verification",      # byte comparison
    "idempotency_check",      # duplicate detection
    "timestamp_freshness",    # staleness check — behavioral blind
    "unit_consistency",       # type/units — 100% fabrication on wrong_units
    "contamination_check",    # injection markers — model follows injections
})

MODEL_TASKS = frozenset({
    "language_understanding",
    "choice_between_options",
    "summarization",
    "hypothesis_generation",
    "creative_synthesis",
    "human_communication",    # writing responses to owner
    "context_interpretation",
})


def route(task_type: str) -> str:
    """Returns 'code' or 'model'. Structural = always code. Unknown = code (fail-closed)."""
    if task_type in STRUCTURAL_TASKS:
        return "code"
    if task_type in MODEL_TASKS:
        return "model"
    return "code"  # fail-closed: unknown tasks never reach model


def route_batch(task_types):
    """Returns dict of {task_type: route}. For dry-run audit."""
    return {t: route(t) for t in task_types}


def structural_tasks_routed_to_model() -> int:
    """Audit: count structural tasks that would go to model (must be 0)."""
    return sum(1 for t in STRUCTURAL_TASKS if route(t) == "model")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.dry_run:
        result = {
            "structural_tasks_routed_to_model": structural_tasks_routed_to_model(),
            "total_structural": len(STRUCTURAL_TASKS),
            "total_model": len(MODEL_TASKS),
            "routing": route_batch(list(STRUCTURAL_TASKS | MODEL_TASKS)),
        }
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        print(__doc__)
