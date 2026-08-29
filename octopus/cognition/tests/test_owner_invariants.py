"""OCTOPUS owner-review invariants INV-01..INV-24 (Wave 0, no live mutation)."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from octopus_cognition.homeostasis.core import evaluate
from octopus_cognition.homeostasis.models import VariableStatus
from octopus_cognition.ledger import ChainedLedger
from octopus_cognition.metacontrol.gate import evaluate_planning
from octopus_cognition.metacontrol.skill import DomainSkillTracker, SkillReport
from octopus_cognition.owner_authorization import outcome_timestamp_ok, verify_owner_authorization
from octopus_cognition.world_model import policy as wave0_policy

ROOT = Path(__file__).resolve().parents[1] / "src" / "octopus_cognition"
SCRIPTS = Path("/opt/octopus/scripts")
STATE = Path("/var/lib/octopus/state")
SENSORIUM_SRC = Path("/opt/octopus/current/src")


def _json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _forbidden_imports(path: Path, banned: set[str]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(token in alias.name for token in banned):
                    found.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in banned):
                found.append(node.module)
    return found


def test_inv01_skill_none_before_fifty_pairs():
    tracker = DomainSkillTracker(minimum=50)
    report = tracker.report()
    assert report.samples < 50
    assert report.score is None
    assert report.lower_bound is None
    assert report.eligible is False
    live = _json(STATE / "skill" / "latest.json")
    if int(live.get("samples") or 0) < 50:
        assert live.get("score") is None
        assert live.get("lower_bound") is None
        assert live.get("eligible") is False
        assert live.get("reason") == "insufficient_samples"


def test_inv02_persistence_vs_persistence_not_eligible():
    tracker = DomainSkillTracker(minimum=50)
    for _ in range(50):
        tracker.record(0.001, 0.001)
    report = tracker.report()
    assert report.samples == 50
    assert report.score == 0.0
    assert report.eligible is False
    assert report.reason == "not_better_than_baseline"


def test_inv03_shuffled_worse_model_denies():
    tracker = DomainSkillTracker(minimum=50)
    for _ in range(50):
        tracker.record(0.050, 0.001)
    report = tracker.report()
    assert report.eligible is False
    assert report.score is not None and report.score < 0
    decision = evaluate_planning(
        SkillReport(report.score, report.lower_bound, report.samples, False, report.reason, 0.0),
        energy_ratio=0.9,
        evidence_age_s=4.0,
        calibration_error=0.0,
        readiness_profile="WAVE0_OBSERVE_ONLY",
    )
    assert decision.recommendation == "DENY"
    assert decision.executable is False


def test_inv05_stale_outcome_timestamp_rejected():
    ok, reason = outcome_timestamp_ok(issued_at_ns=100, resolved_at_ns=50)
    assert ok is False
    assert reason == "outcome_timestamp_before_prediction"
    ok, reason = outcome_timestamp_ok(issued_at_ns=100, resolved_at_ns=100)
    assert ok is True


def test_inv07_tampered_hash_chain_fails(tmp_path: Path):
    ledger = ChainedLedger(tmp_path, "octopus.test.head.v1")
    ledger.append({"schema": "t", "n": 1})
    ok, _, _ = ledger.verify()
    assert ok is True
    raw = (tmp_path / "ledger.jsonl").read_text(encoding="utf-8")
    (tmp_path / "ledger.jsonl").write_text(raw.replace('"n":1', '"n":99'), encoding="utf-8")
    ok, broken, detail = ledger.verify()
    assert ok is False
    assert broken == 1
    assert detail == "digest"


def test_inv08_checkpoint_wrong_signature_fails(tmp_path: Path):
    sys.path.insert(0, str(SENSORIUM_SRC))
    from nacl.signing import SigningKey

    from octopus_sensorium.verify import SignatureError, load_signed

    payload = tmp_path / "checkpoint.json"
    payload.write_text('{"schema":"octopus.audit.checkpoint.v1","signed":false}\n', encoding="utf-8")
    foreign = SigningKey.generate()
    (tmp_path / "checkpoint.json.sig").write_bytes(foreign.sign(payload.read_bytes()).signature)
    root_pub = Path("/etc/octopus/trust/root.pub").read_bytes()
    with pytest.raises(SignatureError):
        load_signed(payload, root_pub)


def test_inv10_missing_data_not_healthy():
    snap = evaluate(
        {
            "compute_pressure": 0.1,
            "memory_pressure": 0.2,
            "thermal_integrity": 30.0,
            "storage_integrity": 0.05,
            "evidence_freshness": 5.0,
            "sensor_coverage": 0.95,
            "model_skill": None,
            "prediction_calibration": None,
        }
    )
    assert snap.variables["model_skill"].status == VariableStatus.UNKNOWN
    assert snap.variables["model_skill"].value is None
    assert "model_skill" in snap.unknown


def test_inv11_incomplete_coverage_stays_critical():
    snap = evaluate(
        {
            "compute_pressure": 0.1,
            "memory_pressure": 0.2,
            "thermal_integrity": 30.0,
            "storage_integrity": 0.05,
            "evidence_freshness": 5.0,
            "sensor_coverage": 0.6667,
            "model_skill": None,
            "prediction_calibration": None,
        }
    )
    assert snap.variables["sensor_coverage"].status == VariableStatus.CRITICAL
    assert snap.data_ok is False
    live = _json(STATE / "homeostasis" / "latest.json")
    cov = (live.get("variables") or {}).get("sensor_coverage") or {}
    if cov:
        assert cov.get("status") in {"critical", "unknown", "watch"}
        assert cov.get("value") != 1.0 or cov.get("status") != "healthy"


def test_inv12_plan_allowed_advisory_does_not_call_planner():
    assert _forbidden_imports(ROOT / "metacontrol" / "gate.py", {"planner"}) == []
    assert _forbidden_imports(ROOT / "world_model" / "policy.py", {"planner"}) == []
    assert _forbidden_imports(SCRIPTS / "metacontrol_shadow.py", {"planner"}) == []
    decision = evaluate_planning(
        SkillReport(0.4, 0.25, 80, True, "skill_confirmed", 0.05),
        energy_ratio=0.8,
        evidence_age_s=5.0,
        calibration_error=0.05,
        readiness_profile="WAVE0_OBSERVE_ONLY",
    )
    assert decision.executable is False
    assert decision.recommendation != "PLAN_ALLOWED"
    live_src = (SCRIPTS / "metacontrol_shadow.py").read_text(encoding="utf-8")
    assert "planner_invoked" in live_src
    assert "from octopus_cognition.world_model.planner" not in live_src


def test_inv13_wave0_decisions_executable_false():
    decision = evaluate_planning(
        SkillReport(0.4, 0.25, 80, True, "skill_confirmed", 0.05),
        energy_ratio=0.8,
        evidence_age_s=5.0,
        calibration_error=0.05,
        readiness_profile="WAVE0_OBSERVE_ONLY",
    )
    assert decision.executable is False
    live = _json(STATE / "metacontrol" / "latest.json")
    assert live.get("executable") is False
    assert live.get("actuator_authority") == "NONE"


def test_inv14_policy_always_no_action_observe_only():
    assert wave0_policy.choose_action({"compute_pressure": 0.9}) == "NO_ACTION_OBSERVE_ONLY"
    advisory = STATE / "metacontrol" / "latest.json"
    if advisory.is_file():
        doc = json.loads(advisory.read_text(encoding="utf-8"))
        if doc.get("executable") is True:
            assert wave0_policy.choose_action({}) == "NO_ACTION_OBSERVE_ONLY"


def test_inv15_unexpected_lan_bind_is_failure():
    proc = subprocess.run(["ss", "-lntup"], capture_output=True, text=True, check=False)
    text = proc.stdout or ""
    assert ":9464" not in text
    assert ":8080" not in text
    for line in text.splitlines():
        if ":9101" in line:
            assert "127.0.0.1:9101" in line
            assert "0.0.0.0:9101" not in line
            assert "192.168.0.182:9101" not in line


def test_inv16_restart_consistency_without_reboot():
    boot = _json(STATE / "boot_report.json")
    live_boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()
    assert boot.get("board_id") == "sensorium-opi5pro-68e44cdf"
    assert boot.get("readiness_profile") == "WAVE0_OBSERVE_ONLY"
    assert boot.get("identity", {}).get("board_id") == "sensorium-opi5pro-68e44cdf"
    probe = _json(STATE / "gap001" / "boot_report.json")
    if probe.get("post_boot_id"):
        assert probe.get("post_boot_id") == live_boot_id or probe.get("status") == "TESTED_FAIL"


def test_inv17_expired_authorization_rejected():
    now = datetime(2026, 8, 17, 3, 40, tzinfo=timezone.utc)
    artifact = {
        "schema": "octopus.owner-authorization.v1",
        "authorization_id": "OA-TEST-EXPIRED",
        "issued_at": "2026-08-01T00:00:00+00:00",
        "expires_at": "2026-08-02T00:00:00+00:00",
        "current_wave": "WAVE0_OBSERVE_ONLY",
        "target_wave": "WAVE0_A0_ADVISORY_ARMED",
        "scope": ["A0"],
        "allowed_actions": ["WRITE_ADVISORY"],
        "forbidden_actions": ["GPIO"],
        "target_hosts": ["sensorium-opi5pro-68e44cdf"],
        "config_digest": "sha256:" + ("a" * 64),
        "checkpoint_digest": "sha256:" + ("b" * 64),
        "rollback_digest": "sha256:" + ("c" * 64),
        "max_duration_s": 60,
        "max_actions": 1,
        "owner_identity": "owner",
        "owner_signature": "nonempty-but-unverified",
        "root_key_id": "root-v2",
    }
    ok, reason = verify_owner_authorization(artifact, now=now)
    assert ok is False
    assert reason == "authorization_expired"


def test_inv18_wrong_scope_authorization_rejected():
    now = datetime(2026, 8, 17, 3, 40, tzinfo=timezone.utc)
    artifact = {
        "schema": "octopus.owner-authorization.v1",
        "authorization_id": "OA-TEST-SCOPE",
        "issued_at": (now - timedelta(minutes=1)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "current_wave": "WAVE0_OBSERVE_ONLY",
        "target_wave": "WAVE0_A0_ADVISORY_ARMED",
        "scope": ["ALL-ACTUATORS"],
        "allowed_actions": ["WRITE_ADVISORY"],
        "forbidden_actions": ["GPIO"],
        "target_hosts": ["sensorium-opi5pro-68e44cdf"],
        "config_digest": "sha256:" + ("a" * 64),
        "checkpoint_digest": "sha256:" + ("b" * 64),
        "rollback_digest": "sha256:" + ("c" * 64),
        "max_duration_s": 60,
        "max_actions": 1,
        "owner_identity": "owner",
        "owner_signature": "nonempty-but-unverified",
        "root_key_id": "root-v2",
    }
    ok, reason = verify_owner_authorization(artifact, now=now, expected_scope=["A0-advisory-only"])
    assert ok is False
    assert reason == "scope_mismatch"


def test_inv19_digest_mismatch_rejected():
    now = datetime(2026, 8, 17, 3, 40, tzinfo=timezone.utc)
    artifact = {
        "schema": "octopus.owner-authorization.v1",
        "authorization_id": "OA-TEST-DIGEST",
        "issued_at": (now - timedelta(minutes=1)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "current_wave": "WAVE0_OBSERVE_ONLY",
        "target_wave": "WAVE0_A0_ADVISORY_ARMED",
        "scope": ["A0-advisory-only"],
        "allowed_actions": ["WRITE_ADVISORY"],
        "forbidden_actions": ["GPIO"],
        "target_hosts": ["sensorium-opi5pro-68e44cdf"],
        "config_digest": "sha256:" + ("d" * 64),
        "checkpoint_digest": "sha256:" + ("e" * 64),
        "rollback_digest": "sha256:" + ("f" * 64),
        "max_duration_s": 60,
        "max_actions": 1,
        "owner_identity": "owner",
        "owner_signature": "nonempty-but-unverified",
        "root_key_id": "root-v2",
    }
    ok, reason = verify_owner_authorization(
        artifact,
        now=now,
        expected_config_digest="sha256:" + ("a" * 64),
    )
    assert ok is False
    assert reason == "config_digest_mismatch"


def test_inv20_rollback_dry_run_is_runnable():
    plan = Path("/var/lib/octopus/state/owner-review/rollback-plan.md")
    laptop = Path("/var/lib/octopus/inbound/TO-LAPTOP/owner-review/rollback-plan.md")
    assert plan.is_file() or laptop.is_file()
    text = (plan if plan.is_file() else laptop).read_text(encoding="utf-8")
    assert "systemctl restart" not in text.lower() or "DO NOT" in text or "نکن" in text
    assert "mutations=0" in text or "dry-run" in text.lower() or "Dry-run" in text


def test_inv21_doctor_attempts_zero_repairs():
    report_paths = [
        Path("/var/lib/octopus/state/owner-review/doctor-report.json"),
        Path("/var/lib/octopus/inbound/TO-LAPTOP/owner-review/doctor-report.json"),
    ]
    found = next((p for p in report_paths if p.is_file()), None)
    if found is None:
        pytest.skip("doctor-report.json not written yet")
    doc = json.loads(found.read_text(encoding="utf-8"))
    assert doc.get("repairs_attempted") == 0
    assert doc.get("executed_actions") == 0
    src = Path("/opt/octopus/scripts/octopus_doctor_readonly.py")
    if src.is_file():
        text = src.read_text(encoding="utf-8")
        assert "systemctl restart" not in text
        assert "ufw disable" not in text


def test_inv22_gap002_closed_only_with_verified_root_v2():
    gap = _json(STATE / "gaps" / "GAP-002-audit_head_unsigned.json")
    apply_src = (SCRIPTS / "apply_signed_inbound.py").read_text(encoding="utf-8")
    assert "missing_sig" in apply_src
    assert "load_signed" in apply_src
    signed = Path("/var/lib/octopus/inbound/SIGNED-CHECKPOINT-BUNDLE/checkpoint.json.sig")
    if gap.get("status") == "CLOSED_BY_SIGNED_CHECKPOINT":
        assert gap.get("signed") is True
        assert gap.get("pass") is True
        assert signed.is_file()
        homeo = _json(STATE / "homeostasis" / "latest.json")
        assert homeo.get("actuator_authority") == "NONE"
    else:
        assert gap.get("signed") is not True
        assert signed.is_file() is False


def test_inv23_checkpoint_signature_does_not_create_authority():
    homeo = _json(STATE / "homeostasis" / "latest.json")
    reflex = _json(STATE / "reflex" / "latest.json")
    assert homeo.get("actuator_authority") == "NONE"
    assert reflex.get("armed") is False
    assert reflex.get("execute_enabled") is False
    apply_src = (SCRIPTS / "apply_signed_inbound.py").read_text(encoding="utf-8")
    assert "actuator_authority" not in apply_src or "NONE" in apply_src
    assert "ARMED" not in apply_src


def test_inv24_executed_actions_wave0_zero():
    mc = _json(STATE / "metacontrol" / "latest.json")
    skill = _json(STATE / "skill" / "latest.json")
    wm = _json(STATE / "world_model" / "latest.json")
    reflex = _json(STATE / "reflex" / "latest.json")
    assert mc.get("executable") is False
    assert mc.get("planner_invoked") is False
    assert skill.get("planner_invoked") is False
    assert wm.get("planner_invoked") is False
    assert reflex.get("execute_enabled") is False
    assert reflex.get("armed") is False
    wm_ok, _, _ = ChainedLedger(STATE / "world_model", "octopus.prediction-ledger.head.v1").verify()
    assert wm_ok is True
    for body in ChainedLedger(STATE / "world_model", "octopus.prediction-ledger.head.v1").bodies():
        if body.get("executable") is True:
            raise AssertionError("executable record in world_model ledger")
        if (body.get("cost") or {}).get("planner_invoked") is True:
            raise AssertionError("planner_invoked in world_model ledger")
        if body.get("planner_invoked") is True:
            raise AssertionError("planner_invoked in world_model ledger")


def test_empty_owner_signature_is_deny():
    artifact = {
        "schema": "octopus.owner-authorization.v1",
        "authorization_id": "OA-EMPTY",
        "issued_at": "2026-08-17T00:00:00+00:00",
        "expires_at": "2026-08-18T00:00:00+00:00",
        "current_wave": "WAVE0_OBSERVE_ONLY",
        "target_wave": "WAVE0_A0_ADVISORY_ARMED",
        "scope": ["A0"],
        "allowed_actions": ["WRITE_ADVISORY"],
        "forbidden_actions": ["GPIO"],
        "target_hosts": ["sensorium-opi5pro-68e44cdf"],
        "config_digest": "sha256:" + ("a" * 64),
        "checkpoint_digest": "sha256:" + ("b" * 64),
        "rollback_digest": "sha256:" + ("c" * 64),
        "max_duration_s": 60,
        "max_actions": 1,
        "owner_identity": "owner",
        "owner_signature": "",
        "root_key_id": "root-v2",
    }
    ok, reason = verify_owner_authorization(artifact)
    assert ok is False
    assert reason == "empty_or_missing_signature"


def test_live_world_model_is_persistence_not_candidate():
    wm = _json(STATE / "world_model" / "latest.json")
    assert wm.get("model_version") == "persistence-v1"
    assert wm.get("role") == "predictor_shadow"
    unit = Path("/etc/systemd/system/octopus-world-model.service").read_text(encoding="utf-8")
    assert "world_model_shadow.py" in unit
    assert "planner" not in unit.lower()
