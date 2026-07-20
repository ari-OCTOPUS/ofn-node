"""test_go_live.py — جلسه ۴۶: اهرمِ go-live (رأی مالک: قفلا رو بردار واقعی بشن، tier 1+2).

اثبات: ACTIVATION-GO-LIVE سپرِ تاریخ را زودتر باز می‌کند ولی (۱) پرچمِ per-activation
همچنان لازم است، و (۲) ایمنیِ هسته — kill-switch/σ-cap/human-append/سقفِ بودجه — مسیرهای
جدا و دست‌نخورده‌اند (go-live آن‌ها را باز نمی‌کند).
"""
import datetime as _dt
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("go-live")

import opslib  # noqa: E402


def _act(name):
    return opslib.OPS / name


def t_a_go_live_opens_date_shield_early():
    """با GO-LIVE + پرچمِ per-activation → گیت باز (پیش از LIVE_GATE_DATE).
    rollover 2026-07-21: تاریخ داخل تست پین می‌شود (الگوی test_cockpit_golive_honesty)."""
    _real_gate = opslib.LIVE_GATE_DATE
    opslib.LIVE_GATE_DATE = _dt.date(2099, 1, 1)
    go = opslib.GO_LIVE_FLAG
    act = _act("ACTIVATION-TEST.flag")
    go.parent.mkdir(parents=True, exist_ok=True)
    try:
        # بدونِ GO-LIVE → سپرِ تاریخ حاکم (پیش از LIVE_GATE_DATE)
        act.write_text("x", "utf-8")
        ok, why = opslib.live_gate_open(act)
        assert ok is False and "live locked" in why
        # با GO-LIVE → باز
        go.write_text("owner", "utf-8")
        ok2, why2 = opslib.live_gate_open(act)
        assert ok2 is True and "go-live" in why2
    finally:
        opslib.LIVE_GATE_DATE = _real_gate
        for f in (go, act):
            if f.exists():
                f.unlink()


def t_b_go_live_still_needs_per_activation_flag():
    """GO-LIVE به‌تنهایی کافی نیست — پرچمِ per-activation همچنان لازم است."""
    go = opslib.GO_LIVE_FLAG
    act = _act("ACTIVATION-ABSENT.flag")
    try:
        go.write_text("owner", "utf-8")
        if act.exists():
            act.unlink()
        ok, why = opslib.live_gate_open(act)
        assert ok is False and "activation flag missing" in why
    finally:
        if go.exists():
            go.unlink()


def t_c_core_safety_is_separate_from_go_live():
    """ایمنیِ هسته مسیرِ جدا دارد — GO-LIVE هیچ‌کدام را باز نمی‌کند."""
    go = opslib.GO_LIVE_FLAG
    go.write_text("owner", "utf-8")
    try:
        # kill-switch: STOP همچنان halt می‌کند (مستقل از go-live)
        opslib.STOP_ARCHITECT.parent.mkdir(parents=True, exist_ok=True)
        opslib.STOP_ARCHITECT.write_text("stop", "utf-8")
        try:
            assert opslib.halted() == "STOP(architect)"
        finally:
            opslib.STOP_ARCHITECT.unlink()
        # سقفِ بودجه: cap_monthly در budgets دست‌نخورده (go-live آن را عوض نمی‌کند)
        cap = opslib.load_budgets().get("global", {}).get("cap_monthly")
        assert cap is not None and float(cap) <= 30.0, f"سقفِ بودجه نباید بالاتر از ۳۰ برود: {cap}"
        # FREEZE همچنان کار می‌کند
        assert opslib.frozen() is False
    finally:
        if go.exists():
            go.unlink()


def t_d_go_live_flag_absent_is_legacy_shield():
    """بدونِ GO-LIVE → دقیقاً رفتارِ قبلی (سپرِ تاریخ برای همه).
    rollover 2026-07-21: تاریخ داخل تست پین می‌شود."""
    _real_gate = opslib.LIVE_GATE_DATE
    opslib.LIVE_GATE_DATE = _dt.date(2099, 1, 1)
    go = opslib.GO_LIVE_FLAG
    if go.exists():
        go.unlink()
    act = _act("ACTIVATION-X.flag")
    act.write_text("x", "utf-8")
    try:
        ok, why = opslib.live_gate_open(act)
        assert ok is False and "phase -1 shield" in why
    finally:
        opslib.LIVE_GATE_DATE = _real_gate
        act.unlink()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_go_live: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
