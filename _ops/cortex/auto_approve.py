#!/usr/bin/env python3
"""auto_approve.py — موتورِ تصمیمِ درجه‌بندیِ خطر (جلسه ۴۶).

رأی مالک: «همه رو آره می‌خوام بگم؛ سیستم خودش تست کنه براساس درجه خطر و اهداف
تنظیم کنه مجوز بده.» یعنی: به‌جای آره/نهِ دستی، سیستم هر پیشنهاد را درجه‌بندیِ خطر
کند، با اهداف بسنجد، خودش را تست کند، و کم‌خطرها را خودکار مجوز دهد و اعمال کند؛
فقط پرخطرها به مالک بروند.

سه گام: classify(خطر) → goal_aligned(هدف) → self_test(تستِ خودِ سیستم) → decide.

**مرزِ سختِ تخطی‌ناپذیر (هرگز خودکار — همیشه رأیِ مالک):** کد، پول، spawn/تکثیر،
secret/کلید، ژنوم/ledger، schema، human-append، kill-switch، σ، merge. اعمالِ خودکار
فقط knobِ $0 و برگشت‌پذیرِ درونِ whitelist (AUTO_KNOBS)، آن‌هم فقط اگر:
  (۱) سوییتِ تستِ خودِ سیستم سبز باشد (CAPABILITY-OK)،
  (۲) مشاهده زنده باشد (ORGANISM-STATE تازه)،
  (۳) بیرونِ دورهٔ refractory (۲۴h)،
  (۴) پرچمِ مجوزِ مالک (ACTIVATION-SELF-IMPROVE-AUTO) باشد،
  (۵) مقدار درونِ کرانِ امن باشد.
هر اعمال در ledger ثبت می‌شود (رد‌گیریِ کامل). حذفِ پرچم = لغوِ فوریِ مجوز.
$0 · stdlib · fail-soft.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib      # noqa: E402
import improve     # noqa: E402 — AUTO_KNOBS + observability_ok + refractory_open

STATE = opslib.STATE_DIR
KNOBS_PATH = STATE / "cortex" / "auto-knobs.json"
LOG_PATH = STATE / "cortex" / "auto-approve-log.jsonl"
GOALS_PATH = opslib.OPS / "GOALS-OCTOPUS.md"

# کلمات پرخطر (فارسی+انگلیسی) — حضورشان = خطرِ بالا = همیشه رأیِ مالک.
_HIGH_RISK = re.compile(
    r"(code|کد|money|پول|دلار|dollar|spawn|تکثیر|replicat|secret|کلید|راز|token|"
    r"schema|ژنوم|genome|ledger|human.?append|امضا|kill|halt|sigma|σ|merge|apply_merge|"
    r"budget|بودجه|wallet|کیف|pem|L4|L5|پرداخت|pay|api.?key)", re.I)


def classify(p: dict) -> str:
    """low | medium | high. change_level + کلمات پرخطر."""
    lvl = str(p.get("change_level", "reconfig"))
    blob = f"{p.get('title', '')} {p.get('action', '')} {p.get('suggested_action', '')}"
    if lvl == "code" or _HIGH_RISK.search(blob):
        return "high"
    if lvl == "reconfig":
        return "medium"
    return "low"   # tune


def read_goals() -> list[str]:
    try:
        text = GOALS_PATH.read_text("utf-8") if GOALS_PATH.exists() else ""
    except OSError:
        return []
    return [ln[2:].strip().lower() for ln in text.splitlines() if ln.startswith("- ")]


def goal_aligned(p: dict) -> bool:
    """هم‌راستا با اهدافِ مالک؟ کم‌خطر پیش‌فرض بله؛ متوسط باید با یک هدف هم‌پوشانی داشته باشد."""
    if classify(p) == "low":
        return True
    goals = read_goals()
    if not goals:
        return True   # فایلِ هدف خالی → مانع نشو (کم‌خطرها)
    blob = f"{p.get('title', '')} {p.get('action', '')}".lower()
    words = {w for w in re.split(r"\W+", blob) if len(w) > 3}
    for g in goals:
        if words & {w for w in re.split(r"\W+", g) if len(w) > 3}:
            return True
    return False


def self_test() -> tuple[bool, str]:
    """«سیستم خودش تست کند»: سوییتِ سبز (CAPABILITY-OK) + مشاهدهٔ زنده + بیرونِ refractory
    + **آرام بودن** (رأی مالک: ترس = محافظه‌کاری، خود-تغییری تحتِ استرس مکث)."""
    # جلسه ۴۶ — گیتِ ترس: زیرسیستمی بد کار می‌کند → هیچ خود-تغییرِ خودکار (fail-closed)
    try:
        import stress
        feared, why = stress.organism_in_fear()
        if feared:
            return False, f"سیستم تحتِ ترس — خود-تغییری مکث: {why}"
    except Exception:  # noqa: BLE001 — نبودِ stress نباید گیت را بشکند
        pass
    try:
        import capability_gate
        if not capability_gate.capability_ok():
            return False, "سوییتِ تستِ خودِ سیستم سبز/معتبر نیست (CAPABILITY-OK)"
    except Exception as e:  # noqa: BLE001
        return False, f"capability-check نشد: {type(e).__name__}"
    ok, why = improve.observability_ok()
    if not ok:
        return False, f"مشاهده زنده نیست: {why}"
    ok2, why2 = improve.refractory_open()
    if not ok2:
        return False, f"دورهٔ نقاهت: {why2}"
    return True, "green"


def _knob_for(p: dict) -> tuple[str, tuple] | None:
    """آیا این پیشنهاد به یک knobِ whitelist نگاشت می‌شود؟ (تنها مسیرِ اعمالِ خودکار)."""
    blob = f"{p.get('title', '')} {p.get('action', '')} {p.get('suggested_action', '')}".lower()
    for k, bounds in improve.AUTO_KNOBS.items():
        if k.lower() in blob:
            return k, bounds
    return None


def _matrix():
    """ماتریسِ خودمختاری (رأی مالک 2026-07-16) — fail-safe: نبودش = رفتارِ قبلی."""
    try:
        import autonomy_matrix
        return autonomy_matrix
    except Exception:  # noqa: BLE001
        return None


def decide(p: dict) -> dict:
    """تصمیمِ درجه‌بندیِ خطر برای یک پیشنهاد.
    خروجی: {action: auto|self|escalate, risk, reason}.

    رأی مالک 2026-07-16 («گیتِ انسانی فقط برای مهم‌ها؛ بقیه تصمیم بگیر و انجام بده،
    سوال نپرس»): با فلگِ OCTOPUS_AUTONOMY_FREE، پیشنهادِ *غیرمهم* دیگر به مالک
    escalate نمی‌شود — یا auto (knobِ امن) یا **self** (خودتصمیمِ ثبت‌شده در ledger،
    بدونِ سوال). ردهٔ مهم (پول/کد/secret/حذف/ارسال/kill/...) همیشه escalate می‌ماند."""
    risk = classify(p)
    am = _matrix()
    free_on = bool(am and am.free_enabled())
    imp, imp_why = (am.is_important(p) if am else (False, ""))
    if risk == "high" or imp:
        return {"action": "escalate", "risk": "high" if risk == "high" else risk,
                "reason": ("خطرِ بالا → رأیِ مالک" if risk == "high"
                           else f"ردهٔ مهم ({imp_why}) → گیتِ تعاملیِ تلگرام")}
    if not goal_aligned(p):
        if free_on:
            return {"action": "self", "verdict": "defer", "risk": risk,
                    "reason": "غیرمهم ولی با اهداف هم‌راستا نیست — خودتصمیم: defer (ثبت، بدونِ سوال)"}
        return {"action": "escalate", "risk": risk, "reason": "با اهداف هم‌راستا نیست → مالک"}
    knob = _knob_for(p)
    if knob is None:
        if free_on:
            return {"action": "self", "verdict": "approve", "risk": risk,
                    "reason": "غیرمهم + هم‌راستا — خودتصمیم: approve (اجرا با مجریِ همان حوزه؛ ثبت‌شده)"}
        return {"action": "escalate", "risk": risk,
                "reason": "مسیرِ اعمالِ خودکارِ امن ندارد (نیازِ کد/دست) → مالک"}
    ok, why = self_test()
    if not ok:
        if free_on:
            return {"action": "self", "verdict": "defer", "risk": risk,
                    "reason": f"غیرمهم ولی تستِ خود رد ({why}) — خودتصمیم: defer تا سبزشدن"}
        return {"action": "escalate", "risk": risk, "reason": f"تستِ خود رد: {why}"}
    return {"action": "auto", "risk": risk, "knob": knob[0], "bounds": knob[1],
            "reason": "کم‌خطر + هم‌راستا + تستِ خود سبز"}


def _current(knob: str) -> float | None:
    try:
        return float(os.environ.get(knob)) if os.environ.get(knob) else None
    except ValueError:
        return None


def apply_knob(knob: str, bounds: tuple, direction: str = "toward-mid") -> dict:
    """اعمالِ امنِ یک knob: مقدارِ نو را به سمتِ میانهٔ کرانِ امن ببر (گامِ کوچک، محافظه‌کار).
    نوشتن به state/auto-knobs.json + env + ledger. برگشت‌پذیر (فایل را پاک کن)."""
    lo, hi = float(bounds[0]), float(bounds[1])
    mid = (lo + hi) / 2
    cur = _current(knob)
    new = cur + (mid - cur) * 0.25 if cur is not None else mid
    new = max(lo, min(hi, new))
    # AUTO_KNOBS همه دامنهٔ صحیح‌اند (cadence/interval). مقدارِ صحیح بنویس تا مصرف‌کننده‌های
    # int(os.environ[...]) (مثلِ wiring.py CHRONO_NUDGE_EVERY_N_BEATS) با «780.0» ValueError نگیرند.
    new = int(round(new))
    try:
        cur_map = json.loads(KNOBS_PATH.read_text("utf-8")) if KNOBS_PATH.exists() else {}
    except (OSError, ValueError):
        cur_map = {}
    cur_map[knob] = new
    try:
        KNOBS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(KNOBS_PATH) as lj:
            lj.write(cur_map)
        os.environ[knob] = str(new)   # اثرِ runtime همین حالا
        opslib.ledger_note("AUTO_APPROVE_APPLY",
                           {"knob": knob, "value": new, "bounds": [lo, hi]},
                           actor="auto-approve")
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
    return {"ok": True, "knob": knob, "value": new}


def _log(entry: dict) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps({**entry, "ts": opslib.now_iso()}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def run(proposals: list[dict]) -> dict:
    """همهٔ پیشنهادها را درجه‌بندی کن. مجوز (پرچمِ مالک یا OCTOPUS_AUTONOMY_FREE) نباشد →
    هیچ اعمالِ خودکار (فقط درجه‌بندی برای شفافیت).
    خروجی: {applied:[...], self_decided:[...], escalated:[...], by_risk:{...}} —
    self_decided = خودتصمیم‌های ثبت‌شده (رأی مالک 07-16: به صفِ مالک نمی‌روند)."""
    am = _matrix()
    has_permission = improve.ACT_AUTO.exists() or bool(am and am.free_enabled())
    applied, escalated, self_decided = [], [], []
    by_risk = {"low": 0, "medium": 0, "high": 0}
    # refractory را فقط یک‌بار در هر run مصرف کن (نه per-proposal)
    tested_once = None
    for p in proposals:
        d = decide(p)
        by_risk[d["risk"]] = by_risk.get(d["risk"], 0) + 1
        if d["action"] == "self":
            rec = {"title": p.get("title"), "verdict": d.get("verdict"),
                   "risk": d["risk"], "why": d["reason"]}
            self_decided.append(rec)
            _log({"decision": "self-" + str(d.get("verdict")), **rec})
            try:  # شفافیتِ بدونِ سوال: هر خودتصمیم در ledger
                opslib.ledger_note("AUTONOMY_SELF_VERDICT", rec, actor="auto-approve")
            except Exception:  # noqa: BLE001
                pass
            continue
        if d["action"] == "auto" and has_permission and not applied:
            # فقط یک اعمالِ خودکار در هر run (گامِ کوچک، ضدِ نوسان) + ثبتِ refractory
            r = apply_knob(d["knob"], d["bounds"])
            if r.get("ok"):
                import datetime as _dt
                try:
                    with opslib.LockedJson(improve.AUTO_STATE_PATH) as lj:
                        lj.write({"last_auto_ts": _dt.datetime.now().timestamp(),
                                  "knob": d["knob"], "value": r["value"]})
                except Exception:  # noqa: BLE001
                    pass
                _log({"decision": "auto-applied", "risk": d["risk"], **r})
                applied.append({"title": p.get("title"), **r})
            else:
                escalated.append({"title": p.get("title"), "why": "اعمال ناموفق"})
        else:
            reason = d["reason"] if has_permission else "منتظرِ مجوزِ مالک (ACTIVATION-SELF-IMPROVE-AUTO)"
            escalated.append({"title": p.get("title"), "risk": d["risk"], "why": reason})
            _log({"decision": "escalated", "risk": d["risk"], "title": p.get("title"),
                  "why": reason})
    return {"permission": has_permission, "applied": applied,
            "self_decided": self_decided, "escalated": escalated, "by_risk": by_risk}


def load_persisted_knobs() -> dict:
    """در بوت: knobهای auto-اعمال‌شده را از دیسک به env بازگردان (تا restart گم نشوند)."""
    try:
        if not KNOBS_PATH.exists():
            return {}
        m = json.loads(KNOBS_PATH.read_text("utf-8"))
        for k, v in m.items():
            if k in improve.AUTO_KNOBS and not os.environ.get(k):
                lo, hi = improve.AUTO_KNOBS[k]
                if lo <= float(v) <= hi:      # فقط درونِ کرانِ امن
                    os.environ[k] = str(v)
        return m
    except (OSError, ValueError):
        return {}


if __name__ == "__main__":
    print(json.dumps({"self_test": self_test(),
                      "permission": improve.ACT_AUTO.exists()}, ensure_ascii=False, indent=2))
