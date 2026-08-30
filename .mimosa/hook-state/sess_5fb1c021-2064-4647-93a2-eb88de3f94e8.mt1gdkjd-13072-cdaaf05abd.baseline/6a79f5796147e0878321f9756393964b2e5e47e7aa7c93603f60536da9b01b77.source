#!/usr/bin/env python3
"""shadow.py — HH-P5: زنجیرهٔ کاملِ قلب در سایه + predicateِ سیم‌کشیِ زنده.

shadow_step: producers → استریم → setpoint → control_law → سینکِ جدا
(`state/pulse/heart-params-shadow.jsonl` + `heart-shadow-latest.json`).
**هرگز periodِ ارگانیسم را نمی‌نویسد** — تنها مصرف‌کنندهٔ مجازِ خروجی برای periodِ
واقعی، seamِ organism.py است آن هم فقط وقتی production_wire_open()==True.

production_wire_open — predicateِ کاملِ M-HEART §۴ (۸ شرط، همه لازم):
SIM_PASS ∧ equations-locked ∧ Gate-0 (producerِ زندهٔ authoritative) ∧ hash-match ∧
OCTOPUS_WIRE_BIO ∧ OCTOPUS_WIRE_PULSE ∧ ACTIVATION-PULSE.flag (فقط مالک) ∧
تاریخ ≥ 2026-07-21. امروز ساختاراً بسته — درست همین است.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

sys.path.insert(0, str(_HERE.parent))
from heart import control_law as cl               # noqa: E402
from heart import interface as hi                 # noqa: E402
from heart import producers, sim_heart, sog_math  # noqa: E402

SHADOW_SINK = opslib.STATE_DIR / "pulse" / "heart-params-shadow.jsonl"
SHADOW_LATEST = opslib.STATE_DIR / "pulse" / "heart-shadow-latest.json"
ACT_PULSE = opslib.OPS / "ACTIVATION-PULSE.flag"


def shadow_step(beat: int = 0, snap: dict | None = None) -> dict:
    """یک ضربانِ سایه: محاسبهٔ کامل، ثبت در سینکِ جدا، صفر effector."""
    signals = producers.compute_all(write=True)
    v = (signals.get("velocity") or {}).get("velocity_per_hr")
    comps = (signals.get("velocity") or {}).get("components", {})
    # کوواریت‌ها فقط برون‌زاد/بالادستی (ضدِ self-grading — ریویوی خصمانه):
    # confirmed/effects از بازیگرانِ خارجی؛ hour برون‌زادِ محض. هیچ beat/cycle.
    import datetime as _dt
    cov = {"confirmed": comps.get("confirmed") or 0,
           "effects": comps.get("effects") or 0,
           "hour": _dt.datetime.now().hour}
    sampled = False
    if v is not None:
        # نمونه‌گیری روی ساعتِ ثابت (نه ضربان) — decision-frequency invariance
        sampled = producers.append_velocity_sample({"v": v, "cov": cov})
    inputs = cl.gather_inputs(beat)
    inputs["velocity"] = signals.get("velocity")
    inputs["cpi"] = signals.get("cpi")
    inputs["delta"] = signals.get("delta_self")
    setpoint = hi.read_setpoint()
    sig, tel = cl.heart_step(inputs, setpoint)
    wire_ok, wire_reasons = production_wire_open()
    record = {
        "ts": opslib.now_iso(),
        "beat": beat,
        "signal": sig.to_json(),
        "period_s": sig.period_s,
        "telemetry": tel,
        "setpoint": None if setpoint is None else setpoint.to_json(),
        "gate0_live_producer": signals.get("gate0_live_producer"),
        "sampled_this_step": sampled,
        "production_wire": {"open": wire_ok, "reasons": wire_reasons},
        # C8: برچسبِ اصالتِ 4.py — VERIFIED/MISMATCH/UNVERIFIABLE. هیچ عددی را عوض
        # نمی‌کند؛ فقط می‌گوید قفلی که سه گیت را `locked` می‌خواند، از کدام منبع آمده
        # و آیا آن منبع امروز قابلِ راستی‌آزمایی هست یا نه. نویسنده همان نویسندهٔ
        # واحدِ همین ظرف است (LockedJson پایین) — نه فایلِ نو، نه نویسندهٔ دوم.
        "sog_provenance": sog_math.source_provenance(),
        "mode": "shadow",
    }
    try:
        SHADOW_SINK.parent.mkdir(parents=True, exist_ok=True)
        opslib.append_jsonl(SHADOW_SINK, {"ts": record["ts"], "beat": beat,
                                          "period_s": sig.period_s,
                                          "sigma_now": sig.sigma_now,
                                          "baro_factor": sig.baro_factor,
                                          "wire_open": wire_ok})
        with opslib.LockedJson(SHADOW_LATEST) as lj:
            lj.write(record)
    except Exception as e:  # noqa: BLE001 — سایه نباید tick را بکشد
        opslib.alert([f"heart shadow sink write failed: {e}"])
    _append_thesis_measurement(beat, signals, tel)
    return record


# ── مسیرِ رویا: دوامِ Δ_self (رأیِ مالک 2026-07-25، پشتِ OCTOPUS_THESIS_MEASURE) ──
# یافتهٔ زندهٔ 2026-07-25: Δ_self هر ضربان حساب می‌شد و روی `heart-shadow-latest.json`
# **بازنویسی** می‌شد؛ هیچ فایلی جریانش نمی‌داد (`heart-params-shadow.jsonl` فقط ۶ کلیدِ
# باروگیرنده دارد). یعنی مهم‌ترین عددِ ردیفِ `delta-self` دفترِ تز تاریخ نداشت، و
# «آیا Δ با nِ بیشتر مثبت می‌شود؟» ساختاراً غیرقابل‌آزمون بود — نه سخت، غیرممکن.
# این تابع کوچک‌ترین جبران است: یک استریمِ جدا، شمای قلب دست‌نخورده، fail-soft،
# default-off. هیچ تصمیمی از این فایل گرفته نمی‌شود — فقط شاهد جمع می‌کند.
THESIS_MEASURE_FLAG = "OCTOPUS_THESIS_MEASURE"
THESIS_STREAM = opslib.STATE_DIR / "thesis" / "measurements.jsonl"


def _append_thesis_measurement(beat: int, signals: dict, tel: dict) -> bool:
    if os.environ.get(THESIS_MEASURE_FLAG) != "1":
        return False
    try:
        ds = (signals.get("delta_self") or {}) if isinstance(signals, dict) else {}
        row = {"ts": opslib.now_iso(), "beat": int(beat), "row_id": "delta-self",
               "delta_self_live": ds.get("delta_self_live"),
               "authoritative": ds.get("authoritative"),
               "n": ds.get("n") or ds.get("samples"),
               "s_informed": ds.get("S_informed"), "s_blind": ds.get("S_blind"),
               "self_referential": ds.get("self_referential"),
               "metronome_share": ds.get("metronome_share"),
               "gate0_live_producer": signals.get("gate0_live_producer")}
        if row["delta_self_live"] is None and isinstance(tel, dict):
            row["delta_self_live"] = tel.get("delta_self_live")
        THESIS_STREAM.parent.mkdir(parents=True, exist_ok=True)
        opslib.append_jsonl(THESIS_STREAM, row)
        return True
    except Exception:  # noqa: BLE001 — شاهدِ تز هرگز ضربان را نمی‌کشد
        return False


def production_wire_open() -> tuple[bool, list[str]]:
    """۸ شرطِ لازمِ سیم‌کشیِ زنده. خروجی: (باز؟، دلایلِ هر شرطِ بسته)."""
    reasons: list[str] = []
    # ۱) SIM_PASS
    rep = sim_heart.read_report()
    if not rep.get("sim_pass"):
        reasons.append("SIM_PASS غایب/false (HEART-SIM-REPORT)")
    # ۲) equations-locked (Δ_self لازم؛ e_shadow یا locked یا excluded-با-w0)
    lock = sog_math.read_lock()
    status = lock.get("status") or {}
    if status.get("delta_self") != "locked":
        reasons.append("ریاضیِ Δ_self قفل نیست (PULSE-EQUATIONS-LOCKED)")
    w_shadow = float(os.environ.get("HEART_W_SHADOW", "0.0"))
    if w_shadow > 0 and status.get("e_shadow") != "locked":
        reasons.append("w_shadow>0 ولی E_shadow قفل نیست")
    if not lock.get("full_run"):
        reasons.append("lock رسمی نیست (full_run=false)")
    # ۳) Gate-0: producerِ زندهٔ Δ_self — authoritative **و** Δ>0
    # صداقت (2026-07-25، شاهدِ زنده): شرطِ قبلی فقط `authoritative` را می‌خواند، و آن
    # با Δ *منفی* هم True است. یعنی «خودشناسیِ منفی» (مدلِ آگاه بدتر از کورِ محض) این
    # گیت را باز می‌کرد — دقیقاً همان دروغی که T4 در سمتِ producer بست ولی به این
    # مصرف‌کننده نرسیده بود (signals: delta_self_live=-0.027143, authoritative=true,
    # gate0_live_producer=false). این گیت درِ ورودِ قلب به تولید است، پس fail-closed:
    # هم عددِ صادقِ gate0_live_producer (اگر باشد) و هم Δ>0 لازم است.
    signals = producers.read_signals()
    _ds = signals.get("delta_self") or {}
    _gate0 = signals.get("gate0_live_producer")
    if _gate0 is None:                       # فایلِ سیگنالِ قدیمی → به قاعدهٔ قبلی برگرد
        _gate0 = bool(_ds.get("authoritative"))
    _dlive = _ds.get("delta_self_live")
    # ترتیبِ دلیل‌ها = ترتیبِ صداقت: هر شرط دلیلِ *خودش* را بدهد. اگر اول `_gate0` را
    # می‌سنجیدیم، Δِ منفی دلیلِ گمراه‌کنندهٔ «authoritative نیست» می‌گرفت — در حالی که
    # دقیقاً authoritative *است* و مشکل منفی‌بودنِ Δ است.
    if not _ds.get("authoritative"):
        reasons.append("Gate-0: producerِ زندهٔ Δ_self هنوز authoritative نیست")
    elif not (isinstance(_dlive, (int, float)) and _dlive > 0):
        reasons.append(f"Gate-0: Δ_selfِ زنده مثبت نیست (delta_self_live={_dlive}) — "
                       "خودشناسیِ منفی این گیت را باز نمی‌کند")
    elif not _gate0:
        reasons.append("Gate-0: gate0_live_producer در سیگنال false است")
    # ۴) hash-match: control_law فعلی == ثبت‌شده در sim-report
    cur = hashlib.sha256(Path(cl.__file__).read_bytes()).hexdigest()
    if rep.get("code_sha256") != cur:
        reasons.append("hash قانونِ کنترل با SIM-REPORT نمی‌خواند (کد عوض شده — sim دوباره)")
    # ۵،۶) flagهای env (هر دو صریح)
    if os.environ.get("OCTOPUS_WIRE_BIO") != "1":
        reasons.append("OCTOPUS_WIRE_BIO خاموش")
    if os.environ.get("OCTOPUS_WIRE_PULSE") != "1":
        reasons.append("OCTOPUS_WIRE_PULSE خاموش")
    # ۷،۸) فعال‌سازیِ مالک + سپرِ تاریخ (live_gate_open هر دو را چک می‌کند)
    ok, why = opslib.live_gate_open(ACT_PULSE)
    if not ok:
        reasons.append(f"live-gate: {why}")
    return (len(reasons) == 0, reasons)


def read_shadow_latest() -> dict:
    try:
        return (json.loads(SHADOW_LATEST.read_text("utf-8"))
                if SHADOW_LATEST.exists() else {})
    except (OSError, ValueError):
        return {}


if __name__ == "__main__":
    print(json.dumps(shadow_step(beat=0), ensure_ascii=False, indent=2))
