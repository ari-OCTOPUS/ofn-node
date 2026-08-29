"""OCT-SENSE-096 uncertainty agent. Shadow/advisory only. Does not equal confidence."""

from __future__ import annotations

import math
import time
import uuid
from collections import defaultdict, deque
from collections.abc import AsyncIterator
from typing import Any

from octopus_sensorium.meta.anomaly import numeric_value, series_key
from octopus_sensorium.meta.shadow import SHADOW_POLICY, assert_shadow_manifest
from octopus_sensorium.sensors.base import BaseSensor, DiscoveryResult, RawObservation, SelfTestResult


class UncertaintySensor(BaseSensor):
    sensor_type = "uncertainty"
    capabilities = {"aleatoric", "epistemic", "stale_penalty", "missing_evidence_penalty"}

    def __init__(self, manifest: dict[str, Any]) -> None:
        super().__init__(manifest)
        assert_shadow_manifest(manifest)
        self.inbox: deque[dict[str, Any]] = deque(maxlen=256)
        self.series: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=32))
        self.pending: list[dict[str, Any]] = []

    def ingest(self, kind: str, payload: dict[str, Any], subject: str = "") -> None:
        if kind != "observation":
            return
        if payload.get("sensor_id") in {"OCT-SENSE-096", "OCT-SENSE-097", "OCT-SENSE-099", "OCT-SENSE-100"}:
            return
        self.inbox.append(payload)

    def _event(self, obs: dict[str, Any], breakdown: dict[str, float], recommendation: str) -> dict[str, Any]:
        mixed = min(1.0, sum(breakdown.values()))
        return {
            "event_id": str(uuid.uuid4()),
            "sensor_id": "OCT-SENSE-096",
            "observation_type": "prediction",
            "observed_property": "meta.uncertainty",
            "target": {
                "sensor_id": obs.get("sensor_id"),
                "event_id": obs.get("event_id"),
                "observed_property": obs.get("observed_property"),
            },
            "uncertainty": {
                "aleatoric": breakdown["aleatoric"],
                "epistemic": breakdown["epistemic"],
                "stale_data_penalty": breakdown["stale"],
                "missing_evidence_penalty": breakdown["missing_evidence"],
                "source_conflict_penalty": breakdown["conflict"],
                "calibration_status": (obs.get("quality") or {}).get("calibration_status") or "unknown",
                "aggregated": round(mixed, 4),
                "not_confidence": True,
            },
            "recommendation": {"active_sensing": recommendation, "actionable": False},
            "policy": {**SHADOW_POLICY, "actionable": False},
        }

    def evaluate(self) -> list[dict[str, Any]]:
        self.pending = []
        now = time.time()
        while self.inbox:
            obs = self.inbox.popleft()
            key = series_key(obs)
            value = numeric_value(obs)
            if value is not None:
                self.series[key].append(value)
            vals = list(self.series[key])
            aleatoric = 0.0
            if len(vals) >= 2:
                mean = sum(vals) / len(vals)
                var = sum((v - mean) ** 2 for v in vals) / len(vals)
                aleatoric = min(1.0, math.sqrt(var) / (abs(mean) + 1.0))
            evidence = obs.get("evidence") or {}
            missing = 0.4 if not evidence.get("supporting_event_ids") else 0.0
            freshness = int((obs.get("quality") or {}).get("freshness_seconds") or 0)
            stale = min(1.0, freshness / 120.0)
            conf = float((obs.get("quality") or {}).get("confidence") or 1.0)
            epistemic = min(1.0, (1.0 - conf) * 0.5 + missing)
            conflict = 0.3 if (obs.get("observation_type") == "contradiction") else 0.0
            breakdown = {
                "aleatoric": round(aleatoric, 4),
                "epistemic": round(epistemic, 4),
                "stale": round(stale, 4),
                "missing_evidence": round(missing, 4),
                "conflict": round(conflict, 4),
            }
            rec = "none"
            if stale > 0.5:
                rec = "refresh_source"
            elif missing > 0:
                rec = "attach_supporting_evidence"
            self.pending.append(self._event(obs, breakdown, rec))
        _ = now
        return list(self.pending)

    async def discover(self) -> DiscoveryResult:
        return DiscoveryResult(present=True, details={"mode": "shadow", "advisory": True})

    async def self_test(self) -> SelfTestResult:
        pub = self.manifest.get("publication") or {}
        ok = pub.get("can_change_readiness") is not True
        return SelfTestResult(passed=ok, message="advisory uncertainty", measurements={"shadow": ok})

    async def observe(self) -> AsyncIterator[RawObservation]:
        events = self.evaluate()
        payload = {"sequence": self.next_sequence(), "events": events}
        yield RawObservation(payload=payload, source_id="meta-uncertainty", bytes_len=len(str(payload)))
