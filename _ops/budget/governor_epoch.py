#!/usr/bin/env python3
"""
governor_epoch.py — T3 پک: حلقهٔ Governor در shadow-mode. صفر enforce، فقط لاگ.

ارتقای هندسی (بینش ۱ ادغام): epoch یک clock ثابت نیست؛ «آلوستاتیک» است —
طول epoch تابع فشار است و سیستم زیر فشار تندتر می‌تپد:

    epoch_minutes = clamp( base · (1 − k·pressure), base/4 .. base·2 )
    pressure = max(spend_velocity, deadline_proximity, anomaly)

  spend_velocity     = مصرف امروز / سقف burst روزانه (budget_gate.CEIL_DAY_AUD تبدیل‌شده به USD — V1 قفل 2026-07-07)
  deadline_proximity = سیگموید ۱۴روزهٔ نزدیک‌ترین deadline ارگان‌ها (DEADLINE SHIELD، H5)
  anomaly            = FREEZE/halt/suspectهای متر صفر

re-plan استراتژیک هفتگی (جمعه) = حلقهٔ کند (slow manifold) — فقط برچسب گزارش، نه مکانیزم جدا.

دو مود:
  dry (پیش‌فرض، $0): تخصیص‌گر قطعی همین فایل منطق داروینی S1..S5 سند METABOLIC را
      روی تلمتری واقعی اجرا و فقط JSON را لاگ می‌کند.
  llm (دوقفله: ACTIVATION-GOVERNOR-LLM.flag مالک + کلید): همان ورودی به مدل econ
      (از budgets.yaml) با system prompt رسمی prompts/metabolic-governor-v0.1.txt؛
      خودِ Governor هم از organ_gate با ارگان ARCHITECT_SYS متر می‌شود (پک: «خود-متر شدن»).

خروجی هر epoch: _ops/budget/epochs/epoch-<ts>.json + NOTE(subtype=ALLOCATION_SHADOW)
به ledger زنجیرهٔ‌هش ژنوم. هیچ‌چیز قطع/اعمال نمی‌شود (I2).
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opslib      # noqa: E402
import telemetry   # noqa: E402

EPOCH_DIR = opslib.BUDGET_DIR / "epochs"
BASE_MIN_DEFAULT = 60.0     # پایهٔ آرام؛ آلوستاتیک بین base/4 و base*2 حرکت می‌کند
PRESSURE_GAIN = 0.75

# P4 (truth-map 2026-07-17): گاورنر-LLM هر epoch اجرا می‌شود؛ یک شرطِ ثابتِ پیکربندی
# (مثلِ قیمتِ قفل‌نشدهٔ DeepSeek → PriceNotLocked) نباید ساعتی همان ⚠️ را اسپم کند
# (۹۵ تکرار در لاگ). هر پیامِ یکتا فقط یک‌بار در هر session (تا restart) هشدار می‌دهد.
_GOV_LLM_ALERTED: set[str] = set()


def _gov_llm_alert_once(key: str, msg: str) -> None:
    """هشدارِ گاورنر-LLM با dedupِ session روی «کلید» — پیامِ تکراری لاگ را غرق نمی‌کند.
    یک اجرای موفق کلیدها را re-arm می‌کند تا خفتگیِ بعدی دوباره یک‌بار هشدار دهد."""
    if key in _GOV_LLM_ALERTED:
        return
    _GOV_LLM_ALERTED.add(key)
    opslib.alert([msg])


def _deadline_proximity(organs: dict) -> tuple[float, str]:
    """سیگموید تیز داخل ۱۴ روز پایانی (H5). خروجی 0..1 + نزدیک‌ترین ددلاین."""
    best, best_name = 0.0, ""
    for name, cfg in organs.items():
        d = cfg.get("deadline")
        if not d:
            continue
        days = (dt.date.fromisoformat(str(d)) - dt.date.today()).days
        x = 1.0 / (1.0 + math.exp((days - 7) / 2.0))   # ~۰ دور، تیز از ~۱۴ روز، ~۱ در ددلاین
        if x > best:
            best, best_name = x, f"{name}@{d} ({days}d)"
    return best, best_name


def pressure_state(snap: dict) -> dict:
    organs = opslib.organ_table()
    try:
        import budget_gate  # noqa: F401
        sys.path.insert(0, str(opslib.SCRIPTS))
        import budget_gate as bg
        burst_cap = bg.CEIL_DAY_AUD / bg.AUD  # سقف burst روزانه به USD (V1: سقف AUD، state به USD)
    except Exception:
        burst_cap = 2.0 / 1.5
    velocity = min(1.0, snap["today"]["usd"] / burst_cap) if burst_cap else 1.0
    deadline, deadline_ref = _deadline_proximity(organs)
    anomaly = 1.0 if (opslib.frozen() or opslib.halted()) else \
        min(1.0, snap.get("suspect_zero_total", 0) / 10.0)
    p = max(velocity, deadline, anomaly)
    return {"spend_velocity": round(velocity, 3), "deadline_proximity": round(deadline, 3),
            "deadline_ref": deadline_ref, "anomaly": round(anomaly, 3), "pressure": round(p, 3)}


def epoch_length_minutes(pressure: float, base_min: float = BASE_MIN_DEFAULT) -> float:
    """آلوستاتیک: فشار بالا → تپش تند (تا base/4)؛ آرامش → متابولیسم پایه (تا base×2)."""
    raw = base_min * (1.0 - PRESSURE_GAIN * pressure)
    return max(base_min / 4.0, min(base_min * 2.0, raw))


def _fitness_dry(snap: dict, organs: dict, weights: dict) -> dict[str, float]:
    """پروکسی قطعی fitness در فاز سایه (EFFICIENCY هنوز خنثی — ~۴ هفته دیتا لازم است؛
    verdict جلسه ۱۶: fitness عددی تا آن موقع فقط سایه)."""
    per_organ = snap.get("per_organ_alltime_musd", {})
    total = max(1, sum(v for k, v in per_organ.items() if not k.startswith("UNMAPPED")))
    _, deadline_ref = _deadline_proximity(organs)
    out = {}
    for name, cfg in organs.items():
        d = cfg.get("deadline")
        days = (dt.date.fromisoformat(str(d)) - dt.date.today()).days if d else 999
        urgency = 1.0 / (1.0 + math.exp((days - 7) / 2.0))
        value = 0.5                                  # پروکسی خنثی تا اتصال APPROVALها (fitness.py)
        efficiency = 0.5                             # خنثی — baseline شخصی هنوز شکل نگرفته
        human = float(cfg.get("human_priority", 1.0)) / 3.0
        waste = min(1.0, snap.get("suspect_zero_total", 0) / 20.0)
        out[name] = round(
            weights.get("value", .3) * value + weights.get("urgency", .25) * urgency
            + weights.get("efficiency", .2) * efficiency + weights.get("human", .2) * human
            - weights.get("waste", .05) * waste, 4)
    return out


def allocate_dry(snap: dict) -> dict:
    """S1..S5 قطعی: FLOOR همه محفوظ (H2) → EXPLORE_PCT رزرو جهش (S3) → headroom به نسبت
    fitness (S2). DEADLINE SHIELD (H5): ارگان ددلاین‌دار زیر FLOOR نمی‌رود (اینجا FLOOR = کف).
    تمام حساب در میکرو-AUD صحیح؛ سهم رقابتی floor می‌شود، پس جمع grantها ساختاراً هرگز
    از cap رد نمی‌شود (round-up تک‌تک ارگان‌ها قبلاً جمع را 0.0001 بالای cap می‌برد — H1 کاذب)."""
    b = opslib.load_budgets()
    g = b["global"]
    organs = opslib.organ_table()
    fx, _ = opslib.fx_aud_per_usd()
    cap = float(g.get("cap_monthly", 30))
    cap_u = opslib.micro(cap)
    explore_u = opslib.micro(cap * float(g.get("explore_pct", 0.10)))
    floors_u = {n: opslib.micro(float(c.get("floor", 0))) for n, c in organs.items()}
    headroom_u = max(0, cap_u - sum(floors_u.values()) - explore_u)
    fit = _fitness_dry(snap, organs, g.get("weights", {}))
    fit_pos = {n: max(0.001, f) for n, f in fit.items()}
    fit_sum = sum(fit_pos.values())
    grants = {}
    total_u = explore_u
    for name in organs:
        share_u = int(headroom_u * fit_pos[name] / fit_sum)
        tot_u = floors_u[name] + share_u
        total_u += tot_u
        grants[name] = {
            "verdict": "GRANT",
            "floor_aud": floors_u[name] / 1e6,
            "competitive_aud": share_u / 1e6,
            "total_month_aud": tot_u / 1e6,
            "fitness": fit[name],
            "tag": "SPEC(shadow — صفر enforce)",
        }
    spent_aud = snap["month"]["aud"]
    return {"cap_monthly_aud": cap, "explore_reserve_aud": explore_u / 1e6,
            "spent_month_aud": spent_aud, "fx_aud_per_usd": fx,
            "grants": grants,
            "h1_check": {"sum_grants_aud": total_u / 1e6,
                         "cap_aud": cap,
                         "ok": total_u <= cap_u}}


# ─── POOL-BAR-DARSAD — barbell allocation (propose-only، additive) ────────────
# تخصیصِ کوشش/API بر اساسِ barbell: CORE~70/SATELLITE~30، satellite_cap،
# تنظیمِ درصد بر اساسِ CONFIRMED AUD، survival-cull (نه payback)، hysteresis.
# این یک مسیرِ parallel/additive است — allocate_dry دست‌نخورده.

def barbell_allocate(confirmed_by_organ: dict | None = None,
                     prev_pcts: dict | None = None,
                     zero_streak: dict | None = None,
                     budgets: dict | None = None) -> dict:
    """تخصیصِ barbell بر اساسِ CONFIRMED AUD. propose-only.
    - confirmed_by_organ: {organ: AUD_confirmed} از attribution.confirmed_revenue
    - prev_pcts: درصدِ قبلیِ هر organ (برای hysteresis). None = شروعِ مساوی.
    - zero_streak: {organ: days_since_last_confirmed} برای survival-cull.
    - budgets: قابل‌تزریق برای تست (نه harness mock). None = opslib.load_budgets().
    خروجی: {organ: pct, barbell: {core_share, satellite_share}, culled: [...], propose_only: True}.
    satellite_cap_pct = سقفِ سختِ هر satellite. hysteresis_max_delta = تغییرِ مجاز."""
    b = budgets or opslib.load_budgets()
    alloc_cfg = (b.get("allocation") or {}).get("barbell", {})
    core_share = float(alloc_cfg.get("core_share", 0.70))
    sat_share = float(alloc_cfg.get("satellite_share", 0.30))
    sat_cap = float(alloc_cfg.get("satellite_cap_pct", 0.10))
    cull_days = int(alloc_cfg.get("cull_zero_streak_days", 30))
    hyst = float(alloc_cfg.get("hysteresis_max_delta", 0.05))
    core_members = set((b.get("allocation") or {}).get("core_members", []))
    sat_members = set((b.get("allocation") or {}).get("satellite_members", []))
    confirmed = confirmed_by_organ or {}
    prev = prev_pcts or {}
    streak = zero_streak or {}

    # ۱) survival-cull: satellite با سیگنالِ صفرِ پایدار → cull (نه payback)
    culled = []
    for org in sat_members:
        days = streak.get(org, 0)
        if days >= cull_days and confirmed.get(org, 0) <= 0:
            culled.append(org)

    # ۲) percentage اولیه: بر اساسِ CONFIRMED AUD درونِ هر گروه
    def _group_pcts(members, total_share):
        # سهم هر organ بر اساسِ CONFIRMED AUD (نسبی درونِ گروه)
        active = [m for m in members if m not in culled]
        confirmed_sum = sum(max(0.0, confirmed.get(m, 0.0)) for m in active)
        pcts = {}
        for m in active:
            if confirmed_sum > 0:
                pcts[m] = (max(0.0, confirmed.get(m, 0.0)) / confirmed_sum) * total_share
            else:
                # بدونِ داده → مساوی تقسیم
                pcts[m] = total_share / max(1, len(active))
        return pcts

    raw_pcts = {}
    raw_pcts.update(_group_pcts(core_members, core_share))
    raw_pcts.update(_group_pcts(sat_members, sat_share))

    # ۳) satellite cap: هیچ satellite از sat_cap بیشتر نگیرد
    capped = {}
    overflow = 0.0
    for org, pct in raw_pcts.items():
        if org in sat_members:
            capped_val = min(pct, sat_cap)
            overflow += (pct - capped_val)
            capped[org] = capped_val
        else:
            capped[org] = pct
    # overflow را به core بده (تناسبی)
    if overflow > 0 and core_members:
        core_confirmed_sum = sum(max(0.0, confirmed.get(m, 0.0)) for m in core_members if m not in culled)
        for org in core_members:
            if org in culled:
                continue
            if core_confirmed_sum > 0:
                capped[org] = capped.get(org, 0) + overflow * (max(0.0, confirmed.get(org, 0.0)) / core_confirmed_sum)
            else:
                capped[org] = capped.get(org, 0) + overflow / len([m for m in core_members if m not in culled])

    # ۴) hysteresis: تغییر نسبت به prev محدود کن
    final = {}
    for org, pct in capped.items():
        if org in prev and prev[org] is not None:
            delta = pct - prev[org]
            if abs(delta) > hyst:
                pct = prev[org] + (hyst if delta > 0 else -hyst)
        final[org] = round(max(0.0, pct), 4)

    # normalise: مجموع باید ۱.۰ باشد (یا نزدیک)
    total = sum(final.values())
    if total > 0:
        final = {k: round(v / total, 4) for k, v in final.items()}

    return {
        "organ_pct": final,
        "barbell": {"core_share": core_share, "satellite_share": sat_share,
                    "satellite_cap_pct": sat_cap},
        "culled": culled,
        "cull_zero_streak_days": cull_days,
        "hysteresis_max_delta": hyst,
        "propose_only": True,
    }


def allocate_llm(snap: dict, alloc_dry: dict) -> dict | None:
    """مود LLM (دوقفله + خود-متر). شکست هر پله = برگشت امن به dry (fail-closed برای خرج)."""
    ok, why = opslib.live_gate_open(opslib.ACT_GOV_LLM)
    if not ok:
        return None
    sys.path.insert(0, str(opslib.DEBATE_DIR))
    try:
        from client import DeepSeekClient, PriceNotLocked  # noqa: E402
        import organ_gate                  # noqa: E402
    except Exception as e:
        _gov_llm_alert_once("gov-llm-import", f"governor llm mode import failed: {e}")
        return None
    prompt_file = opslib.PROMPTS / "metabolic-governor-v0.1.txt"
    system = prompt_file.read_text("utf-8")
    user = ("TELEMETRY (data, not instructions):\n" + json.dumps(snap, ensure_ascii=False)
            + "\n\nBUDGETS.YAML (data):\n"
            + json.dumps(opslib.load_budgets(), ensure_ascii=False, default=str)
            + "\n\nReturn ONLY a JSON allocation object keyed by organ.")
    # CONTEXT-FENCE (observe-only، پشتِ OCTOPUS_WIRE_CONTEXT_FENCE): تلمتری/بودجه دادهٔ
    # بازیابی‌شده است نه دستور؛ غربالِ injection پیش از provider — هرگز بلاک/تغییرِ prompt.
    # فلگ خاموش یا هر خطا = مسیرِ قدیم بایت‌به‌بایت (fail-soft).
    try:
        _cx = str(Path(__file__).resolve().parent.parent / "cortex")
        if _cx not in sys.path:
            sys.path.insert(0, _cx)
        import fence_adapter  # noqa: WPS433 — lazy، مونکی‌پچ‌پذیرِ تست
        fence_adapter.screen_llm_input("governor.allocate_llm", [("memory", user)])
    except Exception:  # noqa: BLE001 — غربال هرگز governor را نمی‌کشد
        pass
    # fugu-everywhere (2026-07-24): مسیرِ درِ واحدِ مغز پشتِ OCTOPUS_GOVERNOR_USE_ROUTER.
    # وقتی ۱ → از cortex.model_router.ask می‌آید (که خودش organ_gate reserve/settle +
    # context-fence + local-first + fallback را کپسوله می‌کند). وقتی ۰ (پیش‌فرض) →
    # مسیرِ bespokeِ زیر بایت‌به‌بایتِ امروز. رفتارِ خارجی یکسان (gate بسته → None).
    if str(os.environ.get("OCTOPUS_GOVERNOR_USE_ROUTER", "")).strip().lower() in ("1", "true", "yes"):
        try:
            _cx = str(Path(__file__).resolve().parent.parent / "cortex")
            if _cx not in sys.path:
                sys.path.insert(0, _cx)
            from model_router import ask as _router_ask  # noqa: WPS433 — lazy
            r = _router_ask("orchestrate", user, system=system, max_tokens=1200, tier="primary")
            if not r.get("ok"):
                return None
            from client import extract_json  # noqa: E402 — فقط parse helper
            _GOV_LLM_ALERTED.clear()
            return {"llm_allocation": extract_json(r.get("text", "")),
                    "model": r.get("model"), "cost_usd": float(r.get("cost_usd", 0.0))}
        except PriceNotLocked as e:
            _gov_llm_alert_once("gov-llm-dormant", f"governor llm خفته (dry): {e}")
            return None
        except Exception as e:  # noqa: BLE001
            _gov_llm_alert_once("gov-llm-error", f"governor router path failed (fallback به dry): {e}")
            return None
    try:
        cl = DeepSeekClient(role="econ")
        est = cl.est_worst_case(len(system) + len(user), max_tokens=1200)
        r = organ_gate.reserve("ARCHITECT_SYS", est, task="governor-epoch")
        if not r.get("allow"):
            opslib.alert([f"governor llm denied by gate: {r.get('reason')}"])
            return None
        try:
            out = cl.complete(system, user, max_tokens=1200)
        except Exception:
            organ_gate.release("ARCHITECT_SYS", est, task="governor-epoch")
            raise
        organ_gate.settle("ARCHITECT_SYS", est, out["cost_usd"], task="governor-epoch")
        from client import extract_json  # noqa: E402
        _GOV_LLM_ALERTED.clear()   # اجرای موفق → همهٔ کلیدها re-arm (خفتگیِ بعدی دوباره هشدار می‌دهد)
        return {"llm_allocation": extract_json(out["text"]),
                "model": out["model"], "cost_usd": out["cost_usd"]}
    except PriceNotLocked as e:
        # شرطِ پیکربندی، نه خطای اجرا: fail-closed (خرجِ پول با نرخِ نامعلوم ممنوع) درست
        # است. یک‌بار هشدارِ «خفته» + برگشتِ امن به dry. مالک price_in/price_out را در
        # budgets.yaml قفل کند (با verdict) یا ACTIVATION-GOVERNOR-LLM.flag را بردارد.
        _gov_llm_alert_once("gov-llm-dormant", f"governor llm خفته (dry): {e}")
        return None
    except Exception as e:  # noqa: BLE001
        _gov_llm_alert_once("gov-llm-error", f"governor llm epoch failed (fallback به dry): {e}")
        return None


def run_epoch(base_min: float = BASE_MIN_DEFAULT) -> dict:
    """یک epoch کامل سایه. برگشتی شامل طول epoch بعدی (برای organism)."""
    stop = opslib.halted()
    snap = telemetry.snapshot()
    conflicts = telemetry.reconcile(snap)
    pres = pressure_state(snap)
    nxt = epoch_length_minutes(pres["pressure"], base_min)
    is_friday = dt.date.today().weekday() == 4
    record = {
        "ts": opslib.now_iso(),
        "epoch_mode": "allostatic — تابع فشار (نه clock ثابت)",
        "pressure": pres,
        "next_epoch_minutes": round(nxt, 1),
        "weekly_replan": is_friday,
        "halted": stop, "frozen": opslib.frozen(), "conflicts": conflicts,
        "telemetry_month": snap["month"], "suspects": snap["suspect_zero_total"],
    }
    # HH-P3: autoregulation قلب — velocity استال → فشارِ کران‌دار؛ Internal-CPI بالا →
    # Governor سفت (epoch کش می‌آید). additive پشتِ OCTOPUS_WIRE_HEART؛ فقط cadence —
    # allocate_dry/pressure_state بایت‌به‌بایت دست‌نخورده (نرخِ خام هرگز spend را تعیین نمی‌کند).
    if not stop and not conflicts and os.environ.get("OCTOPUS_WIRE_HEART") == "1":
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from heart import autoregulation as _autoreg
            _hv = _autoreg.governor_view(snap)
            record["heart_autoreg"] = _hv
            if _hv.get("available"):
                _p_eff = min(1.0, max(pres["pressure"],
                                      float(_hv.get("heart_pressure", 0.0))))
                _nxt_h = epoch_length_minutes(_p_eff, base_min)
                _nxt_h = min(base_min * 2.0,
                             _nxt_h * float(_hv.get("epoch_damping", 1.0)))
                record["next_epoch_minutes_raw"] = record["next_epoch_minutes"]
                record["next_epoch_minutes"] = round(_nxt_h, 1)
                record["heart_pressure_effective"] = round(_p_eff, 3)
        except Exception as _hge:  # noqa: BLE001 — §۴: کوپل نباید epoch را بکشد
            opslib.alert([f"governor heart autoreg failed (non-fatal): "
                          f"{type(_hge).__name__}: {_hge}"])
    if not stop and not conflicts:
        record["allocation_dry"] = allocate_dry(snap)
        # Phase 1: epoch-based sweep of stale gated_effects (fail-soft).
        # چون chrono.db فقط در organism موجود است، sweep hook واقعی
        # در organism.py tick loop قرار دارد. اینجا فقط placeholder record.
        try:
            _chrono_dir = Path(__file__).resolve().parent.parent
            sys.path.insert(0, str(_chrono_dir))
            import chrono as _chrono_mod
            if _chrono_mod is not None and hasattr(_chrono_mod, "ChronoDB"):
                _db_path = _chrono_dir / "state" / "chrono.db"
                if _db_path.exists():
                    _cdb = _chrono_mod.ChronoDB(str(_db_path))
                    _gate = _chrono_mod.EffectorGate(db=_cdb)
                    _sweep = _gate.sweep_stale_effects()
                    if _sweep["refused"] > 0:
                        record["effect_sweep"] = _sweep
        except Exception:  # noqa: BLE001 — sweep نباید epoch را بکشد
            pass
        llm = allocate_llm(snap, record["allocation_dry"])
        if llm:
            record["allocation_llm"] = llm
        # پول‌بر‌درصد: barbell allocation پشتِ flag (additive، propose-only).
        # allocation_dry دست‌نخورده می‌ماند؛ barbell یک نمایِ parallel است.
        if os.environ.get("OCTOPUS_WIRE_BARBELL") == "1":
            try:
                import attribution as _attr_mod
                rev = _attr_mod.confirmed_revenue()
                confirmed_by_organ = {}
                for cell, aud in (rev.get("by_cell") or {}).items():
                    confirmed_by_organ[cell] = aud
                record["allocation_barbell"] = barbell_allocate(
                    confirmed_by_organ=confirmed_by_organ)
            except Exception as _be:  # noqa: BLE001 — §۴
                opslib.alert([f"governor barbell failed (non-fatal): {type(_be).__name__}: {_be}"])
        # Debate loop (Stage-2 creator×architect) پشتِ flag. run_debate خودش live-gated است
        # (live_gate_open تا ۲۰۲۶-۰۷-۲۱). propose-only در paper.
        if os.environ.get("OCTOPUS_WIRE_DEBATE") == "1":
            try:
                sys.path.insert(0, str(opslib.DEBATE_DIR))
                from debate_loop import run_debate as _run_debate
                import topics as _debate_topics  # noqa: E402
                # قرارداد topic: فقط از whitelist ضدتزریق (id/source/text) — dict آزاد
                # KeyError می‌داد. seed-3 = ارزش‌سنجی governor سایه (همان epoch-strategy).
                # snap عمداً وارد topic نمی‌شود (topic داده است، نه کانال ورودی آزاد).
                # DEFECT-W4: هاردکدِ seed-3 یعنی حلقه هر epoch همان یک موضوع را تکرار
                # می‌کرد (۶۳ رویدادِ EXPERIENCE، همه seed-3). پشتِ همان فلگِ مغزِ محلی،
                # whitelist می‌چرخد؛ شمارنده = تعدادِ epochهای قبلی (بدونِ state جدید).
                _topic = _debate_topics.get_topic("seed-3")
                if os.environ.get("OCTOPUS_WIRE_DEBATE_LOCAL") == "1":
                    try:
                        _seq = len(list(EPOCH_DIR.glob("epoch-*.json")))
                        _topic = _debate_topics.next_topic(_seq) or _topic
                    except Exception:  # noqa: BLE001 — چرخش هرگز epoch را نمی‌کشد
                        pass
                record["debate"] = _run_debate(_topic, live=False)
            except Exception as _de:  # noqa: BLE001 — §۴
                opslib.alert([f"governor debate failed (non-fatal): {type(_de).__name__}: {_de}"])
    EPOCH_DIR.mkdir(parents=True, exist_ok=True)
    fname = EPOCH_DIR / ("epoch-" + dt.datetime.now().strftime("%Y%m%dT%H%M%S%f") + ".json")
    fname.write_text(json.dumps(record, ensure_ascii=False, indent=2), "utf-8")
    opslib.ledger_note("ALLOCATION_SHADOW", {
        "pressure": pres["pressure"], "next_epoch_minutes": record["next_epoch_minutes"],
        "spent_month_aud": snap["month"]["aud"], "conflicts": len(conflicts),
        "h1_ok": record.get("allocation_dry", {}).get("h1_check", {}).get("ok"),
        "epoch_file": fname.name}, actor="governor")
    return record


if __name__ == "__main__":
    print(json.dumps(run_epoch(), ensure_ascii=False, indent=2))
