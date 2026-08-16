#!/usr/bin/env python3
"""تست A2 · money_gate — دیوارِ per-actionِ تأییدِ انسانی (fail-closed).
اثبات: ≤آستانه allow · >آستانه بدون token deny · با tokenِ معتبرِ match allow ·
mismatch مبلغ/action deny · وضعیتِ خودگزارشی (نه approved/sent) deny · آستانه از SoT."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("money-gate")
import money_gate  # noqa: E402
from approval_channel import Approval, NotWiredStub, MockApprovalChannel  # noqa: E402


def t_under_gate_allows_without_token():
    r = money_gate.check(15.0, "LEAD-20260707-001")   # ≤20، بدون channel
    assert r["allow"] is True and "under-human-gate" in r["reason"], r


def t_over_gate_denies_without_token():
    r = money_gate.check(50.0, "LEAD-20260707-002")   # >20، NotWired پیش‌فرض
    assert r["allow"] is False and "no valid approval" in r["reason"], r


def t_over_gate_allows_with_valid_matching_approval():
    ch = MockApprovalChannel([Approval("LEAD-20260707-003", 50.0, "approved", "mock-human")])
    r = money_gate.check(50.0, "LEAD-20260707-003", ch)
    assert r["allow"] is True and r["reason"] == "human-approved", r


def t_amount_mismatch_denies():
    ch = MockApprovalChannel([Approval("LEAD-20260707-004", 40.0, "approved")])
    r = money_gate.check(50.0, "LEAD-20260707-004", ch)   # مبلغ نمی‌خواند (تأییدِ ۴۰ برای خرجِ ۵۰)
    assert r["allow"] is False, r


def t_self_report_status_denies():
    # وضعیتِ خارج از approved/sent (ادعای ایجنت مثل "done") هرگز معتبر نیست
    ch = MockApprovalChannel([Approval("LEAD-20260707-005", 50.0, "agent-claims-done")])
    r = money_gate.check(50.0, "LEAD-20260707-005", ch)
    assert r["allow"] is False, r


def t_threshold_from_sot():
    assert money_gate.human_gate_aud() == 20.0   # harness yaml بی‌کلید → کفِ 20


def t_negative_amount_denies():
    r = money_gate.check(-1.0, "LEAD-NEG-001")
    assert r["allow"] is False and r["reason"] == "amount-not-a-spend", r


def t_nan_and_inf_deny_with_honest_reason():
    for a in (float("nan"), float("inf"), float("-inf")):
        r = money_gate.check(a, "LEAD-NONFINITE")
        assert r["allow"] is False and r["reason"] == "amount-not-a-spend", (a, r)


def t_zero_still_under_gate():
    r = money_gate.check(0.0, "LEAD-ZERO")
    assert r["allow"] is True and "under-human-gate" in r["reason"], r


if __name__ == "__main__":
    failed = harness.run([
        ("≤آستانه بدون token → allow", t_under_gate_allows_without_token),
        (">آستانه بدون token → deny", t_over_gate_denies_without_token),
        (">آستانه با تأییدِ معتبرِ match → allow", t_over_gate_allows_with_valid_matching_approval),
        ("mismatch مبلغ → deny", t_amount_mismatch_denies),
        ("وضعیتِ خودگزارشی (نه approved/sent) → deny", t_self_report_status_denies),
        ("آستانهٔ human-gate از budgets.yaml (SoT)", t_threshold_from_sot),
        ("مبلغ منفی → deny", t_negative_amount_denies),
        ("NaN/Inf → deny با دلیل صادق", t_nan_and_inf_deny_with_honest_reason),
        ("صفر هنوز under-gate", t_zero_still_under_gate),
    ])
    sys.exit(1 if failed else 0)
