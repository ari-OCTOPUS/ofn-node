#!/usr/bin/env python3
"""W-C fixture-pipeline runner: fixture -> producers -> scorer -> verifier -> receipt.

Phase 1 (fixture-only): no network, no live API, no runtime database, no
superiority claim. The receipt is canonical JSON; its ``receipt_sha256`` makes
the artifact immutable by reference.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from octopus_observation import obs_fixture
from octopus_observation import producer_strategy
from octopus_observation import producer_persistence
from octopus_observation import scorer
from octopus_observation import verifier

SCHEMA = "octopus.observatory-fixture-v1.receipt/1"


def run_pipeline(n: int = 40, seed: int = 20260830, unresolved: int = 5,
                 generated_at_utc: str | None = None) -> dict:
    claims = obs_fixture.build_fixture(n=n, seed=seed, unresolved=unresolved)
    prov = obs_fixture.provenance_hash(claims)

    strategy_preds = [producer_strategy.predict(c) for c in claims]
    persistence_preds = [producer_persistence.predict(c) for c in claims]

    outcome_by_id = {c.claim_id: c.outcome for c in claims}
    strat_pairs = [(p["claim_id"], p["prediction"], outcome_by_id[p["claim_id"]])
                   for p in strategy_preds]
    pers_pairs = [(p["claim_id"], p["prediction"], outcome_by_id[p["claim_id"]])
                  for p in persistence_preds]

    strat_metrics = scorer.score(strat_pairs)
    pers_metrics = scorer.score(pers_pairs)

    verification = verifier.verify(claims, strategy_preds, persistence_preds,
                                   expected_provenance=prov)

    per_claim_hash = hashlib.sha256(
        json.dumps(strat_metrics["per_claim"], sort_keys=True).encode()
    ).hexdigest()

    receipt = {
        "schema": SCHEMA,
        "phase": "fixture-only",
        "fixture_version": obs_fixture.FIXTURE_VERSION,
        "seed": seed,
        "n_claims": n,
        "unresolved_count": strat_metrics["unresolved_excluded"],
        "missing_data_policy": "claims without observed_at rejected at build; unresolved excluded from scoring with count",
        "provenance_hash": prov,
        "per_claim_contribution_sha256": per_claim_hash,
        "strategy": {"producer": producer_strategy.STRATEGY_VERSION,
                     **{k: strat_metrics[k] for k in ("n", "brier", "ci95", "method")}},
        "persistence": {"producer": producer_persistence.PERSISTENCE_VERSION,
                        **{k: pers_metrics[k] for k in ("n", "brier", "ci95", "method")}},
        "verification": verification,
        "superiority_claim": None,
        "notes": "fixture-only results; not a real-world performance claim",
        "generated_at_utc": generated_at_utc
        or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    receipt["receipt_sha256"] = hashlib.sha256(
        json.dumps(receipt, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    return receipt


if __name__ == "__main__":
    print(json.dumps(run_pipeline(), indent=1, ensure_ascii=False))
