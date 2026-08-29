from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from octopus_sensorium.fusion import CAN_CHANGE_BELIEF, STATUS as FUSION_STATUS
from octopus_sensorium.kernel.lifecycle import PluginLifecycle, PluginState
from octopus_sensorium.kernel.sequences import restore_sequence, save_sequence
from octopus_sensorium.kernel.supervisor import PluginSupervisor
from octopus_sensorium.messaging.deduplication import ContentHashDeduper
from octopus_sensorium.messaging.offline_buffer import OfflineBuffer
from octopus_sensorium.meta.placeholders import PLACEHOLDERS
from octopus_sensorium.models import Observation, Provenance, SensorManifest
from octopus_sensorium.observation import make_observation
from octopus_sensorium.policy.action_boundary import deny, may_actuate
from octopus_sensorium.policy.command_gate import classify
from octopus_sensorium.registry.compatibility import REGISTRY_100_STATUS
from octopus_sensorium.registry.validator import validate_registry_document
from octopus_sensorium.schemas import SCHEMA_ROOT, schema_path
from octopus_sensorium.telemetry import OTEL_STATUS
from octopus_sensorium.world_state.belief import CAN_RESOLVE_BELIEF


def test_envelope_has_required_contract_fields():
    obs = make_observation(
        board_id="sensorium-opi5pro-68e44cdf",
        sensor_id="OCT-SENSE-053.THERMAL",
        sensor_agent_id="agent://sensor/OCT-SENSE-053.THERMAL",
        observed_property="host.soc.temperature",
        value=24.1,
        unit="Cel",
        sequence_number=1,
        source_id="sysfs-thermal",
        collector_version="0.1.0",
        transformations=["milliC_to_C"],
        clock_trust="SYNCED_NTP",
    )
    parsed = Observation.model_validate(obs)
    assert parsed.provenance.signature_verified is False
    assert parsed.provenance.content_hash.startswith("sha256:")
    assert parsed.result.encoding == "json"
    assert parsed.time.time_unverified is False
    assert parsed.quality.time_unverified is False
    assert parsed.evidence.supporting_event_ids == []
    assert parsed.policy.actionable is False
    assert parsed.policy.may_change_readiness is False
    assert parsed.policy.may_quarantine is False
    assert parsed.policy.human_approval_required is True
    assert parsed.security.redaction_applied is False
    assert parsed.routing.raw_available is False


def test_signature_verified_cannot_default_true():
    assert Provenance.model_validate(
        {
            "source_id": "x",
            "collector_version": "0.1.0",
            "content_hash": "sha256:" + "a" * 64,
            "clock_trust": "SYNCED_NTP",
        }
    ).signature_verified is False


def test_observation_rejects_unknown_type():
    obs = make_observation(
        board_id="b",
        sensor_id="s",
        sensor_agent_id="a",
        observed_property="t",
        value=1,
        unit=None,
        sequence_number=1,
        source_id="x",
        collector_version="0.1.0",
        transformations=[],
        clock_trust="SYNCED_NTP",
    )
    obs["observation_type"] = "llm_guess"
    with pytest.raises(ValidationError):
        Observation.model_validate(obs)


def test_json_schemas_exist():
    names = [
        "observation/observation.schema.json",
        "anomaly/anomaly.schema.json",
        "contradiction/contradiction.schema.json",
        "audit/audit.schema.json",
        "manifest/manifest.schema.json",
        "command/command.schema.json",
        "migration/migration.schema.json",
    ]
    for name in names:
        path = schema_path(*name.split("/"))
        assert path.is_file(), path
        json.loads(path.read_text(encoding="utf-8"))
    assert SCHEMA_ROOT.name == "schemas"


def test_plugin_cannot_self_release_quarantine():
    life = PluginLifecycle()
    life.mark("OCT-SENSE-051", PluginState.DISCOVERED)
    life.mark("OCT-SENSE-051", PluginState.QUARANTINED)
    with pytest.raises(Exception):
        life.release_quarantine("OCT-SENSE-051", human_approved=False)
    assert life.release_quarantine("OCT-SENSE-051", human_approved=True) == PluginState.AWAITING_APPROVAL


def test_unknown_plugin_is_refused_not_activated():
    supervisor = PluginSupervisor(plugin_types={})
    supervisor.instantiate(
        [
            {
                "sensor_id": "OCT-SENSE-099",
                "enabled": True,
                "plugin": {"type": "not-a-real-plugin"},
                "security": {"actuator_access": False, "shell_access": False},
            }
        ]
    )
    assert "OCT-SENSE-099" not in supervisor.plugins
    assert "OCT-SENSE-099" in supervisor.skipped_unknown
    assert supervisor.lifecycle.states["OCT-SENSE-099"] == PluginState.FAILED


def test_sequence_persists(tmp_path, monkeypatch):
    path = tmp_path / "seq.json"
    monkeypatch.setattr("octopus_sensorium.kernel.sequences.DEFAULT_PATH", path)
    save_sequence("OCT-SENSE-051", 9)
    assert restore_sequence("OCT-SENSE-051") == 9


def test_action_boundary_never_actuates():
    assert may_actuate() is False
    denied = deny("DIRECT_MOTOR_COMMAND")
    assert denied["allowed"] is False
    assert denied["actuator_authority"] == "NONE"


def test_forbidden_command_classified():
    assert classify("DIRECT_MOTOR_COMMAND") == "FORBIDDEN"
    assert classify("LIST_SENSORS") == "ALLOWLISTED_DEFERRED"


def test_live_registry_validates_without_inventing_sensors():
    import yaml

    document = yaml.safe_load(Path("/etc/octopus/config/registry.yaml").read_text(encoding="utf-8"))
    manifests = validate_registry_document(document)
    ids = {m.sensor_id for m in manifests}
    assert "OCT-SENSE-051" in ids
    assert "OCT-SENSE-092" in ids
    assert len(manifests) == 103
    runtime = [m.sensor_id for m in manifests if m.enabled is True]
    assert set(runtime) == {
        "OCT-SENSE-051",
        "OCT-SENSE-052",
        "OCT-SENSE-053",
        "OCT-SENSE-053.THERMAL",
        "OCT-SENSE-092",
        "OCT-SENSE-095",
    }
    SensorManifest.model_validate({"sensor_id": "OCT-SENSE-001", "status": "PLANNED", "enabled": False})


def test_placeholders_are_not_enabled():
    for spec in PLACEHOLDERS.values():
        assert spec["enabled"] is False
        assert spec["status"] == "MANIFEST_ONLY"
    assert FUSION_STATUS == "NOT_ENABLED"
    assert CAN_CHANGE_BELIEF is False
    assert CAN_RESOLVE_BELIEF is False
    assert OTEL_STATUS == "not_enabled"
    assert REGISTRY_100_STATUS == "APPLIED"


def test_offline_buffer_and_dedup():
    buf = OfflineBuffer(maxlen=2)
    buf.append("octopus.sensorium.heartbeat", {"n": 1})
    buf.append("octopus.sensorium.heartbeat", {"n": 2})
    buf.append("octopus.sensorium.heartbeat", {"n": 3})
    drained = buf.drain()
    assert len(drained) == 2
    assert drained[0][1]["n"] == 2
    dedup = ContentHashDeduper(limit=8)
    assert dedup.accept("sha256:a") is True
    assert dedup.accept("sha256:a") is False
