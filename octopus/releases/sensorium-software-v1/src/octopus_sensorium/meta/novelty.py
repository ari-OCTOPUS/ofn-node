"""OCT-SENSE-097 novelty agent. Shadow/advisory. Novelty is not anomaly."""

from __future__ import annotations

import uuid
from collections import deque
from collections.abc import AsyncIterator
from typing import Any

from octopus_sensorium.meta.shadow import SHADOW_POLICY, assert_shadow_manifest
from octopus_sensorium.sensors.base import BaseSensor, DiscoveryResult, RawObservation, SelfTestResult


class NoveltySensor(BaseSensor):
    sensor_type = "novelty"
    capabilities = {"unseen_hash", "unseen_entity", "unseen_source", "unseen_relation"}

    def __init__(self, manifest: dict[str, Any]) -> None:
        super().__init__(manifest)
        assert_shadow_manifest(manifest)
        self.inbox: deque[dict[str, Any]] = deque(maxlen=256)
        self.seen_hashes: set[str] = set()
        self.seen_entities: set[str] = set()
        self.seen_sources: set[str] = set()
        self.seen_relations: set[str] = set()
        self.seen_transitions: set[str] = set()
        self.seen_categories: set[str] = set()
        self.last_state: dict[str, str] = {}

    def ingest(self, kind: str, payload: dict[str, Any], subject: str = "") -> None:
        if kind != "observation":
            return
        if payload.get("sensor_id") == "OCT-SENSE-097":
            return
        self.inbox.append(payload)

    def evaluate(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        while self.inbox:
            obs = self.inbox.popleft()
            kinds: list[str] = []
            digest = str((obs.get("provenance") or {}).get("content_hash") or "")
            entity = str(((obs.get("subject") or {}).get("entity_id")) or "")
            source = str((obs.get("provenance") or {}).get("source_id") or "")
            relation = f"{obs.get('sensor_id')}:{obs.get('observed_property')}"
            category = str(obs.get("observation_type") or "measurement")
            raw = (obs.get("result") or {}).get("value")
            state = str(raw.get("sub_state")) if isinstance(raw, dict) and raw.get("sub_state") else ""
            if digest and digest not in self.seen_hashes:
                kinds.append("unseen_event_hash")
                self.seen_hashes.add(digest)
            if entity and entity not in self.seen_entities:
                kinds.append("unseen_entity")
                self.seen_entities.add(entity)
            if source and source not in self.seen_sources:
                kinds.append("unseen_source")
                self.seen_sources.add(source)
            if relation not in self.seen_relations:
                kinds.append("unseen_relation")
                self.seen_relations.add(relation)
            if category not in self.seen_categories:
                kinds.append("unseen_schema_compatible_category")
                self.seen_categories.add(category)
            if state:
                prev = self.last_state.get(relation)
                trans = f"{prev}->{state}"
                if prev and trans not in self.seen_transitions:
                    kinds.append("unseen_valid_state_transition")
                    self.seen_transitions.add(trans)
                self.last_state[relation] = state
            if not kinds:
                continue
            out.append(
                {
                    "event_id": str(uuid.uuid4()),
                    "sensor_id": "OCT-SENSE-097",
                    "observation_type": "event",
                    "observed_property": "meta.novelty",
                    "novelty": {
                        "kinds": kinds,
                        "not_anomaly": True,
                        "target_event_id": obs.get("event_id"),
                    },
                    "policy": {**SHADOW_POLICY, "actionable": False},
                }
            )
        return out

    async def discover(self) -> DiscoveryResult:
        return DiscoveryResult(present=True, details={"mode": "shadow", "novelty_ne_anomaly": True})

    async def self_test(self) -> SelfTestResult:
        return SelfTestResult(passed=True, message="novelty≠anomaly", measurements={"shadow": True})

    async def observe(self) -> AsyncIterator[RawObservation]:
        events = self.evaluate()
        payload = {"sequence": self.next_sequence(), "events": events}
        yield RawObservation(payload=payload, source_id="meta-novelty", bytes_len=len(str(payload)))
