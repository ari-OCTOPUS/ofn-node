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


# ── S2b lane B: store hardening (F6/F7/F8) ─────────────────────────────


class TestLaneBStoreHardening:
    def _row(self, claim_id="b-001", **over):
        row = {
            "schema": "claim.v1", "claim_id": claim_id,
            "observed_at": "2026-08-30T08:00:00Z", "resolved_at": None,
            "predicted_p": None, "outcome": None,
        }
        row.update(over)
        return row

    def test_json_suffix_rejected(self, tmp_path):
        # F6 (chosen rule): one writer, one suffix. Two rows under .json
        # would be invalid JSON, so .json is refused outright.
        store = FixtureClaimStore(tmp_path / "claims.jsonl")
        store.append(claim_from_mapping(self._row()))
        with pytest.raises(ObservationContractError,
                            match="fixture-suffix-not-jsonl"):
            FixtureClaimStore(tmp_path / "claims.json")

    def test_yaml_yml_db_still_rejected(self, tmp_path):
        # R-05 regression guard — unchanged by lane B.
        for name in ("c.yaml", "c.yml", "c.db"):
            with pytest.raises(ObservationContractError):
                FixtureClaimStore(tmp_path / name)

    def test_malformed_line_three_names_the_line(self, tmp_path):
        store = FixtureClaimStore(tmp_path / "claims.jsonl")
        store.append(claim_from_mapping(self._row("b-001")))
        store.append(claim_from_mapping(self._row("b-002")))
        with open(store.path, "a", encoding="utf-8") as fh:
            fh.write("SECRET-LINE-NOT-JSON\n")
        with pytest.raises(ObservationContractError,
                            match="fixture-line-not-json:3"):
            store.load()

    def test_malformed_error_never_carries_line_content(self, tmp_path):
        store = FixtureClaimStore(tmp_path / "claims.jsonl")
        store.path.parent.mkdir(parents=True, exist_ok=True)
        store.path.write_text("not json at all\n", encoding="utf-8")
        try:
            store.load()
            raise AssertionError("expected rejection")
        except ObservationContractError as exc:
            assert "not json" not in str(exc)

    def test_duplicate_id_on_append_rejected(self, tmp_path):
        store = FixtureClaimStore(tmp_path / "claims.jsonl")
        store.append(claim_from_mapping(self._row("b-001")))
        with pytest.raises(ObservationContractError,
                            match="claim-duplicate-id:b-001"):
            store.append(claim_from_mapping(self._row("b-001")))

    def test_duplicate_id_in_handwritten_file_rejected_on_load(self, tmp_path):
        path = tmp_path / "claims.jsonl"
        row = self._row("b-009")
        line = json.dumps(row, sort_keys=True)
        path.write_text(line + "\n" + line + "\n", encoding="utf-8")
        with pytest.raises(ObservationContractError,
                            match="claim-duplicate-id:b-009"):
            FixtureClaimStore(path).load()

    def test_store_line_count_counts_rows_not_official_n(self, tmp_path):
        store = FixtureClaimStore(tmp_path / "claims.jsonl")
        store.append(claim_from_mapping(self._row("b-001")))
        store.append(claim_from_mapping(
            self._row("b-002", resolved_at="2026-08-31T08:00:00Z", outcome=1)))
        assert store.store_line_count() == 2
        assert store.derived_resolved_count() == 1
