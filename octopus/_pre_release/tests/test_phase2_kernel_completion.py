from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest
import yaml

from octopus_sensorium.compat import upgrade_observation
from octopus_sensorium.messaging import nats_client
from octopus_sensorium.meta.shadow import SHADOW_POLICY
from octopus_sensorium.models.observation import Observation
from octopus_sensorium.natsbus import ensure_streams
from octopus_sensorium.observation import make_observation
from octopus_sensorium.policy.gate import PolicyDenied, gate_command, gate_observation
from octopus_sensorium.registry.migrations import MIGRATIONS, apply_id_migration
from octopus_sensorium.telemetry import KERNEL_STATUS, OTEL_EXPORT, OTEL_STATUS, SENSOR_055_STATUS
from octopus_sensorium.telemetry.otel import init_otel


WAVE0 = Path("/var/lib/octopus/state/wave0-baseline")
REG_V4 = Path("/var/lib/octopus/state/config-history/registry-v4")
LIVE_REG = Path("/etc/octopus/config/registry.yaml")
LIVE_BOARD = Path("/etc/octopus/config/board.yaml")
V5_HASH = "sha256:19f25383d2611000e3272ad9ad5d55e2e645cb5db757a9419f4e7b6d5f1251c5"
V4_HASH = "sha256:3060e7bb00f93de9ece2f4fe0be4529e92180ed40f63950d3538bca74c4a879d"
WAVE0_REG_HASH = "sha256:046566dab34ca98f7f7c564cde9e8c92b471bae65f93bf7cf4f7d85b9a2fa3d4"
BOARD_HASH = "sha256:b53ec5ba3764f035513535577df5e72f25767e54dda2cedfd5d9b1ca73cd0d5d"


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_ensure_streams_forbidden_on_runtime():
    import asyncio

    async def _call() -> None:
        await ensure_streams(None)  # type: ignore[arg-type]

    with pytest.raises(RuntimeError, match="allow_nats_provisioning=false"):
        asyncio.run(_call())


def test_messaging_module_does_not_export_ensure_streams():
    assert "ensure_streams" not in nats_client.__all__
    assert not hasattr(nats_client, "ensure_streams")
    src = Path("/opt/octopus/src/octopus_sensorium/app.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.extend(alias.name for alias in node.names)
    assert "ensure_streams" not in imported


def test_legacy_observation_upgrades_without_trusting_signature():
    legacy = {
        "event_id": "old",
        "schema_version": "1.0.0",
        "sequence_number": 1,
        "sensorium_board_id": "sensorium-opi5pro-68e44cdf",
        "sensor_id": "OCT-SENSE-051",
        "sensor_agent_id": "agent://sensor/OCT-SENSE-051",
        "observed_property": "host.filesystem.mtime",
        "subject": {"entity_id": "sensorium-opi5pro-68e44cdf", "entity_type": "sensorium_board"},
        "result": {"value": {"path": "/etc/octopus/config"}, "unit": None},
        "time": {
            "phenomenon_time": "2026-08-16T00:00:00+00:00",
            "ingestion_time": "2026-08-16T00:00:00+00:00",
            "processing_time": "2026-08-16T00:00:00+00:00",
            "valid_until": "2026-08-16T00:00:30+00:00",
        },
        "quality": {"valid": True, "confidence": 1.0, "completeness": 1.0, "freshness_seconds": 0, "calibration_status": "unknown"},
        "uncertainty": {"type": "unknown", "score": 0.0, "method": "unspecified"},
        "provenance": {
            "source_id": "posix-stat",
            "collector_version": "0.1.0",
            "transformations": [],
            "content_hash": "sha256:" + "a" * 64,
            "signature_verified": True,
            "clock_trust": "SYNCED_NTP",
        },
        "security": {"classification": "internal", "contains_pii": False},
        "routing": {"priority": "normal", "allowed_consumers": ["octopus-core"], "raw_available": False},
    }
    upgraded = upgrade_observation(legacy)
    parsed = Observation.model_validate(upgraded)
    assert parsed.provenance.signature_verified is False
    assert parsed.result.encoding == "json"
    assert parsed.evidence.supporting_event_ids == []
    assert parsed.policy.actionable is False
    assert "time_unverified" in parsed.time.model_dump()


def test_schema_migrations_preserve_wave0_identities():
    assert apply_id_migration("OCT-SENSE-001") == "OCT-SENSE-053"
    assert apply_id_migration("OCT-SENSE-002") == "OCT-SENSE-053.THERMAL"
    assert apply_id_migration("OCT-SENSE-003") == "OCT-SENSE-051"
    assert apply_id_migration("OCT-SENSE-054") == "OCT-SENSE-053.THERMAL"
    assert apply_id_migration("OCT-SENSE-051") == "OCT-SENSE-051"
    assert all(event.get("from") and event.get("to") for event in MIGRATIONS)


def test_wave0_and_registry_v4_baselines_are_preserved():
    assert _sha(WAVE0 / "registry.yaml") == WAVE0_REG_HASH
    assert _sha(WAVE0 / "board.yaml") == BOARD_HASH
    checksums = (WAVE0 / "checksums.sha256").read_text(encoding="utf-8")
    assert "046566dab34ca98f7f7c564cde9e8c92b471bae65f93bf7cf4f7d85b9a2fa3d4  ./registry.yaml" in checksums
    assert _sha(REG_V4 / "registry.yaml") == V4_HASH
    assert _sha(LIVE_REG) == V5_HASH
    assert _sha(LIVE_BOARD) == BOARD_HASH
    assert _sha(LIVE_REG) != WAVE0_REG_HASH
    assert _sha(LIVE_REG) != V4_HASH


def test_092_095_remain_shadow():
    doc = yaml.safe_load(LIVE_REG.read_text(encoding="utf-8"))
    by_id = {s["sensor_id"]: s for s in doc["sensors"]}
    for sid in ("OCT-SENSE-092", "OCT-SENSE-095"):
        spec = by_id[sid]
        assert spec["mode"] == "shadow"
        assert spec["enabled"] is True
        assert spec["status"] == "SHADOW"
        pub = spec["publication"]
        assert pub.get("can_change_readiness") is False
        assert pub.get("can_quarantine") is False
        assert pub.get("can_execute") is False
    assert SHADOW_POLICY["actionable"] is False
    for sid in ("OCT-SENSE-096", "OCT-SENSE-097", "OCT-SENSE-099", "OCT-SENSE-100"):
        assert by_id[sid]["enabled"] is False


def test_policy_gate_blocks_enforcement_and_commands():
    obs = make_observation(
        board_id="sensorium-opi5pro-68e44cdf",
        sensor_id="OCT-SENSE-092",
        sensor_agent_id="agent://sensor/OCT-SENSE-092",
        observed_property="anomaly",
        value={},
        unit=None,
        sequence_number=1,
        source_id="meta-anomaly",
        collector_version="0.1.0",
        transformations=[],
        clock_trust="SYNCED_NTP",
        observation_type="anomaly",
    )
    gate_observation(obs)
    obs["policy"]["may_change_readiness"] = True
    with pytest.raises(PolicyDenied):
        gate_observation(obs)
    with pytest.raises(PolicyDenied):
        gate_command("LIST_SENSORS")
    with pytest.raises(PolicyDenied):
        gate_command("DIRECT_MOTOR_COMMAND")


def test_otel_kernel_has_no_exporter():
    tracer = init_otel()
    span = tracer.start_span("kernel.test")
    span.end()
    assert OTEL_EXPORT is False
    assert SENSOR_055_STATUS == "not_enabled"
    assert OTEL_STATUS == "not_enabled"
    assert KERNEL_STATUS == "in_process_noop"
