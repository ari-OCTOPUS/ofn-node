"""Agent cockpit self-model section.

A cockpit section with exactly one data path: the producer. It never reads
a hand-maintained file, and when the producer fails it degrades loudly
("unavailable") instead of painting a green screen over a hole. A value
the system could not measure shows up as unknown/absent/stale — never as
a fallback number and never as healthy.

This composes with the existing cockpit read model (same envelope
vocabulary: schema/generated_at/status/data/sources/warnings/stale_after)
without editing it.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Mapping

from ofn.adapters import self_model_producer as producer_module

SECTION_NAME = "self_model"

_GREEN_STATUSES = frozenset({"ok"})


def _clock_value(clock: Callable[[], float]) -> float:
    try:
        value = float(clock())
    except (TypeError, ValueError):
        return time.time()
    return value


def _is_envelope(value: Any) -> bool:
    return (
        isinstance(value, Mapping)
        and isinstance(value.get("schema"), str)
        and isinstance(value.get("status"), str)
        and isinstance(value.get("data"), Mapping)
    )


class SelfModelSection:
    """Callable cockpit section backed by the self-model producer.

    ``producer`` must be a zero-argument callable returning the producer
    envelope (typically ``functools.partial(produce, repo_root=...)``).
    Every read goes through it — there is no cached, hand-written, or
    file-read path.
    """

    def __init__(
        self,
        producer: Callable[[], Mapping[str, Any]],
        clock: Callable[[], float] | None = None,
    ) -> None:
        if not callable(producer):
            raise TypeError("producer must be callable")
        self._producer = producer
        self._clock = clock or time.time

    def read(self) -> dict[str, Any]:
        now_epoch = _clock_value(self._clock)
        try:
            envelope = self._producer()
        except Exception:
            # Fail closed: a broken producer is an unavailable section,
            # never a healthy one.
            return self._unavailable(now_epoch, "producer_failed")
        if not _is_envelope(envelope):
            return self._unavailable(now_epoch, "producer_malformed")
        result = dict(envelope)
        result["section"] = SECTION_NAME
        result["read_at"] = producer_module.rfc3339(now_epoch)
        # The section never upgrades the model's own status; it can only
        # carry it honestly.
        return result

    def __call__(self) -> dict[str, Any]:
        return self.read()

    def _unavailable(self, now_epoch: float, warning: str) -> dict[str, Any]:
        return {
            "schema": producer_module.SCHEMA_ID,
            "section": SECTION_NAME,
            "generated_at": producer_module.rfc3339(now_epoch),
            "status": "unavailable",
            "data": None,
            "sources": [],
            "warnings": [warning],
            "stale_after": producer_module.rfc3339(now_epoch),
        }

    @staticmethod
    def summary_rows(envelope: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Flat rows for a screen. Statuses are passed through verbatim —
        unknown stays unknown; no row is invented and none is upgraded."""
        data = envelope.get("data")
        if not isinstance(data, Mapping):
            return [{
                "sensor_id": SECTION_NAME,
                "status": "unknown",
                "source": None,
                "detail": "section unavailable",
            }]
        rows: list[dict[str, Any]] = []
        for group in ("sensors", "processes", "capabilities"):
            for reading in data.get(group, []):
                rows.append({
                    "sensor_id": reading.get("sensor_id"),
                    "status": reading.get("status"),
                    "value": reading.get("value"),
                    "source": reading.get("source"),
                })
        probe = data.get("brain_probe")
        if isinstance(probe, Mapping):
            rows.append({
                "sensor_id": "brain_probe",
                "status": probe.get("status"),
                "value": probe.get("verdict"),
                "source": probe.get("source"),
            })
        return rows

    @staticmethod
    def is_green(envelope: Mapping[str, Any]) -> bool:
        """Green means the model itself said ok. Unverifiable, degraded,
        unavailable — and anything malformed — are not green."""
        return (
            isinstance(envelope, Mapping)
            and envelope.get("status") in _GREEN_STATUSES
        )
