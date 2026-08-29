"""OCT-SENSE-100 provenance/trust quality agent. Does not decide world truth."""

from __future__ import annotations

import uuid
from collections import deque
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from octopus_sensorium.meta.shadow import SHADOW_POLICY, assert_shadow_manifest
from octopus_sensorium.sensors.base import BaseSensor, DiscoveryResult, RawObservation, SelfTestResult


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class ProvenanceTrustSensor(BaseSensor):
    sensor_type = "provenance"
    capabilities = {"evidence_quality", "duplicate_status", "revocation_status"}

    def __init__(self, manifest: dict[str, Any]) -> None:
        super().__init__(manifest)
        assert_shadow_manifest(manifest)
        self.inbox: deque[dict[str, Any]] = deque(maxlen=256)
        self.seen_hashes: set[str] = set()
        self.revoked: set[str] = set()

    def ingest(self, kind: str, payload: dict[str, Any], subject: str = "") -> None:
        if kind == "health":
            self.revoked = set(payload.get("revoked_fingerprints") or [])
            return
        if kind != "observation":
            return
        if payload.get("sensor_id") == "OCT-SENSE-100":
            return
        self.inbox.append(payload)

    def _grade(self, obs: dict[str, Any]) -> str:
        prov = obs.get("provenance") or {}
        quality = obs.get("quality") or {}
        evidence = obs.get("evidence") or {}
        digest = str(prov.get("content_hash") or "")
        duplicate = bool(digest and digest in self.seen_hashes)
        if digest:
            self.seen_hashes.add(digest)
        if not digest or not str(digest).startswith("sha256:"):
            return "INVALID"
        if prov.get("signature_verified") is True and not prov.get("verified_by"):
            return "CONTRADICTED"
        if quality.get("valid") is False:
            return "INVALID"
        phen = _parse_time((obs.get("time") or {}).get("phenomenon_time"))
        ttl = _parse_time((obs.get("time") or {}).get("valid_until"))
        if ttl and datetime.now(timezone.utc) > ttl:
            return "STALE"
        freshness = int((quality.get("freshness_seconds") or 0))
        if freshness > 120:
            return "STALE"
        if prov.get("clock_trust") not in {"SYNCED_NTP", "SYNCED_PTP"}:
            return "UNVERIFIED"
        if prov.get("signature_verified") is True and prov.get("verified_by"):
            return "VERIFIED"
        if evidence.get("supporting_event_ids") or prov.get("transformations"):
            return "PARTIALLY_VERIFIED"
        if duplicate:
            return "PARTIALLY_VERIFIED"
        return "UNVERIFIED"

    def evaluate(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        while self.inbox:
            obs = self.inbox.popleft()
            grade = self._grade(obs)
            out.append(
                {
                    "event_id": str(uuid.uuid4()),
                    "sensor_id": "OCT-SENSE-100",
                    "observation_type": "state",
                    "observed_property": "meta.provenance",
                    "provenance_trust": {
                        "target_event_id": obs.get("event_id"),
                        "source_id": (obs.get("provenance") or {}).get("source_id"),
                        "collector_version": (obs.get("provenance") or {}).get("collector_version"),
                        "schema_version": obs.get("schema_version"),
                        "content_hash": (obs.get("provenance") or {}).get("content_hash"),
                        "transformations": (obs.get("provenance") or {}).get("transformations") or [],
                        "clock_trust": (obs.get("provenance") or {}).get("clock_trust"),
                        "signature_state": (obs.get("provenance") or {}).get("signature_verified"),
                        "grade": grade,
                        "does_not_assert_world_truth": True,
                    },
                    "policy": {**SHADOW_POLICY, "actionable": False},
                }
            )
        return out

    async def discover(self) -> DiscoveryResult:
        return DiscoveryResult(present=True, details={"mode": "shadow"})

    async def self_test(self) -> SelfTestResult:
        return SelfTestResult(passed=True, message="provenance grades evidence only", measurements={"mutates_source": False})

    async def observe(self) -> AsyncIterator[RawObservation]:
        events = self.evaluate()
        payload = {"sequence": self.next_sequence(), "events": events}
        yield RawObservation(payload=payload, source_id="meta-provenance", bytes_len=len(str(payload)))
