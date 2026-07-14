"""تست‌های budget ledger — fail-closed و ماه‌محور."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ziman.budget import Budget  # noqa: E402

CFG = {
    "budget": {
        "monthly_cap_aud": 15,
        "usd_to_aud": 1.5,
        "state_file": ".budget_state_test.json",
        "prices_usd_per_mtok": {
            "claude-haiku-4-5": {"in": 1.0, "out": 5.0},
        },
    }
}


def test_starts_empty_and_can_spend(tmp_path):
    b = Budget(CFG, base_dir=tmp_path)
    assert b.spent_aud == 0.0
    assert b.remaining_aud() == 15.0
    assert b.can_spend("claude-haiku-4-5", est_in=2000, est_out=800) is True


def test_record_reduces_remaining_and_persists(tmp_path):
    b = Budget(CFG, base_dir=tmp_path)
    # 1M in + 1M out = (1.0 + 5.0) USD * 1.5 = 9.0 AUD
    b.record("claude-haiku-4-5", 1_000_000, 1_000_000)
    assert round(b.remaining_aud(), 2) == 6.0
    # نمونهٔ تازه از همان state باید مصرف را بخواند (ماندگاری)
    b2 = Budget(CFG, base_dir=tmp_path)
    assert round(b2.spent_aud, 2) == 9.0


def test_fail_closed_when_estimate_exceeds_remaining(tmp_path):
    b = Budget(CFG, base_dir=tmp_path)
    b.record("claude-haiku-4-5", 1_000_000, 1_000_000)  # 9 AUD خرج، 6 مانده
    # یک فراخوانِ بزرگ (2M in + 2M out = 18 AUD) نباید مجاز باشد
    assert b.can_spend("claude-haiku-4-5", est_in=2_000_000, est_out=2_000_000) is False
    # فراخوانِ کوچک هنوز مجاز است
    assert b.can_spend("claude-haiku-4-5", est_in=1000, est_out=500) is True


def test_unknown_model_falls_back_to_haiku_price(tmp_path):
    b = Budget(CFG, base_dir=tmp_path)
    cost = b._cost_aud("some-unknown-model", 1_000_000, 0)
    assert round(cost, 2) == 1.5  # 1.0 USD * 1.5
