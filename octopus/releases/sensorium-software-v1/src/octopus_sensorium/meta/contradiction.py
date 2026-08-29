"""OCT-SENSE-095 contradiction meta-sensor. Rule-based, shadow only.

Reads OCT-SENSE-092 anomalies as auxiliary evidence. Does not feed 092.
Does not resolve belief or mark sources unreliable.
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from octopus_sensorium.isolation import IsolationViolation, assert_no_pwm_write
from octopus_sensorium.meta.shadow import SHADOW_POLICY, assert_shadow_manifest
from octopus_sensorium.schema_ids import SensorIdCollision, assert_no_sensor_id_collision
from octopus_sensorium.sensors.base import BaseSensor, DiscoveryResult, RawObservation, SelfTestResult
from octopus_sensorium.snapshot import load_latest, replay_matches_current


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ContradictionSensor(BaseSensor):
    sensor_type = "contradiction"
    capabilities = {
        "state_observation_conflict",
        "freshness_conflict",
        "value_conflict",
        "identity_conflict",
        "policy_state_conflict",
    }

    def __init__(self, manifest: dict[str, Any]) -> None:
        super().__init__(manifest)
        assert_shadow_manifest(manifest)
        matching = manifest.get("matching") or {}
        self.tolerance = float(matching.get("temporal_tolerance_seconds") or 30)
        self.obs_by_sensor: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=128))
        self.last_obs_ts: dict[str, float] = {}
        self.unit_health: dict[str, dict[str, Any]] = {}
        self.anomalies: deque[dict[str, Any]] = deque(maxlen=64)
        self.board_status: dict[str, Any] = {}
        self.boot_report: dict[str, Any] = {}
        self.open: dict[str, dict[str, Any]] = {}
        self.pending: list[dict[str, Any]] = []
        self.auth_obs_times: deque[float] = deque(maxlen=512)
        self.started_at = time.time()
        self._last_emit: dict[str, float] = {}

    def ingest(self, kind: str, payload: dict[str, Any], subject: str = "") -> None:
        if kind == "contradiction":
            return
        if kind == "anomaly":
            if payload.get("observation_type") not in {None, "anomaly"}:
                return
            self.anomalies.append(payload)
            return
        if kind == "health":
            self.board_status = payload
            return
        if kind == "boot_report":
            self.boot_report = payload
            return
        if kind != "observation":
            return
        sid = str(payload.get("sensor_id") or "")
        self.obs_by_sensor[sid].append(payload)
        self.last_obs_ts[sid] = time.time()
        self.auth_obs_times.append(time.time())
        value = (payload.get("result") or {}).get("value")
        if sid == "OCT-SENSE-052" and isinstance(value, dict) and "healthy" in value:
            unit = str(value.get("unit") or "")
            self.unit_health[unit] = {"healthy": bool(value.get("healthy")), "ts": time.time(), "event_id": payload.get("event_id")}

    def _aux_anomalies(self, subject_hint: str) -> list[dict[str, Any]]:
        out = []
        for event in self.anomalies:
            target = (event.get("target") or {}).get("sensor_id") or ""
            if subject_hint and subject_hint not in str(target) and subject_hint not in str(event):
                continue
            out.append(
                {
                    "event_id": event.get("event_id"),
                    "claim": "anomaly candidate from OCT-SENSE-092",
                    "source": "OCT-SENSE-092",
                    "reliability": 0.6,
                }
            )
        return out[:3]

    def _upsert(self, rule_id: str, classification: str, severity: str, proposition: dict[str, Any], supporting: list, opposing: list, query: str) -> None:
        existing = self.open.get(rule_id)
        if existing:
            existing["contradiction"]["last_seen"] = _iso()
            existing["contradiction"]["occurrence_count"] += 1
            existing["contradiction"]["state"] = "OPEN"
            existing["supporting_evidence"] = supporting
            existing["opposing_evidence"] = opposing
            self.pending.append(existing)
            return
        event = {
            "event_id": str(uuid.uuid4()),
            "sensor_id": "OCT-SENSE-095",
            "observation_type": "contradiction",
            "contradiction": {
                "contradiction_id": "con-" + str(uuid.uuid4()),
                "rule_id": rule_id,
                "classification": classification,
                "severity": severity,
                "state": "OPEN",
                "first_seen": _iso(),
                "last_seen": _iso(),
                "occurrence_count": 1,
            },
            "proposition": proposition,
            "supporting_evidence": supporting,
            "opposing_evidence": opposing,
            "resolution": {
                "status": "UNRESOLVED",
                "preferred_explanation": None,
                "recommended_query": query,
                "recommended_action": None,
            },
            "policy": {**SHADOW_POLICY, "human_review_required": False, "actionable": False},
        }
        self.open[rule_id] = event
        self.pending.append(event)

    def _resolve_if_open(self, rule_id: str) -> None:
        existing = self.open.get(rule_id)
        if not existing:
            return
        existing["contradiction"]["state"] = "RESOLVED"
        existing["contradiction"]["last_seen"] = _iso()
        existing["resolution"]["status"] = "RESOLVED"
        existing["resolution"]["preferred_explanation"] = "condition cleared"
        self.pending.append(existing)
        del self.open[rule_id]

    def _r001_r002(self) -> None:
        now = time.time()
        thermal_ts = self.last_obs_ts.get("OCT-SENSE-053.THERMAL", 0)
        unit = self.unit_health.get("octopus-sensorium.service") or {}
        stale = thermal_ts == 0 or now - thermal_ts > 45
        if unit.get("healthy") and stale and now - self.started_at > 45:
            self._upsert(
                "CON-R001",
                "liveness_data_conflict",
                "high",
                {"subject_id": "OCT-SENSE-053.THERMAL", "statement": "plugin is operational and producing observations"},
                [{"event_id": unit.get("event_id"), "claim": "unit is active/running", "source": "OCT-SENSE-052", "reliability": 0.97}]
                + self._aux_anomalies("OCT-SENSE-053.THERMAL"),
                [{"event_id": "missing-window", "claim": "no observation arrived before TTL expiry", "source": "observation_index", "reliability": 0.99}],
                "request health probe from thermal plugin",
            )
        else:
            self._resolve_if_open("CON-R001")
        if unit.get("healthy") is False:
            continuing = any(now - ts < 15 for sid, ts in self.last_obs_ts.items() if sid.startswith("OCT-SENSE-05"))
            if continuing:
                self._upsert(
                    "CON-R002",
                    "process_identity_or_buffer_conflict",
                    "high",
                    {"subject_id": "octopus-sensorium.service", "statement": "inactive unit must not keep producing observations"},
                    [{"claim": "unit healthy=false", "source": "OCT-SENSE-052", "reliability": 0.97}],
                    [{"claim": "observations continue", "source": "observation_index", "reliability": 0.9}],
                    "inspect offline buffer and process identity",
                )
            else:
                self._resolve_if_open("CON-R002")
        else:
            self._resolve_if_open("CON-R002")

    def _r003(self) -> None:
        bus = self.board_status.get("bus_state")
        now = time.time()
        recent = [t for t in self.auth_obs_times if now - t <= 60]
        if bus == "CONNECTED" and now - self.started_at > 60 and not recent:
            self._upsert(
                "CON-R003",
                "bus_semantic_conflict",
                "high",
                {"subject_id": "nats", "statement": "connected bus publishes authenticated observations"},
                [{"claim": "bus_state=CONNECTED", "source": "sensorium.health", "reliability": 0.95}],
                [{"claim": "authenticated_observation_rate=0", "source": "observation_index", "reliability": 0.95}],
                "verify NATS auth and publish path",
            )
        else:
            self._resolve_if_open("CON-R003")

    def _r004_r006(self) -> None:
        report = self.boot_report or {}
        status = self.board_status or {}
        readiness = report.get("readiness_state") or status.get("readiness_state")
        failed = report.get("gates_failed") or []
        if readiness == "READY" and failed:
            self._upsert(
                "CON-R004",
                "readiness_contract_violation",
                "critical",
                {"subject_id": "readiness", "statement": "READY implies gates_failed=[]"},
                [{"claim": f"readiness_state={readiness}", "source": "boot_report", "reliability": 1.0}],
                [{"claim": f"gates_failed={failed}", "source": "boot_report", "reliability": 1.0}],
                "re-run verifier; do not treat READY as ARMED",
            )
        else:
            self._resolve_if_open("CON-R004")
        profile = status.get("readiness_profile") or report.get("readiness_profile") or "WAVE0_OBSERVE_ONLY"
        authority = status.get("actuator_authority") or "NONE"
        estop = ((status.get("safety") or {}) if isinstance(status.get("safety"), dict) else {}).get("estop_channel")
        soft_ok = authority == "PERMITTED_SOFTWARE_A0" and estop == "SOFTWARE_LATCH"
        if profile == "WAVE0_OBSERVE_ONLY" and authority != "NONE" and not soft_ok:
            self._upsert(
                "CON-R005",
                "safety_contract_violation",
                "critical",
                {"subject_id": "safety", "statement": "WAVE0_OBSERVE_ONLY allows NONE or soft PERMITTED_SOFTWARE_A0+SOFTWARE_LATCH"},
                [{"claim": f"profile={profile}", "source": "status", "reliability": 1.0}],
                [{"claim": f"actuator_authority={authority}", "source": "status", "reliability": 1.0}],
                "revert actuator authority to NONE or restore SOFTWARE_LATCH soft unlock",
            )
        else:
            self._resolve_if_open("CON-R005")
        trust = ((status.get("clock") or {}).get("clock_trust")) or ((report.get("clock") or {}).get("clock_trust"))
        if readiness == "READY" and trust and trust not in {"SYNCED_NTP", "SYNCED_PTP"}:
            self._upsert(
                "CON-R006",
                "time_readiness_conflict",
                "critical",
                {"subject_id": "clock", "statement": "READY requires trusted clock"},
                [{"claim": "readiness_state=READY", "source": "boot_report", "reliability": 1.0}],
                [{"claim": f"clock_trust={trust}", "source": "clock", "reliability": 1.0}],
                "wait for NTP/PTP before treating timestamps as trusted",
            )
        else:
            self._resolve_if_open("CON-R006")

    def _r007(self, registry_sensors: list[dict[str, Any]] | None) -> None:
        if not registry_sensors:
            self._resolve_if_open("CON-R007")
            return
        try:
            assert_no_sensor_id_collision(registry_sensors)
            self._resolve_if_open("CON-R007")
        except SensorIdCollision as exc:
            self._upsert(
                "CON-R007",
                "schema_identity_conflict",
                "critical",
                {"subject_id": "registry", "statement": "each enabled sensor_id has one semantic"},
                [],
                [{"claim": str(exc), "source": "registry", "reliability": 1.0}],
                "disable colliding sensor id",
            )

    def _r008(self) -> None:
        snap = load_latest() or {}
        ok, detail = replay_matches_current(snap) if snap else (True, "no snapshot")
        if snap and not ok:
            self._upsert(
                "CON-R008",
                "world_state_integrity_conflict",
                "critical",
                {"subject_id": "snapshot", "statement": "replay hash equals snapshot-derived hash"},
                [{"claim": "latest.json present", "source": "snapshot", "reliability": 1.0}],
                [{"claim": detail, "source": "replay", "reliability": 1.0}],
                "investigate journal/snapshot divergence",
            )
        else:
            self._resolve_if_open("CON-R008")

    def _r009_r010(self) -> None:
        status = self.board_status or {}
        health = status.get("health") or {}
        for sid, plugin_health in health.items():
            if plugin_health != "healthy":
                continue
            if sid.startswith("OCT-SENSE-09") or sid.startswith("OCT-SENSE-10"):
                continue
            unit = self.unit_health.get("octopus-sensorium.service") or {}
            if unit.get("healthy") is False:
                self._upsert(
                    "CON-R009",
                    "process_identity_or_buffer_conflict",
                    "high",
                    {"subject_id": sid, "statement": "plugin health ACTIVE requires process/cgroup"},
                    [{"claim": f"plugin_health={plugin_health}", "source": "sensorium.health", "reliability": 0.9}],
                    [{"claim": "octopus-sensorium.service healthy=false", "source": "OCT-SENSE-052", "reliability": 0.97}],
                    "inspect cgroup and systemd unit",
                )
                break
        else:
            self._resolve_if_open("CON-R009")
        registry = getattr(self, "registry_sensors", None) or []
        disabled = {
            str(spec.get("sensor_id"))
            for spec in registry
            if spec.get("enabled") is False or spec.get("status") in {"DISABLED_BY_POLICY", "MANIFEST_ONLY"}
        }
        running_disabled = [sid for sid in health if sid in disabled and health.get(sid) == "healthy"]
        if running_disabled:
            self._upsert(
                "CON-R010",
                "registry_runtime_conflict",
                "high",
                {"subject_id": running_disabled[0], "statement": "disabled registry sensors must not have a live plugin process"},
                [{"claim": f"registry disabled {running_disabled}", "source": "registry", "reliability": 1.0}],
                [{"claim": "plugin health healthy", "source": "sensorium.health", "reliability": 0.9}],
                "stop unregistered plugin",
            )
        else:
            self._resolve_if_open("CON-R010")

    def _r011_r012(self) -> None:
        status = self.board_status or {}
        report = self.boot_report or {}
        leg = status.get("leg_authority") or report.get("leg_authority") or "DENIED"
        nats_users = status.get("nats_users") or []
        if leg == "DENIED" and "leg01" in nats_users:
            self._upsert(
                "CON-R011",
                "policy_state_conflict",
                "high",
                {"subject_id": "leg01", "statement": "DENIED legs must not have a usable NATS user"},
                [{"claim": "leg_authority=DENIED", "source": "status", "reliability": 1.0}],
                [{"claim": "nats user leg01 present", "source": "nats_config_users", "reliability": 1.0}],
                "apply NATS maintenance bundle to deny-all or remove leg01",
            )
        else:
            self._resolve_if_open("CON-R011")
        mqtt_state = status.get("mqtt_state") or report.get("mqtt_state") or "DISABLED"
        mqtt_open = bool(status.get("mqtt_1883_open") or report.get("mqtt_1883_open"))
        if mqtt_state == "DISABLED" and mqtt_open:
            self._upsert(
                "CON-R012",
                "policy_state_conflict",
                "critical",
                {"subject_id": "mqtt", "statement": "DISABLED MQTT requires port 1883 closed"},
                [{"claim": "mqtt_state=DISABLED", "source": "status", "reliability": 1.0}],
                [{"claim": "port 1883 open", "source": "socket", "reliability": 1.0}],
                "close listener 1883",
            )
        else:
            self._resolve_if_open("CON-R012")

    def _r013(self) -> None:
        found = False
        for sid, items in self.obs_by_sensor.items():
            for obs in items:
                prov = obs.get("provenance") or {}
                if prov.get("signature_verified") is True and not prov.get("verified_by"):
                    found = True
                    self._upsert(
                        "CON-R013",
                        "provenance_conflict",
                        "critical",
                        {"subject_id": sid, "statement": "signature_verified=true requires verification evidence"},
                        [{"claim": f"event_id={obs.get('event_id')}", "source": sid, "reliability": 1.0}],
                        [{"claim": "verified_by missing", "source": "provenance", "reliability": 1.0}],
                        "treat signature as unverified",
                    )
                    break
            if found:
                break
        if not found:
            self._resolve_if_open("CON-R013")

    def _r014(self) -> None:
        status = self.board_status or {}
        fp = status.get("trust_root_fingerprint")
        revoked = set(status.get("revoked_fingerprints") or [])
        if fp and fp in revoked:
            self._upsert(
                "CON-R014",
                "trust_root_conflict",
                "critical",
                {"subject_id": "trust", "statement": "live trust root must not be revoked"},
                [{"claim": f"live={fp}", "source": "root.pub", "reliability": 1.0}],
                [{"claim": "fingerprint in revocation list", "source": "revoked.json", "reliability": 1.0}],
                "install a non-revoked root-v2 public key",
            )
        else:
            self._resolve_if_open("CON-R014")

    def evaluate(self, registry_sensors: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        if registry_sensors is not None:
            self.registry_sensors = registry_sensors
        self.pending = []
        self._r001_r002()
        self._r003()
        self._r004_r006()
        self._r007(getattr(self, "registry_sensors", None))
        self._r008()
        self._r009_r010()
        self._r011_r012()
        self._r013()
        self._r014()
        out: list[dict[str, Any]] = []
        now = time.time()
        for event in self.pending:
            contra = event.get("contradiction") or {}
            key = f"{contra.get('rule_id')}:{contra.get('state')}"
            if contra.get("state") == "RESOLVED":
                out.append(event)
                continue
            last = self._last_emit.get(key, 0)
            if now - last < 60:
                continue
            self._last_emit[key] = now
            out.append(event)
        return out

    async def discover(self) -> DiscoveryResult:
        return DiscoveryResult(present=True, details={"mode": "shadow"})

    async def self_test(self) -> SelfTestResult:
        pub = self.manifest.get("publication") or {}
        shadow_ok = pub.get("can_change_readiness") is not True and pub.get("can_resolve_belief") is not True
        pwm_ok = True
        try:
            assert_no_pwm_write()
        except IsolationViolation:
            pwm_ok = False
        return SelfTestResult(passed=shadow_ok, message=f"shadow={shadow_ok} pwm={pwm_ok}", measurements={"shadow": shadow_ok})

    async def observe(self) -> AsyncIterator[RawObservation]:
        events = self.evaluate(getattr(self, "registry_sensors", None))
        payload = {"sequence": self.next_sequence(), "events": events, "open": list(self.open)}
        yield RawObservation(payload=payload, source_id="meta-contradiction", bytes_len=len(str(payload)))
