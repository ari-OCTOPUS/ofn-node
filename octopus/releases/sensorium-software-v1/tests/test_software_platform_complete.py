from __future__ import annotations

import json
from pathlib import Path

from octopus_sensorium.compat import upgrade_observation
from octopus_sensorium.evidence.quarantine import persist_quarantine
from octopus_sensorium.evidence.store import persist_observation, verify_jsonl
from octopus_sensorium.meta.contradiction import ContradictionSensor
from octopus_sensorium.meta.novelty import NoveltySensor
from octopus_sensorium.meta.policy_safety import PolicySafetySensor
from octopus_sensorium.meta.provenance_trust import ProvenanceTrustSensor
from octopus_sensorium.meta.uncertainty import UncertaintySensor
from octopus_sensorium.models.observation import Observation
from octopus_sensorium.natsbus import ensure_streams
from octopus_sensorium.observation import make_observation
from octopus_sensorium.snapshot import apply_event_dedup, diagnose_journal, load_events, state_hash
from octopus_sensorium.telemetry.metrics import InProcessMetrics


def _shadow(sensor_id: str) -> dict:
    return {
        "sensor_id": sensor_id,
        "mode": "shadow",
        "publication": {
            "shadow_only": True,
            "can_change_readiness": False,
            "can_quarantine": False,
            "can_execute": False,
        },
        "security": {"actuator_access": False, "command_access": False, "shell_access": False},
    }


def test_envelope_has_location_evidence_policy():
    obs = make_observation(
        board_id="sensorium-opi5pro-68e44cdf",
        sensor_id="OCT-SENSE-051",
        sensor_agent_id="agent://sensor/OCT-SENSE-051",
        observed_property="host.filesystem.mtime",
        value={"ok": True},
        unit=None,
        sequence_number=1,
        source_id="posix-stat",
        collector_version="1.0.0",
        transformations=["posix_stat"],
        clock_trust="SYNCED_NTP",
    )
    parsed = Observation.model_validate(obs)
    assert parsed.location.frame == "board"
    assert parsed.evidence is not None
    assert parsed.policy.actionable is False
    assert parsed.provenance.signature_verified is False
    assert 0.0 <= parsed.quality.confidence <= 1.0


def test_legacy_gains_location(tmp_path):
    upgraded = upgrade_observation(
        {
            "event_id": "legacy",
            "schema_version": "1.0.0",
            "sequence_number": 1,
            "sensorium_board_id": "sensorium-opi5pro-68e44cdf",
            "sensor_id": "OCT-SENSE-051",
            "sensor_agent_id": "agent://sensor/OCT-SENSE-051",
            "observation_type": "measurement",
            "observed_property": "x",
            "subject": {"entity_id": "board", "entity_type": "sensorium_board"},
            "result": {"value": 1, "unit": None},
            "time": {
                "phenomenon_time": "2026-08-16T00:00:00+00:00",
                "ingestion_time": "2026-08-16T00:00:00+00:00",
                "processing_time": "2026-08-16T00:00:00+00:00",
                "valid_until": "2026-08-16T00:00:30+00:00",
            },
            "quality": {
                "valid": True,
                "confidence": 1,
                "completeness": 1,
                "freshness_seconds": 0,
                "calibration_status": "unknown",
                "time_unverified": False,
            },
            "uncertainty": {"type": "aleatoric", "score": 0, "method": "device_repeatability"},
            "provenance": {
                "source_id": "legacy",
                "collector_version": "0",
                "transformations": [],
                "content_hash": "sha256:" + "0" * 64,
                "signature_verified": True,
                "clock_trust": "SYNCED_NTP",
            },
            "security": {
                "classification": "internal",
                "contains_pii": False,
                "consent_id": None,
                "untrusted_content": False,
                "redaction_applied": False,
            },
            "routing": {"priority": "normal", "allowed_consumers": ["octopus-core"], "raw_available": False},
            "scope": "board_internal",
            "is_environment_feature": False,
            "subsensor_id": "OCT-SENSE-051",
        }
    )
    assert upgraded["location"]["frame"] == "board"
    assert upgraded["provenance"]["signature_verified"] is False


def test_evidence_jsonl_append_only(tmp_path):
    obs = make_observation(
        board_id="b",
        sensor_id="OCT-SENSE-051",
        sensor_agent_id="a",
        observed_property="p",
        value=1,
        unit=None,
        sequence_number=1,
        source_id="s",
        collector_version="1",
        transformations=[],
        clock_trust="SYNCED_NTP",
    )
    persist_observation("OCT-SENSE-051", obs, tmp_path)
    persist_observation("OCT-SENSE-051", obs, tmp_path)
    text = (tmp_path / "observations.jsonl").read_text(encoding="utf-8")
    assert text.count("\n") == 1
    ok, detail = verify_jsonl(tmp_path)
    assert ok, detail


def test_quarantine_appends(tmp_path):
    path = tmp_path / "malformed.jsonl"
    persist_quarantine(sensor_id="OCT-SENSE-051", stage="DECODE", reason="bad", path=path)
    persist_quarantine(sensor_id="OCT-SENSE-051", stage="SCHEMA_VALIDATE", reason="bad2", path=path)
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2


def test_replay_diagnose_and_duplicate_skip(tmp_path):
    journal = tmp_path / "events.jsonl"
    journal.write_text(
        json.dumps({"seq": 1, "kind": "obs", "content_hash": "sha256:aaa"})
        + "\n"
        + json.dumps({"seq": 1, "kind": "obs", "content_hash": "sha256:aaa"})
        + "\n"
        + json.dumps({"seq": 3, "kind": "obs", "content_hash": "sha256:bbb"})
        + "\n",
        encoding="utf-8",
    )
    corrupt = tmp_path / "corrupt.jsonl"
    corrupt.write_text(journal.read_text(encoding="utf-8") + "{not-json\n", encoding="utf-8")
    diag = diagnose_journal(corrupt)
    assert diag["duplicates"]
    assert 2 in diag["missing"]
    assert diag["corrupt"]
    state: dict = {}
    for event in load_events(journal, after_seq=0):
        state = apply_event_dedup(state, event)
    assert state["observations_published"] == 2


def test_contradiction_r011_leg_user():
    sensor = ContradictionSensor(_shadow("OCT-SENSE-095"))
    sensor.ingest("health", {"leg_authority": "DENIED", "nats_users": ["sensorium", "leg01"]})
    events = sensor.evaluate()
    assert any(e["contradiction"]["rule_id"] == "CON-R011" for e in events)


def test_contradiction_r013_unverified_true():
    sensor = ContradictionSensor(_shadow("OCT-SENSE-095"))
    sensor.ingest(
        "observation",
        {
            "sensor_id": "OCT-SENSE-051",
            "event_id": "x",
            "provenance": {"signature_verified": True},
            "result": {"value": 1},
        },
    )
    events = sensor.evaluate()
    assert any(e["contradiction"]["rule_id"] == "CON-R013" for e in events)


def test_uncertainty_does_not_equal_confidence():
    sensor = UncertaintySensor(_shadow("OCT-SENSE-096"))
    sensor.ingest(
        "observation",
        {
            "sensor_id": "OCT-SENSE-053.THERMAL",
            "observed_property": "host.soc.temperature",
            "event_id": "t1",
            "result": {"value": 40.0},
            "quality": {"confidence": 0.9, "freshness_seconds": 80, "calibration_status": "unknown"},
            "evidence": {},
            "subject": {"entity_id": "board"},
        },
    )
    events = sensor.evaluate()
    assert events
    assert events[0]["uncertainty"]["not_confidence"] is True
    assert events[0]["policy"]["may_change_readiness"] is False


def test_novelty_is_not_anomaly():
    sensor = NoveltySensor(_shadow("OCT-SENSE-097"))
    sensor.ingest(
        "observation",
        {
            "sensor_id": "OCT-SENSE-051",
            "event_id": "n1",
            "observed_property": "host.filesystem.mtime",
            "observation_type": "measurement",
            "subject": {"entity_id": "new-entity"},
            "provenance": {"content_hash": "sha256:abc", "source_id": "posix-stat"},
            "result": {"value": 1},
        },
    )
    events = sensor.evaluate()
    assert events[0]["novelty"]["not_anomaly"] is True
    assert "unseen_entity" in events[0]["novelty"]["kinds"]


def test_policy_safety_cannot_actuate():
    sensor = PolicySafetySensor(_shadow("OCT-SENSE-099"))
    sensor.ingest("health", {"actuator_authority": "FULL", "leg_authority": "DENIED"})
    events = sensor.evaluate()
    assert any((e.get("policy_safety") or {}).get("proposal") == "FAILED_SAFE" for e in events)
    assert all((e.get("policy_safety") or {}).get("may_actuate") is False for e in events if e.get("policy_safety"))


def test_provenance_unverified_default():
    sensor = ProvenanceTrustSensor(_shadow("OCT-SENSE-100"))
    sensor.ingest(
        "observation",
        {
            "event_id": "p1",
            "schema_version": "1.0.0",
            "sensor_id": "OCT-SENSE-051",
            "time": {
                "phenomenon_time": "2026-08-16T15:00:00+00:00",
                "valid_until": "2099-01-01T00:00:00+00:00",
            },
            "quality": {"valid": True},
            "provenance": {
                "source_id": "posix-stat",
                "collector_version": "1",
                "content_hash": "sha256:" + "a" * 64,
                "signature_verified": False,
                "clock_trust": "SYNCED_NTP",
                "transformations": ["posix_stat"],
            },
            "evidence": {},
        },
    )
    events = sensor.evaluate()
    assert events[0]["provenance_trust"]["grade"] in {"UNVERIFIED", "PARTIALLY_VERIFIED"}
    assert events[0]["provenance_trust"]["does_not_assert_world_truth"] is True


def test_ensure_streams_still_denied():
    import asyncio

    async def _run():
        try:
            await ensure_streams(None)
            return False
        except RuntimeError as exc:
            return "allow_nats_provisioning=false" in str(exc)

    assert asyncio.run(_run())


def test_metrics_redact_secrets():
    metrics = InProcessMetrics()
    blob = json.dumps(metrics.as_dict())
    assert "password" not in blob
    assert "private" not in blob


def test_release_rollback_symlink(tmp_path):
    releases = tmp_path / "releases"
    (releases / "wave0-current").mkdir(parents=True)
    (releases / "phase2-kernel-v1").mkdir()
    (releases / "wave0-current" / "marker").write_text("old", encoding="utf-8")
    (releases / "phase2-kernel-v1" / "marker").write_text("new", encoding="utf-8")
    current = tmp_path / "current"
    current.symlink_to(releases / "phase2-kernel-v1")
    current.unlink()
    current.symlink_to(releases / "wave0-current")
    assert (current / "marker").read_text(encoding="utf-8") == "old"
