"""Lightweight connector and inbox metrics, stdlib only.

Tracks counts and timings for inbound webhook processing. Uses simple
in-memory counters — no SQLite, no Prometheus. Read by the owner's
metrics endpoint alongside the existing sysmetrics.

Counters reset on restart. That is the correct behaviour: the owner's panel
shows "since boot" numbers, and a boot already clears transient state.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Mapping


@dataclass
class _Counter:
    value: int = 0


@dataclass
class _Timer:
    total_ms: int = 0
    count: int = 0

    def record(self, ms: int) -> None:
        self.total_ms += ms
        self.count += 1

    @property
    def avg_ms(self) -> float:
        return self.total_ms / self.count if self.count else 0.0


class ConnectorMetrics:
    """In-memory metrics registry for connector/inbox activity."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._inbound: dict[str, _Counter] = {}
        self._processed: dict[str, _Counter] = {}
        self._failed: dict[str, _Counter] = {}
        self._rejected: dict[str, _Counter] = {}  # rate limited / bad sig
        self._timers: dict[str, _Timer] = {}

    def record_inbound(self, connector_id: str) -> None:
        with self._lock:
            self._get(self._inbound, connector_id).value += 1

    def record_processed(self, connector_id: str) -> None:
        with self._lock:
            self._get(self._processed, connector_id).value += 1

    def record_failed(self, connector_id: str) -> None:
        with self._lock:
            self._get(self._failed, connector_id).value += 1

    def record_rejected(self, connector_id: str) -> None:
        with self._lock:
            self._get(self._rejected, connector_id).value += 1

    def record_timing(self, connector_id: str, elapsed_ms: int) -> None:
        with self._lock:
            t = self._timers.setdefault(connector_id, _Timer())
            t.record(elapsed_ms)

    def snapshot(self) -> Mapping[str, Mapping[str, object]]:
        """Return a snapshot of all metrics, keyed by connector_id."""
        with self._lock:
            all_ids = set(self._inbound) | set(self._processed) | set(
                self._failed) | set(self._rejected) | set(self._timers)
            out: dict[str, dict[str, object]] = {}
            for cid in all_ids:
                ib = self._inbound.get(cid, _Counter())
                pr = self._processed.get(cid, _Counter())
                fl = self._failed.get(cid, _Counter())
                rj = self._rejected.get(cid, _Counter())
                tm = self._timers.get(cid, _Timer())
                out[cid] = {
                    "inbound": ib.value,
                    "processed": pr.value,
                    "failed": fl.value,
                    "rejected": rj.value,
                    "avg_processing_ms": round(tm.avg_ms, 1),
                    "processing_count": tm.count,
                }
            return out

    def reset(self) -> None:
        """Clear all metrics. For tests."""
        with self._lock:
            self._inbound.clear()
            self._processed.clear()
            self._failed.clear()
            self._rejected.clear()
            self._timers.clear()

    # -- private --

    @staticmethod
    def _get(mapping: dict, key: str) -> _Counter:
        return mapping.setdefault(key, _Counter())
