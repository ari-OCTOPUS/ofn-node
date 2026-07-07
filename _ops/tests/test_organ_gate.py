#!/usr/bin/env python3
"""تست T2: organ_gate — fail-closed، floorها از فایل، زنجیر به budget_gate، FREEZE/STOP."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("organgate")
import opslib      # noqa: E402
import organ_gate  # noqa: E402


def t_unknown_organ_denied():
    r = organ_gate.reserve("NOT_AN_ORGAN", 0.01)
    assert not r["allow"] and "unknown-organ" in r["reason"], r


def t_reserve_settle_flow():
    r = organ_gate.reserve("ZIMAN", 0.10, task="t")
    assert r["allow"], r
    s = organ_gate.settle("ZIMAN", 0.10, 0.05, task="t")
    assert s["ok"], s
    st = organ_gate.status()
    assert abs(st["organs"]["ZIMAN"]["spent_today_usd"] - 0.05) < 1e-9, st["organs"]["ZIMAN"]
    # budget_gate هم باید همان را ببیند (تنها enforcer)
    bg = st["budget_gate_state"]
    assert abs(bg["spent_today_usd"] - 0.05) < 1e-9, bg


def t_organ_monthly_cap_from_file():
    # ZIMAN: floor 1 AUD → est 1.0 USD = 1.5 AUD > 1 → deny per-organ پیش از budget_gate
    r = organ_gate.reserve("ZIMAN", 1.0)
    assert not r["allow"] and "organ-monthly" in r["reason"], r


def t_debate_loop_default_cap():
    st = organ_gate.status()
    assert st["organs"]["DEBATE_LOOP"]["cap_monthly_aud"] == 5, st["organs"]["DEBATE_LOOP"]
    r = organ_gate.reserve("DEBATE_LOOP", 1.0)   # 1.5 AUD ≤ 5
    assert r["allow"], r
    organ_gate.release("DEBATE_LOOP", 1.0)


def t_budget_gate_daily_chain():
    # سقف burst روزانه budget_gate (V1 همه-AUD 2026-07-07: CEIL_DAY_AUD=2.0) از پشت گیت ما هم دیده شود
    r1 = organ_gate.reserve("DEBATE_LOOP", 0.8)   # (0.05+0.8)×1.5 = 1.275 AUD ≤ 2
    assert r1["allow"], r1
    r2 = organ_gate.reserve("DEBATE_LOOP", 0.8)   # (0.85+0.8)×1.5 = 2.475 AUD > 2
    assert not r2["allow"] and "budget_gate:daily" in r2["reason"], r2
    organ_gate.release("DEBATE_LOOP", 0.8)


def t_freeze_denies():
    opslib.freeze("test")
    r = organ_gate.reserve("ZIMAN", 0.01)
    assert not r["allow"] and "frozen" in r["reason"], r
    opslib.FREEZE_FLAG.unlink()


def t_stop_denies():
    opslib.STOP_METABOLIC.write_text("test", "utf-8")
    r = organ_gate.reserve("ZIMAN", 0.01)
    assert not r["allow"] and "halted" in r["reason"], r
    opslib.STOP_METABOLIC.unlink()


def t_log_written():
    assert opslib.ORGAN_LOG.exists()
    lines = opslib.ORGAN_LOG.read_text("utf-8").strip().splitlines()
    assert len(lines) >= 7, len(lines)


def t_reserve_rollback_on_state_write_failure():
    # شکست نوشتن organ-state پس از رزرو سراسری موفق → باید refund شود (ضد نشت بودجه)
    before = organ_gate.status()["budget_gate_state"]["spent_today_usd"]
    orig_write = opslib.LockedJson.write

    def boom(self, data):
        raise OSError("disk full (test)")

    opslib.LockedJson.write = boom
    try:
        r = organ_gate.reserve("ZIMAN", 0.10, task="rollback-test")
    finally:
        opslib.LockedJson.write = orig_write
    assert not r["allow"] and "organ-state-unreadable" in r["reason"], r
    after = organ_gate.status()["budget_gate_state"]["spent_today_usd"]
    assert abs(after - before) < 1e-9, f"budget leak: before={before} after={after}"
    assert not opslib.frozen(), "rollback موفق نباید FREEZE بگذارد"


if __name__ == "__main__":
    failed = harness.run([
        ("ارگان ناشناخته → deny (fail-closed)", t_unknown_organ_denied),
        ("reserve→settle در هر دو لایه", t_reserve_settle_flow),
        ("سقف ماهانه ارگان از budgets.yaml", t_organ_monthly_cap_from_file),
        ("پیش‌فرض V1 حلقه: cap ماهانه 5 AUD", t_debate_loop_default_cap),
        ("زنجیر به budget_gate (سقف burst روزانه)", t_budget_gate_daily_chain),
        ("FREEZE → deny", t_freeze_denies),
        ("STOP → deny", t_stop_denies),
        ("لاگ append-only گیت", t_log_written),
        ("شکست نوشتن state پس از رزرو → refund سراسری (ضد نشت)", t_reserve_rollback_on_state_write_failure),
    ])
    sys.exit(1 if failed else 0)
