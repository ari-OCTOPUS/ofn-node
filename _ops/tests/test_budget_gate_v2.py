#!/usr/bin/env python3
"""تست A1 · budget_gate v2 — خواندن سقف‌ها از budgets.yaml (SoT) با کفِ fail-closed.
اثبات: (۱) SoT-read واقعی · (۲) strictest=min (yaml شل‌تر → کف می‌ماند) ·
(۳) yaml ناخوانا → کفِ هاردکد (نه crash، نه نامحدود) · (۴) رفتار v1.1 حفظ (non-breaking)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("budget-gate-v2")
sys.path.insert(0, os.environ["SCRIPTS_DIR"])
import budget_gate  # noqa: E402  — تنها enforcer، از scripts/ واقعی

YAML = budget_gate.BUDGETS_YAML   # = <temp>/_ops/budget/budgets.yaml (harness نوشت: cap_monthly 30)


def _write_yaml(text: str) -> None:
    YAML.write_text(text, "utf-8")


def _default_yaml() -> None:
    _write_yaml(harness.TEST_BUDGETS)   # cap_monthly 30؛ بدون cap_daily/disaster/aud_per_usd


def _reset_state() -> None:
    for p in (budget_gate.STATE, budget_gate.LOCK):
        try:
            Path(p).unlink()
        except OSError:
            pass


def t_caps_read_from_sot():
    _default_yaml()
    c = budget_gate._caps()
    assert c["month_aud"] == 30.0 and c["day_aud"] == 2.0 and c["disaster_aud"] == 500.0, c
    assert c["aud"] == 1.5 and "budgets.yaml" in c["src"], c


def t_caps_strictest_min():
    # yaml شل‌تر از کف → کف می‌ماند (هرگز looser از v1.1)
    _write_yaml("global:\n  cap_monthly: 100\n  cap_daily: 9\n  cap_disaster: 9000\nprojects: {}\n")
    c = budget_gate._caps()
    assert c["month_aud"] == 30.0 and c["day_aud"] == 2.0 and c["disaster_aud"] == 500.0, c


def t_caps_tighten_honored():
    # yaml سخت‌تر از کف → همان اعمال می‌شود (SoT واقعاً می‌راند)
    _write_yaml("global:\n  cap_monthly: 5\n  cap_daily: 1\nprojects: {}\n")
    c = budget_gate._caps()
    assert c["month_aud"] == 5.0 and c["day_aud"] == 1.0, c


def t_caps_failclosed_on_garbage():
    _write_yaml("{{{ this is not yaml ::::")
    c = budget_gate._caps()
    assert c["month_aud"] == 30.0 and c["day_aud"] == 2.0 and c["disaster_aud"] == 500.0, c
    assert c["src"] == "hardcode-floor", c


def t_daily_enforced_from_sot():
    # کفِ پیش‌فرض (day=2 AUD, aud=1.5): 0.9 USD = 1.35 AUD < 2 → allow
    _default_yaml(); _reset_state()
    assert budget_gate.reserve("ZIMAN", 0.9)["allow"] is True
    # حالا yaml سقف روزانه را به 1 AUD سفت کند → همان 0.9 USD = 1.35 AUD > 1 → deny
    _write_yaml("global:\n  cap_monthly: 30\n  cap_daily: 1\nprojects: {}\n"); _reset_state()
    r = budget_gate.reserve("ZIMAN", 0.9)
    assert r["allow"] is False and r["reason"] == "daily", r


def t_reserve_release_cycle():
    _default_yaml(); _reset_state()
    r = budget_gate.reserve("ZIMAN", 1.0)      # 1.5 AUD < 2 → allow
    assert r["allow"] is True, r
    budget_gate.release("ZIMAN", 1.0)          # پس‌دادن رزرو
    d = budget_gate._roll(budget_gate._load())
    assert d["spent_today_usd"] == 0.0, d      # نشتِ بودجه نباشد (non-breaking)


def t_disaster_halts_from_sot():
    _default_yaml(); _reset_state()
    budget_gate.reserve("ZIMAN", 0.1)
    budget_gate.settle("ZIMAN", 0.1, 400.0)    # delta 399.9 × 1.5 ≈ 600 AUD ≥ 500 → halt
    d = budget_gate._roll(budget_gate._load())
    assert d["halted"] is True, d


if __name__ == "__main__":
    failed = harness.run([
        ("سقف‌ها از budgets.yaml خوانده می‌شوند (SoT)", t_caps_read_from_sot),
        ("strictest=min: yaml شل‌تر → کفِ هاردکد می‌ماند", t_caps_strictest_min),
        ("yaml سخت‌تر → همان اعمال می‌شود", t_caps_tighten_honored),
        ("yaml ناخوانا → کفِ fail-closed (نه crash/نامحدود)", t_caps_failclosed_on_garbage),
        ("سقف روزانه واقعاً از SoT enforce می‌شود", t_daily_enforced_from_sot),
        ("چرخهٔ reserve/release بدون نشت (non-breaking)", t_reserve_release_cycle),
        ("خطِ فاجعه از SoT → halt", t_disaster_halts_from_sot),
    ])
    sys.exit(1 if failed else 0)
