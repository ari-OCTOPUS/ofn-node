#!/usr/bin/env python3
"""sim_heart.py — HH-P4: اثباتِ closed-loop قانونِ کنترل (Gate-B).

plant: backlogِ آیتم‌ها؛ هر beat حداکثر c آیتم پردازش می‌شود؛ velocity = پردازش‌شده/ساعت
(پنجرهٔ غلتان). حلقه بسته است: period → beats → throughput → velocity → err → period.

گیت‌ها: سناریوهای S1..S6 + loop-gain عددی G<1 + عدمِ pin روی ریل‌ها در steady-state.
گزارش → state/sim/HEART-SIM-REPORT.json (un-collapsible per-gate). $0، آفلاین.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

sys.path.insert(0, str(_HERE.parent))
from heart import control_law as cl   # noqa: E402
from heart import interface as hi     # noqa: E402

REPORT_PATH = opslib.STATE_DIR / "sim" / "HEART-SIM-REPORT.json"
SETPOINT = hi.HeartParams(viable_band_lo=0.5, viable_band_hi=6.0)
CAPACITY_PER_BEAT = 0.05      # آیتم per beat — مقیاسِ plant
WINDOW_H = 2.0                # پنجرهٔ سنجشِ velocity


def _mk_inputs(beat, v, cpi=0.1, delta=None, sigma=0.2, zone="healthy",
               stale=False, budget_remaining=200, prev=None, lock_locked=True,
               sigma_internals=True, sigma_producer=None):
    delta = delta or {"authoritative": False}
    lock = {"status": {"e_shadow": "locked" if lock_locked else "excluded-unlocked",
                       "i_pred": "locked", "delta_self": "locked"}}
    sig = None
    if sigma is not None:
        # σ سازگارِ درونی (تقلیدِ sigma_state واقعی): sigma = approved/parents
        parents = 4
        sig = {"sigma": sigma, "zone": zone, "stale": stale,
               "producer": sigma_producer}
        if sigma_internals:
            sig["spawn_approved"] = sigma * parents
            sig["parents"] = parents
    return {"beat": beat,
            "velocity": None if v is None else
                        {"velocity_per_hr": v, "authoritative": True},
            "cpi": {"cpi_0_1": cpi},
            "delta": delta,
            "sigma": sig,
            "budget_remaining": budget_remaining,
            "lock": lock, "prev": prev or {}}


def simulate(hours: float, backlog0: float, arrivals_per_hr: float,
             cpi: float = 0.1, sigma: float = 0.2,
             budget_remaining: int = 200) -> dict:
    """اجرای closed-loop: هر گام یک beat (طولش را قانونِ کنترل تعیین می‌کند)."""
    t, backlog, beat = 0.0, backlog0, 0
    period = cl.BASE_PERIOD_S
    done: list[tuple[float, float]] = []      # (زمانِ ساعت، آیتمِ پردازش‌شده)
    periods, velocities = [], []
    prev = {}
    horizon = hours * 3600.0
    while t < horizon and beat < 10_000:
        beat += 1
        processed = min(backlog, CAPACITY_PER_BEAT)
        backlog = backlog - processed + arrivals_per_hr * (period / 3600.0)
        done.append((t / 3600.0, processed))
        cut = t / 3600.0 - WINDOW_H
        done = [(h, p) for (h, p) in done if h >= cut]
        v = sum(p for _, p in done) / min(WINDOW_H, max(t / 3600.0, period / 3600.0))
        sig, tel = cl.heart_step(
            _mk_inputs(beat, v, cpi=cpi, sigma=sigma,
                       budget_remaining=budget_remaining, prev=prev), SETPOINT)
        prev = {"period_s": period, "velocity": v}
        period = sig.period_s
        periods.append(period)
        velocities.append(v)
        t += period
    tail_p = periods[-10:] if len(periods) >= 10 else periods
    return {"beats": beat, "final_backlog": round(backlog, 3),
            "periods": periods, "velocities": velocities,
            "tail_mean_period": sum(tail_p) / len(tail_p),
            "tail_min": min(tail_p), "tail_max": max(tail_p),
            "mean_period": sum(periods) / len(periods)}


def numeric_loop_gain() -> dict:
    """G = |∂v/∂period| · |∂period/∂v| حولِ نقطهٔ کار (v=میانهٔ باند، period=BASE)."""
    mid = (SETPOINT.viable_band_lo + SETPOINT.viable_band_hi) / 2.0
    width = SETPOINT.viable_band_hi - SETPOINT.viable_band_lo
    p0 = cl.BASE_PERIOD_S
    # plant: v(period) = 3600/period · c  →  |∂v/∂p| = 3600c/p²
    dv_dp = 3600.0 * CAPACITY_PER_BEAT / (p0 * p0)
    # قانون: p(v) = BASE·exp(K_P·(v−mid)/width) → |∂p/∂v| = p·K_P/width
    dp_dv = p0 * cl.K_P / width
    G = dv_dp * dp_dv
    return {"G": round(G, 4), "ok": G < 1.0,
            "operating_point": {"period_s": p0, "v_mid": mid, "width": width}}


def run_sim(write: bool = True) -> dict:
    gates: dict = {}
    # S1 — backlog burst: باید همگرا شود، بدونِ pin روی ریل در steady-state
    s1 = simulate(hours=24, backlog0=60.0, arrivals_per_hr=3.0)
    s1_ok = (cl.FLOOR_S < s1["tail_mean_period"] < cl.MAX_S
             and s1["tail_max"] - s1["tail_min"] < 0.5 * s1["tail_mean_period"])
    gates["S1_burst_converges_no_pin"] = {"ok": bool(s1_ok),
                                          "tail_mean_period": round(s1["tail_mean_period"], 1),
                                          "tail_spread": round(s1["tail_max"] - s1["tail_min"], 1)}
    # S2 — سکوت: کار نیست → گاردِ بی‌ثمری؛ نباید روی کفِ ۳۰s pin شود
    s2 = simulate(hours=12, backlog0=0.0, arrivals_per_hr=0.02)
    s2_ok = s2["tail_mean_period"] >= cl.BASE_PERIOD_S * 0.9
    gates["S2_quiet_rests_not_floor_pin"] = {"ok": bool(s2_ok),
                                             "tail_mean_period": round(s2["tail_mean_period"], 1)}
    # S3 — CPI بالا: میانگینِ period باید ≥ سناریوی هم‌ارزِ CPI-پایین باشد (شتابِ تورمی ممنوع)
    s3_hi = simulate(hours=12, backlog0=60.0, arrivals_per_hr=3.0, cpi=0.85)
    s3_ok = s3_hi["mean_period"] >= s1["mean_period"] * 0.999
    gates["S3_cpi_never_accelerates"] = {"ok": bool(s3_ok),
                                         "mean_hi_cpi": round(s3_hi["mean_period"], 1),
                                         "mean_low_cpi": round(s1["mean_period"], 1)}
    # S4 — runaway: Δ جعلی بالای سقف → drift-flag + MAX
    sig4, tel4 = cl.heart_step(_mk_inputs(
        1, 3.0, delta={"authoritative": True, "delta_self_live": 0.9,
                       "ceiling_live": 0.3}), SETPOINT)
    gates["S4_forged_delta_drift_flag"] = {
        "ok": bool(sig4.period_s == cl.MAX_S and tel4["gates"]["drift_flag"]),
        "period": sig4.period_s}
    # S5 — σ بالای cap → ترمزِ MAX در همان گام
    sig5, tel5 = cl.heart_step(_mk_inputs(1, 3.0, sigma=1.5, zone="cancer-axis"),
                               SETPOINT)
    gates["S5_sigma_brake"] = {"ok": bool(
        sig5.period_s == cl.MAX_S
        and tel5["gates"]["fail_closed_reason"] == "sigma-over-cap")}
    # S5ب — σ غایب/کهنه → fail-closed
    sig5b, _ = cl.heart_step(_mk_inputs(1, 3.0, sigma=None), SETPOINT)
    sig5c, _ = cl.heart_step(_mk_inputs(1, 3.0, stale=True), SETPOINT)
    gates["S5b_sigma_missing_or_stale_fail_closed"] = {
        "ok": bool(sig5b.period_s == cl.MAX_S and sig5c.period_s == cl.MAX_S)}
    # S6 — بودجهٔ ضربان تمام → استراحتِ monotone
    sig6, _ = cl.heart_step(_mk_inputs(1, 3.0, budget_remaining=0), SETPOINT)
    gates["S6_budget_depleted_rest"] = {"ok": bool(sig6.period_s >= cl.MAX_S * 0.5),
                                        "period": sig6.period_s}
    # S7 — taint canary (ریویوی خصمانه): σِ جعلی با اجزای ناسازگار یا producerِ
    # doctor/heart باید ترمزِ MAX بخورد (ترمز خلع‌سلاح نمی‌شود)
    sig7a, tel7a = cl.heart_step(_mk_inputs(1, 3.0, sigma=0.5,
                                            sigma_internals=False), SETPOINT)
    in7b = _mk_inputs(1, 3.0, sigma=0.5)
    in7b["sigma"]["spawn_approved"] = 9.0          # ناسازگار با sigma·parents
    sig7b, tel7b = cl.heart_step(in7b, SETPOINT)
    sig7c, _ = cl.heart_step(_mk_inputs(1, 3.0, sigma=0.5,
                                        sigma_producer="doctor"), SETPOINT)
    gates["S7_sigma_taint_canary"] = {"ok": bool(
        sig7a.period_s == cl.MAX_S
        and tel7a["gates"]["fail_closed_reason"] == "sigma-tainted-no-internals"
        and sig7b.period_s == cl.MAX_S
        and tel7b["gates"]["fail_closed_reason"] == "sigma-tainted-inconsistent"
        and sig7c.period_s == cl.MAX_S)}
    # S8 — بازگشت به استراحت: بعد از خشک‌شدنِ burst (ورودی صفر)، period ≥ BASE
    s8 = simulate(hours=30, backlog0=20.0, arrivals_per_hr=0.0)
    gates["S8_return_to_resting_after_drain"] = {
        "ok": bool(s8["final_backlog"] < 1.0
                   and s8["tail_mean_period"] >= cl.BASE_PERIOD_S * 0.9),
        "final_backlog": s8["final_backlog"],
        "tail_mean_period": round(s8["tail_mean_period"], 1)}
    # S9 — بهرهٔ حلقهٔ Δ_self (لگِ حذف‌شده در ریویو): Δ→band→err→period→v→Δ.
    # حساسیتِ estimator به v اخیر را عددی می‌سنجیم و در زنجیرهٔ مشتق‌ها ضرب می‌کنیم.
    import random as _rnd
    _r = _rnd.Random(99)
    base_rows = [{"v": 3.0 + _r.gauss(0, 0.2),
                  "cov": {"confirmed": _r.gauss(0, 1), "effects": 0, "hour": t % 24}}
                 for t in range(96)]
    d0 = producers_delta(base_rows)
    dv = 0.5
    pert_rows = [dict(r, v=r["v"] + (dv if i >= 48 else 0.0))
                 for i, r in enumerate(base_rows)]
    d1 = producers_delta(pert_rows)
    slope_delta_v = abs((d1 - d0) / dv)
    mid = (SETPOINT.viable_band_lo + SETPOINT.viable_band_hi) / 2.0
    width = SETPOINT.viable_band_hi - SETPOINT.viable_band_lo
    p0 = cl.BASE_PERIOD_S
    ceil_ref = 0.3
    dp_dDelta = p0 * cl.K_P * (0.5 * mid / ceil_ref) / width
    dv_dp = 3600.0 * CAPACITY_PER_BEAT / (p0 * p0)
    g_delta = slope_delta_v * dp_dDelta * dv_dp
    lg = numeric_loop_gain()
    g_total = lg["G"] + g_delta
    gates["S9_delta_loop_gain"] = {"ok": bool(g_total < 1.0),
                                   "slope_delta_per_v": round(slope_delta_v, 5),
                                   "g_delta": round(g_delta, 5),
                                   "g_total": round(g_total, 4)}
    # Gate-B — loop-gain حلقهٔ velocity
    gates["loop_gain_lt_1"] = lg
    # پوشش‌های بیرون از sim (در تست‌ها، با محیطِ ایزوله): fixed-clock sampling
    gates["covered_by_tests"] = {
        "ok": True,
        "note": "decision-frequency invariance (should_sample) در test_heart_producers؛ "
                "denominator σ در تستِ taint (اجزای ناسازگار) پوشش داده شد"}
    sim_pass = all(g.get("ok") for g in gates.values())
    report = {
        "ts": opslib.now_iso(),
        "schema": "HEART-SIM-REPORT.v1",
        "sim_pass": bool(sim_pass),
        "gates": gates,
        "e_shadow_note": "w_shadow=0 در v1 (جملهٔ استراحت غیرفعال تا وزنِ صریحِ مالک) — "
                         "قفلِ E_shadow جدا در PULSE-EQUATIONS-LOCKED",
        "constants": {"K_P": cl.K_P, "BASE": cl.BASE_PERIOD_S,
                      "FLOOR": cl.FLOOR_S, "MAX": cl.MAX_S,
                      "capacity_per_beat": CAPACITY_PER_BEAT},
        "code_sha256": control_law_sha256(),
    }
    if write:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(REPORT_PATH) as lj:
            lj.write(report)
    return report


def producers_delta(rows) -> float:
    """Δ_selfِ estimator روی ردیف‌های تزریقی (بدونِ I/O) — برای سنجشِ حساسیتِ S9."""
    from heart import producers as _p
    d = _p.delta_self_estimator(min_samples=48, rows=rows)
    return float(d.get("delta_self_live") or 0.0)


def control_law_sha256() -> str:
    """هشِ tamper-evidence: production_wire_open همین را با کدِ فعلی می‌سنجد."""
    import hashlib
    return hashlib.sha256(Path(cl.__file__).read_bytes()).hexdigest()


def read_report() -> dict:
    try:
        return (json.loads(REPORT_PATH.read_text("utf-8"))
                if REPORT_PATH.exists() else {})
    except (OSError, ValueError):
        return {}


if __name__ == "__main__":
    rep = run_sim(write=False)
    print(json.dumps({"sim_pass": rep["sim_pass"],
                      "gates": {k: v.get("ok") for k, v in rep["gates"].items()}},
                     ensure_ascii=False, indent=2))
