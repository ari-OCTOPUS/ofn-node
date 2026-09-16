# -*- coding: utf-8 -*-
"""تستهای هارنس ابلیشن — گیت ماشینی فاز ۵."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ablation"))

from ablation.harness import (  # noqa: E402
    swap_gate_ablation, prediction_ledger_ablation, memory_record_ablation,
)


def test_gate_is_causal_on_underpowered_k5():
    r = swap_gate_ablation(5, 5, 3, 5)
    assert r["with_gate_verdict"] == "RANDOMNESS_UNRESOLVED"
    assert r["without_gate_verdict"] == "SECOND_POSITION_BIAS"
    assert r["gate_is_causal"] is True


def test_gate_not_causal_when_consistent():
    r = swap_gate_ablation(9, 9, 9, 9)
    # rs_ab=1.0, rs_ba=1.0: هر دو بالای 0.9 → STABLE؛ بدون گیت هم CONSISTENT
    assert r["with_gate_verdict"] == "CONSISTENT"
    assert r["without_gate_verdict"] == "CONSISTENT"
    assert r["gate_is_causal"] is False


def test_prediction_ledger_delete_aborted():
    import gc, time as _t
    p = Path(__file__).resolve().parent / f"_tmp_abl_ledger_{int(_t.time() * 1000)}.sqlite"
    r = prediction_ledger_ablation(p)
    assert r["delete_aborted"] is True
    assert r["append_only_is_causal"] is True
    # sqlite روی ویندوز فایل را با اتصالِ باز قفل میکند؛ تلاش برای پاکسازی با retry
    for _ in range(5):
        gc.collect()
        try:
            p.unlink()
            break
        except PermissionError:
            _t.sleep(0.2)


def test_memory_ablation_changes_selection():
    recs = [{"id": "a", "score": 0.9}, {"id": "b", "score": 0.5},
            {"id": "c", "score": 0.7}]
    r = memory_record_ablation(recs)
    assert r["selected_before"] == "a"
    assert r["changed"] is True
    assert r["selected_after"] != "a"


def test_memory_ablation_needs_two_records():
    r = memory_record_ablation([{"id": "a", "score": 1.0}])
    assert r["changed"] is False
