from __future__ import annotations

from pathlib import Path

import yaml

from octopus_sensorium.isolation import reject_actuator_manifest
from octopus_sensorium.schema_ids import assert_no_sensor_id_collision, is_runtime_enabled

STAGING = Path("/var/lib/octopus/staging/phase3-registry-100/registry.yaml")
REQUIRED = (
    "sensor_id",
    "name",
    "family",
    "sensor_type",
    "version",
    "schema_version",
    "status",
    "enabled",
    "capabilities",
    "observed_properties",
    "source_requirements",
    "hardware_requirements",
    "credential_requirements",
    "consent_requirements",
    "network_requirements",
    "plugin",
    "schedule",
    "freshness",
    "resources",
    "security",
    "failure",
    "publication",
    "dependencies",
    "fusion_targets",
    "implementation_wave",
)
ALLOWED_RUNTIME = {
    "OCT-SENSE-051",
    "OCT-SENSE-052",
    "OCT-SENSE-053",
    "OCT-SENSE-053.THERMAL",
    "OCT-SENSE-092",
    "OCT-SENSE-095",
}
ALLOWED_PLUGIN_TYPES = {"filesystem", "process", "system_resources", "thermal", "anomaly", "contradiction"}


def test_staging_registry_has_100_numeric_ids():
    doc = yaml.safe_load(STAGING.read_text(encoding="utf-8"))
    sensors = doc["sensors"]
    numeric = [s for s in sensors if str(s["sensor_id"])[10:].isdigit()]
    ids = {int(s["sensor_id"].split("-")[-1]) for s in numeric}
    assert ids == set(range(1, 101))
    assert doc["config_version"] == 5
    assert_no_sensor_id_collision(sensors)
    for spec in sensors:
        reject_actuator_manifest(spec)
        for key in REQUIRED:
            assert key in spec, f"{spec['sensor_id']} missing {key}"
        assert spec["security"]["actuator_access"] is False
        assert spec.get("simulated") is not True


def test_staging_runtime_plugins_are_only_wave0_real():
    doc = yaml.safe_load(STAGING.read_text(encoding="utf-8"))
    runtime = {s["sensor_id"] for s in doc["sensors"] if is_runtime_enabled(s)}
    assert runtime == ALLOWED_RUNTIME
    for spec in doc["sensors"]:
        plugin = spec.get("plugin")
        if plugin:
            assert plugin.get("type") in ALLOWED_PLUGIN_TYPES
            assert spec["sensor_id"] in ALLOWED_RUNTIME
        else:
            assert spec["sensor_id"] not in ALLOWED_RUNTIME or spec["sensor_id"].endswith(".THERMAL") is False


def test_staging_forbids_thermal_on_015_and_054():
    doc = yaml.safe_load(STAGING.read_text(encoding="utf-8"))
    by_id = {s["sensor_id"]: s for s in doc["sensors"]}
    assert by_id["OCT-SENSE-015"]["status"] == "DISABLED_BY_POLICY"
    assert "thermal" not in by_id["OCT-SENSE-015"]["name"]
    assert by_id["OCT-SENSE-054"]["status"] == "MANIFEST_ONLY"
    assert by_id["OCT-SENSE-054"]["enabled"] is False
    assert by_id["OCT-SENSE-054"]["plugin"] is None
    assert by_id["OCT-SENSE-053.THERMAL"]["status"] == "ACTIVE"
    assert by_id["OCT-SENSE-096"]["status"] == "MANIFEST_ONLY"
    assert by_id["OCT-SENSE-099"]["name"] == "policy_safety"
    assert by_id["OCT-SENSE-100"]["name"] == "provenance_trust"


def test_live_registry_matches_applied_staging():
    live = Path("/etc/octopus/config/registry.yaml").read_bytes()
    staging = STAGING.read_bytes()
    assert live == staging
    import hashlib

    digest = "sha256:" + hashlib.sha256(live).hexdigest()
    assert digest == "sha256:19f25383d2611000e3272ad9ad5d55e2e645cb5db757a9419f4e7b6d5f1251c5"
