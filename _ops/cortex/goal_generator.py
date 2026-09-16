#!/usr/bin/env python3
"""goal_generator — از «جهتِ مالک × وضعِ فعلی × سنجهٔ موجود» یک هدفِ ابطال‌پذیر می‌سازد.

جای این ماژول در قیفِ منشور (SELF-GOAL-CHARTER-2026-07-30 §۱):

    جهت (GOALS-OCTOPUS.md، مالک می‌نویسد)
       ↓  این‌جا
    هدفِ سنجش‌پذیر (اختاپوس) — شرطِ اعتبار: سنجهٔ عددیِ **موجود روی دیسک**
       ↓
    زیرهدف/roadmap → پیش‌ثبت (prereg) → اجرا (test_cycle) → ارزیابی (cycle_evaluator)

سه قاعدهٔ سخت (هرکدام شکست = هدف ساخته نمی‌شود، fail-closed):
  ۱) **سنجه باید همین حالا روی دیسک خواندنی باشد.** هدفِ بی‌ترازو آرزوست؛
     ترازویی که بعداً قرار است ساخته شود، ترازو نیست (درسِ «هر سه سنجهٔ
     خودآگاهی ابزار نداشتند»). metric ناموجود = کاندیدا رد می‌شود.
  ۲) **baseline و target قبل از اجرا قطعی می‌شوند** — target این‌جا ساخته و در
     prereg منجمد می‌شود؛ هیچ مسیری برای جابه‌جایی‌اش بعد از دیدنِ نتیجه نیست
     (همان `alter_acceptance_criteria` که PRE-0 ممنوع کرده).
  ۳) **لینکِ جهت صریح است** — یا به یک خطِ GOALS-OCTOPUS وصل می‌شود یا صریح
     می‌گوید «هیچ‌کدام». سکوت ممنوع (رأیِ VQ-SELFGOAL-003: آزاد، فقط ثبت شود).

چرخشِ روش (pivot) مکانیکی است نه ادعایی: اگر آخرین حکمِ ارزیابِ مستقل برای
همین goal_key شکست (FAIL) بود، روشِ بعدی از فهرستِ روش‌های *متمایز* انتخاب
می‌شود؛ وگرنه همان روش می‌ماند (تکرارِ صادقانه، شمرده می‌شود). کلیدِ چرخش
محتوای روش است نه زمان (درسِ «شمارنده در کلیدِ dedup»).

v1 عمداً rule-based و $0 است (بدونِ مغز): قابلِ‌آزمون، قطعی، بی‌هزینه.
مغز بعداً می‌تواند کاندیدا *اضافه* کند؛ گیتِ اعتبار همین می‌ماند.

$0 · stdlib · fail-soft در خواندن، fail-closed در اعتبار · propose-only.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent            # _ops/cortex
_OPS = _HERE.parent                                 # _ops
for _p in (str(_OPS), str(_OPS / "budget"), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

SCHEMA = "goal_proposal.v1"

# ─── کاتالوگِ کاندیداها ──────────────────────────────────────────────────────
# هر کاندیدا به یک سنجهٔ عددیِ *موجود* روی دیسک بسته است. ترتیب = اولویتِ
# اعلام‌شدهٔ مالک (GOALS-OCTOPUS: درآمد ← تعمیرِ خود/حافظه ← ابزار).
# metric_path نسبت به STATE_DIR است؛ metric_key مسیرِ نقطه‌دار داخلِ JSON.
_CANDIDATES = (
    {
        "key": "money-claimed",
        "goal": "اولین پولِ مطالبه‌شده — attribution.claimed از صفر دربیاید",
        "why": "تنها هدفِ سنجش‌پذیرِ این ماه (رأیِ مالک ۲۰۲۶-۰۷-۳۰). "
               "قید: claimed پولِ محقق نیست؛ ادعای مستندِ پول است (VQ-ACCT-PARK).",
        "direction_hint": ("پول", "claimed", "درآمد"),
        "metric_path": "fitness-latest.json",
        "metric_key": "attribution.claimed",
        "target_rule": "gt-baseline",
        "deadline_cycles": 2,
        "methods": (
            "بررسیِ لیدهای باز و آمادهٔ claim از مسیرِ proposal router — "
            "کوچک‌ترین قدمِ برگشت‌پذیر به‌سوی اولین ادعای مستند",
            "پیشنهادِ صریح به مالک برای ثبتِ attribution.claim روی یک لیدِ "
            "مشخصِ تأییدشده (کارتِ تلگرام، نه اجرای خودکار)",
            "پیگیریِ لیدهای معطلِ لولهٔ نقاشی/Ziman تا یکی به مرحلهٔ "
            "قابلِ‌claim برسد — گزارشِ اصطکاک به مالک",
        ),
    },
    {
        "key": "recall-events",
        "goal": "بازیابیِ حافظه از تقریباً-خاموش دربیاید — رخدادِ بازیابی (events) بالا برود",
        "why": "خطِ پایهٔ ۰۷-۳۰: چهار رخداد در ۵۴۰ سیکل؛ جهتِ مالک: «با خاموش/روشن "
               "هیچ‌چیز گم نشود». سنجه از سریِ recall-trend خوانده می‌شود.",
        "direction_hint": ("حافظه", "گم نشود"),
        "metric_path": "neural/recall-trend.jsonl",
        "metric_key": "events",
        "target_rule": "gt-baseline",
        "deadline_cycles": 2,
        "methods": (
            "نمونه‌گیریِ منظمِ recall در هر چرخه تا سری قابلِ‌روند شود",
            "مرورِ کلیدهای کم‌برد و تداعی با رخدادهای اخیر (پیشنهاد به consolidation)",
            "گزارشِ شکافِ بازیابی به مالک با جفتِ قبل/بعدِ عددی",
        ),
    },
    {
        "key": "tool-precision",
        "goal": "درخواستِ ابزارِ دقیق — نسبتِ precise در دفترِ tool-requests بالا برود",
        "why": "سنجهٔ اولِ خودآگاهی در آزمونِ ۷ روزه؛ دقت ماشین‌خوان است "
               "(چهار میدانِ need/why/cost/alternative).",
        "direction_hint": ("ابزار", "تحلیل"),
        "metric_path": "telegram/tool-requests.jsonl",
        "metric_key": "precise",          # نسبتِ ردیف‌های precise در کلِ درخواست‌ها
        "target_rule": "gt-baseline",
        "deadline_cycles": 2,
        "methods": (
            "پر کردنِ هر چهار میدانِ درخواست پیش از ارسال — قالبِ سخت",
            "بازنویسیِ درخواست‌های ناقصِ گذشته با میدان‌های کامل",
            "گزارشِ درخواست‌های رد‌شده به مالک با علتِ نقص",
        ),
    },
)


# ─── خواندنِ سنجه از دیسک ────────────────────────────────────────────────────
def _resolve(d: dict, dotted: str):
    cur = d
    for part in str(dotted).split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def read_metric(metric_path: str, metric_key: str) -> "float | None":
    """سنجه را از دیسک بخوان. None = ناموجود/ناخوانا (کاندیدا بی‌اعتبار می‌شود).

    JSON: مقدارِ مسیرِ نقطه‌دار. JSONL: میانگین‌گیری نمی‌کنیم — برای کلیدِ
    عددی آخرین ردیفِ سالم؛ برای کلیدِ بولی (مثل precise) نسبتِ True در کلِ
    ردیف‌های دارای آن کلید (نسبت خودش عدد است و روی دیسک بازتولیدپذیر)."""
    p = opslib.STATE_DIR / metric_path
    try:
        if not p.exists():
            return None
        if p.suffix == ".jsonl":
            vals = []
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(d, dict):
                        v = _resolve(d, metric_key)
                        if v is not None:
                            vals.append(v)
            if not vals:
                return None
            if all(isinstance(v, bool) for v in vals):
                return round(sum(1 for v in vals if v) / len(vals), 6)
            nums = [float(v) for v in vals
                    if isinstance(v, (int, float)) and not isinstance(v, bool)]
            return nums[-1] if nums else None
        d = json.loads(p.read_text("utf-8"))
        v = _resolve(d, metric_key) if isinstance(d, dict) else None
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return None
        return float(v)
    except (OSError, ValueError):
        return None


# ─── اعتبار (fail-closed) ────────────────────────────────────────────────────
_REQUIRED = ("goal", "goal_key", "method", "metric_path", "metric_key",
             "baseline", "target", "deadline_cycles", "direction")


def validate(p: dict) -> dict:
    """هدفِ بی‌ترازو یا بی‌target هرگز وارد اجرا نمی‌شود. خروجی: {ok, errors}."""
    errors = []
    for k in _REQUIRED:
        if k not in p or p[k] in (None, ""):
            errors.append(f"missing:{k}")
    t = p.get("target")
    if not (isinstance(t, dict) and t.get("op") in (">", ">=")
            and isinstance(t.get("value"), (int, float))
            and not isinstance(t.get("value"), bool)):
        errors.append("bad:target")
    if not isinstance(p.get("baseline"), (int, float)) or isinstance(p.get("baseline"), bool):
        errors.append("bad:baseline")
    # ترازو باید همین حالا خواندنی باشد — نه «بعداً ساخته می‌شود»
    if not errors:
        v = read_metric(p["metric_path"], p["metric_key"])
        if v is None:
            errors.append("metric-not-on-disk")
    try:
        if int(p.get("deadline_cycles", 0)) < 1:
            errors.append("bad:deadline_cycles")
    except (TypeError, ValueError):
        errors.append("bad:deadline_cycles")
    return {"ok": not errors, "errors": errors}


def _goal_key(goal: str) -> str:
    norm = " ".join(str(goal or "").strip().lower().split())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:12]


def _direction_for(cand: dict, directions: list) -> str:
    """لینکِ صریح به یک خطِ GOALS-OCTOPUS، یا «هیچ‌کدام» — سکوت ممنوع."""
    hints = cand.get("direction_hint") or ()
    for d in directions:
        if any(h in d for h in hints):
            return d
    return "هیچ‌کدام"


def _fail_streak(goal_key: str) -> int:
    """شمارِ FAILهای پیاپی از تازه‌ترین حکمِ همین goal_key به عقب.

    deadline_cycles بدون این عدد یک فیلدِ تزئینی است: هدفِ گیرکرده تا ابد
    صدرِ کاتالوگ می‌ماند و کاندیدای بعدی (که ممکن است واقعاً حرکت کرده
    باشد) هرگز نوبت نمی‌گیرد. فقط‌خواندنی؛ دفتر را عوض نمی‌کند."""
    streak = 0
    vp = opslib.STATE_DIR / "test_cycle" / "verdicts.jsonl"
    rows: list = []
    try:
        if vp.exists():
            with open(vp, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                    except ValueError:
                        continue
                    if (isinstance(d, dict) and d.get("goal_key") == goal_key
                            and d.get("schema") == "cycle_verdict.v1"):
                        rows.append(d)
    except OSError:
        return 0
    for d in reversed(rows):
        if str(d.get("verdict") or "") == "FAIL":
            streak += 1
        else:
            break
    return streak


def _method_index(cand: dict, goal_key: str) -> tuple:
    """چرخشِ مکانیکیِ روش: FAIL ِ آخرینِ حکمِ ارزیابِ مستقل → روشِ بعدی.

    حکم از دفترِ verdicts خوانده می‌شود (cycle_evaluator می‌نویسد؛ این‌جا
    فقط‌خواندنی). بدونِ حکم یا حکمِ غیرFAIL → همان روشِ قبلی (یا صفر)."""
    methods = cand.get("methods") or ("",)
    last_idx, last_verdict = 0, None
    vp = opslib.STATE_DIR / "test_cycle" / "verdicts.jsonl"
    try:
        if vp.exists():
            with open(vp, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                    except ValueError:
                        continue
                    if (isinstance(d, dict) and d.get("goal_key") == goal_key
                            and d.get("schema") == "cycle_verdict.v1"):
                        last_verdict = str(d.get("verdict") or "")
                        try:
                            last_idx = int(d.get("method_index", 0) or 0)
                        except (TypeError, ValueError):
                            last_idx = 0
    except OSError:
        pass
    if last_verdict == "FAIL":
        return (last_idx + 1) % len(methods), f"pivot-after-FAIL(from={last_idx})"
    return last_idx % len(methods), ("hold" if last_verdict else "first")


# ─── تولید ───────────────────────────────────────────────────────────────────
def propose(*, now: "float | None" = None) -> dict:  # noqa: ARG001 — امضای تزریق‌پذیر
    """اولین کاندیدای معتبر به ترتیبِ اولویت. هیچ کاندیدای معتبری نبود →
    ok=False با فهرستِ صریحِ ردشده‌ها (سکوت نداریم؛ درسِ «ثبت را گیت نکن»)."""
    try:
        import goal_directed as _gd
        directions = _gd.load_goals()
    except Exception:  # noqa: BLE001 — نبودِ ماژول = بدونِ لینکِ جهت، نه کرش
        directions = []
    skipped = []
    first_valid = None
    for cand in _CANDIDATES:
        baseline = read_metric(cand["metric_path"], cand["metric_key"])
        if baseline is None:
            skipped.append({"key": cand["key"], "reason": "metric-not-on-disk"})
            continue
        gkey = _goal_key(cand["goal"])
        idx, pivot_note = _method_index(cand, gkey)
        methods = cand["methods"]
        deadline = int(cand.get("deadline_cycles", 2))
        streak = _fail_streak(gkey)
        p = {
            "ok": True, "schema": SCHEMA, "ts": opslib.now_iso(),
            "candidate_key": cand["key"],
            "goal": cand["goal"], "goal_key": gkey,
            "why": cand.get("why", ""),
            "method": methods[idx % len(methods)],
            "method_index": idx % len(methods),
            "method_note": pivot_note,
            "metric_path": cand["metric_path"], "metric_key": cand["metric_key"],
            "baseline": baseline,
            "target": {"op": ">", "value": baseline},
            "deadline_cycles": deadline,
            "fail_streak": streak,
            "direction": _direction_for(cand, directions),
            "goal_source": "self",
        }
        v = validate(p)
        if not v["ok"]:
            skipped.append({"key": cand["key"], "reason": ",".join(v["errors"])})
            continue
        if first_valid is None:
            first_valid = dict(p)
        if streak >= deadline:
            skipped.append({"key": cand["key"], "reason": "deadline-exhausted",
                            "fail_streak": streak, "deadline_cycles": deadline})
            continue
        p["skipped"] = skipped
        return p
    if first_valid is not None:
        # همهٔ کاندیداهای معتبر deadline-exhausted — چرخه را نکش؛ همان اولی
        # با مهرِ صادق. وگرنه test_cycle اسلات می‌سوزاند بی‌شاهد.
        first_valid["method_note"] = (
            str(first_valid.get("method_note") or "") + "|deadline-fallback")
        first_valid["deadline_fallback"] = True
        first_valid["skipped"] = skipped
        return first_valid
    return {"ok": False, "reason": "no-valid-goal", "skipped": skipped}


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps(propose(), ensure_ascii=False, indent=1))
