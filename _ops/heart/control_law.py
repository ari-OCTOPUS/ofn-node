#!/usr/bin/env python3
"""control_law.py — HH-P4: قانونِ Living-Beat (velocity-first).

period از velocity *ظاهر* می‌شود؛ SOG/Doctor فقط باندِ هدف می‌دهد (ADR-001).
σ فقط ترمز است، هرگز شتاب؛ Δ_self (شتاب‌دهنده) همان انضباطِ provenance را دارد
(producer خارجی + drift-guard). CPI/بودجه فقط کُند می‌کنند (ضریب ≥1).

heart_step یک تابعِ pure است (بدونِ I/O) — ورودی‌ها با gather_inputs تزریق می‌شوند؛
fail-closed: ورودیِ حیاتیِ غایب/کهنه → period=MAX (استراحتِ عمیق، نه کرش).
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import statistics
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

sys.path.insert(0, str(_HERE.parent))
from heart import interface as hi     # noqa: E402
from heart import producers, sog_math  # noqa: E402

BASE_PERIOD_S = float(os.environ.get("CHRONO_PERIOD_S", "60.0"))
FLOOR_S = float(os.environ.get("CARDIAC_RESTING_FLOOR_S", "30.0"))
MAX_S = float(os.environ.get("CARDIAC_MAX_PERIOD_S", "900.0"))
K_P = float(os.environ.get("HEART_K_P", "0.7"))
DRIFT_EPS = float(os.environ.get("HEART_DRIFT_EPS", "0.02"))
SIGMA_STALE_H = float(os.environ.get("HEART_SIGMA_STALE_H", "30.0"))  # σ روزانه تازه می‌شود
DAILY_BEAT_CAP = int(os.environ.get("CARDIAC_DAILY_BEAT_CAP", "288"))


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


PRECISION_MIN_N = float(os.environ.get("HEART_PRECISION_MIN_N", "5.0"))


def precision_weight(vstate: "dict | None") -> float:
    """precisionِ سیگنالِ velocity ∈ [0,1] — استانداردِ active-inference (وزنِ inverse-variance
    خطای پیش‌بینی؛ pymdp γ / predictive-coding، بک‌لاگِ ۲۰۲۷ #۲). جایگزینِ اصولیِ gainِ دستی:
    π پایین وقتی سیگنال کم‌نمونه یا نامنظم (بورست‌دار) است، π=۱ در رژیمِ سالم → gainِ کامل.
    چون π≤۱ فقط gain را کم می‌کند، اثباتِ پایداریِ G<1 حفظ (سفت‌تر) می‌شود.
    دادهٔ ناکافی (n<۲) → ۱.۰ (رفتارِ byte-identical با امروز)."""
    v = vstate or {}
    try:
        n = float(v.get("sample_size") or 0)
    except (TypeError, ValueError):
        n = 0.0
    if n < 2:
        return 1.0
    pi_n = min(1.0, n / PRECISION_MIN_N)                       # کفایتِ نمونه (اشباع در n≥۵)
    pi_reg = 1.0
    ts = v.get("confirmed_ts") or []
    if len(ts) >= 3:
        try:
            fts = [float(t) for t in ts]
        except (TypeError, ValueError):
            fts = []
        # پادزهرِ S-batch replay (۲۰۲۶-۰۷-۱۱): ts ِ inf/nan وارد gaps می‌شد و pstdev با
        # OverflowError کرش می‌کرد (نقضِ قیدِ «π همیشه finite، بدون کرش»). non-finite → پاک؛
        # ورودیِ سالم بیت‌به‌بیت همان مسیرِ قبلی را می‌رود (فقط سم‌زدایی، نه تغییرِ منطق).
        fts = [t for t in fts if math.isfinite(t)]
        gaps = [b - a for a, b in zip(fts, fts[1:]) if b > a]
        if len(gaps) >= 2:
            m = sum(gaps) / len(gaps)
            if m > 0:
                cv = statistics.pstdev(gaps) / m              # ضریبِ تغییراتِ گپِ ورود
                pi_reg = 1.0 / (1.0 + max(0.0, cv - 1.0) ** 2)  # Poisson (CV≈۱) = سالم → ۱
    return _clamp(pi_n * pi_reg, 0.0, 1.0)


def gather_inputs(beat: int = 0) -> dict:
    """ورودی‌های heart_step از state-fileها — همه read-only، همه fail-soft/None."""
    signals = producers.read_signals()
    sigma = None
    try:
        p = opslib.STATE_DIR / "replication-latest.json"
        if p.exists():
            rep = json.loads(p.read_text("utf-8"))
            ts = rep.get("ts")
            stale = True
            t = None
            if ts:
                try:
                    t = dt.datetime.fromisoformat(str(ts))
                    if t.tzinfo is not None:
                        t = t.astimezone().replace(tzinfo=None)
                    stale = (dt.datetime.now() - t) > dt.timedelta(hours=SIGMA_STALE_H)
                except ValueError:
                    stale = True
            sig = rep.get("sigma") or {}
            sigma = {"sigma": sig.get("sigma_effective"),
                     "zone": sig.get("zone"), "stale": stale, "ts": ts,
                     "spawn_approved": sig.get("spawn_approved"),
                     "parents": sig.get("parents"),
                     "producer": rep.get("producer")}
    except (OSError, ValueError):
        sigma = None
    budget_remaining = None
    try:
        p = opslib.STATE_DIR / "cardiac-budget.json"
        if p.exists():
            d = json.loads(p.read_text("utf-8"))
            if d.get("date") == opslib.today():
                budget_remaining = max(0, DAILY_BEAT_CAP - int(d.get("spent", 0)))
    except (OSError, ValueError):
        budget_remaining = None
    prev = {}
    try:
        p = opslib.STATE_DIR / "pulse" / "heart-shadow-latest.json"
        if p.exists():
            d = json.loads(p.read_text("utf-8"))
            prev = {"period_s": d.get("period_s"),
                    "velocity": (d.get("telemetry") or {}).get("velocity_per_hr")}
    except (OSError, ValueError):
        prev = {}
    return {"beat": beat, "velocity": signals.get("velocity"),
            "cpi": signals.get("cpi"), "delta": signals.get("delta_self"),
            "sigma": sigma, "budget_remaining": budget_remaining,
            "lock": sog_math.read_lock(), "prev": prev}


def heart_step(inputs: dict, setpoint: "hi.HeartParams | None" = None
               ) -> tuple["hi.HeartSignal", dict]:
    """یک گامِ قانونِ کنترل. خروجی: (HeartSignal, telemetry). هرگز spend/grant."""
    sp = setpoint or hi.read_setpoint() or hi.HeartParams()
    beat = int(inputs.get("beat") or 0)
    gates: dict = {}

    def _rest(reason: str, sigma_now=None, drift=False) -> tuple:
        gates["fail_closed_reason"] = reason
        gates["drift_flag"] = drift
        sig = hi.HeartSignal(beat_seq=beat, period_s=MAX_S,
                             sigma_now=sigma_now, baro_factor=1.0)
        return sig, _telemetry(inputs, sp, gates, MAX_S)

    # ۱) گیتِ سلامتِ σ — ترمز، fail-closed (missing/stale/بالای target → استراحتِ MAX)
    sigma_state = inputs.get("sigma")
    if not sigma_state or sigma_state.get("sigma") is None:
        return _rest("sigma-missing")
    if sigma_state.get("stale"):
        return _rest("sigma-stale", sigma_state.get("sigma"))
    sigma_now = float(sigma_state["sigma"])
    # ۱ب) چکِ taint (تقارنِ ترمز با شتاب‌دهنده — ریویوی خصمانه): σ باید محصولِ
    # حلقهٔ replication باشد و از درون سازگار: sigma_state همیشه spawn_approved/parents
    # را حمل می‌کند و σ=approved/parents. رکوردِ بدونِ اجزا، ناسازگار، یا با ادعای
    # producer∈{doctor,heart} = جعلی → استراحتِ MAX (ترمزِ خلع‌سلاح‌ناپذیر).
    appr, par = sigma_state.get("spawn_approved"), sigma_state.get("parents")
    if appr is None or par is None:
        return _rest("sigma-tainted-no-internals", sigma_now)
    if abs(sigma_now - (float(appr) / max(1.0, float(par)))) > 1e-3:
        return _rest("sigma-tainted-inconsistent", sigma_now)
    if str(sigma_state.get("producer") or "").lower() in ("doctor", "heart"):
        return _rest("sigma-tainted-producer", sigma_now)
    if sigma_now > sp.target_sigma or sigma_state.get("zone") == "cancer-axis":
        return _rest("sigma-over-cap", sigma_now)

    # ۲) drift-guard — ضدِ جعل/ناسازگاریِ شتاب‌دهنده (تقارن با ترمز)
    delta = inputs.get("delta") or {}
    d_live, d_ceil = delta.get("delta_self_live"), delta.get("ceiling_live")
    g_learn = 0.0
    if delta.get("authoritative") and d_live is not None and d_ceil is not None:
        if d_ceil <= 0 or d_live > d_ceil * (1.0 + DRIFT_EPS):
            return _rest("delta-drift-flag", sigma_now, drift=True)
        g_learn = _clamp(d_live / d_ceil, 0.0, 1.0)
    gates["g_learn"] = round(g_learn, 4)

    # ۳) باندِ هدف: setpointِ Doctor/SOG + شیفتِ یادگیری (سقفِ +۵۰٪)
    lo, hiband = sp.viable_band_lo, sp.viable_band_hi
    mid = (lo + hiband) / 2.0
    width = max(hiband - lo, 1e-6)
    mid_eff = mid * (1.0 + 0.5 * g_learn)
    gates["band_effective_mid"] = round(mid_eff, 4)

    # ۴) خطای throughput → period (ظاهرشونده، نه ذخیره‌شده)
    vstate = inputs.get("velocity") or {}
    v = vstate.get("velocity_per_hr")
    if v is None:
        return _rest("no-velocity-source", sigma_now)
    err = _clamp((float(v) - mid_eff) / width, -3.0, 3.0)
    # precision-weighting (active-inference، فلگِ HEART_PRECISION_WEIGHT، پیش‌فرض خاموش،
    # بک‌لاگِ ۲۰۲۷ #۲): خطا با اطمینانِ سیگنال وزن می‌شود (err_eff = π·err). π≤۱ فقط gain
    # را کم می‌کند → پایداریِ G<1 حفظ. خاموش → err_eff=err → خروجی byte-identical با امروز.
    if os.environ.get("HEART_PRECISION_WEIGHT", "0") == "1":
        pi = precision_weight(vstate)
        err_eff = pi * err
        gates["precision"] = round(pi, 4)
        gates["err_eff"] = round(err_eff, 4)
    else:
        err_eff = err
    period_raw = BASE_PERIOD_S * math.exp(K_P * err_eff)
    baro = math.exp(K_P * err_eff)
    gates["err"] = round(err, 4)

    # ۴ب) گاردِ بی‌ثمری (anti-futility): اگر شتابِ قبلی throughput را بالا نبرد،
    # دیگر شتاب نده (سکوت = استراحت، نه pin روی کف)
    prev = inputs.get("prev") or {}
    if (err < 0 and prev.get("period_s") is not None
            and prev["period_s"] <= BASE_PERIOD_S
            and prev.get("velocity") is not None
            and float(v) <= float(prev["velocity"]) + 1e-9):
        period_raw = max(period_raw, BASE_PERIOD_S)
        gates["futility_backoff"] = True

    # ۵) گاردِ تورم — CPI فقط کُند می‌کند (ضریب ≥1)
    cpi_state = inputs.get("cpi") or {}
    cpi = cpi_state.get("cpi_0_1")
    cpi_guard = 1.0
    if cpi is not None:
        cpi_guard = 1.0 + max(0.0, float(cpi) - 0.3) * 1.5
    period_raw *= cpi_guard
    gates["cpi_guard"] = round(cpi_guard, 3)

    # ۶) فشارِ بودجهٔ ضربان — monotone و ≥1
    rem = inputs.get("budget_remaining")
    bp = 1.0
    if rem is not None:
        frac = _clamp(rem / max(DAILY_BEAT_CAP, 1), 0.0, 1.0)
        bp = 1.0 if frac >= 0.5 else 1.0 + (0.5 - frac) * 2.0   # تا ۲× در ته‌کشیدن
        if rem == 0:
            period_raw = max(period_raw, MAX_S * 0.6)
    period_raw *= bp
    gates["budget_pressure"] = round(bp, 3)

    # ۷) جملهٔ استراحتِ E_shadow — فقط اگر قفل و وزنِ صریح (v1: پیش‌فرض ۰)
    w_shadow = float(os.environ.get("HEART_W_SHADOW", "0.0"))
    lock = inputs.get("lock") or {}
    e_locked = (lock.get("status") or {}).get("e_shadow") == "locked"
    gates["e_shadow"] = "locked" if e_locked else "excluded-unlocked"
    gates["w_shadow_active"] = bool(w_shadow > 0 and e_locked)

    period = _clamp(period_raw, FLOOR_S, MAX_S)
    gates["fail_closed_reason"] = None
    gates["drift_flag"] = False
    signal = hi.HeartSignal(beat_seq=beat, period_s=round(period, 2),
                            sigma_now=sigma_now, baro_factor=round(baro, 4))
    return signal, _telemetry(inputs, sp, gates, period)


def _telemetry(inputs: dict, sp: "hi.HeartParams", gates: dict,
               period: float) -> dict:
    v = (inputs.get("velocity") or {}).get("velocity_per_hr")
    cpi = (inputs.get("cpi") or {}).get("cpi_0_1")
    d = (inputs.get("delta") or {}).get("delta_self_live")
    tel = hi.HeartTelemetry(velocity_per_hr=v, cpi_0_1=cpi, delta_self_live=d,
                            band_lo=sp.viable_band_lo, band_hi=sp.viable_band_hi,
                            gates=gates).to_json()
    tel["period_s"] = round(period, 2)
    tel["velocity_per_hr"] = v
    return tel


if __name__ == "__main__":
    sig, tel = heart_step(gather_inputs())
    print(json.dumps({"signal": sig.to_json(), "telemetry": tel},
                     ensure_ascii=False, indent=2))
