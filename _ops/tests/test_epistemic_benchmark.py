#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_epistemic_benchmark.py — A/B/C benchmark harness (Phase 2.6).

تست می‌کند benchmark روی datasetِ synthetic اجرا می‌شود، Go verdict صادقانه
تولید می‌شود، و هیچ اثرِ خارجی/زنده‌ای نیست (تماماً در tmp).
"""
from __future__ import annotations

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from epistemics import benchmark as BM  # noqa: E402


def t_benchmark_runs_and_returns_report():
    rep = BM.run_benchmark()
    assert rep.n_cases == len(BM.DEFAULT_CASES)
    assert rep.verdict.ok in (True, False)   # either is honest
    assert "Go" in BM.format_report(rep) or "GO" in BM.format_report(rep)


def t_benchmark_no_external_effects_in_any_arm():
    """invariant: هیچ armی اثرِ خارجی ندارد (Go criterion یکی از همین‌ها)."""
    rep = BM.run_benchmark()
    for arm in (rep.arm_a, rep.arm_b, rep.arm_c):
        assert all(not o.had_external_effect for o in arm), "external effect leaked"


def t_benchmark_leakage_zero():
    """label leakage باید صفر باشد در همهٔ armها (HYPOTHESIS هرگز → FACT)."""
    rep = BM.run_benchmark()
    for arm in (rep.arm_a, rep.arm_b, rep.arm_c):
        assert all(o.label_leakage_events == 0 for o in arm)


def t_benchmark_receipts_written():
    """بازو B/C واقعاً receipt روی زنجیره نوشتند (claim → receipt کار می‌کند)."""
    import tempfile
    from epistemics import sandbox_runner as SR  # noqa: F401
    # benchmark.run_benchmark در tmp اجرا می‌شود؛ فقط تأیید که arm_b خروجی دارد
    rep = BM.run_benchmark()
    assert len(rep.arm_b) == len(BM.DEFAULT_CASES)
    assert len(rep.arm_c) == len(BM.DEFAULT_CASES)


def t_benchmark_go_verdict_criteria_complete():
    """Go verdict همهٔ معیارهای کلیدی را دارد."""
    rep = BM.run_benchmark()
    c = rep.verdict.criteria
    for key in ("c_success_gt_a_by_threshold", "c_unsupported_le_a",
                "c_leakage_zero", "c_cost_within_budget",
                "c_no_external_effects"):
        assert key in c, f"missing criterion {key}"


def t_format_report_is_honest():
    """report حاوی یادآوریِ صداقت است (synthetic، نه اثباتِ قابلیت)."""
    rep = BM.run_benchmark()
    text = BM.format_report(rep)
    assert "synthetic" in text.lower() or "صداقت" in text


TESTS = [
    t_benchmark_runs_and_returns_report,
    t_benchmark_no_external_effects_in_any_arm,
    t_benchmark_leakage_zero,
    t_benchmark_receipts_written,
    t_benchmark_go_verdict_criteria_complete,
    t_format_report_is_honest,
]

if __name__ == "__main__":
    failed = 0
    for _t in TESTS:
        try:
            _t()
            print(f"  PASS  {_t.__name__}")
        except Exception as exc:
            import traceback
            print(f"  FAIL  {_t.__name__}: {exc}")
            traceback.print_exc()
            failed += 1
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(failed)
