#!/usr/bin/env python3
"""goal_directed.py — ضدِ خودبهبودیِ دایره‌ای؛ هدف‌محور و عملی و سنجش‌پذیر (جلسه ۴۶).

رأی مالک: «خودبهبودی دایره‌ای الکی نباشه — عملی و هدف‌دار و قوی و اتوماتیک باشه.»
مسئله: `generate_proposals` انبوهی پیشنهادِ درون‌مانده می‌سازد («بلوغ را بالا ببر»،
«یک probe اضافه کن»، «یک ماژول را مستند کن») که به هدفِ واقعیِ مالک خدمت نمی‌کنند.

این لایه بین generate و top می‌نشیند و سه کار می‌کند:
  ۱) هر پیشنهاد را به هدفِ مالک (GOALS-OCTOPUS.md) لینک می‌کند؛ پیشنهادِ دایره‌ای
     (خودمتریک، بی‌لینکِ هدف) را دور می‌ریزد یا به سهمیهٔ کوچک می‌راند.
  ۲) اثرِ واقعی را تخمین می‌زند (کسب‌وکار/درآمد/لید > تعمیرِ سلامت > کارِ سندی).
  ۳) نیتِ سنجش را ثبت می‌کند (`state/cortex/outcomes.jsonl`) — تا لوپ بسته و
     غیرِدایره‌ای شود: بعداً معلوم می‌شود آیا تغییر واقعاً چیزی را جابه‌جا کرد.

$0 · stdlib · fail-soft · propose-only (فقط بازچینش/حاشیه‌نویسی، نه اعمال).
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

STATE = opslib.STATE_DIR
GOALS_PATH = opslib.OPS / "GOALS-OCTOPUS.md"
OUTCOMES = STATE / "cortex" / "outcomes.jsonl"
# طرفِ «خود» برای واسنجیِ برخط — همان لِجِر و فلگِ self_model.emit_self_claims
# (ORPH-SELF-CLAIMS): calibration_probe فقط می‌خواند؛ اینجا تولیدکنندهٔ دوم است.
SELF_CLAIMS = STATE / "cortex" / "self-claims.jsonl"
SELF_MONITOR_FLAG = "CORTEX_SELF_MONITOR"
# متریک‌های برون‌دادیِ measure — کلیدِ مشترکِ baseline/بستار (یک منبعِ حقیقت).
# P0-G3 (2026-07-17، ادامهٔ fugu): متریک‌های نزدیک‌به‌عملِ Proposal Router هم واردِ
# منطقِ moved — تا حلقهٔ یادگیری deliver/outcome/value را ببیند، نه فقط درآمدِ نهایی.
# accept_rate عمداً بیرونِ moved-keys است (نسبت است، پایین‌آمدنش خطا نیست) ولی در now هست.
_METRIC_KEYS = ("confirmed_revenue", "revenue_cells", "total_discoveries",
                "proposals_delivered", "proposal_outcomes", "proposal_value_aud")

# T2 لایهٔ ۳ (2026-07-25، مگاپرامپت): درون‌زاد در برابرِ برون‌زاد.
# total_discoveries شمارندهٔ خودِ ارگانیسم است (با تحقیقِ ارگانیسم دربارهٔ خودش بالا
# می‌رود) — «بهبود» با تولیدِ یک کشفِ دیگر دربارهٔ خود ارضا می‌شد = خودارجاعیِ حلقه.
# گواه: baselineهای اولیه فقط یک کلیدِ متحرک داشتند — total_discoveries.
# پشتِ OCTOPUS_HONEST_OUTCOMES: درون‌زاد لاگ می‌شود ولی رأی نمی‌دهد. خاموش = بایت‌به‌بایت.
_ENDOGENOUS_KEYS = frozenset({"total_discoveries"})


def _honest_outcomes() -> bool:
    return os.environ.get("OCTOPUS_HONEST_OUTCOMES") == "1"

# نشانه‌های «دایره‌ای» — بهبودِ خودِ ماشینِ سنجش، نه یک هدفِ واقعی.
_CIRCULAR = re.compile(
    r"(بلوغ|maturity|probe|ماتریس|audit|ممیزی|هم‌آهنگی|coherence|خودآگاهیِ سند|"
    r"docstring|مستند کن|self-model|توضیح)", re.I)
# نشانه‌های هدفِ واقعی/برون‌داد (هرگز دایره‌ای نیستند).
_OUTCOME = re.compile(
    r"(درآمد|revenue|لید|lead|فروش|sale|مشتری|customer|نقاشی|Ziman|زیمن|"
    r"reconcile|واریز|پول‌ساز|یادگیری|کشف|research)", re.I)


def load_goals() -> list[str]:
    try:
        text = GOALS_PATH.read_text("utf-8") if GOALS_PATH.exists() else ""
    except OSError:
        return []
    return [ln[2:].strip() for ln in text.splitlines() if ln.startswith("- ") and ln[2:].strip()]


def _kw(s: str) -> set:
    return {w for w in re.split(r"\W+", str(s).lower()) if len(w) > 3}


def goal_link(p: dict, goals: list[str]) -> str | None:
    """کدام هدفِ مالک را این پیشنهاد پیش می‌برد؟ (یا None)."""
    blob = f"{p.get('title', '')} {p.get('suggested_action', '')} {p.get('rationale', '')}"
    words = _kw(blob)
    if _OUTCOME.search(blob):                       # برون‌دادِ صریح = هدف‌محور
        best = None
        for g in goals:
            if words & _kw(g):
                return g
        return "برون‌دادِ واقعی (درآمد/لید/یادگیری)"
    for g in goals:
        if len(words & _kw(g)) >= 2:
            return g
    return None


def is_circular(p: dict) -> bool:
    """درخودمانده؟ فقط اگر متریکِ داخلی را دستکاری کند، هدفی پیش نبرد، و P0 نباشد
    (P0/امنیت واقعی است، نه دایره‌ای)."""
    if p.get("priority") == "P0":
        return False
    if p.get("source") in ("business-brain", "doctor", "synthesis"):
        return False           # کسب‌وکار/سلامت/ایدهٔ مغز = واقعی
    blob = f"{p.get('title', '')} {p.get('suggested_action', '')}"
    return bool(_CIRCULAR.search(blob)) and not _OUTCOME.search(blob)


def impact(p: dict, goals: list[str]) -> float:
    """اثرِ واقعیِ تخمینی (بالاتر = مهم‌تر). کسب‌وکار/هدف > سلامت > سندی."""
    if p.get("source") == "business-brain" or p.get("category") == "business":
        return 3.0
    if p.get("priority") == "P0":
        return 2.6            # امنیت/گافِ واقعی
    if goal_link(p, goals):
        return 2.2
    if p.get("source") in ("doctor", "synthesis"):
        return 1.6
    if is_circular(p):
        return 0.4
    return 1.0


# ── سهمیهٔ پیشنهادِ دایره‌ای — و چرا تاریخ‌دار است ────────────────────────────
# رأیِ مالک ۲۰۲۶-۰۷-۳۰ (VQ-SELFGOAL-006، گزینهٔ الف منشور §۳.۳): در پنجرهٔ آزمونِ
# SGC-14 سهمیه ۲ → ۶ می‌رود، و در ۲۰۲۶-۰۸-۰۶ **خودبه‌خود** برمی‌گردد.
#
# چرا انقضا در خودِ کد و نه در یادِ آدم‌ها: رأیِ مالک «آزاد، فقط ثبت شود» بود
# (VQ-SELFGOAL-003)، ولی `max_circular=2` هدفِ خودارجاع را فعالانه تنزل می‌دهد —
# پس اختاپوس هدفِ آزاد انتخاب می‌کرد و ماشین دورش می‌ریخت، و ما نتیجه را
# «انتخابِ بدِ اختاپوس» می‌خواندیم در حالی که سانسورِ خودمان بود. ولی همان سهمیه
# بیرون از پنجرهٔ آزمون همان چیزی است که «خودبهبودیِ دایره‌ایِ الکی» را مهار
# می‌کند (رأیِ جلسه ۴۶). یک استثنای بی‌تاریخ، استثنا نیست — قاعدهٔ نو است.
# همان الگویی که `GOALS-OCTOPUS.md` برای سقفِ US$200 به‌کار برد.
MAX_CIRCULAR_DEFAULT = 2
MAX_CIRCULAR_ENV = "OCTOPUS_GOAL_MAX_CIRCULAR"
MAX_CIRCULAR_UNTIL_ENV = "OCTOPUS_GOAL_MAX_CIRCULAR_UNTIL"   # YYYY-MM-DD، شاملِ خودِ روز


# A2 (۲۰۲۶-۰۸-۰۳): جای خالیِ env را رأیِ **tracked** ِ مالک پر می‌کند، چون
# `OCTOPUS-flags.cmd` گیت‌ایگنور است و تنها ردِ ماندگارِ رأی `owner-verdicts.yaml`
# است. env همچنان برنده می‌ماند ⇒ رفتارِ امروز تغییر نمی‌کند. fail-soft.
def _knob(env_name: str) -> str:
    live = str(os.environ.get(env_name, "") or "").strip()
    if live:
        return live
    try:
        _ops = str(Path(__file__).resolve().parents[1])
        if _ops not in sys.path:
            sys.path.insert(0, _ops)
        import owner_verdicts  # noqa: PLC0415
        return owner_verdicts.get(env_name)
    except Exception:  # noqa: BLE001
        return ""


def max_circular_now(today: "str | None" = None) -> dict:
    """سهمیهٔ امروز + دلیلش. `today` **کاملاً** تزریق‌شدنی است — هیچ شاخه‌ای پشتِ
    سرِ صداکننده ساعتِ دیوار را نمی‌خواند (درسِ «ساعتِ نیمه‌تزریقی = بمبِ ساعتی»:
    تابعی که `now` می‌گیرد ولی شاخه‌ای `datetime.now()` می‌خواند، امروز سبز است و
    فردا قرمز، و هیچ اسکنی نمی‌گیردش).

    fail-closed به سمتِ **محافظه‌کار**: env ِ ناخوانا، تاریخِ بدشکل، یا نبودِ
    تاریخِ انقضا ⇒ همان ۲. یعنی یک تایپو استثنا را ابدی نمی‌کند."""
    import datetime as _dt
    raw = _knob(MAX_CIRCULAR_ENV)
    until = _knob(MAX_CIRCULAR_UNTIL_ENV)
    if not raw:
        return {"value": MAX_CIRCULAR_DEFAULT, "reason": "default"}
    if not until:
        # استثنای بی‌تاریخ = قاعدهٔ نو. رأیِ مالک تاریخ داشت، پس بدونِ تاریخ رد است.
        return {"value": MAX_CIRCULAR_DEFAULT, "reason": "no-expiry-declared"}
    try:
        val = int(raw)
    except (TypeError, ValueError):
        return {"value": MAX_CIRCULAR_DEFAULT, "reason": "bad-value"}
    try:
        end = _dt.date.fromisoformat(until)
        now = (_dt.date.fromisoformat(today) if today
               else _dt.date.fromisoformat(opslib.today()))
    except (TypeError, ValueError):
        return {"value": MAX_CIRCULAR_DEFAULT, "reason": "bad-date"}
    if now > end:
        return {"value": MAX_CIRCULAR_DEFAULT, "reason": f"expired:{until}",
                "expired": True}
    return {"value": max(0, min(val, 24)), "reason": f"owner-window:{until}",
            "window_open": True}


def rerank(proposals: list[dict], *, max_circular: "int | None" = None,
           today: "str | None" = None) -> dict:
    """پیشنهادها را هدف‌محور بازچینی کن: دایره‌ای‌ها به ته (سهمیهٔ کوچک)، هدف‌محورها بالا.
    هر پیشنهاد با `serves_goal` و `impact` حاشیه‌نویسی می‌شود. خروجی: {ranked, dropped_circular}.

    `max_circular=None` (پیش‌فرض) یعنی «از پنجرهٔ تاریخ‌دار بپرس»؛ مقدارِ صریحِ
    صداکننده همیشه برنده است (تا تست بتواند بدونِ env حکم بدهد)."""
    _mc = ({"value": int(max_circular), "reason": "explicit"}
           if max_circular is not None else max_circular_now(today))
    max_circular = _mc["value"]
    goals = load_goals()
    scored, circular = [], []
    for p in proposals:
        p = dict(p)
        gl = goal_link(p, goals)
        p["serves_goal"] = gl or ("—" if not is_circular(p) else "دایره‌ای (بی‌هدف)")
        p["impact"] = impact(p, goals)
        (circular if is_circular(p) else scored).append(p)
    scored.sort(key=lambda x: -x["impact"])
    circular.sort(key=lambda x: -x["impact"])
    kept_circular = circular[:max_circular]     # فقط چند تعمیرِ داخلیِ ضروری
    ranked = scored + kept_circular
    return {"ranked": ranked, "n_goal_serving": sum(1 for p in scored if p["impact"] >= 2.0),
            "n_circular_dropped": max(0, len(circular) - len(kept_circular)),
            "goals_count": len(goals),
            # سهمیه و **دلیلش** در خروجی می‌آید تا «چرا این پیشنهاد افتاد؟» از
            # روی دفتر قابلِ بازسازی باشد، نه از حافظهٔ کسی.
            "max_circular": max_circular, "max_circular_reason": _mc["reason"]}


def record_intent(top: list[dict]) -> None:
    """نیتِ سنجش را ثبت کن (لوپ را ببند، غیرِدایره‌ای کن): هر پیشنهادِ صدر چه هدفی و چه
    متریکی را قرار است جابه‌جا کند + baseline. بعداً measure می‌گوید آیا شد.
    هم‌زمان (زیرِ فلگ) ادعای id-کلیددار صادر می‌شود تا با رکوردِ بستارِ measure
    جفت شود — پیش از این، فضای نامِ ادعا و حقیقت disjoint بود (n=0 ابدی)."""
    try:
        base = _baseline_metrics()
        OUTCOMES.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTCOMES, "a", encoding="utf-8") as f:
            for p in top[:3]:
                f.write(json.dumps({
                    "ts": opslib.now_iso(), "id": p.get("id"),
                    "title": p.get("title"), "serves_goal": p.get("serves_goal"),
                    "impact": p.get("impact"), "baseline": base}, ensure_ascii=False) + "\n")
        _emit_intent_claims(top[:3])
    except OSError:
        pass


def _self_monitor_on() -> bool:
    """فلگِ CORTEX_SELF_MONITOR روشن؟ (دقیقاً منطقِ self_model/calibration_probe)."""
    v = str(os.environ.get(SELF_MONITOR_FLAG, "")).strip().lower()
    return v not in ("", "0", "false", "no", "off")


def _emit_intent_claims(top: list[dict]) -> None:
    """برای هر نیتِ ثبت‌شده یک ادعای id-کلیددار به self-claims.jsonl الحاق کن —
    الگوی self_model.emit_self_claims: زیرِ فلگ (خاموش = صفر نوشتن، byte-identical)،
    fail-soft. key = همان idِ نیت؛ confidence = impact/3.0 (هم‌مقیاسِ probe)."""
    if not _self_monitor_on():
        return
    try:
        ts = opslib.now_iso()
        for p in top:
            pid = p.get("id")
            if pid is None or not str(pid).strip():
                continue                      # ادعای بی‌key گرید‌ناپذیر است → صادر نکن
            try:
                conf = max(0.0, min(1.0, float(p.get("impact") or 0.0) / 3.0))
            except (ValueError, TypeError):
                continue
            opslib.append_jsonl(SELF_CLAIMS, {
                "key": str(pid).strip(), "confidence": round(conf, 6), "ts": ts,
                "source": "goal_directed", "schema": "self-claim.v1"})
    except Exception as e:  # noqa: BLE001 — صدورِ ادعا هرگز record_intent را نمی‌کشد
        try:
            opslib.alert([f"goal_directed intent claims failed: {e}"])
        except Exception:  # noqa: BLE001
            pass


def _baseline_metrics() -> dict:
    """متریک‌های برون‌دادیِ واقعی (نه خودمتریک): درآمد، کشف، σ."""
    def _r(p):
        try:
            return json.loads(p.read_text("utf-8")) if p.exists() else {}
        except (OSError, ValueError):
            return {}
    fit = _r(STATE / "fitness-latest.json").get("attribution", {})
    disc = _r(STATE / "discoveries.jsonl") if False else {}
    n_disc = 0
    try:
        dp = STATE / "discoveries.jsonl"
        n_disc = len(dp.read_text("utf-8").splitlines()) if dp.exists() else 0
    except OSError:
        n_disc = 0
    # P0-G3: متریکِ Proposal Router از ORGANISM-STATE.json (نوشتهٔ organism هر tick).
    # فقط اندازه‌گیری — هیچ approve/verdict؛ نبودِ فایل/کلید = صفرها (fail-soft).
    pm = _r(STATE / "ORGANISM-STATE.json").get("proposal_metrics") or {}
    if not isinstance(pm, dict):
        pm = {}
    out = {"confirmed_revenue": fit.get("confirmed", 0),
           "revenue_cells": len(fit.get("revenue_by_cell", {}) or {}),
           "total_discoveries": n_disc,
           "proposals_delivered": int(pm.get("proposals_delivered") or 0),
           "proposal_outcomes": int(pm.get("proposal_outcomes") or 0),
           "proposal_positive": int(pm.get("proposal_positive") or 0),
           "proposal_accept_rate": float(pm.get("proposal_accept_rate") or 0.0),
           "proposal_value_aud": float(pm.get("proposal_value_aud") or 0.0)}
    # Worker D (fake delivery ≠ real delivery): اگر producer شمارِ ارسالِ واقعی را صادقانه
    # گزارش دهد، عبورش بده — ولی هرگز از غیاب جعل نکن (کلیدِ نبوده = ننویس، نه صفرِ ساختگی).
    if "proposals_sent" in pm:
        out["proposals_sent"] = int(pm.get("proposals_sent") or 0)
    return out


def _movement_keys(now: dict, base: dict) -> tuple:
    """کلیدهای مقایسهٔ moved — دو قاعدهٔ صداقت (Worker D):
      (۱) کلیدِ غایب در baseline هرگز حرکت نمی‌سازد — baselineی که متریکی را نسنجیده
          نمی‌تواند شاهدِ رشدِ آن باشد (missing data must not become success).
      (۲) اگر هر دو طرف proposals_sent دارند، «ارسالِ واقعی» جایگزینِ proposals_delivered
          می‌شود — کارتی که send نشده کار نیست (fake delivery != real delivery)."""
    keys = []
    for k in _METRIC_KEYS:
        if k == "proposals_delivered" and "proposals_sent" in now and "proposals_sent" in base:
            k = "proposals_sent"
        if k in now and k in base:
            keys.append(k)
    return tuple(keys)


def _vote_keys(now: dict, base: dict) -> tuple:
    """کلیدهای رأی‌دهندهٔ moved — T2 لایهٔ ۳: با فلگِ صداقت فقط برون‌زاد رأی می‌دهد
    (درون‌زاد لاگ می‌شود ولی رأی نه)؛ فلگ خاموش = همهٔ کلیدها (بایت‌به‌بایتِ قدیم)."""
    keys = _movement_keys(now, base)
    if _honest_outcomes():
        return tuple(k for k in keys if k not in _ENDOGENOUS_KEYS)
    return keys


def _dedupe_intents(intents: list[dict]) -> list[dict]:
    """T2 لایهٔ ۱ (نویسنده): یک id چند بار با baselineهای متفاوت در پنجرهٔ ۲۰تایی
    می‌افتد (هر اجرا یک نیتِ نو append می‌شود) و _close_intents روی همه حلقه می‌زد →
    بیت در همان فراخوان flip می‌شد و دو بستارِ متناقض با یک ts ساخته می‌شد.
    قدیمی‌ترین baseline (اولین دیده‌شده به ترتیبِ فایل) baselineِ واقعی است."""
    seen: dict[str, dict] = {}
    for r in intents:
        rid = str(r.get("id") or "").strip()
        if not rid or rid in seen:
            continue
        seen[rid] = r
    return list(seen.values())


def measure() -> dict:
    """آیا پیشنهادهای اخیر واقعاً متریکی را جابه‌جا کردند؟ (بستنِ لوپ — ضدِ دایره).
    اگر برون‌دادها ثابت مانده‌اند → سیگنالِ «کارِ خودبهبودی به هدف نمی‌رسد».
    بیتِ moved حالا persist هم می‌شود (رکوردِ بستار per-intent) — پیش از این محاسبه
    می‌شد ولی هرگز نوشته نمی‌شد → calibration_probe ساختاراً کور بود (n=0)."""
    now = _baseline_metrics()
    try:
        if not OUTCOMES.exists():
            return {"tracked": 0, "moved": False, "now": now}
        rows = [json.loads(l) for l in OUTCOMES.read_text("utf-8").splitlines()[-20:] if l.strip()]
    except (OSError, ValueError):
        return {"tracked": 0, "moved": False, "now": now}
    # نیت (baseline دارد) از بستار (moved دارد) جدا — فایل حالا هر دو گونه را دارد.
    intents = [r for r in rows if isinstance(r.get("baseline"), dict)]
    if not intents:
        return {"tracked": 0, "moved": False, "now": now}
    oldest = intents[0].get("baseline", {})
    moved = any(now.get(k, 0) > oldest.get(k, 0) for k in _vote_keys(now, oldest))
    _close_intents(intents, rows, now)
    return {"tracked": len(intents), "moved": moved, "now": now, "since": oldest}


def _close_intents(intents: list[dict], rows: list[dict], now: dict) -> None:
    """بستارِ لوپِ واسنجی: برای هر نیتِ ارزیابی‌شده یک رکوردِ حقیقتِ دودویی
    {ts, key, moved} به outcomes.jsonl الحاق کن — دقیقاً شِمایی که
    calibration_probe._load_truth جفت می‌کند (key + فیلدِ دودوییِ moved).
    فقط وقتی می‌نویسد که بیت نسبت به آخرین بستارِ همان key عوض شده باشد
    (رشدِ کران‌دار؛ «تازه‌ترین حقیقت» در probe برنده است). fail-soft."""
    try:
        if _honest_outcomes():                # T2 لایهٔ ۱: تکرارِ متناقض ساختاراً ناممکن
            intents = _dedupe_intents(intents)
        last: dict[str, bool] = {}
        for r in rows:                        # آخرین بستارِ ثبت‌شده per key (به ترتیبِ فایل)
            if "moved" in r and r.get("key"):
                last[str(r["key"])] = bool(r["moved"])
        ts = opslib.now_iso()
        for r in intents:
            rid = r.get("id")
            if rid is None or not str(rid).strip():
                continue                      # نیتِ بی‌id بستار‌پذیر نیست
            rid = str(rid).strip()
            base = r.get("baseline") or {}
            moved_i = any(now.get(k, 0) > base.get(k, 0) for k in _vote_keys(now, base))
            if last.get(rid) == moved_i:
                continue                      # بیت عوض نشده → دوباره‌نویسی نکن
            rec = {"ts": ts, "key": rid, "moved": bool(moved_i),
                   "kind": "closure", "schema": "outcome-closure.v1"}
            if _honest_outcomes():            # T2 لایهٔ ۳: درون‌زاد لاگ می‌شود ولی رأی نه
                endo = {k: {"base": base.get(k, 0), "now": now.get(k, 0)}
                        for k in _movement_keys(now, base) if k in _ENDOGENOUS_KEYS}
                if endo:
                    rec["endogenous_delta"] = endo
                    rec["honest"] = True
            opslib.append_jsonl(OUTCOMES, rec)
            last[rid] = moved_i
    except Exception as e:  # noqa: BLE001 — بستار هرگز measure را نمی‌کشد
        try:
            opslib.alert([f"goal_directed close_intents failed: {e}"])
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    print(json.dumps({"goals": load_goals(), "measure": measure()},
                     ensure_ascii=False, indent=2))
