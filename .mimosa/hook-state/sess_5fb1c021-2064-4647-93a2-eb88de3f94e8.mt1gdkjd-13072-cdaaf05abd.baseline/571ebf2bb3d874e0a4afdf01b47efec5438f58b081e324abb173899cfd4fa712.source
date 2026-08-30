"""
field_value.py — Tri-state field wrapper (Principle P-A)
=========================================================
Every externally-sourced field carries an explicit status.

Status values:
  MEASURED    — value came from a live API call and passed range validation
  MISSING     — field not returned by the source / source unreachable
  UNRELIABLE  — returned but failed quality checks (spam flag, stale, anomalous range)
  ANOMALOUS   — returned but mathematically impossible (negative %, count<0, etc.)

Rule: Scoring and vetoes MUST read .status before reading .value.
      A veto may fire ONLY when status==MEASURED.
      Absence of a safety signal == HOLD/UNKNOWN, never PASS.  (Principle P-D)
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
import time


MEASURED    = "MEASURED"
MISSING     = "MISSING"
UNRELIABLE  = "UNRELIABLE"
ANOMALOUS   = "ANOMALOUS"

VALID_STATUSES = {MEASURED, MISSING, UNRELIABLE, ANOMALOUS}


@dataclass
class FieldValue:
    value:   Any
    status:  str        # one of VALID_STATUSES
    source:  str        # e.g. "GoPlus", "LunarCrush", "DexScreener", "Coinalyze"
    ts:      float = field(default_factory=time.time)

    def __post_init__(self):
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid status {self.status!r}")

    @property
    def is_measured(self) -> bool:
        return self.status == MEASURED

    @property
    def is_usable(self) -> bool:
        """True only when measured — the only state where the value is safe to act on."""
        return self.status == MEASURED

    def to_dict(self) -> dict:
        return {"value": self.value, "status": self.status,
                "source": self.source, "ts": round(self.ts, 1)}

    @staticmethod
    def measured(value, source: str) -> "FieldValue":
        return FieldValue(value=value, status=MEASURED, source=source)

    @staticmethod
    def missing(source: str) -> "FieldValue":
        return FieldValue(value=None, status=MISSING, source=source)

    @staticmethod
    def unreliable(value, source: str) -> "FieldValue":
        return FieldValue(value=value, status=UNRELIABLE, source=source)

    @staticmethod
    def anomalous(value, source: str) -> "FieldValue":
        return FieldValue(value=value, status=ANOMALOUS, source=source)


# ── Validation helpers ────────────────────────────────────────────────────────

def validate_pct(raw, source: str) -> FieldValue:
    """0–100 range for percentage fields. Negative or >100 → ANOMALOUS."""
    if raw is None:
        return FieldValue.missing(source)
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return FieldValue.missing(source)
    if v < 0 or v > 100:
        return FieldValue.anomalous(raw, source)
    return FieldValue.measured(round(v, 4), source)


def validate_count(raw, source: str, min_val: int = 0) -> FieldValue:
    """Non-negative integer count."""
    if raw is None:
        return FieldValue.missing(source)
    try:
        v = int(raw)
    except (TypeError, ValueError):
        return FieldValue.missing(source)
    if v < min_val:
        return FieldValue.anomalous(raw, source)
    return FieldValue.measured(v, source)


def validate_score(raw, source: str, lo: float = 0.0, hi: float = 100.0) -> FieldValue:
    """Generic 0–hi score range."""
    if raw is None:
        return FieldValue.missing(source)
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return FieldValue.missing(source)
    if v < lo or v > hi:
        return FieldValue.anomalous(raw, source)
    return FieldValue.measured(round(v, 4), source)
