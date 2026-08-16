#!/usr/bin/env python3
"""task_router.py — Unified Task Routing Policy (EQUIP G10).

Integrates task class (coding/retrieval/causal), privacy level, cost constraint,
risk tolerance, and latency budget into a single routing decision.

Delegates to existing model_router.ask() for actual LLM calls.
This module is the policy layer — it decides WHAT goes WHERE, not HOW.

Constraints:
  - Routing decision is advisory (suggests tier, model_router executes).
  - Privacy-sensitive tasks always route to local (redact-first).
  - Fallback chain: explicit order, observable.
  - No new dependencies — reuses route_scorer signals.
  - $0, stdlib-only, no network calls.

Planner != Executor != Verifier:
  - task_router = planner (decides routing).
  - model_router.ask() = executor (calls LLM).
  - verifier.py = verifier (checks output).
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))
import opslib  # noqa: E402

from structured_schemas import (
    ClaimStrength,
    PrivacyLevel,
    RoutingDecision,
    TaskClass,
    make_plan,
    validate_structured_output,
)

# ── Task class → default routing ─────────────────────────────────────────────
_TASK_CLASS_ROUTING: dict[str, str] = {
    "coding": "local",           # coding with local 1.5b or fixture
    "retrieval": "local",        # retrieval = local index
    "causal_analysis": "local",  # causal = pattern detection, no paid model
    "classification": "local",
    "summarization": "local",
    "research": "secondary",
    "orchestration": "primary",
    "planning": "primary",
    "unknown": "local",
}

# ── Privacy overrides ──────────────────────────────────────────────────────────
_PRIVACY_FORCE_LOCAL = frozenset({
    PrivacyLevel.SENSITIVE.value,
    PrivacyLevel.PRIVATE.value,
})

# ── Cost budgets per task class (USD nominal) ────────────────────────────────
_COST_BUDGET: dict[str, float] = {
    "coding": 0.0,       # local only
    "retrieval": 0.0,    # local only
    "causal_analysis": 0.0,  # local only
    "classification": 0.0,
    "summarization": 0.02,
    "research": 0.10,
    "orchestration": 0.15,
    "planning": 0.10,
    "unknown": 0.0,
}

# ── Latency budgets (ms) ─────────────────────────────────────────────────────
_LATENCY_BUDGET: dict[str, int] = {
    "coding": 30000,
    "retrieval": 5000,
    "causal_analysis": 10000,
    "classification": 3000,
    "summarization": 15000,
    "research": 60000,
    "orchestration": 120000,
    "planning": 60000,
    "unknown": 10000,
}

# ── Task classification heuristics ────────────────────────────────────────────
_CODING_SIGNALS = frozenset({
    "code", "implement", "write", "function", "class", "module",
    "refactor", "debug", "fix", "build", "compile", "test",
    "برنامه", "کد", "تابع", "کلاس",
})
_RETRIEVAL_SIGNALS = frozenset({
    "find", "search", "lookup", "retrieve", "recall", "fetch",
    "جستجو", "پیدا", "بازیابی",
})
_CAUSAL_SIGNALS = frozenset({
    "cause", "effect", "because", "why", "correlation", "causal",
    "علت", "مسبب", "همبستگی", "رابطه",
})


def _classify_task(text: str) -> str:
    """Classify task from description text."""
    t = (text or "").lower()
    toks = set(t.split())

    if toks & _CODING_SIGNALS:
        return TaskClass.CODING.value
    if toks & _RETRIEVAL_SIGNALS:
        return TaskClass.RETRIEVAL.value
    if toks & _CAUSAL_SIGNALS:
        return TaskClass.CAUSAL_ANALYSIS.value
    return TaskClass.UNKNOWN.value


def _detect_privacy(text: str, *, metadata: dict[str, Any] | None = None) -> str:
    """Detect privacy level from task text and metadata."""
    meta = metadata or {}
    # Explicit privacy marker in metadata
    if meta.get("privacy") in (p.value for p in PrivacyLevel):
        return str(meta["privacy"])

    t = (text or "").lower()
    sensitive_toks = {"password", "secret", "token", "credential", "private",
                      "personal", "sensitive", "api_key"}
    if toks := (set(t.split()) & sensitive_toks):
        return PrivacyLevel.PRIVATE.value
    if "internal" in t or "internal" in str(meta.get("scope", "")):
        return PrivacyLevel.INTERNAL.value
    return PrivacyLevel.PUBLIC.value


def route_task(
    task_description: str | None,
    *,
    task_class: str | TaskClass | None = None,
    privacy: str | PrivacyLevel | None = None,
    cost_limit: float | None = None,
    latency_limit_ms: int | None = None,
    risk_tolerance: str = "low",
    metadata: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Route a task to appropriate tier.

    Returns structured plan with routing decision.
    Privacy-sensitive tasks always force local.
    Cost/latency limits constrain the routing.
    """
    # Defensive: None input
    task_description = str(task_description or "")

    # Determine task class
    tc = str(task_class or _classify_task(task_description))
    if tc not in _TASK_CLASS_ROUTING:
        tc = TaskClass.UNKNOWN.value

    # Determine privacy
    pl = str(privacy or _detect_privacy(task_description, metadata=metadata))

    # Default routing from task class
    suggested = _TASK_CLASS_ROUTING.get(tc, "local")

    # Privacy override: sensitive/private -> always local
    if pl in _PRIVACY_FORCE_LOCAL:
        suggested = "local"

    # Cost constraint: if budget < cost of tier, downgrade
    budget = cost_limit if cost_limit is not None else _COST_BUDGET.get(tc, 0.0)
    tier_cost = {"local": 0.0, "secondary": 0.02, "primary": 0.10}
    if suggested in tier_cost and budget < tier_cost[suggested]:
        # Downgrade
        if suggested == "primary":
            suggested = "secondary"
        elif suggested == "secondary":
            suggested = "local"

    # Latency constraint
    lat_limit = latency_limit_ms or _LATENCY_BUDGET.get(tc, 10000)

    # Build structured plan
    plan = make_plan(
        task_class=tc,
        description=task_description[:500],
        routing=suggested,
        estimated_cost_usd=tier_cost.get(suggested, 0.0),
        estimated_latency_ms=lat_limit,
        risk_level=risk_tolerance,
        producer="task_router",
        trace_id=trace_id,
        metadata={"privacy": pl, "cost_budget": budget,
                  "latency_budget_ms": lat_limit},
    )
    return plan


def route_batch(
    tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Route multiple tasks. Each task dict: {description, task_class?, privacy?, ...}."""
    results = []
    for t in tasks:
        r = route_task(
            t.get("description", ""),
            task_class=t.get("task_class"),
            privacy=t.get("privacy"),
            cost_limit=t.get("cost_limit"),
            latency_limit_ms=t.get("latency_limit_ms"),
            metadata=t.get("metadata"),
        )
        results.append(r)
    return results


def fallback_chain(suggested_tier: str) -> list[str]:
    """Return the ordered fallback chain for a tier."""
    chains = {
        "primary": ["primary", "secondary", "local"],
        "secondary": ["secondary", "local"],
        "local": ["local"],
        "rejected": [],
    }
    return chains.get(suggested_tier, ["local"])


if __name__ == "__main__":
    # Quick self-test
    tasks = [
        {"description": "implement a sorting algorithm"},
        {"description": "find the octopus configuration file"},
        {"description": "analyze correlation between budget and performance"},
        {"description": "summarize the architecture document", "privacy": "internal"},
        {"description": "plan a deep refactoring of the cortex module"},
        {"description": "process private financial data"},
    ]
    for t in tasks:
        r = route_task(t["description"])
        print(f"  {t['description'][:50]:50s} -> {r['routing']} ({r['task_class']})")
