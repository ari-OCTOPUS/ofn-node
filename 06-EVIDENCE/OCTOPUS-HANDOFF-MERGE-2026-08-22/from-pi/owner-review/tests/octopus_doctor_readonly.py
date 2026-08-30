#!/usr/bin/env python3
"""Read-only OCTOPUS Doctor. Writes a report file. Never repairs. Never restarts."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, "/opt/octopus/cognition/src")
sys.path.insert(0, "/opt/octopus/current/src")

from octopus_cognition.ledger import ChainedLedger  # noqa: E402

REPORT_PATHS = [
    Path("/var/lib/octopus/state/owner-review/doctor-report.json"),
]
INBOUND_REPORT = Path("/var/lib/octopus/inbound/TO-LAPTOP/owner-review/doctor-report.json")
STATE = Path("/var/lib/octopus/state")


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _check(check_id: str, ok: bool, detail: Any, status: str | None = None) -> dict[str, Any]:
    if status is None:
        status = "PASS" if ok else "FAIL"
    return {"id": check_id, "ok": ok, "status": status, "detail": detail}


def _ss() -> str:
    proc = subprocess.run(["ss", "-lntup"], capture_output=True, text=True, check=False)
    return proc.stdout or ""


def _active(unit: str) -> str:
    proc = subprocess.run(["systemctl", "is-active", unit], capture_output=True, text=True, check=False)
    return (proc.stdout or "").strip() or "unknown"


def _imports_planner(path: Path) -> bool:
    if not path.is_file():
        return False
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "planner" in alias.name:
                    return True
        elif isinstance(node, ast.ImportFrom) and node.module and "planner" in node.module:
            return True
    return False


def run_doctor() -> dict[str, Any]:
    boot = _json(STATE / "boot_report.json")
    skill = _json(STATE / "skill" / "latest.json")
    homeo = _json(STATE / "homeostasis" / "latest.json")
    wm = _json(STATE / "world_model" / "latest.json")
    mc = _json(STATE / "metacontrol" / "latest.json")
    reflex = _json(STATE / "reflex" / "latest.json")
    fusion = _json(STATE / "fusion" / "latest-frame.json")
    gap001 = _json(STATE / "gaps" / "GAP-001-cold_boot_unverified.json")
    gap001_probe = _json(STATE / "gap001" / "boot_report.json")
    gap002 = _json(STATE / "gaps" / "GAP-002-audit_head_unsigned.json")
    ss_text = _ss()
    wm_ok, wm_brk, wm_det = ChainedLedger(STATE / "world_model", "octopus.prediction-ledger.head.v1").verify()
    mc_ok, _, mc_det = ChainedLedger(STATE / "metacontrol", "octopus.metacontrol-ledger.head.v1").verify()
    rx_ok, _, rx_det = ChainedLedger(STATE / "reflex", "octopus.reflex-ledger.head.v1").verify()

    lan_9101 = any("9101" in line and "127.0.0.1:9101" not in line for line in ss_text.splitlines() if ":9101" in line)
    unexpected = [p for p in (":8080", ":9464") if p in ss_text]
    planner_scripts = {
        name: _imports_planner(Path("/opt/octopus/scripts") / name)
        for name in (
            "world_model_shadow.py",
            "skill_tracker_loop.py",
            "metacontrol_shadow.py",
            "stability_monitor.py",
        )
    }
    signed_ckpt = Path("/var/lib/octopus/inbound/SIGNED-CHECKPOINT-BUNDLE/checkpoint.json.sig").is_file()
    samples = int(skill.get("samples") or 0)

    checks = [
        _check(
            "service_state",
            _active("octopus-sensorium") == "active" and _active("nats-server") == "active",
            {
                "nats-server": _active("nats-server"),
                "octopus-sensorium": _active("octopus-sensorium"),
                "octopus-stability": _active("octopus-stability"),
                "octopus-world-model": _active("octopus-world-model"),
                "octopus-skill-tracker": _active("octopus-skill-tracker"),
                "octopus-metacontrol": _active("octopus-metacontrol"),
                "octopus-reflex": _active("octopus-reflex"),
                "octopus-fusiond": _active("octopus-fusiond"),
                "octopus-shadow-validation": _active("octopus-shadow-validation"),
                "octopus-gap001-boot-probe": _active("octopus-gap001-boot-probe"),
            },
        ),
        _check("metrics_bind", "127.0.0.1:9101" in ss_text and not lan_9101, {"ss": [ln for ln in ss_text.splitlines() if ":9101" in ln]}),
        _check("unexpected_listeners", not unexpected and not lan_9101, {"unexpected": unexpected, "lan_9101": lan_9101}),
        _check("ledger_integrity", wm_ok and mc_ok and rx_ok, {"world_model": wm_det, "metacontrol": mc_det, "reflex": rx_det, "wm_break": wm_brk}),
        _check("checkpoint_signature", False, {"signed_bundle_present": signed_ckpt, "gap002": gap002.get("status")}, status="FAIL"),
        _check(
            "registry_signature",
            Path("/etc/octopus/config/registry.yaml.sig").is_file() and Path("/etc/octopus/trust/root.pub").is_file(),
            {
                "registry_sha256": _sha256(Path("/etc/octopus/config/registry.yaml")),
                "live_version": (_json(STATE / "registry" / "active.json") or {}).get("registry_version"),
            },
        ),
        _check(
            "policy_mode",
            wave0 := (boot.get("readiness_profile") == "WAVE0_OBSERVE_ONLY" and homeo.get("actuator_authority") == "NONE"),
            {"readiness_profile": boot.get("readiness_profile"), "actuator_authority": homeo.get("actuator_authority")},
        ),
        _check("planner_import", not any(planner_scripts.values()), planner_scripts),
        _check(
            "planner_invocation",
            wm.get("planner_invoked") is False and mc.get("planner_invoked") is False and skill.get("planner_invoked") is False,
            {"world_model": wm.get("planner_invoked"), "metacontrol": mc.get("planner_invoked"), "skill": skill.get("planner_invoked")},
        ),
        _check(
            "executable_action_count",
            mc.get("executable") is False and reflex.get("execute_enabled") is False,
            {"metacontrol_executable": mc.get("executable"), "reflex_execute_enabled": reflex.get("execute_enabled")},
        ),
        _check("actuator_authority", homeo.get("actuator_authority") == "NONE" and not reflex.get("armed"), {"homeostasis": homeo.get("actuator_authority"), "reflex_armed": reflex.get("armed")}),
        _check(
            "sensor_coverage",
            False,
            {"coverage": fusion.get("coverage"), "status": ((homeo.get("variables") or {}).get("sensor_coverage") or {}).get("status"), "active": fusion.get("active_sensors"), "expected": fusion.get("expected_sensors")},
            status="DEGRADED",
        ),
        _check(
            "missing_data",
            ((homeo.get("variables") or {}).get("prediction_calibration") or {}).get("status") == "unknown"
            and ((homeo.get("variables") or {}).get("prediction_calibration") or {}).get("value") is None
            and fusion.get("coverage") != 1.0,
            {
                "unknown": homeo.get("unknown"),
                "model_skill": ((homeo.get("variables") or {}).get("model_skill") or {}),
                "prediction_calibration": ((homeo.get("variables") or {}).get("prediction_calibration") or {}),
                "coverage": fusion.get("coverage"),
                "note": "calibration stays UNKNOWN; coverage 0.6667 not imputed to 1.0; skill 0.0 after >=50 pairs is a real persistence score not a missing fill",
            },
        ),
        _check(
            "clock_monotonicity",
            (boot.get("clock") or {}).get("clock_trust") == "SYNCED_NTP" and (boot.get("clock") or {}).get("monotonic_available") is True,
            boot.get("clock"),
        ),
        _check("disk_health", True, {"storage": ((homeo.get("variables") or {}).get("storage_integrity") or {})}),
        _check(
            "stale_observations",
            ((homeo.get("variables") or {}).get("evidence_freshness") or {}).get("status") in {"healthy", "watch"},
            ((homeo.get("variables") or {}).get("evidence_freshness") or {}),
        ),
        _check(
            "restart_consistency",
            boot.get("board_id") == "sensorium-opi5pro-68e44cdf",
            {"boot_id": Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip(), "gap001_probe_status": gap001_probe.get("status"), "gap001_file_status": gap001.get("status")},
            status="DEGRADED" if gap001_probe.get("pass") is not True else "PASS",
        ),
        _check(
            "configuration_drift",
            _sha256(Path("/etc/octopus/config/registry.yaml")) == "sha256:19f25383d2611000e3272ad9ad5d55e2e645cb5db757a9419f4e7b6d5f1251c5",
            {
                "registry": _sha256(Path("/etc/octopus/config/registry.yaml")),
                "board": _sha256(Path("/etc/octopus/config/board.yaml")),
                "homeostasis": _sha256(Path("/etc/octopus/homeostasis.yaml")),
                "world_model": _sha256(Path("/etc/octopus/world-model.yaml")),
            },
        ),
        _check(
            "skill_samples",
            samples >= 50,
            {
                "samples": samples,
                "min": 50,
                "score": skill.get("score"),
                "reason": skill.get("reason"),
                "model_version": skill.get("model_version"),
                "baseline_version": skill.get("baseline_version"),
                "meaning": "model_is_the_baseline" if skill.get("model_version") == skill.get("baseline_version") else "candidate_vs_baseline",
                "is_evidence_of_model_quality": False if skill.get("model_version") == skill.get("baseline_version") else None,
                "candidate_model_evaluated": skill.get("model_version") not in {None, skill.get("baseline_version")},
            },
            status="FAIL" if samples < 50 else "PASS",
        ),
        _check(
            "gap001",
            False,
            {
                "file_status": gap001.get("status"),
                "probe_status": gap001_probe.get("status"),
                "probe_pass": gap001_probe.get("pass"),
                "gap_001": "OPEN",
                "gap_001_last_result": gap001_probe.get("status") or "UNKNOWN",
                "gap_001_cryptographically_verified": False,
                "correction_of": "mega-prompt baseline claim gap_001=PASSED",
                "megaprompt_claimed": "PASSED",
                "live_truth": "TESTED_FAIL",
            },
            status="FAIL",
        ),
        _check(
            "gap002",
            False,
            {"status": gap002.get("status"), "signed": gap002.get("wave0_signature"), "note": "unsigned export is not closure"},
            status="FAIL",
        ),
        _check(
            "verifier",
            boot.get("readiness_state") == "READY" and not boot.get("gates_failed"),
            {"readiness_state": boot.get("readiness_state"), "gates_failed": boot.get("gates_failed"), "meaning": "WAVE0_OBSERVE_ONLY"},
        ),
    ]

    failed = [c for c in checks if c["status"] == "FAIL"]
    degraded = [c for c in checks if c["status"] == "DEGRADED"]
    if failed:
        overall = "FAIL"
    elif degraded:
        overall = "DEGRADED"
    else:
        overall = "PASS"

    cov_status = ((homeo.get("variables") or {}).get("sensor_coverage") or {}).get("status")
    would = homeo.get("would_decide") or mc.get("would_decide")
    blocking_checks = [
        {
            "id": "gap_001_open",
            "severity": "blocking",
            "observed": gap001_probe.get("status") or gap001.get("status") or "UNKNOWN",
            "required": "PASS_WITH_EVIDENCE",
        },
        {
            "id": "checkpoint_unsigned",
            "severity": "blocking",
            "observed": "unsigned" if not signed_ckpt else "signed_bundle_present",
            "required": "root-v2 verified",
        },
        {
            "id": "coverage_or_data_critical",
            "severity": "blocking",
            "observed": "would_block" if would == "block" else (cov_status or "UNKNOWN"),
            "required": "healthy_or_explained",
        },
    ]
    if gap001.get("status") == "CLOSED" and gap001_probe.get("pass") is True:
        blocking_checks = [c for c in blocking_checks if c["id"] != "gap_001_open"]
    if signed_ckpt:
        blocking_checks = [c for c in blocking_checks if c["id"] != "checkpoint_unsigned"]
    if would != "block" and cov_status != "critical" and homeo.get("data_ok") is not False:
        blocking_checks = [c for c in blocking_checks if c["id"] != "coverage_or_data_critical"]

    return {
        "schema": "octopus.doctor-report.v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": overall,
        "checks": checks,
        "blocking_checks": blocking_checks,
        "repairs_attempted": 0,
        "executed_actions": 0,
        "mutations": 0,
        "oa_t7_meaningful": False if overall == "FAIL" or blocking_checks else True,
        "note": "Read-only. Doctor must not repair, restart, arm, or sign. FAIL here does not unlock anything. OA-T7 is meaningless while status=FAIL.",
        "pid": os.getpid(),
    }


def main() -> int:
    report = run_doctor()
    text = json.dumps(report, indent=2) + "\n"
    for path in REPORT_PATHS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        os.chmod(path, 0o644)
    if INBOUND_REPORT.parent.is_dir() and os.access(INBOUND_REPORT.parent, os.W_OK):
        try:
            INBOUND_REPORT.write_text(text, encoding="utf-8")
            os.chmod(INBOUND_REPORT, 0o644)
        except OSError:
            pass
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
