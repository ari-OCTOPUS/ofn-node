#!/usr/bin/env python3
"""
organ_gate.py — T2 پک: گیت per-organ *روی* budget_gate (نه جایگزینش).

قرارداد (سازگار با budget_gate): قبل از هر call → reserve(organ, est_usd)؛
اگر allow: بعد از call → settle(organ, est_usd, actual_usd)؛ شکست call → release.

زنجیرهٔ تصمیم (deny هر لایه = deny کل، fail-closed):
  STOP/STOP-METABOLIC → FREEZE.flag → ارگان ناشناخته → state ناخوانا →
  سقف ماهانهٔ ارگان (AUD، از budgets.yaml) → budget_gate.reserve (سراسری، تنها enforcer).

اعداد: FLOOR/cap/priority همه از budgets.yaml (I6: هیچ عددی در این کد نیست).
تفسیر فاز سایه: تا Governor زنده نشده، سقف ماهانهٔ هر ارگان = FLOOR خودش (سهمیهٔ حیات)؛
grant بیشتر فقط از مسیر Governor→verdict انسانی خواهد آمد.

⚠ SHARD (V1، دست‌نخورده طبق پک): budget_gate.py سه مسئلهٔ ثبت‌شده دارد —
  CEIL_DAY_USD=2.0 هاردکد (تفسیر فعلی: سقف burst روزانه)؛ پارامتر agent بی‌اثر
  (همین فایل جبرانش می‌کند)؛ خط DISASTER مقدار AUD را با ثابت USD مقایسه می‌کند
  (budget_gate.py:90). فیکس فقط با verdict مالک؛ این لایه دفاعی رفتار می‌کند:
  settle ناموفق/استثنا → FREEZE (حسابداری نامعلوم = توقف خرج، نه ادامهٔ کور).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opslib  # noqa: E402

sys.path.insert(0, str(opslib.SCRIPTS))
import budget_gate  # noqa: E402  — تنها enforcer (I2)


def _log(op: str, organ: str, est: float, verdict: dict, task: str = "") -> None:
    opslib.append_jsonl(opslib.ORGAN_LOG, {
        "ts": opslib.now_iso(), "op": op, "organ": organ,
        "est_usd": est, "task": task, **verdict})


def _roll(state: dict) -> dict:
    t, m = opslib.today(), opslib.month()
    if state.get("month") != m:
        state = {"month": m, "organs": {}}
    state.setdefault("organs", {})
    for o in state["organs"].values():
        if o.get("date") != t:
            o["date"], o["spent_today_musd"] = t, 0
    return state


def _refund_global(organ: str, est_usd: float) -> None:
    """رزروِ سراسریِ گرفته‌شده ولی ثبت‌نشده در state ارگان را پس می‌دهد (ضد نشت بودجه).
    شکستِ خودِ refund = حسابداری نامعلوم → FREEZE (همان فلسفهٔ settle)."""
    try:
        budget_gate.settle(organ, est_usd, 0.0)
    except Exception as e:  # noqa: BLE001
        opslib.freeze(f"reserve-rollback failed for {organ}: {e}")


def reserve(organ: str, est_usd: float, task: str = "") -> dict:
    """گیت دومرحله‌ای. خروجی: {allow: bool, reason?: str, reserved?: float}."""
    stop = opslib.halted()
    if stop:
        v = {"allow": False, "reason": f"halted:{stop}"}
        _log("reserve", organ, est_usd, v, task); return v
    if opslib.frozen():
        v = {"allow": False, "reason": "frozen-conflict (I3) — رفع دستی FREEZE.flag"}
        _log("reserve", organ, est_usd, v, task); return v
    try:
        organs = opslib.organ_table()
        fx, _ = opslib.fx_aud_per_usd()
    except Exception as e:  # budgets.yaml ناخوانا = fail-closed
        opslib.freeze(f"budgets.yaml unreadable in reserve: {e}")
        v = {"allow": False, "reason": "budgets-unreadable"}
        _log("reserve", organ, est_usd, v, task); return v
    if organ not in organs:
        v = {"allow": False, "reason": f"unknown-organ:{organ} (fail-closed؛ ارگان‌ها فقط از budgets.yaml)"}
        _log("reserve", organ, est_usd, v, task); return v

    cfg = organs[organ]
    # سقف ماهانهٔ ارگان به AUD: cap_monthly صریح (DEBATE_LOOP) وگرنه FLOOR (فاز سایه)
    cap_aud = float(cfg.get("cap_monthly", cfg.get("floor", 0)))
    g_reserved = False   # آیا رزرو سراسری budget_gate گرفته شده؟ (برای rollback در شکست)
    try:
        with opslib.LockedJson(opslib.ORGAN_STATE) as lj:
            state = _roll(lj.read())
            org = state["organs"].setdefault(
                organ, {"date": opslib.today(), "spent_today_musd": 0, "spent_month_musd": 0})
            est_musd = opslib.micro(est_usd)
            month_after_aud = opslib.usd(org["spent_month_musd"] + est_musd) * fx
            if month_after_aud > cap_aud:
                v = {"allow": False,
                     "reason": f"organ-monthly: AU${month_after_aud:.4f} > cap AU${cap_aud:.2f}"}
                _log("reserve", organ, est_usd, v, task); return v
            # لایهٔ سراسری — budget_gate تنها enforcer است؛ deny او = deny کل
            g = budget_gate.reserve(organ, est_usd)
            if not g.get("allow"):
                v = {"allow": False, "reason": f"budget_gate:{g.get('reason', '?')}"}
                _log("reserve", organ, est_usd, v, task); return v
            g_reserved = True
            org["spent_today_musd"] += est_musd
            org["spent_month_musd"] += est_musd
            lj.write(state)
    except TimeoutError:
        if g_reserved:      # رزرو سراسری بدون ثبت ارگان = نشت؛ پس بده
            _refund_global(organ, est_usd)
        v = {"allow": False, "reason": "organ-state-lock-busy (fail-closed)"}
        _log("reserve", organ, est_usd, v, task); return v
    except Exception as e:  # state ناخوانا/ناقص = fail-closed، نه crash و نه ادامه
        if g_reserved:
            _refund_global(organ, est_usd)
        v = {"allow": False, "reason": f"organ-state-unreadable:{e}"}
        _log("reserve", organ, est_usd, v, task); return v
    v = {"allow": True, "reserved": est_usd}
    _log("reserve", organ, est_usd, v, task)
    return v


def settle(organ: str, est_usd: float, actual_usd: float, task: str = "") -> dict:
    """تخمین → واقعی، در هر دو لایه. هر استثنای لایهٔ زیرین = FREEZE (حسابداری نامعلوم)."""
    delta_musd = opslib.micro(actual_usd) - opslib.micro(est_usd)
    try:
        with opslib.LockedJson(opslib.ORGAN_STATE) as lj:
            state = _roll(lj.read())
            org = state["organs"].setdefault(
                organ, {"date": opslib.today(), "spent_today_musd": 0, "spent_month_musd": 0})
            org["spent_today_musd"] = max(0, org["spent_today_musd"] + delta_musd)
            org["spent_month_musd"] = max(0, org["spent_month_musd"] + delta_musd)
            lj.write(state)
        budget_gate.settle(organ, est_usd, actual_usd)
    except Exception as e:  # settle بدون fail-closed در budget_gate (تلهٔ B.1) → اینجا جبران
        opslib.freeze(f"settle failed for {organ}: {e}")
        v = {"ok": False, "reason": f"settle-failed:{e}"}
        _log("settle", organ, est_usd, v, task); return v
    v = {"ok": True, "actual_usd": actual_usd}
    _log("settle", organ, est_usd, v, task)
    return v


def release(organ: str, est_usd: float, task: str = "") -> dict:
    """call شکست‌خورده → پس‌دادن رزرو (بدون نشت بودجه)."""
    return settle(organ, est_usd, 0.0, task=task or "release")


def status() -> dict:
    """وضعیت خوانا برای CLI/داشبورد/UI."""
    import json
    try:
        with opslib.LockedJson(opslib.ORGAN_STATE) as lj:
            state = _roll(lj.read())
    except Exception as e:
        return {"error": str(e)}
    fx, fx_tag = opslib.fx_aud_per_usd()
    organs = opslib.organ_table()
    rows = {}
    for name, cfg in organs.items():
        st = state.get("organs", {}).get(name, {})
        cap = float(cfg.get("cap_monthly", cfg.get("floor", 0)))
        rows[name] = {
            "floor_aud": cfg.get("floor", 0),
            "cap_monthly_aud": cap,
            "spent_month_aud": round(opslib.usd(st.get("spent_month_musd", 0)) * fx, 6),
            "spent_today_usd": round(opslib.usd(st.get("spent_today_musd", 0)), 6),
            "human_priority": cfg.get("human_priority"),
            "deadline": str(cfg.get("deadline") or ""),
        }
    try:
        gate = budget_gate._roll(budget_gate._load())  # فقط‌خواندنی برای گزارش
    except Exception as e:
        gate = {"error": str(e)}
    return {"ts": opslib.now_iso(), "fx_aud_per_usd": fx, "fx_tag": fx_tag,
            "frozen": opslib.frozen(), "halted": opslib.halted(),
            "organs": rows, "budget_gate_state": gate}


if __name__ == "__main__":
    import json
    print(json.dumps(status(), ensure_ascii=False, indent=2))
