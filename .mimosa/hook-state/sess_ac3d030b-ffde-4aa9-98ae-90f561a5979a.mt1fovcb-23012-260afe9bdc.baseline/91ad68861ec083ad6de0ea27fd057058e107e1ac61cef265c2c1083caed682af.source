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
  (۵) مقدار درونِ کرانِ امن باشد،
  (۶) اگر مالک OCTOPUS_ARM_SENSITIVE_DEFAULT=1 کرد (۲۰۲۶-۰۸-۰۴، DR-001)، یک
      arm-token تازهٔ دوکلیدی برای self_improve_auto لازم است (arm_gate.py).
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
sys.path.insert(0, str(_HERE.parent))          # _ops — برای decision_gate/trajectory_log
import opslib      # noqa: E402
import improve     # noqa: E402 — AUTO_KNOBS + observability_ok + refractory_open
import arm_gate    # noqa: E402

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


_RISK_CLASS = {"high": 4, "med": 3, "medium": 3, "low": 1}


def _shadow_gate(p: dict, risk: str, imp: bool) -> bool:
    """گیتِ ۵۱/۴۹ را **موازیِ** مسیرِ امروز می‌سنجد — بدونِ هیچ اثری بر تصمیم.

    چرا سایه و نه سیم: قبل از اینکه اجازهٔ اجرا به چیزی بدهیم باید بدانیم چند بار
    با قاضیِ امروز اختلاف پیدا می‌کند و در کدام جهت. جهتِ خطرناک یکی است:
    `imp=False` (امروز می‌گوید بی‌اهمیت، پس خودتصمیم مجاز است) ولی گیت ردهٔ نابودی
    ببیند — یعنی چیزی که امروز **بی‌سؤال** رد می‌شود. نقطهٔ کورِ ۱۳۸ دقیقاً همین
    شکل بود: `{"params": {"amount_aud": 500}}` که خواندنِ سطحیِ کلیدها نمی‌دیدش.

    fail-soft مطلق: هر خطایی این‌جا بی‌صدا رد می‌شود — سنجش هرگز حق ندارد مسیرِ
    تصمیم را بشکند."""
    # ⚠️ مسیر در زمانِ import ست می‌شود، نه این‌جا. نسخهٔ اول همین‌جا
    # `sys.path.insert(0, _ops)` می‌زد — یعنی وسطِ یک فراخوانِ زنده، ترتیبِ
    # resolutionِ ماژول‌ها برای کلِ پروسه عوض می‌شد. سوییت یک بار همان‌جا
    # لرزید و بارِ بعد سبز شد؛ سبزِ دوم اثباتِ سلامت نیست، فقط اثباتِ شانس است.
    try:
        import decision_gate as _dg
        rec = _dg.decide(action=str(p.get("title") or p.get("action") or "")[:120],
                         payload=p,
                         evidence=p.get("evidence"),
                         risk_class=_RISK_CLASS.get(str(risk), 4),
                         trace_id=str(p.get("id") or "")[:64])
        rec["shadow_of"] = {"is_important": bool(imp), "risk": str(risk)}
        # اختلافِ جهت‌دار: امروز آزاد، گیت بسته. این عدد است که ارزشِ مسلح‌کردن را
        # ثابت (یا رد) می‌کند.
        rec["divergence"] = bool(rec.get("destruction_risk") and not imp)
        _dg.record(rec)
        # G0 — همین نقطه تنها جایی است که «وضعیت» و «تصمیم» با هم حاضرند. اگر
        # این‌جا ثبت نشود، بعداً هیچ‌جا نمی‌شود بازسازی‌شان کرد.
        import trajectory_log as _tl
        _tl.step(traj_id=str(p.get("id") or "")[:64], phase="decide",
                 state={"risk": str(risk), "is_important": bool(imp),
                        "evidence_score": rec.get("evidence_score")},
                 action=str(p.get("title") or p.get("action") or "")[:120],
                 decision={"executor": rec.get("executor"),
                           "destruction_risk": rec.get("destruction_risk")},
                 meta={"source": "auto_approve.decide"})
        # VQ-DEEP-GATE-AUTHORITATIVE-001 (۲۰۲۶-۰۸-۰۳، رأیِ مالک «زنده‌اش کن»).
        # تا امروز این تابع `None` می‌داد و `rec` دور ریخته می‌شد — یعنی خوانندهٔ
        # **عمیق** (که `flatten()` می‌زند و مبلغِ تودرتو را می‌بیند) فقط ناظری بود
        # که هیچ‌چیز را عوض نمی‌کرد، و خوانندهٔ **کم‌عمق** مرجع می‌ماند. نمونهٔ
        # بلایندسپات #۱۳۸: `{"params": {"amount_aud": 500}}` برای `is_important`
        # و `classify` هر دو یک بلابِ خالی است ⇒ «آزاد» طبقه‌بندی می‌شد.
        # حالا نتیجه برمی‌گردد. مصرفش در `decide()` عمداً **یک‌جهته** است —
        # فقط می‌تواند escalate کند، هرگز چیزی را آزاد نمی‌کند (همان الگوی
        # `_autonomy_allows`). پس بدترین حالتِ یک مثبتِ کاذب، یک سؤالِ اضافه از
        # مالک است، نه یک اثرِ بی‌گیت.
        return bool(rec.get("destruction_risk"))
    except Exception:  # noqa: BLE001
        pass
    return False


def _autonomy_allows(p: dict, risk: str, imp: bool) -> tuple:
    """آیا این پیشنهاد داخلِ اختیارِ اعطاشدهٔ مالک است؟ (fail-closed)

    سه شرطِ هم‌زمان، و هر سه لازم:
      · فلگِ اختیار روشن باشد،
      · ردهٔ خطر پایین و **غیرمهم** باشد (پس هیچ‌وقت پول/کد/راز را نمی‌گیرد)،
      · و `autonomy_grant` صریحاً بگوید بله.

    خروجی (False, "") یعنی «چیزی نمی‌گویم» — نه «نه». پس نبودِ اختیار هرگز
    مسیرِ امروز را عوض نمی‌کند."""
    if imp or risk == "high":
        return (False, "")
    try:
        import sys as _s
        from pathlib import Path as _P
        _o = str(_P(__file__).resolve().parent.parent)
        if _o not in _s.path:
            _s.path.insert(0, _o)
        import autonomy_grant as _ag
        if not _ag.enabled():
            return (False, "")
        blob = f"{p.get('title', '')} {p.get('action', '')} {p.get('suggested_action', '')}"
        r = _ag.may("read_only", blob[:200])
        return (bool(r.get("ok")), str(r.get("why") or ""))
    except Exception:  # noqa: BLE001 — نبودِ ماژول = رفتارِ امروز
        return (False, "")


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
    # خوانندهٔ عمیق (decision_gate، با flatten ِ بازگشتی). با فلگِ خاموش رفتار
    # بایت‌به‌بایتِ قبلی است؛ با فلگِ روشن فقط **اضافه** escalate می‌کند.
    _deep_destroy = _shadow_gate(p, risk, imp)
    if _deep_destroy and not imp:
        try:
            import decision_gate as _dgf
            if _dgf.enabled():
                imp, imp_why = True, "خوانندهٔ عمیق: مبلغ/خطرِ تودرتو (decision_gate)"
        except Exception:  # noqa: BLE001
            pass
    # ۲۰۲۶-۰۷-۲۷ — `autonomy_grant` ساخته شده بود و **صفر صداکننده** داشت:
    # یعنی حتی با فلگِ روشن هیچ اتفاقی نمی‌افتاد. ماژولِ اختیار خودش یتیم بود،
    # که بدترین شکلِ ممکن است — چون از بیرون شبیهِ «اختیار داریم» به‌نظر می‌رسید.
    #
    # این‌جا تنها مصرف‌کننده‌اش است و **فقط در یک جهت** کار می‌کند: می‌تواند
    # پیشنهادِ بی‌خطر را از صفِ مالک بردارد، ولی هرگز چیزی را که مالک باید
    # ببیند رد نمی‌کند. اگر اختیار چیزی نگوید، رفتار دقیقاً همان قبل است.
    _granted, _gwhy = _autonomy_allows(p, risk, imp)
    if risk == "high" or imp:
        return {"action": "escalate", "risk": "high" if risk == "high" else risk,
                "reason": ("خطرِ بالا → رأیِ مالک" if risk == "high"
                           else f"ردهٔ مهم ({imp_why}) → گیتِ تعاملیِ تلگرام")}
    if not goal_aligned(p):
        if free_on:
            return {"action": "self", "verdict": "defer", "risk": risk,
                    "reason": "غیرمهم ولی با اهداف هم‌راستا نیست — خودتصمیم: defer (ثبت، بدونِ سوال)"}
        return {"action": "escalate", "risk": risk, "reason": "با اهداف هم‌راستا نیست → مالک"}
    if _granted:
        return {"action": "self", "verdict": "approve", "risk": risk,
                "reason": f"اختیارِ اعطاشده: {_gwhy} — خودتصمیم، ثبت‌شده"}
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
            # گیتِ اضافیِ arm_gate (۲۰۲۶-۰۸-۰۴، DR-001): defense-in-depth، فقط
            # سخت‌تر می‌کند هرگز شل‌تر — پیش‌فرض بدونِ اثر (byte-identical) تا
            # مالک OCTOPUS_ARM_SENSITIVE_DEFAULT=1 نکرده (که already روشن است).
            # این‌جا و نه داخلِ apply_knob خودش: apply_knob یک صداکنندهٔ دومِ
            # کاملاً جدا دارد — doctor.py:apply_merge، که فقط بعدِ تپِ تلگرامِ
            # مالک اجرا می‌شود (OCTOPUS_WIRE_MERGE_APPLIES_KNOB جداگانه). گیتِ
            # اینجا آن مسیرِ already-owner-approved را دست‌نخورده می‌گذارد و فقط
            # مسیرِ خودکار (بدونِ تپِ مالک) را arm-token می‌خواهد.
            _arm_ok, _arm_why = arm_gate.guard("self_improve_auto")
            if not _arm_ok:
                reason = f"arm-gate-denied:{_arm_why}"
                escalated.append({"title": p.get("title"), "risk": d["risk"], "why": reason})
                _log({"decision": "escalated", "risk": d["risk"], "title": p.get("title"),
                      "why": reason})
                # ۲۰۲۶-۰۸-۰۴ — این شاخه قبلاً کاملاً بی‌صدا بود: escalated فقط در
                # این return و در لاگِ محلی می‌نشست، هیچ صداکننده‌ای آن را
                # نمی‌خواند و هیچ کارت/آلارمی به مالک نمی‌رفت (drive() ِ self_patch
                # کارتِ قدیمی دارد، اینجا معادلش نبود). opslib.alert خودش
                # dedupِ امضامحورِ ۶ساعته دارد، پس تکرارِ همین رد در چرخه‌های
                # بعدی spam نمی‌شود.
                try:
                    opslib.alert([
                        f"auto_approve: knobِ {d.get('knob')} برای «{p.get('title')}» "
                        f"آماده بود (کم‌خطر + هم‌راستا + سوییتِ سبز) ولی arm_gate رد کرد "
                        f"({_arm_why}) — یک arm-token تازهٔ دوکلیدی برای "
                        f"self_improve_auto لازم است."])
                except Exception:  # noqa: BLE001 — آلارم هرگز حلقه را نمی‌کشد
                    pass
                continue
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
