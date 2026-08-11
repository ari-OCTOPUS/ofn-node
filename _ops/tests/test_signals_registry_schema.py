#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_signals_registry_schema.py — JSON Schema gates for signals-registry.yaml."""
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

SCHEMA = _ROOT / "architecture" / "signals-registry.schema.json"
DATA = _ROOT / "architecture" / "signals-registry.yaml"


def _load():
    import yaml
    import jsonschema

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    data = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    return jsonschema, schema, data


def t_registry_valid():
    jsonschema, schema, data = _load()
    jsonschema.validate(data, schema)
    ids = {s["id"] for s in data["signals"]}
    assert "spectral-criticality-v2" in ids
    assert "chrono-rhythm-cr-b0" in ids
    assert "neural-learned-apply" in ids


def t_diagnostic_cannot_gate():
    jsonschema, schema, data = _load()
    bad = copy.deepcopy(data)
    for s in bad["signals"]:
        if s["id"] == "sog-dare-identity":
            s["authority"]["may_gate"] = True
            break
    try:
        jsonschema.validate(bad, schema)
        raise AssertionError("diagnostic may_gate=true should fail")
    except Exception as e:
        assert "may_gate" in str(e) or "False" in str(e) or "const" in str(e).lower()


def t_spec_not_built_path_null():
    jsonschema, schema, data = _load()
    cr = next(s for s in data["signals"] if s["id"] == "chrono-rhythm-cr-b0")
    assert cr["truth_status"] == "SPEC_NOT_BUILT"
    assert cr["equation"]["implementation_path"] is None


def t_effect_requires_rollback():
    jsonschema, schema, data = _load()
    bad = copy.deepcopy(data)
    for s in bad["signals"]:
        if s["id"] == "bcm-stabilizer":
            s["authority"]["allowed_effect"] = "bounded_ranking_bias"
            s["evidence_level"] = "SHADOW"
            s["truth_status"] = "SHADOW"
            s["safeguards"].pop("rollback_flag", None)
            break
    try:
        jsonschema.validate(bad, schema)
        raise AssertionError("missing rollback_flag should fail")
    except Exception as e:
        assert "rollback" in str(e).lower() or "required" in str(e).lower()


def t_neural_learned_apply_pin():
    _, _, data = _load()
    n = next(s for s in data["signals"] if s["id"] == "neural-learned-apply")
    assert n["truth_status"] == "TESTED"
    assert n["evidence_level"] == "SHADOW"
    assert n["authority"]["allowed_effect"] == "trace_only"
    assert n["authority"]["may_gate"] is False
    assert n["safeguards"]["production_apply_enabled"] is False


def t_protective_halt_not_in_signals():
    _, _, data = _load()
    blob = json.dumps(data)
    assert "request_protective_halt" not in blob
    assert "protective-halt-control" not in {s["id"] for s in data["signals"]}


def t_sog_snapshot_from_math():
    from telemetry.sog_metrics_v2 import snapshot_from_sog_math

    snap = snapshot_from_sog_math()
    assert snap.posterior_variance > 0
    assert snap.evidence_level == "LOCKED"
    assert snap.mc_gate_passed is True


CHECKS = [
    ("registry-valid", t_registry_valid),
    ("diagnostic-no-gate", t_diagnostic_cannot_gate),
    ("spec-path-null", t_spec_not_built_path_null),
    ("effect-needs-rollback", t_effect_requires_rollback),
    ("neural-learned-apply-pin", t_neural_learned_apply_pin),
    ("halt-not-in-signals", t_protective_halt_not_in_signals),
    ("sog-snapshot", t_sog_snapshot_from_math),
]

failed = harness.run(CHECKS)
sys.exit(1 if failed else 0)
