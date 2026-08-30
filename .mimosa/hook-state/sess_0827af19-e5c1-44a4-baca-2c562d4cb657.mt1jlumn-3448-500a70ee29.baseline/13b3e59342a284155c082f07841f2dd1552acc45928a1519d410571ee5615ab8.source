#!/usr/bin/env python3
"""test_deepseek_weekly_cap.py — سقفِ دلاریِ هفتگیِ DeepSeek (۲۰۲۶-۰۸-۱۳، رأیِ مالک).

قبلاً tier=secondary (DeepSeek) زیرِ همان شمارندهٔ روزانهٔ مشترکِ Fugu بود —
با تمام‌شدنِ سهمیهٔ Fugu، DeepSeek هم بی‌دلیل مسدود می‌شد با اینکه قیمتش
(v4-flash) طوری ارزان است که سقفِ دلاری تقریباً هرگز نباید ببندد. این تست
تأیید می‌کند: DeepSeek حالا گیتِ مستقلِ دلاریِ هفتگیِ خودش را دارد و
Fugu دست‌نخورده مانده.
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("deepseek-weekly-cap")
OPS = Path(__file__).resolve().parent.parent
for _p in (OPS / "budget", OPS / "cortex"):
    sys.path.insert(0, str(_p))

import opslib  # noqa: E402
import fugu_quota as fq  # noqa: E402

_PAID_CALLS = opslib.STATE_DIR / "paid-calls.jsonl"


def _write_calls(rows):
    _PAID_CALLS.parent.mkdir(parents=True, exist_ok=True)
    with _PAID_CALLS.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _row(provider, cost_usd, days_ago=0.0):
    ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - days_ago * 86400))
    return {"ts": ts, "provider": provider, "cost_usd": cost_usd, "ok": True}


def t_no_log_file_means_zero_spend():
    if _PAID_CALLS.exists():
        _PAID_CALLS.unlink()
    assert fq.deepseek_weekly_spend_usd() == 0.0


def t_sums_only_deepseek_within_7_days():
    _write_calls([
        _row("deepseek", 1.0, days_ago=0.1),
        _row("deepseek", 2.5, days_ago=3.0),
        _row("sakana", 999.0, days_ago=0.1),       # provider غلط — نباید بشمارد
        _row("deepseek", 5.0, days_ago=7.5),       # بیرونِ پنجرهٔ ۷روزه
    ])
    spend = fq.deepseek_weekly_spend_usd()
    assert abs(spend - 3.5) < 1e-9, spend


def t_malformed_lines_are_fail_soft():
    _PAID_CALLS.write_text(
        'not json at all\n'
        '{"provider": "deepseek", "cost_usd": 1.0, "ts": "' +
        time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + '"}\n'
        '{"provider": "deepseek"}\n'   # بدون ts — رد شود، crash نکند
        '\n',
        encoding="utf-8",
    )
    spend = fq.deepseek_weekly_spend_usd()
    assert abs(spend - 1.0) < 1e-9, spend


def t_under_cap_allows_with_default_20usd():
    _write_calls([_row("deepseek", 5.0, days_ago=0.1)])
    os.environ.pop("DEEPSEEK_WEEKLY_COST_CAP_USD", None)
    out = fq._deepseek_weekly_reserve()
    assert out["allow"] is True, out
    assert out["weekly_cap_usd"] == 20.0
    assert abs(out["weekly_spend_usd"] - 5.0) < 1e-9


def t_at_or_over_cap_denies_with_clear_reason():
    _write_calls([_row("deepseek", 21.0, days_ago=0.1)])
    out = fq._deepseek_weekly_reserve()
    assert out["allow"] is False, out
    assert out["reason"] == "deepseek-weekly-cost-cap"


def t_custom_cap_via_env():
    _write_calls([_row("deepseek", 3.0, days_ago=0.1)])
    os.environ["DEEPSEEK_WEEKLY_COST_CAP_USD"] = "2"
    try:
        out = fq._deepseek_weekly_reserve()
        assert out["allow"] is False, out
        assert out["weekly_cap_usd"] == 2.0
    finally:
        os.environ.pop("DEEPSEEK_WEEKLY_COST_CAP_USD", None)


def t_reserve_secondary_routes_to_weekly_gate_not_shared_counter():
    """reserve('secondary') نباید اصلاً شمارندهٔ مشترکِ fugu-quota.json را لمس کند."""
    fq_state = opslib.STATE_DIR / "fugu-quota.json"
    if fq_state.exists():
        fq_state.unlink()
    _write_calls([_row("deepseek", 1.0, days_ago=0.1)])
    out = fq.reserve("secondary", "ARCHITECT_SYS")
    assert out["allow"] is True, out
    assert out["reason"] == "ok"
    assert "weekly_spend_usd" in out
    # شمارندهٔ مشترک نباید نوشته/تغییر کرده باشد (اصلاً secondary دیگر آن را نمی‌بیند)
    assert not fq_state.exists(), "reserve(secondary) نباید fugu-quota.json بسازد/بنویسد"


def t_reserve_primary_unchanged_still_shared_counter():
    """reserve('primary') باید دقیقاً همان رفتارِ قبلی (شمارندهٔ روزانه) را داشته باشد."""
    fq_state = opslib.STATE_DIR / "fugu-quota.json"
    if fq_state.exists():
        fq_state.unlink()
    os.environ["FUGU_DAILY_CALL_CAP"] = "2"
    try:
        r1 = fq.reserve("primary", "ARCHITECT_SYS")
        r2 = fq.reserve("primary", "ARCHITECT_SYS")
        r3 = fq.reserve("primary", "ARCHITECT_SYS")
        assert r1["allow"] is True and r2["allow"] is True, (r1, r2)
        assert r3["allow"] is False and r3["reason"] == "daily-cap", r3
    finally:
        os.environ.pop("FUGU_DAILY_CALL_CAP", None)
        if fq_state.exists():
            fq_state.unlink()


def t_deepseek_cap_full_does_not_block_fugu_primary():
    """قلبِ رأی مالک: سقفِ DeepSeek بستن نباید Fugu را ببندد و برعکس."""
    fq_state = opslib.STATE_DIR / "fugu-quota.json"
    if fq_state.exists():
        fq_state.unlink()
    _write_calls([_row("deepseek", 999.0, days_ago=0.1)])  # DeepSeek کاملاً بسته
    out_secondary = fq.reserve("secondary", "ARCHITECT_SYS")
    assert out_secondary["allow"] is False, out_secondary
    out_primary = fq.reserve("primary", "ARCHITECT_SYS")
    assert out_primary["allow"] is True, out_primary  # Fugu دست‌نخورده


if __name__ == "__main__":
    failed = harness.run([
        ("no-log-file-zero-spend", t_no_log_file_means_zero_spend),
        ("sums-only-deepseek-within-7-days", t_sums_only_deepseek_within_7_days),
        ("malformed-lines-fail-soft", t_malformed_lines_are_fail_soft),
        ("under-cap-allows-default-20usd", t_under_cap_allows_with_default_20usd),
        ("at-or-over-cap-denies", t_at_or_over_cap_denies_with_clear_reason),
        ("custom-cap-via-env", t_custom_cap_via_env),
        ("reserve-secondary-routes-to-weekly-gate", t_reserve_secondary_routes_to_weekly_gate_not_shared_counter),
        ("reserve-primary-unchanged", t_reserve_primary_unchanged_still_shared_counter),
        ("deepseek-cap-full-does-not-block-fugu", t_deepseek_cap_full_does_not_block_fugu_primary),
    ])
    sys.exit(1 if failed else 0)
