#!/usr/bin/env python3
"""Replay-safe observation.v1 foundation tests. No network, no hardware."""
from __future__ import annotations

import json
import tempfile
from dataclasses import FrozenInstanceError
from pathlib import Path

from octopus_observation.observation_record import (
    ObservationContractError,
    ObservationV1,
    observation_from_mapping,
    sha256_hex,
)
from octopus_observation.replay_adapters import FakeAdapter, ReplayAdapter


PKG = Path(__file__).resolve().parents[1] / "octopus_observation"
OBSERVED = "2026-08-30T08:00:00Z"
RECEIVED = "2026-08-30T08:00:05Z"
NOW = "2026-08-30T08:10:00Z"
RAW_HASH = sha256_hex(b"fixture-raw")


def _physical_payload() -> dict:
    return {
        "schema": "observation.v1",
        "observation_id": "11111111-1111-1111-1111-111111111111",
        "sensor_id": "board-cpu-temp",
        "source_type": "physical",
        "observed_at": OBSERVED,
        "received_at": RECEIVED,
        "value": 41.25,
        "unit": "degC",
        "uncertainty": {"kind": "stddev", "value": 0.5},
        "calibration": {
            "calibration_id": "cpu-temp-2026-08",
            "calibrated_at": "2026-08-01T00:00:00Z",
            "method": "two-point",
        },
        "quality_flags": [],
        "provenance": {
            "device_id": "board-180",
            "adapter": "replay-fixture",
            "adapter_version": "1.0.0",
            "raw_hash": RAW_HASH,
        },
        "privacy_class": "internal",
        "simulation": False,
    }


def test_valid_simulated_record_from_fake() -> None:
    record = FakeAdapter().emit(observed_at=OBSERVED, received_at=RECEIVED)
    record.validate()
    assert record.schema == "observation.v1"
    assert record.simulation is True
    assert record.source_type == "simulated"
    assert record.grants_action_authority() is False
    assert record.can_self_approve() is False


def test_simulated_cannot_masquerade_as_physical() -> None:
    payload = _physical_payload()
    payload["source_type"] = "simulated"
    payload["simulation"] = False
    try:
        observation_from_mapping(payload)
    except ObservationContractError as exc:
        assert "simulated-unlabeled" in str(exc)
    else:
        raise AssertionError("mixed simulated/physical label was accepted")


def test_physical_cannot_be_labeled_simulated() -> None:
    payload = _physical_payload()
    payload["simulation"] = True
    try:
        observation_from_mapping(payload)
    except ObservationContractError as exc:
        assert "physical-labeled-simulated" in str(exc)
    else:
        raise AssertionError("physical record accepted as simulated")


def test_fake_adapter_cannot_claim_physical() -> None:
    record = FakeAdapter().emit(observed_at=OBSERVED, received_at=RECEIVED)
    try:
        ObservationV1(
            observation_id=record.observation_id,
            sensor_id=record.sensor_id,
            source_type="physical",
            observed_at=record.observed_at,
            received_at=record.received_at,
            value=record.value,
            unit=record.unit,
            uncertainty=record.uncertainty,
            calibration=record.calibration,
            quality_flags=record.quality_flags,
            provenance=record.provenance,
            privacy_class=record.privacy_class,
            simulation=False,
        ).validate()
    except ObservationContractError as exc:
        assert "fake-adapter-cannot-claim-physical" in str(exc)
    else:
        raise AssertionError("fake adapter provenance accepted as physical")


def test_unknown_uncertainty_cannot_become_zero() -> None:
    payload = _physical_payload()
    payload["uncertainty"] = {"kind": "unknown", "value": 0}
    try:
        observation_from_mapping(payload)
    except ObservationContractError as exc:
        assert "unknown-uncertainty-cannot-become-numeric" in str(exc)
    else:
        raise AssertionError("unknown uncertainty collapsed to zero")


def test_raw_observation_is_immutable() -> None:
    record = FakeAdapter().emit(observed_at=OBSERVED, received_at=RECEIVED)
    try:
        record.value = 99  # type: ignore[misc]
    except FrozenInstanceError:
        return
    raise AssertionError("observation value was mutated")


def test_normalize_creates_separate_record() -> None:
    raw = FakeAdapter().emit(observed_at=OBSERVED, received_at=RECEIVED)
    derived = raw.normalize(now_utc=NOW, method="scale-celsius")
    assert derived.observation_id != raw.observation_id
    assert derived.derived_from == raw.observation_id
    assert "normalized" in derived.quality_flags
    assert raw.derived_from is None
    assert "normalized" not in raw.quality_flags


def test_stale_observation_is_detectable() -> None:
    record = FakeAdapter().emit(observed_at=OBSERVED, received_at=RECEIVED)
    assert record.is_stale(now_utc="2026-08-30T08:00:30Z", max_age_seconds=60) is False
    assert record.is_stale(now_utc="2026-08-30T09:00:00Z", max_age_seconds=60) is True


def test_naive_timestamp_fails_closed() -> None:
    payload = _physical_payload()
    payload["observed_at"] = "2026-08-30T08:00:00"
    try:
        observation_from_mapping(payload)
    except ObservationContractError as exc:
        assert "observed_at-not-rfc3339-utc" in str(exc)
    else:
        raise AssertionError("naive timestamp accepted")


def test_malformed_provenance_fails_closed() -> None:
    payload = _physical_payload()
    payload["provenance"]["raw_hash"] = "not-a-hash"
    try:
        observation_from_mapping(payload)
    except ObservationContractError as exc:
        assert "provenance-raw-hash-invalid" in str(exc)
    else:
        raise AssertionError("malformed provenance accepted")


def test_observation_cannot_grant_action_authority() -> None:
    payload = _physical_payload()
    payload["may_execute"] = True
    try:
        observation_from_mapping(payload)
    except ObservationContractError as exc:
        assert "authority-keys-forbidden" in str(exc)
    else:
        raise AssertionError("authority-bearing observation accepted")


def test_observation_cannot_self_approve() -> None:
    payload = _physical_payload()
    payload["self_approved"] = True
    try:
        observation_from_mapping(payload)
    except ObservationContractError as exc:
        assert "authority-keys-forbidden" in str(exc)
    else:
        raise AssertionError("self-approving observation accepted")


def test_replay_adapter_loads_fixture() -> None:
    payload = _physical_payload()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "cpu-temp.json"
        path.write_text(json.dumps({"observations": [payload]}), encoding="utf-8")
        records = ReplayAdapter().load(path)
    assert len(records) == 1
    record = records[0]
    assert record.source_type == "physical"
    assert record.simulation is False
    assert record.provenance.adapter == "replay"
    assert "replayed" in record.quality_flags
    assert record.grants_action_authority() is False


def test_replay_malformed_fixture_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "bad.json"
        path.write_text("{not-json", encoding="utf-8")
        try:
            ReplayAdapter().load(path)
        except ObservationContractError as exc:
            assert "replay-json-invalid" in str(exc)
        else:
            raise AssertionError("malformed replay fixture accepted")


def test_modules_do_not_import_network() -> None:
    record_src = (PKG / "observation_record.py").read_text(encoding="utf-8")
    adapter_src = (PKG / "replay_adapters.py").read_text(encoding="utf-8")
    banned = ("import requests", "import httpx", "import socket", "urllib.request", "subprocess")
    for src in (record_src, adapter_src):
        for token in banned:
            assert token not in src, token
