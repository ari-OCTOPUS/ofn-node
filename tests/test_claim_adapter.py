"""S2b lane A — claim adapter contract tests (F1/F2/F3/F4/F9/F10/F11).

Every test here pins an owner ruling or a defect in the register:
strict time on both paths, int outcome with legacy bool opt-in, predicted_p
validated on unresolved rows, schema presence, byte-stable round-trip,
and features that are required, never invented.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from octopus_observation.claim_adapter import (
    claim_v1_to_record, record_to_claim_v1,
)
from octopus_observation.claim_record import (
    ClaimV1, claim_from_mapping, claim_to_legacy_json,
)
from octopus_observation.observation_record import ObservationContractError
from octopus_observation.obs_fixture import build_fixture

FIXTURE = Path(__file__).resolve().parents[1] / "octopus_observation" / "fixtures" / "claims.v1.jsonl"

FA = 0.25
FB = 0.75


def _resolved_row(**over):
    row = {
        "schema": "claim.v1", "claim_id": "t-001",
        "observed_at": "2026-08-30T08:00:00Z",
        "resolved_at": "2026-08-31T08:00:00Z",
        "predicted_p": 0.7, "outcome": True,
    }
    row.update(over)
    return row


def _unresolved_row(**over):
    return _resolved_row(resolved_at=None, outcome=None, **over)


class TestStrictTime:
    def test_equal_timestamps_rejected_on_both_paths_same_error_class(self):
        row = _resolved_row(resolved_at="2026-08-30T08:00:00Z")
        # Path 1: the claim.v1 row itself refuses equal timestamps.
        with pytest.raises(ObservationContractError, match="future-data"):
            claim_from_mapping(row)
        # Path 2: the same row, hand-built, is refused by the adapter too —
        # and by the same error class.
        claim = ClaimV1(schema=row["schema"], claim_id=row["claim_id"],
                        observed_at=row["observed_at"],
                        resolved_at=row["resolved_at"],
                        predicted_p=row["predicted_p"], outcome=1)
        with pytest.raises(ObservationContractError, match="future-data"):
            claim_v1_to_record(claim, feature_a=FA, feature_b=FB)


class TestPredictedP:
    def test_out_of_range_on_unresolved_row_rejected(self):
        # F9 regression: this used to pass because validate() returned early.
        with pytest.raises(ObservationContractError, match="predicted-p-out-of-range"):
            claim_from_mapping(_unresolved_row(predicted_p=7.5))

    def test_non_number_rejected(self):
        with pytest.raises(ObservationContractError, match="predicted-p-not-number"):
            claim_from_mapping(_resolved_row(predicted_p="high"))


class TestSchemaPresence:
    def test_row_without_schema_rejected(self):
        row = _resolved_row()
        del row["schema"]
        with pytest.raises(ObservationContractError, match="claim-schema-missing"):
            claim_from_mapping(row)


class TestOutcome:
    def test_true_normalizes_to_one(self):
        assert claim_from_mapping(_resolved_row(outcome=True)).outcome == 1

    def test_two_rejected(self):
        with pytest.raises(ObservationContractError, match="outcome-not-binary"):
            claim_from_mapping(_resolved_row(outcome=2))

    def test_legacy_json_re_emits_bool_only_on_request(self):
        claim = claim_from_mapping(_resolved_row())
        assert claim.to_dict()["outcome"] == 1
        assert json.loads(claim_to_legacy_json(claim))["outcome"] is True


class TestRoundTrip:
    def test_packaged_fixture_round_trips_byte_stable(self):
        rows = [json.loads(line) for line in
                FIXTURE.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert rows, "packaged fixture is missing"
        for row in rows:
            claim = claim_from_mapping(row)
            record = claim_v1_to_record(claim, feature_a=FA, feature_b=FB)
            back = record_to_claim_v1(record, predicted_p=claim.predicted_p)
            assert back == claim
            assert json.dumps(back.to_dict(), sort_keys=True) == \
                json.dumps(claim.to_dict(), sort_keys=True)

    def test_canonical_fixture_round_trips_through_the_adapter(self):
        for record in build_fixture(n=6, unresolved=2):
            claim = record_to_claim_v1(record, predicted_p=0.5)
            again = claim_v1_to_record(claim, feature_a=record.feature_a,
                                       feature_b=record.feature_b)
            assert again == record

    def test_non_canonical_input_is_normalized(self):
        # F11: fractional seconds collapse to the one canonical form.
        claim = claim_from_mapping(_resolved_row(
            observed_at="2026-08-30T08:00:00.500Z",
            resolved_at="2026-08-31T08:00:00.500Z"))
        record = claim_v1_to_record(claim, feature_a=FA, feature_b=FB)
        assert record.observed_at == "2026-08-30T08:00:00Z"
        assert record.resolved_at == "2026-08-31T08:00:00Z"


class TestFeatures:
    def test_adapter_without_features_raises(self):
        claim = claim_from_mapping(_unresolved_row())
        with pytest.raises(ObservationContractError, match="claim-missing-features"):
            claim_v1_to_record(claim)
        with pytest.raises(ObservationContractError, match="claim-missing-features"):
            claim_v1_to_record(claim, feature_a=FA, feature_b=None)

    def test_features_travel_untouched(self):
        claim = claim_from_mapping(_unresolved_row())
        record = claim_v1_to_record(claim, feature_a=FA, feature_b=FB)
        assert (record.feature_a, record.feature_b) == (FA, FB)
