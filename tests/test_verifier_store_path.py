"""S2b lane C — verifier reach over the store path (F12/F13).

Two properties, each proven the honest way:
- the boundary check actually reaches claim_record/fixture_store/claim_adapter:
  a deliberate bad import injected into a TEMP COPY is detected (the real
  files are never touched);
- the store-path flip probe fails loud when a producer peeks at outcome.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from octopus_observation.claim_record import ClaimV1, claim_from_mapping
from octopus_observation.observation_record import ObservationContractError
from octopus_observation.obs_fixture import FixtureError
from octopus_observation.verifier import (
    STORE_PATH_MODULES, module_boundary_check, store_path_flip_probe,
)

PKG = Path(__file__).resolve().parents[1] / "octopus_observation"


def _v1_rows():
    return [
        claim_from_mapping({
            "schema": "claim.v1", "claim_id": "c-001",
            "observed_at": "2026-08-30T08:00:00Z",
            "resolved_at": "2026-08-31T08:00:00Z",
            "predicted_p": 0.7, "outcome": 1}),
        claim_from_mapping({
            "schema": "claim.v1", "claim_id": "c-002",
            "observed_at": "2026-08-30T09:00:00Z",
            "resolved_at": None, "predicted_p": None, "outcome": None}),
    ]


FEATURES = {"c-001": (0.25, 0.75), "c-002": (0.6, 0.4)}


def _feature_supplier(claim):
    return FEATURES[claim.claim_id]


class TestBoundaryReach:
    def test_clean_package_passes_and_covers_the_three_modules(self):
        problems = module_boundary_check()
        assert problems == []

    def test_injected_bad_import_in_temp_copy_is_detected(self, tmp_path):
        for mod in STORE_PATH_MODULES:
            copy = tmp_path / f"case-{mod}"
            copy.mkdir()
            for name in ("scorer", "producer_strategy", "producer_persistence",
                         *STORE_PATH_MODULES):
                src = PKG / f"{name}.py"
                if src.is_file():
                    shutil.copyfile(src, copy / f"{name}.py")
            target = copy / f"{mod}.py"
            target.write_text(
                target.read_text(encoding="utf-8")
                + "\nimport producer_strategy  # deliberate violation\n",
                encoding="utf-8")
            problems = module_boundary_check(pkg_dir=copy)
            assert f"{mod} imports producer_strategy" in problems, (
                f"boundary check does not reach {mod}")

    def test_missing_store_module_is_reported_not_skipped(self, tmp_path):
        copy = tmp_path / "missing-case"
        copy.mkdir()
        for name in ("scorer", "producer_strategy", "producer_persistence"):
            shutil.copyfile(PKG / f"{name}.py", copy / f"{name}.py")
        problems = module_boundary_check(pkg_dir=copy)
        for mod in STORE_PATH_MODULES:
            assert f"{mod} missing from boundary set" in problems


class TestStorePathFlipProbe:
    def test_real_producers_pass_through_the_store_path(self):
        checks = store_path_flip_probe(_v1_rows(),
                                       feature_supplier=_feature_supplier)
        assert checks["store_no_duplicate_ids"] is True
        assert checks["store_strict_time"] is True
        assert checks["store_path_flip_unchanged"] is True

    def test_outcome_peeking_fake_producer_fails_the_probe(self):
        def peeking(record):
            # Predictions that depend on outcome — exactly what the probe
            # exists to catch.
            base = 0.5 if record.outcome is None else float(record.outcome)
            return {"claim_id": record.claim_id, "prediction": base,
                    "as_of": record.observed_at}

        checks = store_path_flip_probe(_v1_rows(),
                                       feature_supplier=_feature_supplier,
                                       strategy=peeking)
        assert checks["store_path_flip_unchanged"] is False

    def test_duplicate_ids_never_reach_a_producer(self):
        rows = _v1_rows()
        dupes = rows + [ClaimV1(**{**rows[0].__dict__, "claim_id": rows[0].claim_id})]
        # Same id twice: the adapter output must be refused (via _validate),
        # which raises before any producer runs.
        with pytest.raises(FixtureError, match="duplicate"):
            store_path_flip_probe(dupes, feature_supplier=_feature_supplier)

    def test_strict_time_violation_never_reaches_a_producer(self):
        rows = _v1_rows()
        bad = ClaimV1(schema=rows[0].schema, claim_id="c-003",
                      observed_at="2026-08-30T08:00:00Z",
                      resolved_at="2026-08-30T08:00:00Z",
                      predicted_p=None, outcome=0)
        # The adapter's own strict rule fires first (ObservationContractError);
        # the probe's batch-level FixtureError is the second lock. Either way
        # the violating row never reaches a producer.
        with pytest.raises((ObservationContractError, FixtureError),
                            match="future-data"):
            store_path_flip_probe(rows + [bad],
                                  feature_supplier=lambda c: FEATURES.get(
                                      c.claim_id, (0.5, 0.5)))
