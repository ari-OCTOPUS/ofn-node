"""Typed Observation + quality enum. No policy imports."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import math


class Quality(str, Enum):
    VALID = "VALID"
    STALE = "STALE"
    MISSING = "MISSING"
    CONFLICTING = "CONFLICTING"
    WARMUP = "WARMUP"
    UNLOCATED = "UNLOCATED"
    FUTURE_DATA = "FUTURE_DATA"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    RESTART_ARTIFACT_SUSPECTED = "RESTART_ARTIFACT_SUSPECTED"


def parse_dt(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        s = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return dt.astimezone(timezone.utc)


@dataclass
class Observation:
    observation_id: str
    source_id: str
    metric: str
    value: float | int | str | bool | None
    unit: str
    occurred_at: datetime
    recorded_at: datetime
    decision_time: datetime
    beat: int | None
    boot_id: str | None
    process_id: int | None
    provenance_path: str
    source_hash: str | None
    quality: str
    quality_reasons: list[str] = field(default_factory=list)
    latest_only: bool = False
    historical_claim: bool = False
    window_n: int | None = None
    window_ready: int | None = None
    node_id: str | None = None
    _validation_hash: str | None = field(default=None, init=False, repr=False, compare=False)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("_validation_hash", None)
        if isinstance(d["value"], float) and not math.isfinite(d["value"]):
            d["value"] = {"invalid_numeric_literal": repr(d["value"])}
        for k in ("occurred_at", "recorded_at", "decision_time"):
            v = d[k]
            if isinstance(v, datetime):
                d[k] = v.isoformat() if v.tzinfo is None else v.astimezone(timezone.utc).isoformat()
        return d
