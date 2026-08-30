"""Fake and replay adapters for observation.v1. No network, no hardware."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .observation_record import (
    Calibration,
    ObservationContractError,
    ObservationV1,
    Provenance,
    QUALITY_REPLAYED,
    Uncertainty,
    new_observation_id,
    observation_from_mapping,
    sha256_hex,
)


ADAPTER_VERSION = "1.0.0"


def _require_utc_pair(observed_at: str, received_at: str) -> None:
    # Validation is owned by ObservationV1; this keeps adapter construction explicit.
    if not observed_at or not received_at:
        raise ObservationContractError("adapter-timestamps-missing")


class FakeAdapter:
    """Deterministic simulated sensor. Cannot emit a physical observation."""

    name = "fake"
    version = ADAPTER_VERSION

    def emit(
        self,
        *,
        sensor_id: str = "fake-cpu-temp",
        observed_at: str,
        received_at: str,
        value: float = 42.5,
        unit: str = "degC",
        seed: str = "replay-safe-seed",
    ) -> ObservationV1:
        _require_utc_pair(observed_at, received_at)
        raw = f"{seed}|{sensor_id}|{observed_at}|{value}|{unit}".encode("utf-8")
        record = ObservationV1(
            observation_id=new_observation_id(),
            sensor_id=sensor_id,
            source_type="simulated",
            observed_at=observed_at,
            received_at=received_at,
            value=value,
            unit=unit,
            uncertainty=Uncertainty(kind="unknown", value=None),
            calibration=Calibration(
                calibration_id="fake-unspecified",
                calibrated_at=None,
                method="none",
            ),
            quality_flags=("simulated",),
            provenance=Provenance(
                device_id="fake-board",
                adapter=self.name,
                adapter_version=self.version,
                raw_hash=sha256_hex(raw),
            ),
            privacy_class="internal",
            simulation=True,
        )
        record.validate()
        if record.source_type == "physical" or record.simulation is False:
            raise ObservationContractError("fake-adapter-physical-masquerade")
        return record


class ReplayAdapter:
    """Load previously recorded observations from a local fixture. No I/O except the file."""

    name = "replay"
    version = ADAPTER_VERSION

    def load(self, path: str | Path) -> list[ObservationV1]:
        target = Path(path)
        try:
            raw = target.read_bytes()
        except OSError as exc:
            raise ObservationContractError(f"replay-unreadable:{type(exc).__name__}") from exc
        try:
            payload: Any = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ObservationContractError("replay-json-invalid") from exc
        if isinstance(payload, dict):
            items = payload.get("observations", payload)
            if isinstance(items, dict):
                items = [items]
        elif isinstance(payload, list):
            items = payload
        else:
            raise ObservationContractError("replay-payload-shape")
        if not isinstance(items, list) or not items:
            raise ObservationContractError("replay-empty")
        records: list[ObservationV1] = []
        for item in items:
            if not isinstance(item, dict):
                raise ObservationContractError("replay-item-not-object")
            record = observation_from_mapping(item)
            flags = tuple(dict.fromkeys((*record.quality_flags, QUALITY_REPLAYED)))
            replayed = ObservationV1(
                observation_id=record.observation_id,
                sensor_id=record.sensor_id,
                source_type=record.source_type,
                observed_at=record.observed_at,
                received_at=record.received_at,
                value=record.value,
                unit=record.unit,
                uncertainty=record.uncertainty,
                calibration=record.calibration,
                quality_flags=flags,
                provenance=Provenance(
                    device_id=record.provenance.device_id,
                    adapter=self.name,
                    adapter_version=self.version,
                    raw_hash=record.provenance.raw_hash,
                ),
                privacy_class=record.privacy_class,
                simulation=record.simulation,
                schema=record.schema,
                signature=record.signature,
                derived_from=record.derived_from,
                extra=dict(record.extra),
            )
            replayed.validate()
            records.append(replayed)
        return records
