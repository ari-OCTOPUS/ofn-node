from octopus_cognition.skill_bootstrap import (
    block_bootstrap_skill,
    complementary_metrics,
    iid_bootstrap_skill,
    m2_evidence_permitted,
)


def _ar_pairs(n: int = 80):
    # Strong serial correlation: candidate_loss slowly wanders.
    pairs = []
    loss = 0.2
    for i in range(n):
        loss = 0.9 * loss + 0.02 * ((i % 7) - 3) / 3.0
        pairs.append({"candidate_loss": abs(loss), "persistence_loss": 0.25})
    return pairs


def test_block_bootstrap_uses_contiguous_blocks():
    pairs = _ar_pairs()
    out = block_bootstrap_skill(pairs, rounds=200, seed=1, block_size=8)
    assert out["method"] == "block_bootstrap"
    assert out["usable"] is True
    assert out["block_size"] == 8
    assert out["lower"] is not None
    assert out["acceptance"] == "REQUIRED_FOR_SERIAL_TELEMETRY"


def test_iid_bootstrap_forbidden_for_acceptance():
    out = iid_bootstrap_skill(_ar_pairs(), rounds=200, seed=1)
    assert out["acceptance"] == "FORBIDDEN_FOR_SERIAL_TELEMETRY"


def test_insufficient_samples_not_usable():
    out = block_bootstrap_skill(
        [{"candidate_loss": 0.1, "persistence_loss": 0.2}] * 10,
        rounds=10,
    )
    assert out["usable"] is False
    assert out["lower"] is None


def test_m1_hard_prerequisite_for_m2_evidence():
    assert m2_evidence_permitted("PASS") is True
    assert m2_evidence_permitted("BLOCKED") is False
    assert m2_evidence_permitted("PARTIAL") is False


def test_complementary_metrics_include_worst_domain():
    out = complementary_metrics(
        [],
        calibration_error=0.02,
        missingness_rate=0.1,
        per_domain_skill={"a": 0.04, "b": -0.01},
    )
    assert out["calibration_error"] == 0.02
    assert out["missingness_rate"] == 0.1
    assert out["per_domain_worst_case_skill"] == -0.01
    assert out["skill_is_not_sole_criterion"] is True
