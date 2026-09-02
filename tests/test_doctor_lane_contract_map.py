# Lane LB tests — contract map, prescription shape, experiment validation,
# refusal to execute untrusted code, receipts (scenarios 11, 12 + contract).
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ofn.doctor import contract_map, validate_prescription  # noqa: E402
from ofn.doctor.contract_map import (  # noqa: E402
    CONTRACT_SOURCE_SHA256, REQUIREMENTS, SandboxNotVerifiedError,
    execute_mutation, extract_gaps, load_contract, requirement_stats,
)
from ofn.doctor.miniyaml import MiniYAMLError, loads  # noqa: E402
from ofn.doctor.receipts import ReceiptLog, sha256_file  # noqa: E402


# ───────────────────────────── miniyaml + contract ─────────────────────────────

def test_miniyaml_parses_the_real_contract():
    c = load_contract()
    assert c["schema"] == "lab-doctor-contract.v1"
    assert c["doctor"]["diagnosis_observed"]["output_shape"]["bottleneck"] == "string"
    assert len(c["flow"]) == 12
    assert c["gates"]["gate_3"]["name"] == "hard_lab_sandbox"
    assert c["lab"]["hard_sandbox_requirements"]["cpu_limit"]["required"] is True
    assert c["experiment_contract"]["required_before_execution"]["risk_budget"][
        "max_external_effects"] == 0


def test_miniyaml_inline_list_and_types():
    doc = loads("a: [x, y]\nb: 3\nc: true\nd:\n  - one\n  - two\n")
    assert doc["a"] == ["x", "y"]
    assert doc["b"] == 3 and doc["c"] is True
    assert doc["d"] == ["one", "two"]


def test_miniyaml_fails_closed():
    with pytest.raises(MiniYAMLError):
        loads("a: 1\na: 2")                     # duplicate key
    with pytest.raises(MiniYAMLError):
        loads("a:\n\tb: 1")                     # tab
    with pytest.raises(MiniYAMLError):
        loads("a: {x: 1}")                      # inline mapping not in subset
    with pytest.raises(MiniYAMLError):
        loads("a: 1\n  b: 2")                   # stray indent


def test_bundled_contract_is_byte_identical_to_source():
    bundled = Path(contract_map.__file__).with_name("contract") / "LAB-DOCTOR-CONTRACT.yaml"
    assert sha256_file(bundled) == CONTRACT_SOURCE_SHA256


# ───────────────────────────── requirement map ─────────────────────────────

def test_every_requirement_is_fully_mapped():
    for r in REQUIREMENTS:
        assert r.req_id and r.contract_path and r.requirement
        assert r.code_symbol and r.test_symbol and r.failure_mode and r.receipt
        assert r.status in ("IMPLEMENTED", "DELEGATED_LANE_C", "BACKLOG_ITEM")


def test_requirement_stats_sum_to_total():
    stats = requirement_stats()
    assert stats["total"] == len(REQUIREMENTS)
    assert sum(v for k, v in stats.items() if k != "total") == len(REQUIREMENTS)


def test_mapped_tests_exist_on_disk():
    tests_dir = Path(__file__).parent
    for r in REQUIREMENTS:
        if r.status == "IMPLEMENTED":
            module, _, test_name = r.test_symbol.partition("::")
            fname = module.replace(".", "/") + ".py"
            fpath = tests_dir / Path(fname).name
            assert fpath.exists(), f"missing test file for {r.req_id}: {fname}"
            body = fpath.read_text(encoding="utf-8")
            assert f"def {test_name}(" in body, \
                f"{r.req_id}: test {test_name} not found in {fpath.name}"


def test_extract_gaps_finds_the_known_missing_organs():
    gaps = extract_gaps(load_contract())
    items = {g["item"] for g in gaps}
    assert any("novelty_gate" in i for i in items)
    assert any("hard_sandbox" in i for i in items)
    assert all(g["status"] for g in gaps)


# ───────────────────────────── refusal + validation ─────────────────────────────

def test_untrusted_execution_is_refused():
    with pytest.raises(SandboxNotVerifiedError) as ei:
        execute_mutation("print('trust me')")
    assert "NOT_A_VERIFIED_HARD_SANDBOX" in str(ei.value)


def test_self_promotion_bans_are_enforced():
    bans = contract_map.SELF_JUDGMENT_BANS
    assert "self-promotion to VERIFIED" in bans
    # the lane may not raise its own evidence grade: stats come from measurement only
    stats = requirement_stats()
    implemented = stats.get("IMPLEMENTED", 0)
    assert implemented == sum(1 for r in REQUIREMENTS if r.status == "IMPLEMENTED")


def test_prescription_shape():
    good = {
        "observed_symptom": "s", "causal_hypothesis": "h",
        "proposed_mutation": {"target_path": "a/b.py", "target_zone": "B1",
                              "description": "d"},
        "falsification_condition": "f", "expected_cost": {"tokens": 10, "calls": 1,
                                                          "risk_weight": 0.1, "time_s": 5},
        "rollback": "r", "evidence_refs": ["e1"],
    }
    assert validate_prescription(good) == []
    bad = dict(good)
    bad["proposed_mutation"] = {"target_path": "x", "target_zone": "B9", "description": ""}
    bad["rollback"] = ""
    v = validate_prescription(bad)
    assert any("target_zone" in x for x in v)
    assert any("rollback" in x for x in v)
    assert validate_prescription({}) != []


def _exp(**over):
    base = {
        "experiment_id": "E-1", "hypothesis": "h", "frozen_metric": "m",
        "baseline_ref": "b", "candidate_ref": "c", "control_or_placebo": "p",
        "target_zone": "B1",
        "risk_budget": {"tokens": 100, "calls": 1, "risk_weight": 0.5,
                        "max_external_effects": 0},
        "timeout_s": 30, "stop_condition": "s", "rollback": "r",
        "replay_recipe": "x", "falsifier": "f", "independent_judge": "j",
        "expected_receipts": ["receipt.jsonl"],
    }
    base.update(over)
    return base


def test_validate_experiment():
    assert contract_map.validate_experiment(_exp()) == []
    assert any("max_external_effects" in v for v in
               contract_map.validate_experiment(
                   _exp(risk_budget={"tokens": 1, "calls": 1, "risk_weight": 1,
                                     "max_external_effects": 2})))
    assert any("timeout_s" in v for v in contract_map.validate_experiment(_exp(timeout_s=0)))
    assert any("rollback" in v for v in contract_map.validate_experiment(_exp(rollback="")))
    assert any("target_zone" in v for v in contract_map.validate_experiment(_exp(target_zone="B9")))
    assert any("falsifier" in v for v in contract_map.validate_experiment(_exp(falsifier="")))


# ───────────────────────────── receipts (11, 12) ─────────────────────────────

def test_11_receipt_is_valid_parseable_jsonl(tmp_path):
    log = ReceiptLog(tmp_path / "receipt.jsonl")
    log.write("round_start", vault_root="X")
    log.write_manifest("integrity_before", {"a.md": "aa", "b.md": "bb"})
    log.write("finding", finding_id="F-1")
    report = log.verify()
    assert report == {"lines": 3, "bad_lines": [], "valid": True}
    assert len(log.read_all()) == 3


def test_12_tampered_line_is_detected(tmp_path):
    log = ReceiptLog(tmp_path / "receipt.jsonl")
    log.write("round_start", vault_root="X")
    log.write("finding", finding_id="F-1", severity="HIGH")
    p = tmp_path / "receipt.jsonl"
    text = p.read_text(encoding="utf-8").replace("HIGH", "LOW")   # tamper
    p.write_text(text, encoding="utf-8")
    report = ReceiptLog(p).verify()
    assert report["valid"] is False
    assert report["bad_lines"]
