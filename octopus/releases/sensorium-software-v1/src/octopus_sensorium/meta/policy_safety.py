"""OCT-SENSE-099 policy/safety contract agent. Advisory only. Cannot actuate or mutate the host."""

from __future__ import annotations

import socket
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from octopus_sensorium.meta.shadow import SHADOW_POLICY, assert_shadow_manifest
from octopus_sensorium.policy.action_boundary import may_actuate
from octopus_sensorium.sensors.base import BaseSensor, DiscoveryResult, RawObservation, SelfTestResult
from octopus_sensorium.verify import content_hash, load_revoked, load_root_public_key

V2 = "sha256:a20d836d1f461482c76c4d3ed6c6de301d38b3e8e0ef4707e87d7b45e2223a40"


class PolicySafetySensor(BaseSensor):
    sensor_type = "policy"
    capabilities = {"contract_check", "advisory_degraded", "advisory_failed_safe"}

    def __init__(self, manifest: dict[str, Any]) -> None:
        super().__init__(manifest)
        assert_shadow_manifest(manifest)
        self.snapshot: dict[str, Any] = {}

    def ingest(self, kind: str, payload: dict[str, Any], subject: str = "") -> None:
        if kind in {"health", "boot_report"}:
            self.snapshot.update(payload)

    def _mqtt_open(self) -> bool:
        sock = socket.socket()
        sock.settimeout(0.3)
        try:
            sock.connect(("127.0.0.1", 1883))
            return True
        except OSError:
            return False
        finally:
            sock.close()

    def _nats_users(self) -> list[str]:
        conf = Path("/etc/nats/nats-server.conf")
        try:
            if not conf.exists():
                return []
            users: list[str] = []
            for line in conf.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith("user:"):
                    users.append(stripped.split(":", 1)[1].strip())
            return users
        except OSError:
            return []

    def _private_v2_present(self) -> bool:
        return Path("/root/OCTOPUS-ROOT-V2/private").exists() or Path("/root/octopus-ca/root.ed25519").exists()

    def evaluate(self) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        snap = self.snapshot
        actuator = snap.get("actuator_authority") or "NONE"
        estop = ((snap.get("safety") or {}) if isinstance(snap.get("safety"), dict) else {}).get("estop_channel")
        soft_ok = actuator == "PERMITTED_SOFTWARE_A0" and estop == "SOFTWARE_LATCH"
        if (actuator != "NONE" and not soft_ok) or may_actuate():
            findings.append(("FAILED_SAFE", "actuator_authority", f"actuator_authority={actuator}"))
        if self._mqtt_open():
            findings.append(("FAILED_SAFE", "mqtt", "port 1883 open"))
        if snap.get("leg_authority") not in {None, "DENIED"}:
            findings.append(("FAILED_SAFE", "leg", str(snap.get("leg_authority"))))
        users = self._nats_users()
        if "leg01" in users and (snap.get("leg_authority") or "DENIED") == "DENIED":
            findings.append(("DEGRADED", "leg_nats_user", "leg01 NATS user present while DENIED"))
        try:
            pub = load_root_public_key()
            fp = content_hash(pub)
            revoked = load_revoked()
            fps = set(revoked.get("revoked_key_fingerprints") or [])
            if fp in fps:
                findings.append(("FAILED_SAFE", "trust_root", "live root is revoked"))
            if fp != V2:
                findings.append(("DEGRADED", "trust_root", "live root is not root-v2"))
        except Exception as exc:
            findings.append(("DEGRADED", "trust_root", type(exc).__name__))
        if self._private_v2_present():
            findings.append(("FAILED_SAFE", "private_key", "signing private key present on board"))
        clock = (snap.get("clock") or {}).get("clock_trust") or snap.get("clock_trust")
        if snap.get("readiness_state") == "READY" and clock and clock not in {"SYNCED_NTP", "SYNCED_PTP"}:
            findings.append(("DEGRADED", "clock", str(clock)))
        events = []
        for proposal, topic, detail in findings:
            events.append(
                {
                    "event_id": str(uuid.uuid4()),
                    "sensor_id": "OCT-SENSE-099",
                    "observation_type": "fault",
                    "observed_property": "meta.policy_safety",
                    "policy_safety": {
                        "topic": topic,
                        "detail": detail,
                        "proposal": proposal,
                        "may_restart_service": False,
                        "may_delete_files": False,
                        "may_change_permissions": False,
                        "may_actuate": False,
                    },
                    "policy": {**SHADOW_POLICY, "actionable": False, "human_approval_required": True},
                }
            )
        if not events:
            events.append(
                {
                    "event_id": str(uuid.uuid4()),
                    "sensor_id": "OCT-SENSE-099",
                    "observation_type": "state",
                    "observed_property": "meta.policy_safety",
                    "policy_safety": {"proposal": "NONE", "contracts_ok": True},
                    "policy": {**SHADOW_POLICY, "actionable": False},
                }
            )
        return events

    async def discover(self) -> DiscoveryResult:
        return DiscoveryResult(present=True, details={"mode": "shadow", "cannot_actuate": True})

    async def self_test(self) -> SelfTestResult:
        return SelfTestResult(passed=not may_actuate(), message="observe-only contracts", measurements={"may_actuate": False})

    async def observe(self) -> AsyncIterator[RawObservation]:
        events = self.evaluate()
        payload = {"sequence": self.next_sequence(), "events": events}
        yield RawObservation(payload=payload, source_id="meta-policy-safety", bytes_len=len(str(payload)))
