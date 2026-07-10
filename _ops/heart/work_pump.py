#!/usr/bin/env python3
"""work_pump.py — HH-P9: پمپِ کار — «طبق ضربان، کارِ واقعی».

حلقهٔ گم‌شدهٔ vision مالک: ضربانِ (سایهٔ) قلب → اجرای کارِ واقعی → حافظه → ارتقا.
cadenceِ پمپ از **periodِ سایهٔ قلب** فرمان می‌گیرد: قلبِ تندتر = پنجره‌های کارِ
بیشتر در ساعت — بدونِ اینکه tick ارگانیسم یا HLC دست بخورد ($0، additive).

«نقشه‌ریزیِ درونی» v1 = فایلِ planِ ماشین‌خوان (`state/pulse/work-plan.json`) که
templateهای کارِ تکرارشونده را نگه می‌دارد؛ Doctor بعداً از راهِ RFC برایش تغییر
propose می‌کند (human-append). دو ردهٔ کار:
  - $0 (الان اجرا می‌شوند): health-snapshot، gap-report از حافظهٔ مدرسه.
  - paid (سرچ/یادگیریِ LLM): ساختار آماده، پشتِ live-gate (تاریخ ≥ 2026-07-21 +
    پرچمِ فقط-مالک ACTIVATION-WORK-LLM.flag) — تا آن روز صادقانه skip با دلیل.

خطوطِ قرمز: kill-switch اول · هیچ importِ پولی در سطحِ ماژول (مسیرِ paid موظف است
در روزِ بازشدن lazy از organ_gate بگذرد — I2) · هر کار در log + NOTE ثبت می‌شود
(حافظه/ممیزی) · propose-only نسبت به همه‌چیزِ بیرون از state/pulse خودش.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

PULSE_DIR = opslib.STATE_DIR / "pulse"
PLAN_PATH = PULSE_DIR / "work-plan.json"
STATE_PATH = PULSE_DIR / "work-state.json"
LOG_PATH = PULSE_DIR / "work-log.jsonl"
HEALTH_PATH = PULSE_DIR / "work-health.json"
ACT_WORK_LLM = opslib.OPS / "ACTIVATION-WORK-LLM.flag"

DEFAULT_PLAN = {
    "schema": "work-plan.v1",
    "note": "نقشهٔ درونیِ کار — تغییرِ ساختاری فقط با RFC/رأی مالک",
    "templates": [
        {"kind": "health", "every_s": 21600, "paid": False,
         "goal": "اسنپ‌شاتِ سلامتِ بدن برای حافظه/کابین"},
        {"kind": "gap_report", "every_s": 43200, "paid": False,
         "goal": "کم‌آگاه‌ترین موضوع‌های مدرسه — خوراکِ نقشهٔ یادگیری"},
        {"kind": "search", "every_s": 86400, "paid": True,
         "goal": "سرچِ واقعیِ وب برای گپِ روز (provider = رأی مالک)"},
        {"kind": "llm_learn", "every_s": 86400, "paid": True,
         "goal": "چکیده‌سازی/یادگیریِ LLM از یافته‌ها → حافظهٔ ماندگار"},
    ],
}
MIN_PUMP_INTERVAL_S = 60.0


def _read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}


def load_plan() -> dict:
    """plan را بخوان؛ اولین بار seed کن (تنها نوشتنِ ساختاری، atomic)."""
    plan = _read_json(PLAN_PATH)
    if plan.get("schema") == "work-plan.v1" and plan.get("templates"):
        return plan
    try:
        PULSE_DIR.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(PLAN_PATH) as lj:
            lj.write(DEFAULT_PLAN)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"work_pump plan seed failed: {e}"])
    return DEFAULT_PLAN


def _now_ts(now: dt.datetime | None) -> float:
    return (now or dt.datetime.now()).timestamp()


# ─── اجراکننده‌های $0 ───────────────────────────────────────────────────────────
def _exec_health() -> dict:
    """اسنپ‌شاتِ سبکِ سلامت: تلمتری + قلبِ سایه → فایلِ health (خوراکِ کابین/حافظه)."""
    tel = _read_json(opslib.STATE_DIR / "telemetry-latest.json")
    shadow = _read_json(PULSE_DIR / "heart-shadow-latest.json")
    rep = _read_json(opslib.STATE_DIR / "replication-latest.json")
    out = {
        "ts": opslib.now_iso(),
        "month_aud": (tel.get("month") or {}).get("aud"),
        "suspect_zero": tel.get("suspect_zero_total"),
        "sigma": ((rep.get("sigma") or {}).get("sigma_effective")),
        "period_shadow_s": shadow.get("period_s"),
        "gate0": shadow.get("gate0_live_producer"),
        "wire_open": (shadow.get("production_wire") or {}).get("open"),
    }
    try:
        with opslib.LockedJson(HEALTH_PATH) as lj:
            lj.write(out)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
    return {"ok": True, "summary": {k: out[k] for k in
                                    ("sigma", "period_shadow_s", "gate0")}}


def _exec_gap_report() -> dict:
    """سه موضوعِ کم‌آگاهِ مدرسه (فقط‌خواندنی) — خوراکِ سرچ/یادگیریِ آینده."""
    sch = _read_json(opslib.STATE_DIR / "school-awareness.json")
    aw = sch.get("awareness") or {}
    if not aw:
        return {"ok": True, "gaps": [], "note": "مدرسه هنوز آگاهی ثبت نکرده"}
    gaps = sorted(aw.items(), key=lambda kv: kv[1])[:3]
    return {"ok": True, "gaps": [{"topic": k, "awareness": round(v, 4)}
                                 for k, v in gaps]}


def _exec_paid_lane(kind: str, tpl: dict) -> dict:
    """ردهٔ paid (search/llm_learn): دوقفله — تاریخ + پرچمِ مالک. بسته → skipِ صادق.
    روزی که باز شود، هر call موظف است lazy از organ_gate بگذرد (الگوی allocate_llm)."""
    ok, why = opslib.live_gate_open(ACT_WORK_LLM)
    if not ok:
        return {"ok": False, "skipped": f"live-locked: {why}",
                "unlock": "تاریخ ≥ 2026-07-21 + ACTIVATION-WORK-LLM.flag (فقط مالک) "
                          "+ providerِ سرچ با رأی مالک (HH-P9)"}
    # (فقط پشتِ گیتِ باز اجرا می‌شود — پیاده‌سازیِ providerها در HH-P9 گامِ ۳)
    return {"ok": False, "skipped": "provider-not-wired: رأی مالک برای provider لازم است"}


_EXECUTORS = {"health": _exec_health, "gap_report": _exec_gap_report}


# ─── پمپ ────────────────────────────────────────────────────────────────────────
def pump_step(beat: int = 0, period_s: float | None = None,
              now: dt.datetime | None = None) -> dict:
    """یک پنجرهٔ کار، هم‌گام با ضربانِ سایه.

    فاصلهٔ بینِ دو پنجره = max(periodِ سایه، ۶۰s) — قلبِ تندتر (periodِ کوتاه‌تر)
    یعنی پنجره‌های کارِ بیشتر در ساعت؛ قلبِ در استراحت (MAX=900) یعنی کارِ کمتر.
    در هر پنجره حداکثر یک taskِ سررسید اجرا می‌شود (کران‌دار، ضدِ طوفانِ کار)."""
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return {"skipped": "kill-switch"}
    if opslib.frozen():
        return {"skipped": "FREEZE"}
    ts = _now_ts(now)
    state = _read_json(STATE_PATH)
    interval = max(float(period_s or 300.0), MIN_PUMP_INTERVAL_S)
    last = float(state.get("last_window_ts", 0.0))
    if ts - last < interval:
        return {"idle": "not-due", "next_in_s": round(interval - (ts - last), 1)}
    plan = load_plan()
    last_run = state.get("last_run") or {}
    picked = None
    for tpl in plan.get("templates", []):
        kind = tpl.get("kind")
        if not kind:
            continue
        if ts - float(last_run.get(kind, 0.0)) >= float(tpl.get("every_s", 86400)):
            picked = tpl
            break
    result: dict
    if picked is None:
        result = {"idle": "no-task-due"}
    else:
        kind = picked["kind"]
        if picked.get("paid"):
            result = {"kind": kind, **_exec_paid_lane(kind, picked)}
        else:
            fn = _EXECUTORS.get(kind)
            result = {"kind": kind, **(fn() if fn
                                       else {"ok": False, "error": "no-executor"})}
        last_run[kind] = ts
        rec = {"ts": opslib.now_iso(), "beat": beat,
               "period_s": period_s, **result}
        try:
            opslib.append_jsonl(LOG_PATH, rec)
        except Exception as e:  # noqa: BLE001
            opslib.alert([f"work_pump log failed: {e}"])
        if result.get("ok"):
            opslib.ledger_note("WORK_PUMP", {
                "kind": kind, "beat": beat,
                "period_s": period_s}, actor="heart-work-pump")
    try:
        with opslib.LockedJson(STATE_PATH) as lj:
            lj.write({"last_window_ts": ts, "last_run": last_run,
                      "ts": opslib.now_iso()})
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"work_pump state write failed: {e}"])
    return result


def read_log(n: int = 20) -> list[dict]:
    """آخرین n کار (برای کابین/ممیزی). fail-soft."""
    if not LOG_PATH.exists():
        return []
    try:
        lines = LOG_PATH.read_text("utf-8").splitlines()[-n:]
        return [json.loads(x) for x in lines if x.strip()]
    except (OSError, ValueError):
        return []


if __name__ == "__main__":
    print(json.dumps(pump_step(beat=0, period_s=60.0), ensure_ascii=False, indent=2))
