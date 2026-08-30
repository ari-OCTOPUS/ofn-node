"""Replay-safe observation.v1 record contract.

Portable extract of the immutable observation.v1 record contract.
The vault USGS/HN parser and ``_ops`` observatory runtime are not on this lineage.

No network, no hardware, no action authority, no self-approval.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping


SCHEMA = "observation.v1"
SOURCE_TYPES = frozenset({"physical", "api", "file", "human", "simulated"})
UNCERTAINTY_KINDS = frozenset({"stddev", "interval", "categorical", "unknown"})
PRIVACY_CLASSES = frozenset({"public", "internal", "sensitive", "secret"})
_RFC3339_UTC = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+]00:00)$"
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_AUTHORITY_KEYS = frozenset({
    "authority",
    "may_execute",
    "may_trigger_tool",
    "may_gate",
    "approved",
    "self_approved",
    "approval",
    "owner_signature",
    "execute",
    "actuator",
})
QUALITY_REPLAYED = "replayed"
QUALITY_NORMALIZED = "normalized"
QUALITY_STALE = "stale"
QUALITY_FUTURE = "future_data"


class ObservationContractError(ValueError):
    """Fail-closed validation error for observation.v1."""


def parse_utc(value: str, *, field_name: str) -> datetime:
    raw = str(value or "").strip()
    if not raw or not _RFC3339_UTC.match(raw):
        raise ObservationContractError(f"{field_name}-not-rfc3339-utc")
    normalized = raw.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ObservationContractError(f"{field_name}-timezone-missing")
    if parsed.utcoffset() != timedelta(0):
        raise ObservationContractError(f"{field_name}-not-utc")
    return parsed.astimezone(timezone.utc)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def new_observation_id() -> str:
    return str(uuid.uuid4())


@dataclass(frozen=True)
class Uncertainty:
    kind: str
    value: float | dict[str, Any] | None = None

    def validate(self) -> None:
        if self.kind not in UNCERTAINTY_KINDS:
            raise ObservationContractError(f"uncertainty-kind-invalid:{self.kind}")
        if self.kind == "unknown":
            if self.value is not None:
                raise ObservationContractError("unknown-uncertainty-cannot-become-numeric")
            return
        if self.kind == "stddev":
            if not isinstance(self.value, (int, float)) or isinstance(self.value, bool):
                raise ObservationContractError("stddev-value-not-number")
            if float(self.value) < 0:
                raise ObservationContractError("stddev-value-negative")
            return
        if self.kind == "interval":
            if not isinstance(self.value, dict):
                raise ObservationContractError("interval-value-not-object")
            lo = self.value.get("low")
            hi = self.value.get("high")
            if not isinstance(lo, (int, float)) or not isinstance(hi, (int, float)):
                raise ObservationContractError("interval-bounds-not-number")
            if float(lo) > float(hi):
                raise ObservationContractError("interval-bounds-inverted")
            return
        if self.kind == "categorical" and self.value is None:
            raise ObservationContractError("categorical-value-missing")


@dataclass(frozen=True)
class Calibration:
    calibration_id: str | None
    calibrated_at: str | None
    method: str | None

    def validate(self) -> None:
        if self.calibrated_at is not None:
            parse_utc(self.calibrated_at, field_name="calibrated_at")
        if self.calibration_id is not None and not str(self.calibration_id).strip():
            raise ObservationContractError("calibration-id-blank")
        if self.method is not None and not str(self.method).strip():
            raise ObservationContractError("calibration-method-blank")


@dataclass(frozen=True)
class Provenance:
    device_id: str | None
    adapter: str
    adapter_version: str
    raw_hash: str

    def validate(self) -> None:
        if not str(self.adapter or "").strip():
            raise ObservationContractError("provenance-adapter-missing")
        if not str(self.adapter_version or "").strip():
            raise ObservationContractError("provenance-adapter-version-missing")
        digest = str(self.raw_hash or "").strip().lower()
        if not _SHA256_HEX.match(digest):
            raise ObservationContractError("provenance-raw-hash-invalid")
        if self.device_id is not None and not str(self.device_id).strip():
            raise ObservationContractError("provenance-device-id-blank")


@dataclass(frozen=True)
class ObservationV1:
    observation_id: str
    sensor_id: str
    source_type: str
    observed_at: str
    received_at: str
    value: Any
    unit: str | None
    uncertainty: Uncertainty
    calibration: Calibration
    quality_flags: tuple[str, ...]
    provenance: Provenance
    privacy_class: str
    simulation: bool
    schema: str = SCHEMA
    signature: str | None = None
    derived_from: str | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.schema != SCHEMA:
            raise ObservationContractError(f"schema-mismatch:{self.schema}")
        if not str(self.observation_id or "").strip():
            raise ObservationContractError("observation-id-missing")
        if not str(self.sensor_id or "").strip():
            raise ObservationContractError("sensor-id-missing")
        if self.source_type not in SOURCE_TYPES:
            raise ObservationContractError(f"source-type-invalid:{self.source_type}")
        if self.privacy_class not in PRIVACY_CLASSES:
            raise ObservationContractError(f"privacy-class-invalid:{self.privacy_class}")
        if not isinstance(self.simulation, bool):
            raise ObservationContractError("simulation-not-bool")
        if self.source_type == "simulated" and self.simulation is not True:
            raise ObservationContractError("simulated-unlabeled")
        if self.source_type == "physical" and self.simulation is not False:
            raise ObservationContractError("physical-labeled-simulated")
        if self.source_type == "physical" and self.provenance.adapter == "fake":
            raise ObservationContractError("fake-adapter-cannot-claim-physical")
        observed = parse_utc(self.observed_at, field_name="observed_at")
        received = parse_utc(self.received_at, field_name="received_at")
        if received < observed:
            raise ObservationContractError("received-before-observed")
        self.uncertainty.validate()
        self.calibration.validate()
        self.provenance.validate()
        if self.signature is not None and not str(self.signature).strip():
            raise ObservationContractError("signature-blank")
        if self.derived_from is not None and not str(self.derived_from).strip():
            raise ObservationContractError("derived-from-blank")
        extras = dict(self.extra)
        forbidden = _FORBIDDEN_AUTHORITY_KEYS.intersection(extras)
        if forbidden:
            raise ObservationContractError(
                f"authority-keys-forbidden:{sorted(forbidden)}"
            )
        if extras.get("grants_action_authority") is True:
            raise ObservationContractError("observation-cannot-grant-action-authority")
        if extras.get("self_approved") is True or extras.get("approved") is True:
            raise ObservationContractError("observation-cannot-self-approve")

    def grants_action_authority(self) -> bool:
        return False

    def can_self_approve(self) -> bool:
        return False

    def is_stale(self, *, now_utc: str, max_age_seconds: int) -> bool:
        if max_age_seconds < 0:
            raise ObservationContractError("max-age-negative")
        observed = parse_utc(self.observed_at, field_name="observed_at")
        now = parse_utc(now_utc, field_name="now_utc")
        return (now - observed) > timedelta(seconds=max_age_seconds)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "observation_id": self.observation_id,
            "sensor_id": self.sensor_id,
            "source_type": self.source_type,
            "observed_at": self.observed_at,
            "received_at": self.received_at,
            "value": self.value,
            "unit": self.unit,
            "uncertainty": {"kind": self.uncertainty.kind, "value": self.uncertainty.value},
            "calibration": {
                "calibration_id": self.calibration.calibration_id,
                "calibrated_at": self.calibration.calibrated_at,
                "method": self.calibration.method,
            },
            "quality_flags": list(self.quality_flags),
            "provenance": {
                "device_id": self.provenance.device_id,
                "adapter": self.provenance.adapter,
                "adapter_version": self.provenance.adapter_version,
                "raw_hash": self.provenance.raw_hash,
            },
            "privacy_class": self.privacy_class,
            "simulation": self.simulation,
            "signature": self.signature,
            "derived_from": self.derived_from,
        }

    def normalize(self, *, now_utc: str, method: str) -> "ObservationV1":
        self.validate()
        parse_utc(now_utc, field_name="now_utc")
        if not str(method or "").strip():
            raise ObservationContractError("normalize-method-blank")
        flags = tuple(dict.fromkeys((*self.quality_flags, QUALITY_NORMALIZED)))
        derived = replace(
            self,
            observation_id=new_observation_id(),
            received_at=now_utc,
            quality_flags=flags,
            derived_from=self.observation_id,
            extra=dict(self.extra),
        )
        derived.validate()
        if derived.observation_id == self.observation_id:
            raise ObservationContractError("derived-id-collision")
        return derived


def observation_from_mapping(data: Mapping[str, Any]) -> ObservationV1:
    if not isinstance(data, Mapping):
        raise ObservationContractError("record-not-object")
    forbidden = _FORBIDDEN_AUTHORITY_KEYS.intersection(data)
    if forbidden:
        raise ObservationContractError(f"authority-keys-forbidden:{sorted(forbidden)}")
    try:
        uncertainty_raw = data["uncertainty"]
        calibration_raw = data["calibration"]
        provenance_raw = data["provenance"]
        record = ObservationV1(
            schema=str(data.get("schema", SCHEMA)),
            observation_id=str(data["observation_id"]),
            sensor_id=str(data["sensor_id"]),
            source_type=str(data["source_type"]),
            observed_at=str(data["observed_at"]),
            received_at=str(data["received_at"]),
            value=data.get("value"),
            unit=None if data.get("unit") is None else str(data.get("unit")),
            uncertainty=Uncertainty(
                kind=str(uncertainty_raw["kind"]),
                value=uncertainty_raw.get("value"),
            ),
            calibration=Calibration(
                calibration_id=calibration_raw.get("calibration_id"),
                calibrated_at=calibration_raw.get("calibrated_at"),
                method=calibration_raw.get("method"),
            ),
            quality_flags=tuple(str(flag) for flag in data.get("quality_flags", [])),
            provenance=Provenance(
                device_id=provenance_raw.get("device_id"),
                adapter=str(provenance_raw.get("adapter", "")),
                adapter_version=str(provenance_raw.get("adapter_version", "")),
                raw_hash=str(provenance_raw.get("raw_hash", "")),
            ),
            privacy_class=str(data["privacy_class"]),
            simulation=bool(data["simulation"]),
            signature=data.get("signature"),
            derived_from=data.get("derived_from"),
            extra={
                key: value
                for key, value in data.items()
                if key
                not in {
                    "schema",
                    "observation_id",
                    "sensor_id",
                    "source_type",
                    "observed_at",
                    "received_at",
                    "value",
                    "unit",
                    "uncertainty",
                    "calibration",
                    "quality_flags",
                    "provenance",
                    "privacy_class",
                    "simulation",
                    "signature",
                    "derived_from",
                }
            },
        )
    except ObservationContractError:
        raise
    except (KeyError, TypeError, AttributeError) as exc:
        raise ObservationContractError(f"malformed-record:{type(exc).__name__}") from exc
    record.validate()
    return record


def dumps_canonical(record: ObservationV1) -> bytes:
    return json.dumps(record.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
