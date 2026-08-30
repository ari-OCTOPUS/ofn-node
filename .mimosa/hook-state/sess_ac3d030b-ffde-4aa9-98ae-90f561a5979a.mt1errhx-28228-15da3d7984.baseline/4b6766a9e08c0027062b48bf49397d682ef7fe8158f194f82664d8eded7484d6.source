"""test_activation_untracked.py — D2 (2026-07-21): اهرم‌های ACTIVATION-*.flag دیگر tracked نیستند.

قبلاً (کامیت «Wave 0 live» 6a38af8) ۸ فایلِ ACTIVATION-*.flag در گیت commit شده بودند →
یک restart می‌توانست بی‌صدا لِین‌های زنده/پولی را باز کند (paid cortex، work-llm، heart-doctor،
debate، self-improve-auto، pulse، و بایپسِ سراسریِ تاریخ go-live). این فایل اثبات می‌کند که با
**غیابِ** این فلگ‌ها هر گیتِ زنده **بسته** است — حتی وقتی سپرِ تاریخ کاملاً باز باشد (post-rollover).

نکتهٔ صداقتی: غیاب در درختِ زنده کارِ گامِ deploy است (rm فیزیکی + verify)؛ این تست فقط قرارداد
«فلگ نباشد → گیت بسته» را قفل می‌کند تا رگرسیون نکند. فعال‌سازی = عملِ صریحِ مالک (runbook)، نه
پیش‌فرضِ commit‌شده.
"""
import datetime as _dt
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))
sys.path.insert(0, str(_HERE.parent / "heart"))

import harness
ENV = harness.setup("activation-untracked")

import opslib          # noqa: E402
import model_router    # noqa: E402

# ۸ فلگِ فعال‌سازیِ لِینِ زنده که D2 آن‌ها را untrack کرد (باید در درختِ تست غایب باشند)
_LIVE_FLAGS = [
    "ACTIVATION-CORTEX-PAID.flag", "ACTIVATION-DEBATE.flag", "ACTIVATION-GO-LIVE.flag",
    "ACTIVATION-HEART-DOCTOR.flag", "ACTIVATION-PULSE.flag", "ACTIVATION-RESEARCH-EARLY.flag",
    "ACTIVATION-SELF-IMPROVE-AUTO.flag", "ACTIVATION-WORK-LLM.flag",
]


def _clear_flags():
    for name in _LIVE_FLAGS:
        f = opslib.OPS / name
        if f.exists():
            f.unlink()


def t_a_flags_absent_in_harness_tree():
    """درختِ تستِ ایزوله هیچ فلگِ فعال‌سازی ندارد (پیش‌فرضِ امن)."""
    _clear_flags()
    for name in _LIVE_FLAGS:
        assert not (opslib.OPS / name).exists(), name


def t_b_paid_gate_closed_after_rollover_when_flags_absent():
    """قلبِ D2: حتی با سپرِ تاریخِ کاملاً باز (تاریخِ گذشته = post-rollover)، غیابِ فلگ‌ها
    گیتِ پولی را می‌بندد. اگر فلگ‌ها commit می‌ماندند این False نمی‌شد."""
    _clear_flags()
    real = opslib.LIVE_GATE_DATE
    opslib.LIVE_GATE_DATE = _dt.date(2020, 1, 1)   # سپرِ تاریخ کاملاً باز
    try:
        ok, why = model_router.paid_gate()
        assert ok is False, f"paid_gate باید بسته باشد ولی باز است: {why}"
        # چون RESEARCH-EARLY غایب است → مسیرِ live_gate_open(CORTEX-PAID) → «flag missing»
        assert "activation flag missing" in why, why
    finally:
        opslib.LIVE_GATE_DATE = real


def t_c_live_gate_open_closed_for_every_absent_flag():
    """live_gate_open برای هر فلگِ غایب False است (سپرِ تاریخ باز؛ فقط غیابِ فلگ می‌بندد)."""
    _clear_flags()
    real = opslib.LIVE_GATE_DATE
    opslib.LIVE_GATE_DATE = _dt.date(2020, 1, 1)
    try:
        for name in ("ACTIVATION-CORTEX-PAID.flag", "ACTIVATION-WORK-LLM.flag",
                     "ACTIVATION-HEART-DOCTOR.flag", "ACTIVATION-DEBATE.flag"):
            ok, why = opslib.live_gate_open(opslib.OPS / name)
            assert ok is False and "activation flag missing" in why, (name, why)
    finally:
        opslib.LIVE_GATE_DATE = real


def t_d_go_live_absent_means_no_date_bypass():
    """با غیابِ ACTIVATION-GO-LIVE، اهرمِ زودهنگام خاموش است → پیش از تاریخ سپر حاکم می‌ماند."""
    _clear_flags()
    real = opslib.LIVE_GATE_DATE
    opslib.LIVE_GATE_DATE = _dt.date(2099, 1, 1)   # پیش از سپر
    try:
        # go-live غایب → early=False → سپرِ تاریخ می‌بندد (نه «flag missing»)
        ok, why = opslib.live_gate_open(opslib.OPS / "ACTIVATION-CORTEX-PAID.flag")
        assert ok is False and "phase -1 shield" in why, why
    finally:
        opslib.LIVE_GATE_DATE = real


def t_e_research_early_absent_paid_path_is_date_gate():
    """با غیابِ RESEARCH-EARLY، paid_gate به مسیرِ live_gate_open می‌رود (نه overrideِ زودهنگام)."""
    _clear_flags()
    real = opslib.LIVE_GATE_DATE
    opslib.LIVE_GATE_DATE = _dt.date(2020, 1, 1)
    try:
        ok, why = model_router.paid_gate()
        assert ok is False
        # نباید پیامِ overrideِ research-early باشد (چون فلگش غایب است)
        assert "research-early override" not in why, why
    finally:
        opslib.LIVE_GATE_DATE = real


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_activation_untracked: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
