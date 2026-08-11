#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_registry_semantic_validator.py — Stage 2–3 semantic rules (no WORKLOCK)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_ROOT = _OPS.parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "tests"))
sys.path.insert(0, str(_OPS / "scripts"))

import harness  # noqa: E402
import yaml  # noqa: E402

from validate_signals_registry import validate_registry  # noqa: E402

DATA = _ROOT / "architecture" / "signals-registry.yaml"


def _base():
    return yaml.safe_load(DATA.read_text(encoding="utf-8"))


def _report(data: dict) -> dict:
    raw = yaml.safe_dump(data, sort_keys=False).encode("utf-8")
    return validate_registry(data, raw_yaml=raw, root=_ROOT)


def t_realistic_yaml_passes():
    r = validate_registry(root=_ROOT)
    assert r["ok"], r["errors"]
    assert r["signal_count"] >= 8
    assert r["registry_digest_sha256"]
    assert "timestamp" in r


def t_duplicate_id_fails():
    data = _base()
    data["signals"].append(copy.deepcopy(data["signals"][0]))
    r = _report(data)
    assert r["ok"] is False
    assert any("duplicate_id" in e for e in r["errors"]), r["errors"]


def t_diagnostic_may_gate_fails():
    data = _base()
    for s in data["signals"]:
        if s["role"] == "diagnostic":
            s["authority"]["may_gate"] = True
            break
    r = _report(data)
    assert r["ok"] is False
    assert any("may_gate" in e for e in r["errors"]), r["errors"]


def t_spec_not_built_with_code_path_fails():
    data = _base()
    for s in data["signals"]:
        if s["id"] == "chrono-rhythm-cr-b0":
            s["equation"]["implementation_path"] = "_ops/wiring.py"
            break
    r = _report(data)
    assert r["ok"] is False
    assert any("SPEC_NOT_BUILT" in e for e in r["errors"]), r["errors"]


def t_shadow_effect_without_rollback_fails():
    data = _base()
    for s in data["signals"]:
        if s["id"] == "spectral-criticality-v2":
            s["safeguards"].pop("rollback_flag", None)
            break
    r = _report(data)
    assert r["ok"] is False
    assert any("rollback_flag" in e for e in r["errors"]), r["errors"]


def t_armed_without_seven_days_fails():
    data = _base()
    for s in data["signals"]:
        if s["id"] == "bcm-stabilizer":
            s["truth_status"] = "ARMED"
            s["evidence_level"] = "ARMED"
            s["evidence"]["shadow_window_days"] = 2
            s["evidence"]["tests"] = ["test_bcm_forgetting.py"]
            break
    r = _report(data)
    assert r["ok"] is False
    assert any("shadow_window_days" in e for e in r["errors"]), r["errors"]


def t_neural_apply_enabled_true_fails():
    data = _base()
    for s in data["signals"]:
        if s["id"] == "neural-learned-apply":
            s["safeguards"]["production_apply_enabled"] = True
            break
    r = _report(data)
    assert r["ok"] is False
    assert any("production_apply_enabled" in e for e in r["errors"]), r["errors"]


def t_missing_implementation_path_fails():
    data = _base()
    for s in data["signals"]:
        if s["id"] == "bcm-stabilizer":
            s["equation"]["implementation_path"] = "_ops/neural/does-not-exist.py"
            break
    r = _report(data)
    assert r["ok"] is False
    assert any("missing_implementation_path" in e for e in r["errors"]), r["errors"]


def t_missing_test_path_fails():
    data = _base()
    for s in data["signals"]:
        if s["id"] == "bcm-stabilizer":
            s["evidence"]["tests"] = ["test_this_file_does_not_exist_zz.py"]
            break
    r = _report(data)
    assert r["ok"] is False
    assert any("missing_test_path" in e for e in r["errors"]), r["errors"]


def t_report_has_digest_and_sha_fields():
    r = validate_registry(root=_ROOT)
    assert "registry_digest_sha256" in r
    assert "git_sha" in r
    assert "signal_count" in r
    assert "timestamp" in r
    assert isinstance(r["errors"], list)
    assert isinstance(r["warnings"], list)


CHECKS = [
    ("realistic-pass", t_realistic_yaml_passes),
    ("duplicate-id-fail", t_duplicate_id_fails),
    ("diagnostic-may-gate-fail", t_diagnostic_may_gate_fails),
    ("spec-with-path-fail", t_spec_not_built_with_code_path_fails),
    ("shadow-no-rollback-fail", t_shadow_effect_without_rollback_fails),
    ("armed-no-7d-fail", t_armed_without_seven_days_fails),
    ("neural-apply-true-fail", t_neural_apply_enabled_true_fails),
    ("missing-impl-fail", t_missing_implementation_path_fails),
    ("missing-test-fail", t_missing_test_path_fails),
    ("report-fields", t_report_has_digest_and_sha_fields),
]

failed = harness.run(CHECKS)
sys.exit(1 if failed else 0)
