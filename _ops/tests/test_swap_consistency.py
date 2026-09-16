# -*- coding: utf-8 -*-
"""تستهای ابزار سنجش سازگاری جایگاه — گیت ماشینی فاز ۱ (ابزار سنجش)."""
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "measure"))

from measure.swap_consistency import (  # noqa: E402
    SwapConfig, ReliabilityGate, classify_swap, swap_consistency_rate,
    unanimity_p_value, min_k_for_alpha, required_attempts, wilson_ci,
    void_breakdown, receipt,
)


def test_unanimity_values_match_review():
    assert abs(unanimity_p_value(5) - 0.0625) < 1e-12
    assert abs(unanimity_p_value(9) - 0.00390625) < 1e-12
    assert abs(unanimity_p_value(11) - 0.0009765625) < 1e-12


def test_min_k_for_alpha():
    assert min_k_for_alpha(0.05) == 6
    assert min_k_for_alpha(0.01) == 8
    assert min_k_for_alpha(0.005) == 9   # پیشنهاد بازبینی: K=9 حداقل


def test_wilson_zero_of_twenty_upper_about_16pct():
    lo, hi = wilson_ci(0, 20)
    assert lo == 0.0
    assert abs(hi - 0.1611) < 0.01


def test_probability_of_zero_voids_at_13_56pct():
    p = (1 - 8 / 59) ** 20
    assert abs(p - 0.0542) < 0.002


def test_required_attempts_95_percent_not_expectation():
    # 30/(1-p) ≈ 35 است ولی برای 95٪ اطمینان 39 لازم است.
    assert required_attempts(30, 8 / 59) == 39
    assert required_attempts(30, 0.245) == 46
    assert required_attempts(9, 8 / 59) == 13
    # انتظاری هرگز کافی نیست:
    assert required_attempts(30, 8 / 59) > math.ceil(30 / (1 - 8 / 59))


def test_gate_underpowered_k5_unresolved():
    g = ReliabilityGate().evaluate(rs_ab=1.0, k_ab=5, rs_ba=0.6, k_ba=5)
    assert g["verdict"] == "RANDOMNESS_UNRESOLVED"
    assert g["ok"] is False
    assert g["k_min"] >= 9


def test_gate_k9_unanimous_ab_stable_ba_unstable():
    g = ReliabilityGate().evaluate(rs_ab=1.0, k_ab=9, rs_ba=0.6, k_ba=9)
    assert g["verdict"] == "INSTABILITY_SIGNIFICANT"
    assert g["ok"] is True


def test_classify_bias_only_after_gate():
    # K=5 با RS=1.0 → گیت رد → UNRESOLVED (نه bias)
    r = classify_swap(5, 5, 0, 5)
    assert r["verdict"] == "RANDOMNESS_UNRESOLVED"
    # K=9 با RS_AB=1.0 و RS_BA=0.0 → bias واقعی پس از گیت
    r2 = classify_swap(9, 9, 0, 9)
    assert r2["verdict"] in ("SECOND_POSITION_BIAS", "FIRST_POSITION_BIAS")


def test_consistency_rate_label_measured_never_verified():
    r = swap_consistency_rate(8, 9)
    assert r["label"] == "MEASURED"
    assert r["grade"] == "MEASURED"
    assert "VERIFIED" not in json_dump(r)


def test_void_breakdown_separates_categories():
    rows = [
        {"void_reason": "format: judge returned unparsable json"},
        {"void_reason": "judge timeout"},
        {"void_reason": "provider upstream error"},
        {"void_reason": "fallback also failed"},
        {"void_reason": "unknown"},
    ]
    b = void_breakdown(rows)
    assert b["format_void"] == 1
    assert b["judge_void"] == 1
    assert b["provider_void"] == 1
    assert b["fallback_void"] == 1
    assert b["other_void"] == 1
    assert b["total_void"] == 5


def test_receipt_is_replayable():
    a = receipt(caller="test", inputs={"k": 9}, seed="s1")
    b = receipt(caller="test", inputs={"k": 9}, seed="s1")
    assert a["input_hash"] == b["input_hash"]
    assert a["judge_contract_version"]
    assert "ts_iso" in a


def test_config_is_frozen():
    cfg = SwapConfig()
    try:
        cfg.rs_min = 0.0
        raised = False
    except Exception:
        raised = True
    assert raised


def json_dump(o):
    import json
    return json.dumps(o, ensure_ascii=False)
