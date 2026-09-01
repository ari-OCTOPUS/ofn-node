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
# S2b lane C (F12): the store path — claim_record, fixture_store and the
# adapter — is inside the boundary now. None of them may reach the scorer,
# the producers or the fixture runner; reaching any of those would let a
# serialization shape influence or observe scoring.
FORBIDDEN_STORE_PATH_IMPORTS = (
    "scorer", "producer_strategy", "producer_persistence", "fixture_run",
)
STORE_PATH_MODULES = ("claim_record", "fixture_store", "claim_adapter")


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


def module_boundary_check(pkg_dir: Path | None = None) -> list[str]:
    """Verify scorer/producer/store-path import boundaries in the package.

    ``pkg_dir`` defaults to this package's directory. Tests pass a temporary
    copy so a deliberate violation can be injected without ever touching the
    real files.
    """
    here = (pkg_dir or Path(__file__).resolve().parent)
    problems: list[str] = []
    scorer_src = (here / "scorer.py").read_text(encoding="utf-8")
    problems += [f"scorer imports {m}" for m in
                 static_import_check(scorer_src, FORBIDDEN_SCORER_IMPORTS)]
    for mod, forbidden in FORBIDDEN_CROSS_IMPORTS.items():
        src = (here / f"{mod}.py").read_text(encoding="utf-8")
        problems += [f"{mod} imports {m}" for m in
                     static_import_check(src, forbidden)]
    for mod in STORE_PATH_MODULES:
        path = here / f"{mod}.py"
        if not path.is_file():
            problems.append(f"{mod} missing from boundary set")
            continue
        src = path.read_text(encoding="utf-8")
        problems += [f"{mod} imports {m}" for m in
                     static_import_check(src, FORBIDDEN_STORE_PATH_IMPORTS)]
    return problems


def store_path_flip_probe(claims_v1, *, feature_supplier,
                          strategy=None, persistence=None) -> dict:
    """F13: the outcome-flip probe, run over the adapter/store path.

    ``claims_v1`` are claim.v1 rows; ``feature_supplier(claim)`` returns the
    ``(feature_a, feature_b)`` pair for each row (the adapter refuses to
    invent them). Rows are converted through ``claim_adapter`` — which means
    the output inherits ``_validate`` guarantees: duplicate ids and
    resolved_at <= observed_at are rejected before any producer runs.

    The real producers are used unless callables are supplied; tests inject
    deliberately outcome-peeking fakes and expect the probe to report False
    rather than wave them through.
    """
    from octopus_observation.claim_adapter import claim_v1_to_record

    strat = strategy if strategy is not None else producer_strategy.predict
    pers = persistence if persistence is not None else producer_persistence.predict

    records = [claim_v1_to_record(c, feature_a=feature_supplier(c)[0],
                                  feature_b=feature_supplier(c)[1])
               for c in claims_v1]
    # Adapter-output guarantees from _validate, enforced as hard assertions:
    # a violating batch never reaches a producer.
    ids = [r.claim_id for r in records]
    if len(ids) != len(set(ids)):
        raise FixtureError("store-path duplicate claim_id")
    for r in records:
        if r.resolved_at is not None and r.resolved_at <= r.observed_at:
            raise FixtureError(f"store-path future-data violation: {r.claim_id}")
    checks: dict[str, object] = {
        "store_no_duplicate_ids": True,
        "store_strict_time": True,
    }
    # Same flip as verify(): outcome inverted, everything else untouched.
    flipped = [dataclasses.replace(c, outcome=None if c.outcome is None
                                   else 1 - c.outcome) for c in records]
    checks["store_path_flip_unchanged"] = (
        [strat(c) for c in flipped] == [strat(c) for c in records]
        and [pers(c) for c in flipped] == [pers(c) for c in records])
    return checks


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
