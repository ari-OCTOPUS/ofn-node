#!/usr/bin/env python3
"""Piece 1: claim.v1 timestamps + JSON fixture store. No Brier. No official n."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from octopus_observation.claim_record import ClaimV1, claim_from_mapping
from octopus_observation.fixture_store import FixtureClaimStore
from octopus_observation.observation_record import ObservationContractError

FIXTURE = Path(__file__).resolve().parents[1] / "octopus_observation" / "fixtures" / "claims.v1.jsonl"


def test_unresolved_claim_valid() -> None:
    claim = claim_from_mapping(
        {
            "schema": "claim.v1",
            "claim_id": "c-open",
            "observed_at": "2026-08-30T08:00:00Z",
            "resolved_at": None,
            "predicted_p": 0.5,
            "outcome": None,
        }
    )
    assert claim.is_resolved() is False


def test_resolved_after_observed() -> None:
    claim = claim_from_mapping(
        {
            "schema": "claim.v1",
            "claim_id": "c-ok",
            "observed_at": "2026-08-30T08:00:00Z",
            "resolved_at": "2026-08-30T09:00:00Z",
            "predicted_p": 0.2,
            "outcome": False,
        }
    )
    assert claim.is_resolved() is True


def test_resolved_before_observed_rejected() -> None:
    with pytest.raises(ObservationContractError, match="future-data-violation"):
        claim_from_mapping(
            {
                "schema": "claim.v1",
                "claim_id": "c-bad",
                "observed_at": "2026-08-30T09:00:00Z",
                "resolved_at": "2026-08-30T08:00:00Z",
                "predicted_p": 0.2,
                "outcome": True,
            }
        )


def test_bad_timestamp_rejected() -> None:
    with pytest.raises(ObservationContractError, match="observed_at"):
        claim_from_mapping(
            {
                "schema": "claim.v1",
                "claim_id": "c-ts",
                "observed_at": "yesterday",
                "resolved_at": None,
                "predicted_p": None,
                "outcome": None,
            }
        )


def test_store_roundtrip(tmp_path: Path) -> None:
    store = FixtureClaimStore(tmp_path / "claims.jsonl")
    claim = ClaimV1(
        schema="claim.v1",
        claim_id="c-rt",
        observed_at="2026-08-30T08:00:00Z",
        resolved_at="2026-08-30T10:00:00Z",
        predicted_p=0.1,
        outcome=True,
    )
    store.append(claim)
    loaded = store.load()
    assert len(loaded) == 1
    assert loaded[0].claim_id == "c-rt"
    assert store.derived_resolved_count() == 1


def test_packaged_fixture_derived_count_is_not_official_n() -> None:
    store = FixtureClaimStore(FIXTURE)
    count = store.derived_resolved_count()
    assert count == 1
    raw = FIXTURE.read_text(encoding="utf-8")
    assert json.loads(raw.splitlines()[0])["schema"] == "claim.v1"


def test_yaml_and_db_paths_forbidden(tmp_path: Path) -> None:
    with pytest.raises(ObservationContractError, match="yaml"):
        FixtureClaimStore(tmp_path / "claims.yaml")
    with pytest.raises(ObservationContractError, match="db"):
        FixtureClaimStore(tmp_path / "evidence.db")
