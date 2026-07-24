"""test_heart_control.py — HH-P4: قانونِ کنترل + شبیه‌سازیِ closed-loop (Gate-B).

سناریوهای S1..S9 + loop-gain (هر دو لگ) + گاردهای ساختاری. deterministic.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("heart-control")

import importlib                     # noqa: E402
import heart.control_law as cl       # noqa: E402
import heart.sim_heart as sh         # noqa: E402
import heart.interface as hi         # noqa: E402
importlib.reload(cl)
importlib.reload(sh)

REPORT = sh.run_sim(write=True)      # یک‌بار، در state موقتِ harness
SP = sh.SETPOINT


def t_a_sim_pass_all_gates():
    """کلِ گیت‌های Gate-B (S1..S9 + loop-gain) باید سبز باشند — SIM-PASS."""
    bad = {k: v for k, v in REPORT["gates"].items() if not v.get("ok")}
    assert not bad, bad
    assert REPORT["sim_pass"] is True


def t_b_loop_gain_both_legs():
    """G_velocity و G_total (با لگِ Δ_self) هر دو <1؛ لگِ Δ کوچک (نمونه‌گیریِ ساعت-ثابت)."""
    lg = REPORT["gates"]["loop_gain_lt_1"]
    dg = REPORT["gates"]["S9_delta_loop_gain"]
    assert lg["G"] < 1.0
    assert dg["g_total"] < 1.0
    assert dg["g_delta"] < 0.5


def t_c_sigma_terminal_veto():
    """verdictهای σ ترمینال‌اند — هیچ محاسبهٔ بعدی MAX را بازنویسی نمی‌کند."""
    for kwargs, reason in [
        (dict(sigma=None), "sigma-missing"),
        (dict(stale=True), "sigma-stale"),
        (dict(sigma=1.5, zone="cancer-axis"), "sigma-over-cap"),
        (dict(sigma=0.5, sigma_internals=False), "sigma-tainted-no-internals"),
        (dict(sigma=0.5, sigma_producer="doctor"), "sigma-tainted-producer"),
    ]:
        sig, tel = cl.heart_step(sh._mk_inputs(1, 3.0, **kwargs), SP)
        assert sig.period_s == cl.MAX_S, (kwargs, sig.period_s)
        assert tel["gates"]["fail_closed_reason"] == reason, (reason, tel["gates"])


def t_d_no_velocity_fail_closed():
    """بدونِ منبعِ velocity → MAX (استراحتِ عمیق، نه حدس)."""
    sig, tel = cl.heart_step(sh._mk_inputs(1, None), SP)
    assert sig.period_s == cl.MAX_S
    assert tel["gates"]["fail_closed_reason"] == "no-velocity-source"


def t_e_below_band_accelerates_above_slows():
    """زیرِ باند → periodِ کوتاه‌تر از BASE؛ بالای باند → بلندتر (نرخِ ظاهرشونده)."""
    fast, _ = cl.heart_step(sh._mk_inputs(1, 0.6, cpi=0.0), SP)
    slow, _ = cl.heart_step(sh._mk_inputs(1, 12.0, cpi=0.0), SP)
    assert fast.period_s < cl.BASE_PERIOD_S < slow.period_s
    assert cl.FLOOR_S <= fast.period_s and slow.period_s <= cl.MAX_S


def t_f_cpi_and_budget_only_slow():
    """cpi_guard و budget_pressure هرگز شتاب نمی‌دهند (ضریب ≥1)."""
    base, tb = cl.heart_step(sh._mk_inputs(1, 3.0, cpi=0.0), SP)
    noisy, tn = cl.heart_step(sh._mk_inputs(1, 3.0, cpi=0.9), SP)
    tight, tt = cl.heart_step(sh._mk_inputs(1, 3.0, cpi=0.0, budget_remaining=10), SP)
    assert noisy.period_s >= base.period_s
    assert tn["gates"]["cpi_guard"] >= 1.0
    assert tight.period_s >= base.period_s
    assert tt["gates"]["budget_pressure"] >= 1.0


def t_g_delta_shifts_band_within_cap():
    """Δ_selfِ authoritative باند را بالا می‌برد (تا +۵۰٪) → target بالاتر → شتابِ نسبی."""
    no_d, t0 = cl.heart_step(sh._mk_inputs(1, 3.25, cpi=0.0), SP)
    with_d, t1 = cl.heart_step(sh._mk_inputs(
        1, 3.25, cpi=0.0,
        delta={"authoritative": True, "delta_self_live": 0.2,
               "ceiling_live": 0.25}), SP)
    assert t1["gates"]["g_learn"] > 0
    assert t1["gates"]["band_effective_mid"] > t0["gates"]["band_effective_mid"]
    assert t1["gates"]["band_effective_mid"] <= 3.25 * 1.5 + 1e-9
    assert with_d.period_s < no_d.period_s      # target بالاتر → همین v «کمبود» است


def t_h_signal_shape_is_adr():
    """HeartSignal دقیقاً چهار فیلدِ ADR-001؛ HeartParams بدونِ هیچ فیلدِ نرخ."""
    sig, _ = cl.heart_step(sh._mk_inputs(1, 3.0), SP)
    assert set(sig.to_json().keys()) == {"schema", "beat_seq", "period_s",
                                         "sigma_now", "baro_factor"}
    for f in hi.HeartParams.__dataclass_fields__:
        low = f.lower()
        assert "rate" not in low and "bpm" not in low and "period" not in low, f
    assert hi.HeartParams().viable_band == (0.5, 6.0)   # property ADR-form


def t_f2_budget_pressure_uses_owner_cap():
    """فشارِ بودجه با capِ setpointِ مالک سنجیده می‌شود نه فقط envِ سراسری.
    همان spent با capِ کوچک‌تر = فشارِ بیشتر؛ و رسیدن به cap = استراحتِ عمیق."""
    inp = sh._mk_inputs(1, 3.0, cpi=0.0)
    inp["budget_spent"] = 200
    inp.pop("budget_remaining")
    wide = hi.HeartParams(viable_band_lo=SP.viable_band_lo,
                          viable_band_hi=SP.viable_band_hi, daily_beat_cap=1000)
    tight = hi.HeartParams(viable_band_lo=SP.viable_band_lo,
                           viable_band_hi=SP.viable_band_hi, daily_beat_cap=240)
    _, t_wide = cl.heart_step(dict(inp), wide)
    _, t_tight = cl.heart_step(dict(inp), tight)
    assert t_wide["gates"]["budget_pressure"] == 1.0
    assert t_tight["gates"]["budget_pressure"] > 1.0, t_tight["gates"]
    # capِ مصرف‌شده → همان استراحتِ عمیقِ مسیرِ remaining==0
    at_cap = dict(inp)
    at_cap["budget_spent"] = 240
    sig, tel = cl.heart_step(at_cap, tight)
    assert sig.period_s >= cl.MAX_S * 0.6, sig.period_s
    # سازگاریِ عقب‌رو: بدونِ budget_spent مسیرِ قدیمِ budget_remaining دست‌نخورده است
    old = sh._mk_inputs(1, 3.0, cpi=0.0, budget_remaining=0)
    assert old.get("budget_spent") is None
    sig_old, _ = cl.heart_step(old, SP)
    assert sig_old.period_s >= cl.MAX_S * 0.6


def t_i_report_honesty_uncollapsible():
    """گزارش، وضعیتِ e_shadow را صریح حمل می‌کند + hashِ tamper-evidence دارد."""
    assert "e_shadow_note" in REPORT
    assert REPORT["code_sha256"] and len(REPORT["code_sha256"]) == 64
    assert REPORT["schema"] == "HEART-SIM-REPORT.v1"


def t_j_structural_no_money_no_spend_fields():
    """ساختاری: هیچ importِ پول در control_law/sim_heart؛ خروجی هیچ فیلدِ spend/grant."""
    for mod in (cl, sh):
        src = Path(mod.__file__).read_text("utf-8")
        for bad in ("import organ_gate", "import money_gate", "import budget_gate",
                    "from organ_gate", "from money_gate", "allocate_dry"):
            assert bad not in src, f"{mod.__name__}: {bad}"
    sig, tel = cl.heart_step(sh._mk_inputs(1, 3.0), SP)
    flat = str(sig.to_json()) + str(tel)
    assert "grant" not in flat and "spend_alloc" not in flat


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_heart_control: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
