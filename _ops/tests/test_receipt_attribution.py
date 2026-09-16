# -*- coding: utf-8 -*-
"""T50 (دستور مالک #۸ §۵): فیلدهای انتساب رسید — task_id/run_id/UNATTRIBUTED.

additive: رسید بدون task_id همچنان ساخته می‌شود ولی صریحاً UNATTRIBUTED؛
رسید با task_id برچسب TASK می‌گیرد. رفتار قبلی (بدون فیلدها) تغییر نکرده —
فقط فیلد اضافه شده."""
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS / "cortex"))

from cost_receipt import CostReceiptAdapter  # noqa: E402


def _build(adapter=None, **kw):
    a = adapter or CostReceiptAdapter()
    base = dict(trace_id="t-test-1", provider="deepseek", model="test-deepseek-v4",
                ts_req="2026-08-20T04:00:00+00:00", ts_resp="2026-08-20T04:00:01+00:00",
                budget_before_aud=1.0, free_tier=True)
    base.update(kw)
    return a.build(**base)


def test_receipt_without_task_is_unattributed():
    r = _build()
    assert r["task_id"] == "" and r["run_id"] == ""
    assert r["attribution"] == "UNATTRIBUTED"


def test_receipt_with_task_and_run():
    r = _build(task_id="k9-triple-judge", run_id="run-20260820A")
    assert r["task_id"] == "k9-triple-judge"
    assert r["run_id"] == "run-20260820A"
    assert r["attribution"] == "TASK"


def test_legacy_fields_untouched():
    r = _build(task_id="x")
    for legacy in ("schema", "trace_id", "provider", "exact_model",
                   "request_timestamp", "response_timestamp", "budget_before_aud",
                   "receipt_status", "cost_method"):
        assert legacy in r, f"legacy field lost: {legacy}"
    assert r["schema"] == "cost-receipt/1"


def test_idempotency_still_works_with_attribution():
    a = CostReceiptAdapter()
    r1 = _build(a, task_id="t1", input_sha256="abc")
    r2 = _build(a, task_id="t1", input_sha256="abc")
    assert r1["trace_id"] == r2["trace_id"] and r2["attribution"] == "TASK"
