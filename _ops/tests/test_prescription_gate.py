# -*- coding: utf-8 -*-
"""تستهای گیت تجویز دکتر — گیت ماشینی فاز ۴. سه تجویز؛ حداقل یکی باید ابطال شود."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "doctor_contract"))

from doctor_contract.prescription_gate import validate, run_falsifier, CostCap  # noqa: E402


def _rx(**over):
    rx = {
        "observed_symptom": "نرخ VOID بالا در خط اول داور",
        "causal_hypothesis": "قرارداد میدانهای کلاینت ناقص است",
        "proposed_mutation": {"target_path": "_ops/cortex/client.py",
                              "target_zone": "B2",
                              "description": "فقط content ارسال شود"},
        "falsification_condition": {"metric": "void_rate", "threshold": 0.10,
                                    "direction": "gt"},
        "expected_cost": {"tokens": 500, "calls": 2, "risk_weight": 2.0, "time_s": 60},
        "rollback": "git revert + تست قبلی",
        "evidence_refs": ["voidrate20.json"],
    }
    rx.update(over)
    return rx


def test_valid_prescription_passes():
    r = validate(_rx())
    assert r["valid"] is True
    assert r["zone"] == "B2"


def test_missing_fields_rejected():
    r = validate(_rx(causal_hypothesis=""))
    assert r["valid"] is False
    assert "causal_hypothesis" in r["missing"]


def test_b0_target_goes_to_owner_queue():
    r = validate(_rx(proposed_mutation={
        "target_path": "PRE-0/CONSTITUTION.md", "target_zone": "B0",
        "description": "x"}))
    assert r["valid"] is False
    assert "owner-queue" in r["reason"]


def test_unknown_zone_blocked():
    r = validate(_rx(proposed_mutation={"target_path": "x", "target_zone": "??",
                                        "description": "x"}))
    assert r["valid"] is False
    assert r["reason"].startswith("unknown-zone")


def test_cost_over_cap_rejected():
    r = validate(_rx(expected_cost={"tokens": 999999, "calls": 999, "risk_weight": 99,
                                    "time_s": 99999}), cap=CostCap())
    assert r["valid"] is False
    assert r["reason"] == "cost-over-cap"


def test_falsifier_falsifies_one_of_three():
    rx1 = _rx(falsification_condition={"metric": "void_rate", "threshold": 0.10,
                                       "direction": "gt"})
    rx2 = _rx(falsification_condition={"metric": "hit_rate", "threshold": 0.8,
                                       "direction": "lt"})
    rx3 = _rx(falsification_condition={"metric": "latency_s", "threshold": 5.0,
                                       "direction": "gt"})
    snap = {"void_rate": 0.08, "hit_rate": 0.9, "latency_s": 8.0}
    results = [run_falsifier(rx, snap) for rx in (rx1, rx2, rx3)]
    # rx1: void_rate 0.08 < 0.10 → gt شرط «بیشتر از آستانه» → falsified
    # rx2: hit_rate 0.9 < 0.8؟ نه → pass
    # rx3: latency 8 > 5 → falsified
    assert any(r["falsified"] is True for r in results)
    assert results[1]["falsified"] is False
    assert results[2]["falsified"] is True


def test_falsifier_not_evaluable_when_snapshot_missing():
    r = run_falsifier(_rx())
    assert r["status"] == "not-evaluable"
    assert r["falsified"] is None


def test_doctor_never_patches_nothing_to_test_but_contract_says_lab():
    # گیتِ تجویز فقط مسیر LAB را باز میکند؛ هیچ تابعی در این ماژول فایل نمینویسد.
    import inspect
    src = inspect.getsource(validate) + inspect.getsource(run_falsifier)
    assert "open(" not in src and "write_text" not in src and "Path(" not in src
