"""Numeric series windows for OCT-SENSE-092. MAD is used instead of mean/std."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def mad(values: list[float], med: float | None = None) -> float:
    if not values:
        return 0.0
    centre = median(values) if med is None else med
    return median([abs(v - centre) for v in values])


def modified_zscore(value: float, values: list[float], *, abs_fallback: float = 0.5) -> tuple[float, float, float]:
    """Return (score, median, mad). Zero MAD uses an absolute fallback."""
    med = median(values)
    spread = mad(values, med)
    if spread <= 0:
        if abs(value - med) <= abs_fallback:
            return 0.0, med, 0.0
        score = abs(value - med) / abs_fallback
        return score, med, 0.0
    score = 0.6745 * (value - med) / spread
    return score, med, spread


@dataclass
class Sample:
    ts: float
    value: float
    event_id: str = ""


@dataclass
class SeriesWindow:
    key: str
    maxlen: int = 60
    samples: deque[Sample] = field(default_factory=deque)
    cusum_pos: float = 0.0
    cusum_neg: float = 0.0
    first_ts: float = 0.0

    def add(self, value: float, ts: float | None = None, event_id: str = "") -> None:
        now = ts or time.time()
        if not self.samples:
            self.first_ts = now
        self.samples.append(Sample(ts=now, value=float(value), event_id=event_id))
        while len(self.samples) > self.maxlen:
            self.samples.popleft()

    def values(self) -> list[float]:
        return [s.value for s in self.samples]

    def timestamps(self) -> list[float]:
        return [s.ts for s in self.samples]

    def expected_interval(self) -> float | None:
        ts = self.timestamps()
        if len(ts) < 3:
            return None
        deltas = [ts[i] - ts[i - 1] for i in range(1, len(ts)) if ts[i] > ts[i - 1]]
        if not deltas:
            return None
        return median(deltas)

    def snapshot(self) -> dict[str, Any]:
        vals = self.values()
        med = median(vals) if vals else None
        return {
            "key": self.key,
            "count": len(vals),
            "median": med,
            "mad": mad(vals, med) if vals else None,
            "first_ts": self.first_ts,
            "last_ts": self.samples[-1].ts if self.samples else None,
            "cusum_pos": self.cusum_pos,
            "cusum_neg": self.cusum_neg,
            "samples": [{"ts": s.ts, "value": s.value, "event_id": s.event_id} for s in self.samples],
        }

    @classmethod
    def from_snapshot(cls, blob: dict[str, Any], maxlen: int) -> "SeriesWindow":
        window = cls(key=str(blob.get("key") or ""), maxlen=maxlen)
        window.cusum_pos = float(blob.get("cusum_pos") or 0.0)
        window.cusum_neg = float(blob.get("cusum_neg") or 0.0)
        window.first_ts = float(blob.get("first_ts") or 0.0)
        for sample in blob.get("samples") or []:
            window.add(
                float(sample["value"]),
                ts=float(sample.get("ts") or time.time()),
                event_id=str(sample.get("event_id") or ""),
            )
        return window


def update_cusum(
    window: SeriesWindow,
    value: float,
    *,
    k_sigma: float = 0.5,
    h_sigma: float = 5.0,
) -> tuple[float, float, float]:
    """Two-sided CUSUM. Returns (pos, neg, sigma)."""
    vals = window.values()
    if len(vals) < 2:
        return window.cusum_pos, window.cusum_neg, 0.0
    prior = vals[:-1] or vals
    med = median(prior)
    spread = mad(prior, med)
    sigma = 1.4826 * spread if spread > 0 else 0.1
    k = k_sigma * sigma
    window.cusum_pos = max(0.0, window.cusum_pos + (value - med - k))
    window.cusum_neg = max(0.0, window.cusum_neg + (med - k - value))
    return window.cusum_pos, window.cusum_neg, sigma
