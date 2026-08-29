from octopus_cognition.milestone_gate import apply_prerequisites, evaluate_gate, gate, unmet_ids


def test_gate_pass_only_when_all_match_and_evidence_present():
    conditions = [
        {"id": "a", "expected": "PASS", "observed": "PASS", "evidence": "file-a"},
        {"id": "b", "expected": 0, "observed": 0, "evidence": "file-b"},
    ]
    assert gate(conditions) == "PASS"
    assert unmet_ids(conditions) == []


def test_missing_evidence_is_blocked():
    conditions = [
        {"id": "doctor_pass", "expected": "PASS", "observed": "PASS", "evidence": None},
    ]
    assert gate(conditions) == "BLOCKED"
    assert unmet_ids(conditions) == ["doctor_pass"]


def test_mismatch_is_blocked():
    conditions = [
        {"id": "gap_001_closed", "expected": "CLOSED_TESTED_PASS", "observed": "OPEN", "evidence": "probe"},
    ]
    assert gate(conditions) == "BLOCKED"


def test_m1_hard_blocks_m2_even_if_m2_conditions_would_pass():
    chained = apply_prerequisites({"M0_FREEZE": "BLOCKED", "M1_INTEGRITY": "BLOCKED", "M2_CANDIDATE": "PASS"})
    assert chained["M2_CANDIDATE"] == "BLOCKED"
    chained_ok = apply_prerequisites({"M1_INTEGRITY": "PASS", "M2_CANDIDATE": "PASS"})
    assert chained_ok["M2_CANDIDATE"] == "PASS"


def test_m1_blocked_forbids_authority_change():
    doc = {
        "milestone": "M1_INTEGRITY",
        "blocking_conditions": [
            {"id": "doctor_pass", "expected": "PASS", "observed": "FAIL", "evidence": None},
        ],
        "authority_change_permitted": True,
    }
    out = evaluate_gate(doc)
    assert out["gate_result"] == "BLOCKED"
    assert out["authority_change_permitted"] is False
