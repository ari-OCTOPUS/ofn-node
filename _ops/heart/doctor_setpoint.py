#!/usr/bin/env python3
"""doctor_setpoint.py — HH-P6: دکترِ تکاملی = مدولاتورِ w-slow.

Doctor **setpoint** می‌نویسد نه نرخ (ADR-001): per-epoch باندِ target-velocity را
پیشنهاد می‌کند و از نتیجهٔ محقق‌شده یاد می‌گیرد. سیاستِ پیش‌فرض قطعی و $0 است؛
مسیرِ چند-ایجنتیِ LLM (4d_system/brain) پشتِ live-gateِ دوقفلهٔ مالک+تاریخ.

w-slow یعنی: تغییرِ کند، کران‌دار، hysteresis سخت — Doctor هرگز نمی‌تواند قلب را
تسخیر کند؛ فقط باند را ذره‌ذره جابه‌جا می‌کند و σ/کران‌های مطلق همیشه حاکم‌اند.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

sys.path.insert(0, str(_HERE.parent))
from heart import interface as hi   # noqa: E402
from heart import producers        # noqa: E402

ACT_HEART_DOCTOR = opslib.OPS / "ACTIVATION-HEART-DOCTOR.flag"
MAX_BAND_DELTA_PCT = 0.20        # hysteresis: حداکثر ±۲۰٪ per epoch
DEFAULT_BAND = (0.5, 6.0)
EMA_ALPHA = 0.3


def propose_setpoint(prev: "hi.HeartParams | None", signals: dict) -> "hi.HeartParams":
    """سیاستِ قطعیِ w-slow: باند به سمتِ velocityِ پایدارِ محقق‌شده میل می‌کند؛
    Δ_selfِ authoritative سقف را (تا +۵۰٪) بالا می‌برد؛ CPI/σ-alert باند را جمع می‌کند."""
    prev = prev or hi.HeartParams(viable_band_lo=DEFAULT_BAND[0],
                                  viable_band_hi=DEFAULT_BAND[1])
    lo, hiband = prev.viable_band_lo, prev.viable_band_hi
    mid, width = (lo + hiband) / 2.0, (hiband - lo)
    v_state = signals.get("velocity") or {}
    d_state = signals.get("delta_self") or {}
    c_state = signals.get("cpi") or {}
    rationale = []
    target_mid = mid
    # یادگیریِ کند: EMA به سمتِ velocityِ واقعاً محقق‌شده (فقط اگر authoritative)
    v = v_state.get("velocity_per_hr")
    if v is not None and v_state.get("authoritative"):
        target_mid = (1 - EMA_ALPHA) * mid + EMA_ALPHA * float(v)
        rationale.append(f"EMA به سمتِ v={v}")
    # Δ_self بالا (یادگیریِ فعالِ اثبات‌شده) → گشایشِ سقف تا +۵۰٪
    stretch = 1.0
    if d_state.get("authoritative") and d_state.get("delta_self_live") is not None \
            and d_state.get("ceiling_live"):
        g = max(0.0, min(1.0, d_state["delta_self_live"] / d_state["ceiling_live"]))
        stretch = 1.0 + 0.5 * g
        if g > 0:
            rationale.append(f"Δ_self g={round(g, 3)} → گشایشِ سقف ×{round(stretch, 2)}")
    # CPI بالا → جمع‌شدنِ باند (استراحت/احتیاط)
    cpi = c_state.get("cpi_0_1")
    shrink = 1.0
    if cpi is not None and cpi > 0.5:
        shrink = 1.0 - 0.4 * (cpi - 0.5) / 0.5      # تا ×۰.۶
        rationale.append(f"CPI={cpi} → جمع‌شدن ×{round(shrink, 2)}")
    target_mid *= shrink
    # hysteresis سخت: میانه حداکثر ±۲۰٪ حرکت کند
    delta_cap = mid * MAX_BAND_DELTA_PCT
    new_mid = max(mid - delta_cap, min(mid + delta_cap, target_mid))
    new_width = max(width * shrink, new_mid * 0.5)   # باند هرگز تیغ‌نازک نشود
    new_lo = max(0.05, new_mid - new_width / 2.0)
    new_hi = min(hi.ABS_BAND_MAX_PER_HR, (new_mid + new_width / 2.0) * stretch)
    params = hi.HeartParams(
        target_sigma=prev.target_sigma,
        viable_band_lo=round(new_lo, 4),
        viable_band_hi=round(max(new_hi, new_lo + 0.1), 4),
        epoch_seq=prev.epoch_seq + 1,                # monotonic
        target_mass_scale=prev.target_mass_scale,
        daily_beat_cap=prev.daily_beat_cap,
        baroreflex_gain=prev.baroreflex_gain,
    )
    if params.validate():
        # هر نقضی → عقب‌نشینی به باندِ قبلی با seq+1 (fail-safe، هرگز setpointِ خراب)
        params = hi.HeartParams(
            target_sigma=prev.target_sigma,
            viable_band_lo=prev.viable_band_lo,
            viable_band_hi=prev.viable_band_hi,
            epoch_seq=prev.epoch_seq + 1,
            target_mass_scale=prev.target_mass_scale,
            daily_beat_cap=prev.daily_beat_cap,
            baroreflex_gain=prev.baroreflex_gain)
    return params


def run_epoch_setpoint(write: bool = True) -> dict:
    """یک epochِ w-slow: بخوان → پیشنهاد → بنویس + NOTE. propose-only.

    HH-P8 رأی ۱ (مصوبِ مالک 2026-07-10): بدونِ setpointِ قبلی، باندِ اولیه از
    velocityِ واقعاً مشاهده‌شده seed می‌شود (یک‌باره، معاف از hysteresis)؛ اگر هنوز
    هیچ مشاهده‌ای نیست، نوشتن به تعویق می‌افتد تا اولین velocity برسد."""
    prev = hi.read_setpoint()
    signals = producers.read_signals()
    if prev is None:
        v_obs = (signals.get("velocity") or {}).get("velocity_per_hr")
        if v_obs is None:
            return {"ts": opslib.now_iso(), "written": False,
                    "reason": "awaiting-first-velocity",
                    "note": "seed باند به تعویق افتاد — هنوز مشاهده‌ای نیست (HH-P8)"}
        mid = max(float(v_obs), 0.02)
        width = max(float(v_obs), 0.1)
        seeded = hi.HeartParams(
            viable_band_lo=round(max(0.02, mid - width / 2.0), 4),
            viable_band_hi=round(min(hi.ABS_BAND_MAX_PER_HR, mid + width / 2.0), 4),
            epoch_seq=1)
        if not seeded.validate():
            out = {"ts": opslib.now_iso(), "epoch_seq": 1,
                   "band": [seeded.viable_band_lo, seeded.viable_band_hi],
                   "prev_band": None, "llm": None, "written": False,
                   "rationale": "seeded-from-observation (HH-P8)"}
            if write:
                out["written"] = hi.write_setpoint(seeded)
                if out["written"]:
                    opslib.ledger_note("HEART_SETPOINT", {
                        "epoch_seq": 1, "band_lo": seeded.viable_band_lo,
                        "band_hi": seeded.viable_band_hi, "seeded": True,
                    }, actor="heart-doctor")
            return out
    params = propose_setpoint(prev, signals)
    llm = llm_refine(params, signals)
    out = {"ts": opslib.now_iso(), "epoch_seq": params.epoch_seq,
           "band": [params.viable_band_lo, params.viable_band_hi],
           "prev_band": None if prev is None else
                        [prev.viable_band_lo, prev.viable_band_hi],
           "llm": llm, "written": False}
    if write:
        out["written"] = hi.write_setpoint(params)
        if out["written"]:
            opslib.ledger_note("HEART_SETPOINT", {
                "epoch_seq": params.epoch_seq,
                "band_lo": params.viable_band_lo,
                "band_hi": params.viable_band_hi,
                "llm": bool(llm),
            }, actor="heart-doctor")
    return out


_DOCTOR_LLM_ALERTED = False  # module-level dedup: یک warning در عمرِ پروسه، نه هر epoch


def llm_refine(setpoint: "hi.HeartParams", signals: dict) -> dict | None:
    """مسیرِ چند-ایجنتیِ پولی (الگوی allocate_llm): دوقفله — تاریخ + فایلِ مالک.
    بسته/شکست = None (برگشتِ امن به سیاستِ قطعی). امروز ساختاراً بسته است."""
    global _DOCTOR_LLM_ALERTED
    ok, why = opslib.live_gate_open(ACT_HEART_DOCTOR)
    if not ok:
        return None
    # (پشتِ گیت — فقط وقتی مالک باز کند اجرا می‌شود؛ $0 تا آن روز)
    try:
        if str(opslib.DEBATE_DIR) not in sys.path:   # WS-2: idempotent — نشتِ sys.path per-epoch
            sys.path.insert(0, str(opslib.DEBATE_DIR))
        from client import DeepSeekClient  # noqa: E402
        import organ_gate                  # noqa: E402
        system = ("You are the w-slow modulator of a hybrid heart. Given signals, "
                  "propose ONLY a JSON viable_band {lo,hi} for target velocity. "
                  "Never propose a rate/period.")
        user = json.dumps({"setpoint": setpoint.to_json(),
                           "signals": {k: signals.get(k) for k in
                                       ("velocity", "cpi", "delta_self")}},
                          ensure_ascii=False)
        # CONTEXT-FENCE (observe-only، پشتِ OCTOPUS_WIRE_CONTEXT_FENCE): سیگنال/setpoint
        # دادهٔ بازیابی‌شده است نه دستور؛ غربالِ injection پیش از provider — هرگز بلاک/
        # تغییرِ prompt. فلگ خاموش یا هر خطا = مسیرِ قدیم بایت‌به‌بایت (fail-soft).
        # توجه: model_router خودش همین غربال را داخلِ _ask_impl می‌زند، پس مسیرِ router
        # زیر آن پوشش است؛ مسیرِ bespokeِ قدیم این بلوکِ صریح را نگه می‌دارد.
        try:
            _cx = str(_HERE.parent / "cortex")
            if _cx not in sys.path:
                sys.path.insert(0, _cx)
            import fence_adapter  # noqa: WPS433 — lazy، مونکی‌پچ‌پذیرِ تست
            fence_adapter.screen_llm_input("heart.doctor_setpoint", [("memory", user)])
        except Exception:  # noqa: BLE001 — غربال هرگز دکتر را نمی‌کشد
            pass
        # fugu-everywhere (2026-07-24): مسیرِ درِ واحدِ مغز پشتِ OCTOPUS_HEART_DOCTOR_USE_ROUTER.
        # وقتی ۱ → از model_router.ask (tier=secondary، کارِ متوسط)؛ خودش organ_gate +
        # context-fence + local-first + fallback دارد. وقتی ۰ (پیش‌فرض) → مسیرِ bespokeِ زیر.
        if str(os.environ.get("OCTOPUS_HEART_DOCTOR_USE_ROUTER", "")).strip().lower() in ("1", "true", "yes"):
            try:
                _cx2 = str(_HERE.parent / "cortex")
                if _cx2 not in sys.path:
                    sys.path.insert(0, _cx2)
                from model_router import ask as _router_ask  # noqa: WPS433 — lazy
                r = _router_ask("synthesize", user, system=system, max_tokens=400, tier="secondary")
                if not r.get("ok"):
                    return None
                from client import extract_json  # noqa: E402 — فقط parse helper
                return {"suggestion": extract_json(r.get("text", "")),
                        "cost_usd": float(r.get("cost_usd", 0.0))}
            except Exception as e:  # noqa: BLE001 — fail-safe به سیاستِ قطعی
                if not _DOCTOR_LLM_ALERTED:
                    _DOCTOR_LLM_ALERTED = True
                    opslib.alert([f"heart doctor router path failed (fallback به policy): "
                                  f"{type(e).__name__}: {e}"])
                return None
        cli = DeepSeekClient(role="econ")
        est = cli.est_worst_case(len(system) + len(user), max_tokens=400)
        r = organ_gate.reserve("ARCHITECT_SYS", est, task="heart-doctor")
        if not r.get("allow"):
            return None
        try:
            out = cli.complete(system, user, max_tokens=400)
        except Exception:
            organ_gate.release("ARCHITECT_SYS", est, task="heart-doctor")
            raise
        organ_gate.settle("ARCHITECT_SYS", est, out["cost_usd"], task="heart-doctor")
        from client import extract_json  # noqa: E402
        return {"suggestion": extract_json(out["text"]), "cost_usd": out["cost_usd"]}
    except Exception as e:  # noqa: BLE001 — fail-safe به سیاستِ قطعی
        # dedup: یک‌بار در عمرِ پروسه (opslib.alert خودش dedup ندارد) تا
        # governor-alerts هر epoch غرق نشود. fail-safe تغییری نمی‌کند.
        if not _DOCTOR_LLM_ALERTED:
            _DOCTOR_LLM_ALERTED = True
            opslib.alert([f"heart doctor llm failed (fallback قطعی): {e} "
                          f"(هر epoch تکرار نمی‌شود تا زمانی که gate/کلید درست شود.)"])
        return None


if __name__ == "__main__":
    print(json.dumps(run_epoch_setpoint(write=False), ensure_ascii=False, indent=2))
