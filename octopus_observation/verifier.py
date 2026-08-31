#!/usr/bin/env python3
"""Independent verifier (W-C).

Uses only independent properties of the artifacts it is handed:
- fixture integrity: duplicate IDs, missing timestamps, unresolved policy,
  resolution ordering, provenance (tamper) hash;
- producer independence: outcome-flip probe (predictions must not change),
  copied-baseline detection (identical strategy/persistence outputs);
- static boundary: scorer source must not import either producer; producers
  must not import each other.
"""
from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

from octopus_observation import obs_fixture
from octopus_observation import producer_strategy
from octopus_observation import producer_persistence
from octopus_observation.obs_fixture import ClaimRecord, FixtureError, provenance_hash

FORBIDDEN_SCORER_IMPORTS = ("producer_strategy", "producer_persistence")
FORBIDDEN_CROSS_IMPORTS = {
    "producer_strategy": ("producer_persistence",),
    "producer_persistence": ("producer_strategy",),
}


def static_import_check(source: str, forbidden: tuple[str, ...]) -> list[str]:
    """Return the list of forbidden module names imported by ``source``."""
    tree = ast.parse(source)
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [(node.module or "").split(".")[0]]
        else:
            continue
        bad.extend(n for n in names if n in forbidden)
    return bad


def module_boundary_check() -> list[str]:
    """Verify scorer/producer import boundaries inside this package."""
    here = Path(__file__).resolve().parent
    problems: list[str] = []
    scorer_src = (here / "scorer.py").read_text(encoding="utf-8")
    problems += [f"scorer imports {m}" for m in
                 static_import_check(scorer_src, FORBIDDEN_SCORER_IMPORTS)]
    for mod, forbidden in FORBIDDEN_CROSS_IMPORTS.items():
        src = (here / f"{mod}.py").read_text(encoding="utf-8")
        problems += [f"{mod} imports {m}" for m in
                     static_import_check(src, forbidden)]
    return problems


def verify(claims: list[ClaimRecord],
           strategy_preds: list[dict],
           persistence_preds: list[dict],
           expected_provenance: str | None = None) -> dict:
    checks: dict[str, object] = {}

    obs_fixture._validate(claims)
    checks["fixture_valid"] = True

    if expected_provenance is not None:
        actual = provenance_hash(claims)
        checks["provenance_match"] = actual == expected_provenance
        if actual != expected_provenance:
            return {"ok": False, "checks": checks,
                    "error": "FIXTURE_TAMPERED"}

    ids = [c.claim_id for c in claims]
    checks["no_duplicate_ids"] = len(ids) == len(set(ids))

    # Outcome-flip probe: producers must be outcome-blind.
    flipped = [dataclasses.replace(c, outcome=None if c.outcome is None
                                   else 1 - c.outcome) for c in claims]
    strat_flip = [producer_strategy.predict(c) for c in flipped]
    pers_flip = [producer_persistence.predict(c) for c in flipped]
    checks["no_future_data_leakage"] = (
        strat_flip == strategy_preds and pers_flip == persistence_preds)

    # Copied-baseline detection.
    strat_p = [p["prediction"] for p in strategy_preds]
    pers_p = [p["prediction"] for p in persistence_preds]
    checks["not_copied_baseline"] = strat_p != pers_p

    # as_of ordering: predictions are stamped at observation time.
    obs_by_id = {c.claim_id: c.observed_at for c in claims}
    checks["as_of_ordering"] = all(
        p["as_of"] == obs_by_id.get(p["claim_id"]) for p in strategy_preds
    ) and all(p["as_of"] == obs_by_id.get(p["claim_id"])
              for p in persistence_preds)

    checks["module_boundaries"] = module_boundary_check()

    ok = all(v is True for k, v in checks.items() if isinstance(v, bool)) \
        and not checks["module_boundaries"]
    return {"ok": ok, "checks": checks}
